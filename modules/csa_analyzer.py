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
  "anticipazione_percentuale": percentuale anticipazione sull'importo contrattuale (es. 20.0). null se non indicata esplicitamente (si applica il default 20% Art. 125 D.Lgs. 36/2023),
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
  ],
  "subaffidamenti": {
    "importo_totale": "importo totale subaffidamenti (€) come stringa o numero, null se non presente nel CSA",
    "numero_subaffidatari": 0,
    "lista_subaffidatari": [
      {
        "nome": "nome subaffidatario",
        "importo": "importo subaffidamento come stringa o numero",
        "descrizione_lavori": "descrizione lavori affidati"
      }
    ]
  },
  "ordini_servizio": {
    "numero_totale": 0,
    "lista_ordini": [
      {
        "data": "YYYY-MM-DD",
        "numero": "OS-001/2026",
        "descrizione": "descrizione breve del lavoro",
        "importo": "importo in euro come stringa o null se non indicato"
      }
    ]
  }
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

anticipazione_percentuale: percentuale di anticipazione sull'importo contrattuale netto (al netto del ribasso) prevista dal CSA o dal contratto. Il limite legale è 20% (Art. 125 D.Lgs. 36/2023); alcune SA prevedono percentuali inferiori (es. 10%, 15%). null se non indicata esplicitamente.

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

subaffidamenti: cerca nel CSA i subaffidamenti (sub-subappalti, Art. 122 D.Lgs. 36/2023). Se il CSA menziona subaffidatari o cottimisti: estrai importo_totale e lista_subaffidatari. Se non menzionati: importo_totale = null, numero_subaffidatari = 0, lista_subaffidatari = [].

ordini_servizio: cerca nel testo le espressioni "Ordine di Servizio", "OS n.", "verbale OS", "ordine di servizio n.". Estrai: data emissione (YYYY-MM-DD), numero OS (es. OS-001/2026), breve descrizione, importo se indicato. Se non emessi o non citati nel CSA: numero_totale = 0, lista_ordini = [].

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


def _parse_num_simple(v) -> float:
    if v is None:
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace("€", "").replace(" ", "").replace("\xa0", "")
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except (ValueError, TypeError):
        return 0.0


def _post_processa_csa_data(data: dict) -> dict:
    subaffidamenti_data = data.get("subaffidamenti") or {}
    data["subaffidamenti_importo"] = _parse_num_simple(subaffidamenti_data.get("importo_totale"))
    data["subaffidamenti_numero"] = int(subaffidamenti_data.get("numero_subaffidatari") or 0)

    ordini_data = data.get("ordini_servizio") or {}
    data["ordini_servizio_numero"] = int(ordini_data.get("numero_totale") or 0)
    data["ordini_servizio_lista"] = ordini_data.get("lista_ordini") or []

    return data


