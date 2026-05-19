import anthropic
import json
import time
import streamlit as st
from io import BytesIO

MODEL_FAST = "claude-haiku-4-5-20251001"

_COSTO_INPUT_HAIKU = 0.80 / 1_000_000
_COSTO_OUTPUT_HAIKU = 4.00 / 1_000_000


EXTRACTION_PROMPT = """Sei un esperto di appalti pubblici italiani (D.Lgs. 36/2023, DM 49/2018, Allegato II.12). Analizza questo Capitolato Speciale d'Appalto (CSA) e restituisci SOLO un oggetto JSON valido con i seguenti campi:

{
  "indirizzo_cantiere": "indirizzo completo del cantiere (via, numero civico se presente)",
  "comune": "nome del comune",
  "provincia": "sigla provincia (es. MI, RM, NA)",
  "regione": "nome della regione",
  "tipo_lavori": "descrizione sintetica della tipologia di lavori",
  "categorie_materiali": ["lista", "materiali", "principali"],
  "lavorazioni_specialistiche": ["lista", "lavorazioni", "specialistiche"],
  "importo_lavori": "importo totale dei lavori se presente, altrimenti null",
  "durata_lavori_giorni": numero intero giorni se presente altrimenti null,
  "stazione_appaltante": "nome della stazione appaltante",
  "cig": "codice CIG di esattamente 10 caratteri alfanumerici (es. 8E33B74813) oppure null se non trovato",
  "cup": "codice CUP di esattamente 15 caratteri alfanumerici (es. J37H21000190004) oppure null se non trovato",
  "categorie_soa": [
    {
      "codice": "OG3",
      "descrizione_categoria": "Strade, autostrade, ponti, viadotti, ferrovie, metropolitane",
      "classifica": "IV",
      "prevalente": true,
      "motivazione": "motivazione sintetica"
    }
  ],
  "sal_intervallo_giorni": intero o null,
  "sal_importo_minimo_euro": float o null,
  "sal_percentuale_minima": float o null,
  "sal_tipo": "tempo|importo|misto",
  "penale_giornaliera_permille": float o null,
  "penale_massima_percentuale": float o null,
  "riserve_iscrizione_giorni": intero o null,
  "riserve_quantificazione_giorni": intero o null,
  "collaudo_giorni": intero o null,
  "importo_oneri_sicurezza": float o null,
  "subappalto_percentuale_massima": percentuale massima subappaltabile come float (es. 30.0) o null se non indicata,
  "subappalto_categorie_vietate": ["lista codici SOA o lavorazioni non subappaltabili"] o lista vuota [],
  "subappalto_autorizzazione_richiesta": true se è richiesta autorizzazione esplicita della SA, false altrimenti,
  "subappalto_qualificazione_richiesta": true se il subappaltatore deve possedere qualificazione SOA, false altrimenti,
  "subaffidamento_percentuale_massima": percentuale massima dell'importo del subappalto subaffidabile come float (es. 20.0) o null se non indicata,
  "subappalto_note": "eventuali condizioni particolari, obblighi di comunicazione o limiti specifici sul subappalto/subaffidamento, oppure null",
  "obblighi_appaltatore": ["Obbligo operativo 1", "Obbligo operativo 2"],
  "tipo_contratto": "A corpo|A misura|A corpo e misura",
  "prezzario_nome": "nome del prezzario adottato oppure null",
  "prezzario_regione": "regione del prezzario oppure null se non specificato",
  "prezzario_anno": "anno di riferimento del prezzario come stringa es. 2023 oppure null",
  "obblighi_stazione_appaltante": ["Obbligo SA 1", "Obbligo SA 2"],
  "checklist_prime_settimane": [
    {"attivita": "Descrizione attivita", "termine_giorni": 1, "priorita": "alta"}
  ],
  "checklist_accettazione_materiali": [
    {"attivita": "Descrizione", "termine_giorni": null, "priorita": "alta"}
  ],
  "checklist_sicurezza": [
    {"attivita": "Descrizione", "termine_giorni": null, "priorita": "alta"}
  ],
  "checklist_assicurative": [
    {"attivita": "Descrizione", "termine_giorni": 10, "priorita": "alta"}
  ],
  "elaborati": [
    {
      "codice": "TAV.01",
      "titolo": "Planimetria generale",
      "categoria": "grafico",
      "descrizione": "descrizione sintetica dell'elaborato"
    }
  ]
}

ISTRUZIONI SPECIFICHE:

categorie_materiali: usa termini come "calcestruzzo", "acciaio", "laterizi", "bitume", "tubazioni", "impianti elettrici", "inerti", etc.

lavorazioni_specialistiche: usa termini come "demolizioni", "fondazioni speciali", "carpenteria metallica", "opere stradali", "impianti meccanici", etc.

categorie_soa: identifica le categorie SOA (OG1-OG13 o OS1-OS35 ex Allegato II.12 D.Lgs.36/2023) pertinenti ai lavori. Classifica per importo: I=fino a €258.228 | II=fino a €516.457 | III=fino a €1.032.913 | IV=fino a €2.582.284 | V=fino a €5.164.569 | VI=fino a €10.329.138 | VII=fino a €15.493.707 | VIII=oltre €15.493.707. Max 5 categorie. prevalente: true solo per la categoria con importo maggiore.

sal_importo_minimo_euro: importo minimo della rata SAL in euro (valore base senza ribasso), se indicato esplicitamente nel CSA. null se non trovato o se è specificato solo come percentuale.

sal_percentuale_minima: percentuale dell'importo contrattuale che costituisce la soglia minima per l'emissione del SAL (es. se il CSA dice "rata non inferiore al 30% dell'importo contrattuale" → 30.0). null se non presente o se l'importo è già espresso in euro.

sal_tipo: "tempo" se solo intervallo giorni, "importo" se solo soglia economica, "misto" se entrambi i criteri sono presenti.

obblighi_appaltatore: 8-15 obblighi operativi principali (adempimenti documentali, polizze, comunicazioni, tempistiche, presenze in cantiere).

obblighi_stazione_appaltante: 4-8 obblighi principali della SA (pagamenti, autorizzazioni, termini di emissione SAL e certificati).

checklist_prime_settimane: 12-15 attivita urgenti nei primi 30 giorni dalla consegna. priorita: "alta" per scadenze entro 10 gg, "media" entro 30 gg.

checklist_accettazione_materiali: 8-12 attività per la corretta accettazione dei materiali in cantiere (verifiche CE/DoP, campionamenti, prove di laboratorio, registrazione lotti, DDT, conformità al capitolato).

checklist_sicurezza: 8-12 attività per la gestione della sicurezza (D.Lgs. 81/2008): notifica preliminare, POS, DPI, formazione lavoratori, coordinamento CSE, registro infortuni, visite mediche, sorveglianza cantiere.

checklist_assicurative: tutte le polizze richieste con massimali e termini in giorni.

cig: il Codice Identificativo Gara ha ESATTAMENTE 10 caratteri alfanumerici. Cercarlo nella prima pagina, nell'intestazione o nel frontespizio del documento. Formato tipico: lettere e cifre miste (es. 8E33B74813). Se non presente o incerto restituire null.

cup: il Codice Unico di Progetto ha ESATTAMENTE 15 caratteri alfanumerici. Formato tipico: inizia con lettera, seguono cifre e lettere (es. J37H21000190004). Cercarlo nella prima pagina o nell'intestazione. Se non presente o incerto restituire null.

subappalto_percentuale_massima: percentuale massima subappaltabile indicata nel CSA (art.119 D.Lgs.36/2023). Il limite legale di default è 30%; se il CSA prevede una percentuale diversa (superiore o inferiore) indicarla. null se non esplicitamente indicata.

subappalto_categorie_vietate: lista delle categorie SOA o lavorazioni per cui il subappalto è esplicitamente vietato (es. categoria prevalente, lavorazioni a carattere speciale). Lista vuota [] se nessun divieto specifico è indicato.

subappalto_autorizzazione_richiesta: true se il CSA richiede autorizzazione preventiva della Stazione Appaltante per ogni subappalto. Di norma è true per gli appalti pubblici (art.119 c.4).

subappalto_qualificazione_richiesta: true se il subappaltatore deve possedere qualificazione SOA nella categoria subappaltata.

subaffidamento_percentuale_massima: percentuale massima dell'importo del singolo subappalto che può essere ulteriormente subaffidato (cosiddetto sub-subappalto o cottimo). null se non indicata.

subappalto_note: eventuali condizioni particolari (es. obbligo di comunicazione nominativi 10 gg prima, limiti sul numero di subappaltatori, obblighi DURC del subappaltatore, clausole antimafia). null se nessuna condizione specifica.

tipo_contratto: "A corpo" se l'appalto prevede un corrispettivo globale forfettario per l'esecuzione dell'opera (art.1 DM 49/2018), "A misura" se il corrispettivo è determinato in base alle quantità effettivamente eseguite (contabilità a misura), "A corpo e misura" se il contratto è misto. Cercare nel CSA le parole chiave "a corpo", "a misura", "forfettario", "quantità", "liste prezzi".

prezzario_nome: nome del prezzario, listino prezzi o tariffa adottata come riferimento per il computo metrico estimativo (es. "Prezziario DEI", "Prezzario Regionale Lombardo", "Prezzario ANAS", "Listino Camera di Commercio", "Prezzario Regionale"). null se non specificato.

prezzario_regione: regione di riferimento del prezzario se esplicitamente indicata nel documento (es. "Lombardia", "Lazio", "Campania"). null se non specificato.

prezzario_anno: anno di riferimento del prezzario come stringa di 4 cifre (es. "2023"). null se non specificato.

elaborati: elenco degli elaborati progettuali citati nel CSA. Cerca nell'indice degli elaborati, nel frontespizio o negli allegati. categorie: "tecnico" (relazioni, computo metrico, elenco prezzi, PSC, cronoprogramma), "grafico" (tavole, planimetrie, sezioni, particolari costruttivi), "amministrativo" (schema contratto, capitolato, disciplinare). Se il CSA non elenca elaborati restituisci lista vuota [].

Restituisci SOLO il JSON valido, senza testo aggiuntivo, senza markdown, senza backtick."""


def conta_pagine_pdf(pdf_bytes: bytes) -> int:
    try:
        from pypdf import PdfReader
        return len(PdfReader(BytesIO(pdf_bytes)).pages)
    except Exception:
        return 0


def stima_token_pdf(pdf_bytes: bytes) -> int:
    try:
        from pypdf import PdfReader
        reader = PdfReader(BytesIO(pdf_bytes))
        testo = " ".join((page.extract_text() or "") for page in reader.pages)
        return max(len(testo) // 4, len(pdf_bytes) // 6)
    except Exception:
        return len(pdf_bytes) // 6


def _ripara_json_troncato(raw: str) -> dict:
    """Tenta di riparare un JSON troncato chiudendo le strutture aperte."""
    stack: list[str] = []
    stack_at_last: list[str] = []
    in_string = False
    i = 0
    last_complete = 0

    while i < len(raw):
        c = raw[i]
        if in_string:
            if c == "\\" and i + 1 < len(raw):
                i += 2
                continue
            if c == '"':
                in_string = False
        else:
            if c == '"':
                in_string = True
            elif c in ("{", "["):
                stack.append(c)
            elif c in ("}", "]"):
                if stack:
                    stack.pop()
                last_complete = i + 1
                stack_at_last = stack.copy()
            elif c == "," and stack:
                last_complete = i
                stack_at_last = stack.copy()
        i += 1

    if not in_string and not stack:
        return json.loads(raw)

    if last_complete == 0:
        raise ValueError("JSON troncato troppo presto per essere riparato.")

    truncated = raw[:last_complete].rstrip().rstrip(",")
    closing = "".join("}" if b == "{" else "]" for b in reversed(stack_at_last))
    repaired = truncated + closing
    return json.loads(repaired)


@st.cache_data(show_spinner=False)
def analyze_csa(testo: str, api_key: str) -> dict:
    """Analisi Haiku sul testo pre-estratto da Smart Extract. Sempre singola chiamata."""
    client = anthropic.Anthropic(api_key=api_key)

    message = client.messages.create(
        model=MODEL_FAST,
        max_tokens=8192,
        timeout=150.0,
        messages=[
            {
                "role": "user",
                "content": f"{EXTRACTION_PROMPT}\n\nTESTO DEL CSA:\n{testo}",
            }
        ],
    )

    raw = message.content[0].text.strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    if message.stop_reason == "max_tokens":
        return _ripara_json_troncato(raw)

    return json.loads(raw)


def estrai_pagine_pdf(pdf_bytes: bytes, da: int, a: int) -> bytes:
    """Estrae l'intervallo di pagine [da, a) dal PDF e restituisce i bytes."""
    from pypdf import PdfReader, PdfWriter
    reader = PdfReader(BytesIO(pdf_bytes))
    writer = PdfWriter()
    for i in range(da, min(a, len(reader.pages))):
        writer.add_page(reader.pages[i])
    buf = BytesIO()
    writer.write(buf)
    return buf.getvalue()


def unisci_analisi(d1: dict, d2: dict) -> dict:
    """Unisce due risultati di analisi CSA. d1 (prime pagine) ha priorità sui campi scalari."""
    _CAMPI_LISTA = {
        "categorie_materiali", "lavorazioni_specialistiche", "categorie_soa",
        "obblighi_appaltatore", "obblighi_stazione_appaltante",
        "checklist_prime_settimane", "checklist_accettazione_materiali",
        "checklist_sicurezza", "checklist_assicurative",
    }
    merged: dict = {}
    for key in set(d1) | set(d2):
        v1, v2 = d1.get(key), d2.get(key)
        if key in _CAMPI_LISTA:
            merged[key] = (v1 or []) + (v2 or [])
        else:
            merged[key] = v1 if v1 is not None else v2
    # Deduplicazione checklist per "attivita"
    for ck in ("checklist_prime_settimane", "checklist_accettazione_materiali",
               "checklist_sicurezza", "checklist_assicurative"):
        seen: set = set()
        merged[ck] = [
            it for it in merged.get(ck, [])
            if it.get("attivita", "") not in seen and not seen.add(it.get("attivita", ""))
        ]
    # Max 5 categorie SOA
    merged["categorie_soa"] = merged.get("categorie_soa", [])[:5]
    return merged


# DEPRECATO — sostituito da Smart Extract
# @st.cache_data(show_spinner=False)
# def analyze_csa_parte(pdf_bytes_parte: bytes, api_key: str) -> dict:
#     return analyze_csa(pdf_bytes_parte, api_key)


# ── Chunked analysis — DEPRECATO: sostituito da Smart Extract ─────────────────

# MAX_CHARS_PER_CHUNK = 100_000  # DEPRECATO

CHUNK_PROMPT_TEMPLATE = (
    "Sei un assistente specializzato in Capitolati Speciali d'Appalto (CSA) italiani "
    "(D.Lgs. 36/2023).\n"
    "Analizza il testo fornito (parte {parte} di {totale}) ed estrai SOLO le informazioni "
    "presenti, senza inventare nulla.\n"
    "Rispondi SOLO con JSON valido, nessun testo aggiuntivo.\n\n"
    "{{\n"
    '  "scadenze": [{{"voce": "...", "giorni": 0, "riferimento_articolo": "..."}}],\n'
    '  "penali": [{{"descrizione": "...", "importo_o_percentuale": "...", '
    '"riferimento_articolo": "..."}}],\n'
    '  "importi": [{{"voce": "...", "importo": "...", "riferimento_articolo": "..."}}],\n'
    '  "obblighi_dt": [{{"obbligo": "...", "riferimento_articolo": "..."}}],\n'
    '  "documenti_richiesti": [{{"documento": "...", "scadenza": "...", '
    '"riferimento_articolo": "..."}}],\n'
    '  "note_importanti": ["..."]\n'
    "}}\n"
    "Se una categoria non ha contenuti in questo testo restituisci lista vuota [].\n"
    "TESTO (parte {parte}/{totale}):\n{chunk}"
)

_SCHEMA_CONSOLIDATION = """{
  "indirizzo_cantiere": "...", "comune": "...", "provincia": "XX", "regione": "...",
  "tipo_lavori": "...", "categorie_materiali": ["..."], "lavorazioni_specialistiche": ["..."],
  "importo_lavori": "€ X.XXX.XXX,00 o null", "durata_lavori_giorni": 180,
  "stazione_appaltante": "...", "cig": "10 char alfanumerici o null", "cup": "15 char o null",
  "categorie_soa": [{"codice":"OG3","descrizione_categoria":"...","classifica":"IV","prevalente":true,"motivazione":"..."}],
  "sal_intervallo_giorni": null, "sal_importo_minimo_euro": null, "sal_percentuale_minima": null, "sal_tipo": "tempo|importo|misto",
  "penale_giornaliera_permille": null, "penale_massima_percentuale": null,
  "riserve_iscrizione_giorni": null, "riserve_quantificazione_giorni": null,
  "collaudo_giorni": null, "importo_oneri_sicurezza": null,
  "subappalto_percentuale_massima": null, "subappalto_categorie_vietate": [],
  "subappalto_autorizzazione_richiesta": true, "subappalto_qualificazione_richiesta": true,
  "subaffidamento_percentuale_massima": null, "subappalto_note": null,
  "obblighi_appaltatore": ["..."], "obblighi_stazione_appaltante": ["..."],
  "tipo_contratto": "A corpo|A misura|A corpo e misura",
  "prezzario_nome": null, "prezzario_regione": null, "prezzario_anno": null,
  "checklist_prime_settimane": [{"attivita":"...","termine_giorni":10,"priorita":"alta"}],
  "checklist_accettazione_materiali": [{"attivita":"...","termine_giorni":null,"priorita":"media"}],
  "checklist_sicurezza": [{"attivita":"...","termine_giorni":null,"priorita":"alta"}],
  "checklist_assicurative": [{"attivita":"...","termine_giorni":10,"priorita":"alta"}],
  "elaborati": [{"codice":"TAV.01","titolo":"...","categoria":"grafico","descrizione":"..."}]
}"""

CONSOLIDATION_PROMPT_TEMPLATE = (
    "Sei un esperto di appalti pubblici italiani (D.Lgs. 36/2023, DM 49/2018, "
    "Allegato II.12).\n"
    "Hai ricevuto {n} analisi parziali dello stesso CSA in formato JSON.\n"
    "Unificale eliminando duplicati. Ordina scadenze per giorni crescenti. "
    "Ordina penali per importo crescente.\n"
    "Rispondi SOLO con JSON valido nel seguente schema csa_data, nessun testo aggiuntivo:\n\n"
    "{schema}\n\n"
    "Per categorie_soa: classifica per importo: I≤€258K | II≤€516K | III≤€1.033K | "
    "IV≤€2.582K | V≤€5.165K | VI≤€10.329K | VII≤€15.494K | VIII>€15.494K. Max 5 categorie.\n"
    "ANALISI PARZIALI:\n{json_parziali}"
)


@st.cache_data(show_spinner=False)
def _estrai_pagine_rilevanti(pdf_bytes: bytes) -> tuple[str, dict]:
    """Estrae solo le pagine rilevanti per il DTC tramite keyword matching.
    Ritorna (testo_filtrato, stats) con n_pagine_totali, n_pagine_estratte,
    pagine_per_categoria. Riduce 374 pagine a ~40-80 pagine rilevanti."""
    import fitz

    KEYWORDS = {
        "penali": [
            "penale", "penali", "art.113", "art. 113",
            "ritardo", "sanzione", "decurtazione",
        ],
        "scadenze": [
            "termine", "giorni naturali", "giorni consecutivi",
            "scadenza", "ultimazione lavori", "consegna dei lavori",
            "entro e non oltre",
        ],
        "sal": [
            "stato avanzamento", "s.a.l.", "sal ",
            "acconto", "certificato di pagamento",
            "rata di acconto", "importo minimo",
        ],
        "obblighi": [
            "obblighi dell'appaltatore", "oneri a carico",
            "direttore tecnico", "direttore di cantiere",
            "responsabilità dell'impresa",
        ],
        "subappalto": [
            "subappalto", "art.119", "art. 119",
            "subappaltatore", "cottimo",
        ],
        "revisione": [
            "revisione prezzi", "art.60", "art. 60",
            "istat", "indice dei prezzi", "compensazione",
        ],
        "garanzie": [
            "cauzione definitiva", "polizza car",
            "polizza rct", "garanzia fideiussoria", "durc",
        ],
        "importi": [
            "importo contrattuale", "importo netto",
            "ribasso", "base d'asta", "somme a disposizione",
        ],
    }

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    n_totale = len(doc)

    pagine_rilevanti: set[int] = set()
    pagine_per_categoria: dict[str, list[int]] = {cat: [] for cat in KEYWORDS}

    for n_pag, pagina in enumerate(doc):
        testo_pag = pagina.get_text().lower()
        for categoria, keywords in KEYWORDS.items():
            if any(kw.lower() in testo_pag for kw in keywords):
                pagine_rilevanti.add(n_pag)
                if n_pag > 0:
                    pagine_rilevanti.add(n_pag - 1)
                if n_pag < n_totale - 1:
                    pagine_rilevanti.add(n_pag + 1)
                pagine_per_categoria[categoria].append(n_pag + 1)

    testo_filtrato = ""
    for n_pag in sorted(pagine_rilevanti):
        testo_filtrato += f"\n\n--- PAGINA {n_pag + 1} ---\n"
        testo_filtrato += doc[n_pag].get_text()

    doc.close()

    stats = {
        "n_pagine_totali": n_totale,
        "n_pagine_estratte": len(pagine_rilevanti),
        "pagine_per_categoria": {
            cat: pags for cat, pags in pagine_per_categoria.items() if pags
        },
    }

    return testo_filtrato, stats


@st.cache_data(show_spinner=False)
def conta_token_api(testo: str, api_key: str) -> int:
    """Conta i token esatti del testo filtrato (Smart Extract) via API count_tokens.
    Fallback a stima locale se l'API non è disponibile."""
    if not api_key:
        return len(testo) // 4
    client = anthropic.Anthropic(api_key=api_key)
    stats = st.session_state.get("_smart_extract_stats", {})
    if stats:
        n_tot = stats.get("n_pagine_totali", 0)
        n_est = stats.get("n_pagine_estratte", 0)
        if n_tot > 0:
            riduzione = 100 - n_est * 100 // n_tot
            st.info(
                f"📄 PDF: {n_tot} pagine totali\n\n"
                f"🎯 Smart Extract: {n_est} pagine rilevanti\n\n"
                f"📉 Riduzione: -{riduzione}% pagine"
            )
        for cat, pags in stats.get("pagine_per_categoria", {}).items():
            if pags:
                st.caption(f"  ✓ {cat}: {len(pags)} pagine")
    try:
        resp = client.beta.messages.count_tokens(
            model=MODEL_FAST,
            messages=[{
                "role": "user",
                "content": f"{EXTRACTION_PROMPT}\n\nTESTO DEL CSA:\n{testo}",
            }],
        )
        return resp.input_tokens
    except Exception:
        return len(testo) // 4


def _estrai_testo_pdf_fallback(pdf_bytes: bytes) -> str:
    """Estrae il testo grezzo dal PDF usando PyMuPDF (metodo base)."""
    import fitz  # PyMuPDF
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pagine = [pagina.get_text() for pagina in doc]
    doc.close()
    return "\n".join(pagine)


def _estrai_testo_pdf_ottimizzato(pdf_bytes: bytes) -> str:
    """Estrae il testo in formato Markdown ottimizzato per LLM via pymupdf4llm.
    Riduce i token del 30-50% su PDF grandi rispetto all'estrazione grezza."""
    import pymupdf4llm
    import fitz
    import tempfile
    import os
    import re
    from collections import Counter

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(pdf_bytes)
        tmp_path = tmp.name

    try:
        testo_md = pymupdf4llm.to_markdown(tmp_path)

        # Rimuovi righe vuote multiple (>2 consecutive)
        testo_md = re.sub(r'\n{3,}', '\n\n', testo_md)
        # Rimuovi numeri di pagina isolati (es. "- 47 -" o "47\n")
        testo_md = re.sub(r'\n\s*-?\s*\d+\s*-?\s*\n', '\n', testo_md)
        # Rimuovi header/footer ripetuti (stringhe identiche > 5 volte)
        righe = testo_md.split('\n')
        freq = Counter(r.strip() for r in righe if len(r.strip()) > 10)
        ripetuti = {r for r, c in freq.items() if c > 5}
        righe_pulite = [r for r in righe if r.strip() not in ripetuti]
        testo_md = '\n'.join(righe_pulite)

        return testo_md
    finally:
        os.unlink(tmp_path)


def _estrai_testo_pdf(pdf_bytes: bytes) -> str:
    """Estrae il testo dal PDF: usa pymupdf4llm se disponibile, altrimenti PyMuPDF grezzo."""
    try:
        return _estrai_testo_pdf_ottimizzato(pdf_bytes)
    except Exception:
        return _estrai_testo_pdf_fallback(pdf_bytes)


def _parse_json_clean(raw: str) -> dict:
    """Rimuove markdown code fence e parsa il JSON."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    return json.loads(raw)


# DEPRECATO — funzioni chunked non più usate con Smart Extract
# def _analizza_chunk(...): ...
# def _consolida_chunks(...): ...
# def analyze_csa_chunked(...): ...
# def _countdown_rate_limit(...): ...