def _valida_csa_data(data: dict) -> dict:
    """Valida i dati estratti contro i limiti normativi D.Lgs. 36/2023.
    Aggiunge '_warnings_validazione' con anomalie rilevate e corregge
    automaticamente i valori impossibili."""
    warnings_val = []

    # Subappalto max 30% — Art. 119 D.Lgs. 36/2023
    sub_pct = data.get("subappalto_percentuale_massima")
    if sub_pct is not None:
        try:
            sub_pct = float(sub_pct)
            if sub_pct > 30.0:
                warnings_val.append(
                    f"⚠️ Subappalto {sub_pct}% supera limite legale 30% (Art. 119) — "
                    "verifica il testo del CSA"
                )
            if sub_pct <= 0:
                data["subappalto_percentuale_massima"] = None
                warnings_val.append("⚠️ Subappalto percentuale <= 0 — reimpostato a null")
        except (ValueError, TypeError):
            pass

    # Anticipazione max 20% — Art. 125 D.Lgs. 36/2023
    ant_pct = data.get("anticipazione_percentuale")
    if ant_pct is not None:
        try:
            ant_pct = float(ant_pct)
            if ant_pct > 20.0:
                warnings_val.append(
                    f"⚠️ Anticipazione {ant_pct}% supera limite legale 20% (Art. 125) — "
                    "corretto a 20%"
                )
                data["anticipazione_percentuale"] = 20.0
            elif ant_pct <= 0:
                data["anticipazione_percentuale"] = None
        except (ValueError, TypeError):
            pass

    # Penale giornaliera: range ragionevole 0.1‰–3‰
    penale = data.get("penale_giornaliera_permille")
    if penale is not None:
        try:
            penale = float(penale)
            if penale > 3.0:
                warnings_val.append(
                    f"⚠️ Penale giornaliera {penale}‰ inusuale (range tipico 0.3–1‰) — "
                    "verifica manualmente"
                )
            if penale <= 0:
                data["penale_giornaliera_permille"] = None
        except (ValueError, TypeError):
            pass

    # Penale massima: tipicamente 10% — Art. 113 D.Lgs. 36/2023
    penale_max = data.get("penale_massima_percentuale")
    if penale_max is not None:
        try:
            if float(penale_max) > 10.0:
                warnings_val.append(
                    f"⚠️ Penale massima {penale_max}% supera soglia tipica 10% (Art. 113) — "
                    "verifica il testo del CSA"
                )
        except (ValueError, TypeError):
            pass

    # Durata lavori: range ragionevole 10–1500 giorni
    durata = data.get("durata_lavori_giorni")
    if durata is not None:
        try:
            durata = int(durata)
            if durata < 10:
                warnings_val.append(
                    f"⚠️ Durata lavori {durata} giorni sembra troppo breve — "
                    "probabile errore di estrazione"
                )
                data["durata_lavori_giorni"] = None
            elif durata > 1500:
                warnings_val.append(
                    f"⚠️ Durata lavori {durata} giorni sembra eccessiva — "
                    "verifica manualmente"
                )
        except (ValueError, TypeError):
            pass

    # Riserve iscrizione: tipicamente 15 gg — Art. 121 D.Lgs. 36/2023
    ris_isc = data.get("riserve_iscrizione_giorni")
    if ris_isc is not None:
        try:
            if int(ris_isc) > 30:
                warnings_val.append(
                    f"⚠️ Riserve iscrizione {ris_isc}gg supera termine tipico 15gg — "
                    "verifica Art. 121 D.Lgs. 36/2023"
                )
        except (ValueError, TypeError):
            pass

    # CIG: esattamente 10 caratteri alfanumerici
    cig = data.get("cig")
    if cig and str(cig).strip() not in ("—", "null", "None", ""):
        cig_clean = str(cig).strip().upper()
        if len(cig_clean) != 10 or not cig_clean.isalnum():
            warnings_val.append(
                f"⚠️ CIG '{cig}' non ha il formato corretto (10 caratteri alfanumerici) — "
                "verifica manualmente"
            )
            data["cig"] = None

    # CUP: esattamente 15 caratteri alfanumerici
    cup = data.get("cup")
    if cup and str(cup).strip() not in ("—", "null", "None", ""):
        cup_clean = str(cup).strip().upper()
        if len(cup_clean) != 15 or not cup_clean.isalnum():
            warnings_val.append(
                f"⚠️ CUP '{cup}' non ha il formato corretto (15 caratteri alfanumerici) — "
                "verifica manualmente"
            )
            data["cup"] = None

    # Importo lavori: deve essere > 0
    importo_raw = data.get("importo_lavori")
    if importo_raw is not None:
        val_imp = _parse_num_simple(importo_raw)
        if val_imp <= 0:
            warnings_val.append("⚠️ Importo lavori <= 0 — probabile errore di estrazione")
            data["importo_lavori"] = None

    # SAL tipo coerente con i valori numerici
    sal_tipo = data.get("sal_tipo")
    sal_gg = data.get("sal_intervallo_giorni")
    sal_imp = data.get("sal_importo_minimo_euro")
    sal_pct = data.get("sal_percentuale_minima")
    if sal_tipo == "tempo" and not sal_gg:
        warnings_val.append("⚠️ SAL tipo 'tempo' ma sal_intervallo_giorni è null — rimosso tipo")
        data["sal_tipo"] = None
    if sal_tipo == "importo" and not sal_imp and not sal_pct:
        warnings_val.append("⚠️ SAL tipo 'importo' ma importo/percentuale null — rimosso tipo")
        data["sal_tipo"] = None

    data["_warnings_validazione"] = warnings_val
    data["_n_warnings"] = len(warnings_val)
    return data


def _calcola_confidence(data: dict) -> dict:
    """Calcola un punteggio di confidenza 0–100 per ogni campo critico.
    100 = estratto senza anomalie, 0 = non estratto."""
    campi_critici = {
        "importo_lavori":                "💰 Importo lavori",
        "durata_lavori_giorni":          "📅 Durata lavori",
        "stazione_appaltante":           "🏛️ Stazione appaltante",
        "tipo_lavori":                   "🏗️ Tipo lavori",
        "sal_tipo":                      "📊 SAL tipo",
        "penale_giornaliera_permille":   "⚠️ Penale giornaliera",
        "penale_massima_percentuale":    "⚠️ Penale massima",
        "subappalto_percentuale_massima": "🤝 Subappalto %",
        "cig":                           "🔑 CIG",
        "cup":                           "🔑 CUP",
        "anticipazione_percentuale":     "💶 Anticipazione %",
        "tipo_contratto":                "📋 Tipo contratto",
        "categorie_soa":                 "🏆 Categorie SOA",
    }

    warnings_set = set()
    for w in data.get("_warnings_validazione", []):
        for campo in campi_critici:
            if campo.replace("_", " ") in w.lower() or campo in w.lower():
                warnings_set.add(campo)

    confidence = {}
    score_totale = 0

    for campo, label in campi_critici.items():
        valore = data.get(campo)
        vuoto = (
            valore is None
            or valore == ""
            or valore == "—"
            or (isinstance(valore, list) and len(valore) == 0)
        )
        if vuoto:
            score = 0
        elif campo in warnings_set:
            score = 40
        else:
            score = 90
        confidence[campo] = {"label": label, "score": score, "valore": valore}
        score_totale += score

    score_medio = score_totale // len(campi_critici)
    data["_confidence"] = confidence
    data["_confidence_score"] = score_medio
    return data


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


def _chiama_api_con_retry(client, max_retry: int = 5, **kwargs):
    """Chiama client.messages.create con retry automatico per errori 529 e rate limit.
    Usa exponential backoff. Dopo 3 tentativi falliti per overload prova con Haiku."""
    for tentativo in range(max_retry):
        try:
            return client.messages.create(**kwargs)
        except anthropic.APIStatusError as e:
            if e.status_code == 529:
                attesa = (2 ** tentativo) + 1
                if tentativo >= 2:
                    kwargs["model"] = "claude-haiku-4-5-20251001"
                    st.warning("⚠️ Fallback su Haiku per ridurre carico...")
                st.warning(
                    f"⏳ API sovraccarica, riprovo tra {attesa}s "
                    f"(tentativo {tentativo + 1}/{max_retry})..."
                )
                time.sleep(attesa)
                continue
            elif e.status_code == 400 and "too long" in str(e).lower():
                raise
            raise
        except anthropic.RateLimitError:
            attesa = (2 ** tentativo) + 1
            st.warning(
                f"⏳ Rate limit, riprovo tra {attesa}s "
                f"(tentativo {tentativo + 1}/{max_retry})..."
            )
            time.sleep(attesa)
            continue
    raise Exception(
        "API Anthropic non disponibile dopo 5 tentativi. "
        "Riprova tra qualche minuto."
    )


@st.cache_data(show_spinner=False)
def analyze_csa(testo: str, api_key: str) -> dict:
    """Analisi CSA con chunking automatico se testo supera 160.000 token stimati.
    Stima token: len(testo) / 4 (approssimazione conservativa)."""
    MAX_TOKEN_SICURO = 160_000
    stima_token = len(testo) // 4
    if stima_token <= MAX_TOKEN_SICURO:
        return _analyze_csa_singolo(testo, api_key)
    else:
        return _analyze_csa_chunked(testo, api_key)


def _analyze_csa_singolo(testo: str, api_key: str) -> dict:
    """Singola chiamata API con retry per overload."""
    client = anthropic.Anthropic(api_key=api_key)
    message = _chiama_api_con_retry(
        client,
        model=MODEL_FAST,
        max_tokens=8192,
        timeout=150.0,
        messages=[{
            "role": "user",
            "content": f"{EXTRACTION_PROMPT}\n\nTESTO DEL CSA:\n{testo}",
        }],
    )
    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    if message.stop_reason == "max_tokens":
        result = _post_processa_csa_data(_ripara_json_troncato(raw))
    else:
        result = _post_processa_csa_data(json.loads(raw))
    result = _valida_csa_data(result)
    result = _calcola_confidence(result)
    return result


def _analyze_csa_chunked(testo: str, api_key: str) -> dict:
    """Divide il testo in chunk da ~120.000 token stimati,
    analizza ogni chunk separatamente, poi consolida con LLM."""
    import math
    client = anthropic.Anthropic(api_key=api_key)

    CHARS_PER_CHUNK = 120_000 * 4  # ~120k token stimati
    n_chunks = math.ceil(len(testo) / CHARS_PER_CHUNK)

    st.info(
        f"📄 Testo CSA lungo ({len(testo) // 4:,} token stimati) — "
        f"analisi in {n_chunks} parti..."
    )

    risultati_parziali = []
    for i in range(n_chunks):
        start = i * CHARS_PER_CHUNK
        end = min((i + 1) * CHARS_PER_CHUNK, len(testo))
        chunk = testo[start:end]

        st.caption(f"  🔄 Analisi parte {i + 1}/{n_chunks}...")

        prompt_chunk = CHUNK_PROMPT_TEMPLATE.format(
            parte=i + 1,
            totale=n_chunks,
            chunk=chunk,
        )

        message = _chiama_api_con_retry(
            client,
            model=MODEL_FAST,
            max_tokens=8192,
            timeout=150.0,
            messages=[{"role": "user", "content": prompt_chunk}],
        )

        raw = message.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        try:
            if message.stop_reason == "max_tokens":
                risultati_parziali.append(
                    _post_processa_csa_data(_ripara_json_troncato(raw))
                )
            else:
                risultati_parziali.append(
                    _post_processa_csa_data(json.loads(raw))
                )
        except Exception:
            continue

    if not risultati_parziali:
        raise ValueError("Nessun chunk analizzato correttamente.")

    if len(risultati_parziali) == 1:
        result = _valida_csa_data(risultati_parziali[0])
        result = _calcola_confidence(result)
        return result

    st.caption("  🔗 Consolidamento risultati...")
    json_parziali = "\n\n".join(
        f"--- PARTE {i + 1} ---\n{json.dumps(r, ensure_ascii=False, indent=2)}"
        for i, r in enumerate(risultati_parziali)
    )
    prompt_consolidation = CONSOLIDATION_PROMPT_TEMPLATE.format(
        n=len(risultati_parziali),
        schema=_SCHEMA_CONSOLIDATION,
        json_parziali=json_parziali,
    )
    message = _chiama_api_con_retry(
        client,
        model=MODEL_FAST,
        max_tokens=8192,
        timeout=150.0,
        messages=[{"role": "user", "content": prompt_consolidation}],
    )
    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    try:
        result = _post_processa_csa_data(json.loads(raw))
    except Exception:
        result = risultati_parziali[0]
        for r in risultati_parziali[1:]:
            result = unisci_analisi(result, r)
    result = _valida_csa_data(result)
    result = _calcola_confidence(result)
    return result


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


def valida_subaffidamenti(csa_data: dict) -> dict:
    """Valida subaffidamenti rispetto al limite del 10% (Art. 122 D.Lgs. 36/2023)."""
    importo_netto = _parse_num_simple(csa_data.get("importo_netto")) or _parse_num_simple(csa_data.get("importo_lavori"))
    importo_subaffid = _parse_num_simple(csa_data.get("subaffidamenti_importo"))
    limite_10 = importo_netto * 0.10

    if importo_netto <= 0:
        return {
            "is_valid": True,
            "importo": importo_subaffid,
            "limite": 0.0,
            "superato": 0.0,
            "percentuale": 0.0,
            "messaggio": "⚠️ Importo netto non disponibile",
        }

    return {
        "is_valid": importo_subaffid <= limite_10,
        "importo": importo_subaffid,
        "limite": limite_10,
        "superato": max(0.0, importo_subaffid - limite_10),
        "percentuale": importo_subaffid / importo_netto * 100,
        "messaggio": (
            f"✅ Entro limite ({importo_subaffid / importo_netto * 100:.1f}%)"
            if importo_subaffid <= limite_10
            else f"❌ SUPERA limite di € {importo_subaffid - limite_10:,.0f}"
        ),
    }


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
  "elaborati": [{"codice":"TAV.01","titolo":"...","categoria":"grafico","descrizione":"..."}],
  "subaffidamenti": {"importo_totale": null, "numero_subaffidatari": 0, "lista_subaffidatari": []},
  "ordini_servizio": {"numero_totale": 0, "lista_ordini": []}
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
            "penalità", "mora", "inadempienza",
        ],
        "scadenze": [
            "termine", "giorni naturali", "giorni consecutivi",
            "scadenza", "ultimazione lavori", "consegna dei lavori",
            "entro e non oltre", "giorni lavorativi", "giorni solari",
            "ultimazione", "consegna cantiere",
        ],
        "sal": [
            "stato avanzamento", "s.a.l.", "sal ",
            "acconto", "certificato di pagamento",
            "rata di acconto", "importo minimo",
            "avanzamento lavori", "contabilità", "libretto misure",
            "stato avanzamento lavori",
        ],
        "obblighi": [
            "obblighi dell'appaltatore", "oneri a carico",
            "direttore tecnico", "direttore di cantiere",
            "responsabilità dell'impresa", "obblighi dell'impresa",
            "oneri dell'appaltatore", "adempimenti",
        ],
        "subappalto": [
            "subappalto", "art.119", "art. 119",
            "subappaltatore", "cottimo", "subaffidamento",
            "art.122", "art. 122", "sub-appalto",
        ],
        "revisione": [
            "revisione prezzi", "art.60", "art. 60",
            "istat", "indice dei prezzi", "compensazione",
            "adeguamento prezzi", "revisione del corrispettivo",
            "aggiornamento prezzi",
        ],
        "garanzie": [
            "cauzione definitiva", "polizza car",
            "polizza rct", "garanzia fideiussoria", "durc",
            "assicurazione", "polizza", "fideiussione",
            "garanzia definitiva", "polizza infortuni",
        ],
        "importi": [
            "importo contrattuale", "importo netto",
            "ribasso", "base d'asta", "somme a disposizione",
            "importo lavori", "valore appalto", "corrispettivo",
            "importo totale", "quadro economico",
        ],
        "anticipazione": [
            "anticipazione", "art.125", "art. 125",
            "anticipazione del prezzo", "anticipo contrattuale",
            "anticipazione contrattuale",
        ],
        "riserve": [
            "riserve", "art.120", "art. 121", "art. 120",
            "riserva", "contestazione", "pretese dell'appaltatore",
            "registro di contabilità", "atti contabili",
        ],
        "varianti": [
            "variante", "varianti", "art.120",
            "modifica contrattuale", "perizia di variante",
            "lavori aggiuntivi", "opere aggiuntive",
        ],
        "collaudo": [
            "collaudo", "certificato di regolare esecuzione",
            "cre", "commissione collaudo", "art.116",
            "allegato ii.14", "verifica di conformità",
        ],
        "cam": [
            "criteri ambientali minimi", "cam",
            "dm 23/06/2022", "acquisti verdi",
            "gpp", "appalti verdi", "ambientali minimi",
        ],
        "tracciabilita": [
            "tracciabilità", "cig", "cup",
            "l. 136/2010", "legge 136",
            "codice identificativo", "codice unico",
            "flussi finanziari",
        ],
        "sicurezza": [
            "piano di sicurezza", "psc", "pos",
            "coordinatore sicurezza", "d.lgs. 81",
            "dlgs 81", "oneri sicurezza", "cse", "csp",
            "notifica preliminare",
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
