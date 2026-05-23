# CLAUDE.md

Guida per Claude Code (claude.ai/code) su questo repository.
Lingua di sviluppo: tutto il codice, la UI, i prompt e gli output sono in **italiano**.

---

## Obiettivo del progetto

Strumento web (Streamlit) per il **Direttore Tecnico di Cantiere (DTC)**, dipendente
dell'impresa appaltatrice, che gestisce appalti pubblici italiani regolati da
**D.Lgs. 36/2023** e **DM 49/2018**.

---

## 📚 Quadro Normativo di Riferimento

### 🏛️ APPALTI PUBBLICI — PRIMARIE
- **D.Lgs. 36/2023** + correttivo **D.Lgs. 209/2024** — Codice dei Contratti Pubblici (vigente dal 01/07/2023, aggiornato 31/12/2024)
- **DM 49/2018** — Direzione Lavori, contabilità, SAL, collaudo, riserve
- **Allegato II.12 D.Lgs. 36/2023** — Norme tecniche esecuzione contratti
- **L. 136/2010** — Tracciabilità flussi finanziari (CIG obbligatorio)

### 📋 ARTICOLI CHIAVE D.LGS. 36/2023
- **Art. 60** — Revisione prezzi (franchigia 5%, clausole revisionali)
- **Art. 113** — Penali per ritardo (‰ giornaliero, cap massimo)
- **Art. 119** — Subappalto (limite 30% importo contrattuale)
- **Art. 120** — Varianti in corso d'opera e riserve
- **Art. 121** — Riserve: iscrizione tempestiva, esplicitazione 15gg, risposta DL 30gg
- **Art. 122** — Subaffidamenti (limite 10% importo contrattuale)
- **Art. 125** — Anticipazione contrattuale (max 20%, recupero proporzionale su ogni SAL)

### 🦺 SICUREZZA SUL LAVORO
- **D.Lgs. 81/2008** (TUSL) — Testo Unico Sicurezza, Titolo IV Cantieri (Artt. 88-104)
- **D.Lgs. 106/2009** — Correttivo TUSL
- **DPR 222/2003** — Contenuti minimi PSC
- **Art. 89 D.Lgs. 81/2008** — Definizioni: CSP, CSE, Responsabile Lavori
- **Art. 92 D.Lgs. 81/2008** — Obblighi coordinatore sicurezza in esecuzione
- **Art. 97 D.Lgs. 81/2008** — Obblighi datore lavoro impresa affidataria (DTC)

### 🌿 CRITERI AMBIENTALI MINIMI (CAM)
- **DM 23/06/2022** — CAM Edilizia (prodotti, materiali, requisiti ambientali)
- Applicazione obbligatoria negli appalti pubblici (Art. 57 D.Lgs. 36/2023)
- Schede accettazione: spunta CAM obbligatoria per materiali soggetti

### 🏗️ NORME TECNICHE COSTRUZIONI
- **DM 17/01/2018** (NTC 2018) — Norme Tecniche Costruzioni
- **Circ. MIT 21/01/2019 n.7** — Istruzioni applicazione NTC 2018
- **DPR 380/2001** — Testo Unico Edilizia

### 💰 CONTABILITÀ LAVORI (DM 49/2018)
- **Art. 14 DM 49/2018** — Registro di contabilità
- **Art. 15 DM 49/2018** — Libretto delle misure
- **Art. 20 DM 49/2018** — SAL: cadenza e contenuti minimi
- **Art. 23 DM 49/2018** — Conto finale lavori
- **Art. 25 DM 49/2018** — Certificato di regolare esecuzione

### 🔥 ANTINCENDIO E IMPIANTI
- **DPR 151/2011** — Regolamento prevenzione incendi
- **DM 3/8/2015** — Codice Prevenzione Incendi (CPI)
- **DM 37/2008** — Impianti tecnologici negli edifici

### 🌍 AMBIENTE
- **D.Lgs. 152/2006** (Codice Ambiente) — Rifiuti da C&D
- **DM 69/2018** — End of Waste terre e rocce da scavo

### 🛡️ ANTIMAFIA E TRASPARENZA
- **D.Lgs. 159/2011** — Codice Antimafia (DURC, SOA, white list)
- **D.Lgs. 33/2013** — Trasparenza PA
- **L. 136/2010** — Tracciabilità flussi (CIG su ogni pagamento)

---

## 🤖 Skill Normative Claude Code

Le seguenti skill sono installate in `.claude/skills/` (progetto) e `~/.claude/skills/` (globale):

| Skill | Norma | Comando |
|-------|-------|---------|
| codice-appalti | D.Lgs. 36/2023 + correttivo 2024 | `/codice-appalti` |
| dm49-direzione-lavori | DM 49/2018 | `/dm49-direzione-lavori` |
| sicurezza-cantieri | D.Lgs. 81/2008 Titolo IV | `/sicurezza-cantieri` |
| tracciabilita-cig | L. 136/2010 | `/tracciabilita-cig` |
| book-to-skill | Converte PDF normativi in skill | `/book-to-skill ~/Downloads/norma.pdf nome` |

---

## ⚙️ Regole per Claude Code — Conformità Normativa

Quando scrivi o modifichi codice per STRUMENTODT:

1. **Cita la norma nei commenti** quando hardcodi un limite legale (es. `# Art. 125 D.Lgs. 36/2023`)
2. **Limiti numerici con fonte normativa**:
   - Subappalto: max **30%** importo netto (Art. 119 D.Lgs. 36/2023)
   - Subaffidamenti: max **10%** importo del singolo subappalto (Art. 122 D.Lgs. 36/2023)
   - Anticipazione: max **20%** importo contrattuale netto (Art. 125 D.Lgs. 36/2023)
   - Riserve — iscrizione: **15 giorni** dall'evento generatore (Art. 121 D.Lgs. 36/2023)
   - Riserve — esplicitazione: **15 giorni** dalla firma atto contabile (Art. 121 D.Lgs. 36/2023)
   - Riserve — risposta DL: **30 giorni** dall'esplicitazione (Art. 121 D.Lgs. 36/2023)
   - Penale massima: cap definito nel CSA, tipicamente **10%** importo netto (Art. 113 D.Lgs. 36/2023)
   - Revisione prezzi — franchigia: **5%** (Art. 60 D.Lgs. 36/2023; correttivo 2024: 3% per alcune categorie)
   - Collaudo/CRE: entro **6 mesi** dall'ultimazione (Allegato II.14 D.Lgs. 36/2023)
   - Pagamento SAL: entro **30 giorni** dal certificato di pagamento (Art. 108 D.Lgs. 36/2023)
3. **Prima di ogni nuova funzionalità**: verifica la conformità normativa usando le skill `/codice-appalti` o `/dm49-direzione-lavori`
4. **Valori estratti dal CSA** hanno sempre precedenza sui default normativi (il CSA può restringere ma non ampliare i limiti di legge)

---

## Stato attuale — Sessione 2026-05-09 serale

### ✅ Completate in questa sessione (serale)

| Feature | Dettaglio |
|---------|-----------|
| **Fix PDF > 100 pagine** | Rimosso invio base64 all'API; tutte le funzioni usano `_estrai_testo_pdf()` (PyMuPDF) — risolve `A maximum of 100 PDF pages may be provided` |
| **Chunked analysis** | `analyze_csa_chunked()` per PDF > 150K token: N chunk da ~80K token con CHUNK_PROMPT + consolidamento finale; risolve `prompt is too long: 215241 tokens > 200000` |
| **Token counting pre-analisi** | `conta_token_api()` (@st.cache_data) con `client.beta.messages.count_tokens()`; stima costo e n. chunk in sidebar prima dell'analisi |
| **Tab 📄 Documenti ridisegnato** | 3 sezioni sempre visibili (Grafici/Tecnici/Amministrativi); documenti come card riga con badge, varianti con badge rosso, upload per card, ricerca testo PyMuPDF; form "➕ Aggiungi documento" per categoria; stato in `doc_elaborati` (dict per categoria) |
| **🔄 Varianti e Proroghe Calendario** | Nuova sezione dopo Sospensioni: lista varianti/proroghe con tipo (Variante/Proroga/Sospensione tecnica), descrizione, data approvazione, giorni (±); preview live nuova scadenza nel form; propagazione `durata + giorni_varianti` a `calcola_calendario()`, Dashboard, Export Excel; persistito in `_varianti_proroghe` nel JSON |

### ⏸️ In sospeso — prompt pronti, non ancora inviati

1. **Data consegna cantiere globale in sidebar** + propagazione a tutti i tab
2. **SAL emessi nel Calendario**: importo ↔ percentuale
3. **Doppio avanzamento affiancato**: lavori % vs temporale %
4. **Anticipazione contrattuale 20%**

### ▶️ Prossimo step (prima cosa alla prossima sessione)

1. Inviare il prompt "data consegna + SAL + avanzamento" già pronto
2. Poi struttura cartelle automatica per ogni analisi CSA

---

## Stato base — Sessione 2026-05-09 (mattina/pomeriggio)

> **Decisione architetturale:** app semplificata — una sola analisi Haiku, tutto operativo, niente materia legale.
> Rimossi: tab "⚖️ Analisi Contrattuale", tab "🔍 Interpretazione", opzione "analisi parziale", modalità economica, uso di Sonnet.
> `csa_data` ora contiene tutti i campi estratti (era diviso tra `csa_data` + `contract_details`).

### Funzionalità implementate e operative

| # | Tab | Descrizione | Modulo |
|---|-----|-------------|--------|
| 1 | 🏠 Dashboard | Metriche chiave (importo, durata, SAL, avanzamento temporale) + 2a fila KPI (subappalti %, riserve, NC, SAL contabilità) + azioni rapide | `app.py` |
| 2 | 📋 Sintesi CSA | Dati generali + tipo contratto + prezzario + categorie SOA + parametri contrattuali chiave + obblighi parti | `csa_analyzer.py` |
| 3 | ✅ Checklist | **Sistema gestione attività**: 4 stati (Da fare/In corso/Completato/In ritardo), referente per voce, upload documenti con 👁️ Visualizza + ⬇️ Scarica, salvataggio JSON | `app.py`, `doc_viewer.py` |
| 4 | 📄 Documenti | **Repository digitale elaborati**: elenco estratto dal CSA (grafico/tecnico/amministrativo), upload PDF per codice, ricerca testo nel PDF (PyMuPDF); **Varianti approvate** con data e note; **✍️ Redazione** (expander collassato): Riserva art.120, Verbale Consegna, Proroga, Contestazione | `contract_analyzer.py`, `app.py` |
| 5 | 📅 Calendario | **3 modalità SAL** (tempo/importo/misto) + sospensioni + **ribasso d'asta** applicato; `data_consegna` condivisa con Checklist | `calendar_manager.py` |
| 6 | 💰 Penali & Revisione | Calcolo penali + revisione prezzi art.60 — **importo netto dopo ribasso come default** | `penalties.py` |
| 7 | 🏢 Operatori Economici | Gerarchia **L0/L1/L2**: Appaltatore principale (DURC 120gg auto-scadenza, Visura, Polizza CAR/RCT) → Subappaltatori (30% art.119) → Subaffidatari; semaforo DURC verde/giallo/rosso | `operatori_tab.py` |
| 8 | 📚 Registri | **5 sezioni**: Riserve (art.120), Verbali (consegna/sosp./ripresa/collaudo), Non Conformità, Ordini di Servizio, Contabilità SAL | `registri_tab.py` |
| 9 | 🗺️ Mappa Fornitori | Geocoding Nominatim + ricerca Overpass API + mappa Folium interattiva | `geocoder.py`, `supplier_search.py`, `map_renderer.py` |
| 10 | 📋 Log Attività | Log cronologico di tutte le operazioni, filtri tab/testo, export PDF, cancellazione | `log_manager.py` |
| 11 | ❓ Guida | Documentazione integrata: introduzione, guida passo per passo, FAQ, note legali | `app.py` |
| — | 🎮 Demo | Modalità demo senza API Key (dati fittizi cantiere stradale Bergamo BG) | `demo_data.py` |

### Funzionalità globali (sidebar)

| Funzionalità | Dove | Dettaglio |
|---|---|---|
| **Ribasso d'asta** | Sidebar — sempre visibile | Percentuale ribasso → calcola importo netto; propaga a Calendario, Penali, Revisione prezzi; **salvato nel JSON** e ripristinato al caricamento analisi |
| **Export Excel multi-foglio** | Sidebar — sezione Esporta | 4 fogli: Sintesi CSA+SOA, Scadenze+Obblighi, Checklist, Calendario — via `openpyxl` |
| **Notifiche email scadenze** | Sidebar — expander | SMTP/STARTTLS (Gmail/Outlook); invia HTML con scadenze critiche entro N giorni via `smtplib` |
| **Export PDF calendario** | Tab Calendario | Tabella eventi con colori passato/futuro/critico via `fpdf2` + font DejaVu Unicode |
| **📂 Analisi salvate** | Sidebar — expander sempre visibile | Elenco JSON in `results/`; carica senza rifare analisi API; elimina con 🗑️; badge ✅ sull'analisi attiva |

### Struttura file attuale

```
claudeai/
├── CLAUDE.md
├── app.py                      # App principale Streamlit (2.667 righe)
├── requirements.txt
├── fonts/
│   ├── DejaVuSans.ttf          # Font Unicode per PDF (scaricato da dejavu-fonts 2.37)
│   └── DejaVuSans-Bold.ttf
├── results/                    # JSON analisi salvate (creata automaticamente al primo salvataggio)
│   └── documenti/              # File allegati caricati nelle checklist
└── modules/
    ├── __init__.py
    ├── csa_analyzer.py         # Analisi Haiku: estrae tutti i campi + elaborati; chunked per PDF > 150K token (~420 righe)
    ├── contract_analyzer.py    # Solo redazione documenti: generate_document() + _DOCUMENT_PROMPTS (127 righe)
    ├── calendar_manager.py     # Calendario: 3 modalità SAL + sospensioni (221 righe)
    ├── penalties.py            # Calcolo penali + revisione prezzi art.60 (86 righe)
    ├── demo_data.py            # Dati demo unificati in DEMO_CSA_DATA (include ex contract_details) (442 righe)
    ├── geocoder.py             # Nominatim geocoding (33 righe)
    ├── supplier_search.py      # Overpass API + categorie OSM (172 righe)
    ├── map_renderer.py         # Mappa Folium (73 righe)
    ├── log_manager.py          # Log attività: aggiungi_log() + render_log_tab() + export PDF log (278 righe)
    ├── operatori_tab.py        # Operatori Economici L0/L1/L2: render_operatori_tab() + render_durc_semaphore() (725 righe)
    ├── registri_tab.py         # Registri ufficiali: Riserve, Verbali, NC, OS, Contabilità SAL (1.289 righe)
    └── doc_viewer.py           # render_doc_buttons(): PDF blob URL, immagini thumbnail, Office download (137 righe)
```

---

## Architettura attuale

```
[PDF CSA] → _estrai_pagine_rilevanti() [@cache_data] → testo filtrato + stats
testo filtrato → analyze_csa() [@cache_data, Haiku] → csa_data (dict)
csa_data → calendar_manager (SAL 3 modi), penalties (penali+art.60), contract_analyzer (doc generation), operatori_tab, registri_tab
geocoder (Nominatim) → supplier_search (Overpass API) → map_renderer (Folium) — tab Mappa Fornitori
doc_viewer.render_doc_buttons(path, key) → PDF blob URL | immagini thumbnail | Office download — usato da checklist, operatori, registri
API: sempre singola chiamata Haiku (Smart Extract garantisce < 150k token)
```

**Chiamate Claude API:**
- **Smart Extract** → `_estrai_pagine_rilevanti(pdf_bytes)`: PyMuPDF filtra pagine per keyword (penali/scadenze/SAL/obblighi/subappalto/revisione/garanzie/importi) + contesto ±1 pagina → riduce 374 pag a ~40-80 pag → sempre < 150k token
- **Singola chiamata Haiku** → `analyze_csa(testo, api_key)`: riceve testo pre-filtrato, max_tokens=8192; `analyze_csa_chunked()` **deprecata e non più usata**
- `generate_document()` — on-demand; Haiku; genera lettere/verbali formali (riserva, verbale consegna, proroga, contestazione)
- **Nessun PDF base64 mai inviato all'API** — solo testo estratto da PyMuPDF

**Rimossi/Deprecati:**
- `analyze_contract_details()` — eliminato; i suoi campi ora estratti da `analyze_csa()`
- `interpret_clause()` — eliminato (materia legale rimossa dall'app)
- `analyze_csa_chunked()` — **deprecata** (sostituita da Smart Extract); codice commentato in `csa_analyzer.py`
- Uso di `claude-sonnet-4-6` — app usa solo `claude-haiku-4-5-20251001`

---

## Tech Stack

| Componente | Tecnologia |
|---|---|
| UI | Streamlit ≥ 1.35 |
| Analisi CSA completa + documenti | Claude API `claude-haiku-4-5-20251001` **unico modello** (costo < $0.05/CSA) |
| Export PDF | `fpdf2` ≥ 2.7 + font DejaVu Unicode |
| Export Excel | `openpyxl` ≥ 3.1 |
| Notifiche email | `smtplib` stdlib (STARTTLS, porta 587) |
| Geocoding | Nominatim (OSM, gratuito) |
| Ricerca fornitori | Overpass API (OSM, gratuito) |
| Mappa | Folium + streamlit-folium |
| Calcoli puri | Python stdlib (datetime, math, dataclasses) |
| Dati tabellari | pandas ≥ 2.0 |

**Nessuna dipendenza a pagamento** oltre a Claude API.

---

## Decisioni implementative chiave

- La Claude API Key è inserita a runtime nella sidebar (mai hardcoded)
- `analyze_csa()` ha `@st.cache_data` — sopravvive ai rerun se stesso PDF + stessa key
- **Unica chiamata Haiku**: un solo `analyze_csa()` estrae tutti i campi operativi (era diviso tra analisi base Haiku + analisi profonda Sonnet)
- **Prompt caching** (`cache_control: ephemeral`): il PDF è inviato una volta sola, il prompt è marcato `ephemeral` per caching lato Anthropic
- **`details = csa_data`** alias in `app.py` — tutti i tab che leggevano da `contract_details` leggono trasparentemente da `csa_data`
- **JSON troncato**: `_ripara_json_troncato()` in `csa_analyzer.py` — scanner bracket-stack che chiude le parentesi aperte all'ultima posizione sicura; attivato automaticamente se `stop_reason == "max_tokens"`
- **max_tokens 8192**: per `analyze_csa()` — sufficiente per CSA fino a ~100 pagine
- **Rate limit 429**: `_chiama_con_rate_limit()` in `app.py` — countdown live con `st.empty()` + loop `time.sleep(1)`, retry automatico fino a 2 volte con attesa 60s
- **Nessun limite di pagine**: rimosso `_limita_pagine()` — l'utente vede stima costo e decide se procedere
- Il calendario usa **giorni di calendario** per i SAL: il DL emette SAL anche durante sospensioni
- Le sospensioni **totali** estendono `data_fine_lavori`; le **parziali** sono solo registrate
- **Ribasso d'asta**: calcolato a livello app (`importo_netto`) e propagato a tutti i tab
- **SAL a importo**: il giorno del SAL è stimato con avanzamento lineare `round(n×soglia/importo×durata)`
- **SAL misto**: unione dei due trigger (tempo + importo), deduplicati se distanti < 7 giorni
- Font DejaVu per PDF: scaricato in `fonts/` dalla release ufficiale 2.37 (supporto Unicode completo)
- `st.session_state` è la cache per tutte le chiamate API; reset su nuovo upload o uscita demo
- La modalità demo usa importazione lazy (`from modules.demo_data import ...` dentro le funzioni)
- **Mappa fornitori**: ricerca con prefisso `nwr` (node+way+relation) invece di solo `node`; raggio default 50km; link Google Maps e Pagine Gialle per ogni categoria anche con 0 risultati OSM
- **Email SMTP**: usa `server.send_message(msg)` (non `sendmail()`) per evitare crash su caratteri non-ASCII italiani in oggetto/corpo
- **Analisi salvate**: `_salva_analisi()` scrive JSON in `results/<slug_pdf>.json` dopo ogni analisi; `_lista_analisi_salvate()` legge la cartella ordinando per data modifica; sezione sidebar `st.expander("📂 Analisi salvate")` **sempre visibile** — mostra messaggio vuoto se nessun file, si apre automaticamente se un'analisi salvata è attiva; il caricamento imposta `_file_id = "__saved__<nome>"` senza chiamate API
- **Salvataggio stato esteso**: `_salva_stato_cantiere()` salva nel JSON anche `checklist_stato`, `log_attivita`, `operatori_economici`, `ribasso_pct`, `registri`, `data_consegna_cantiere` — ricaricati al prossimo load dell'analisi salvata
- **Doc viewer**: `doc_viewer.render_doc_buttons(path, key)` — PDF apre in nuova scheda via blob URL JavaScript (non data: URL — bloccati dai browser); immagini (JPG/PNG) thumbnail con expand nativo; Office (docx/xlsx) due download button; usato in Checklist, Operatori, Registri
- **Ribasso d'asta persistente**: widget con `key="ribasso_pct"` + `on_change=_on_ribasso_change`; salvato in `_ribasso_pct` nel JSON; ripristinato via chiave staging `_ribasso_pendente` (impostata prima dell'istanziazione del widget nel rerun successivo — necessario perché Streamlit vieta `st.session_state[widget_key] = val` dopo l'istanziazione)
- **Operatori Economici L0/L1/L2**: `operatori_tab.py` con struttura gerarchica; DURC validità 120gg automatica da data emissione; Visura con data scadenza manuale; semaforo verde/giallo(≤30gg)/rosso(scaduto); alert DURC loggato una volta per sessione via `_durc_alerts_logged` flag; `render_durc_semaphore()` usato anche dalla Dashboard
- **Upload idempotency guard**: tutti i `st.file_uploader` confrontano `nome_file_calcolato != nome_file_corrente` prima di scrivere su disco e richiamare `st.rerun()` — evita loop infinito in cui ogni rerun riprocessa l'upload
- **Data consegna condivisa**: `st.session_state.data_consegna_cantiere` (date|None) è la singola sorgente di verità; sia Calendario che Checklist leggono/scrivono qui; uso di `or date.today()` per gestire sia chiavi assenti che chiavi con valore None esplicito
- **Log attività**: `aggiungi_log(azione, dettaglio, tab)` chiamato da tutti i tab su ogni operazione significativa (caricamento CSA, cambio data consegna, aggiunta sospensione, generazione documento, upload file, aggiunta subappaltatore, iscrizione riserva, ecc.)
- **Tab Documenti — repository elaborati**: 3 expander sempre visibili (grafico/tecnico/amministrativo); ogni documento come card riga con badge codice, badge variante rosso, stato caricato/mancante, upload PDF, `render_doc_buttons()`, ricerca testo PyMuPDF; form "➕ Aggiungi documento" in fondo a ciascuna sezione (categoria determinata dalla sezione); stato persistito in `doc_elaborati` (dict per categoria) nel JSON come `_doc_elaborati`; migrazione automatica da vecchio formato (`elaborati_caricati` + `varianti`) al nuovo all'apertura del tab
- **Chunked analysis**: `conta_token_api()` (@st.cache_data) usa `client.beta.messages.count_tokens()` su testo estratto; se > 150 000 token → `analyze_csa_chunked()` con CHUNK_PROMPT semplificato (~80K token/chunk) + CONSOLIDATION_PROMPT finale; `nonlocal` non usabile a livello modulo Streamlit — progress callback usa chiusura senza nonlocal

---

## Session State — chiavi usate

| Chiave | Tipo | Contenuto |
|---|---|---|
| `_file_id` | str | ID file uploadato (`"__demo__"` in demo, `"__saved__<nome>.json"` se analisi salvata caricata) |
| `_demo_active` | bool | True se modalità demo attiva |
| `_pdf_nome` | str | Nome originale del file PDF caricato (usato per il salvataggio) |
| `pdf_bytes` | bytes \| None | Contenuto PDF caricato |
| `csa_data` | dict | Output `analyze_csa()` — contiene TUTTI i campi (dati generali + SOA + SAL + penali + obblighi + checklists) |
| `coords` | tuple(float,float) | (lat, lon) cantiere |
| `suppliers` | DataFrame | Lista fornitori OSM |
| `sospensioni` | list[Sospensione] | Sospensioni aggiunte nel tab Calendario |
| `_sosp_counter` | int | ID incrementale per sospensioni |
| `_doc_{type}` | str | Documento generato per tipo (riserva, verbale_consegna, proroga, contestazione) |
| `checklist_stato` | dict | Stato attività checklist: `{categoria: {idx: {stato, referente_nome, referente_email, referente_ruolo, documento_nome}}}` |
| `data_consegna_cantiere` | date \| None | Data consegna cantiere — **condivisa** tra tab Calendario e Checklist; usata per rilevare ritardi |
| `operatori_economici` | dict | Struttura L0/L1/L2: `{appaltatore: {ragione_sociale, piva, documenti}, subappaltatori: [{id, ragione_sociale, piva, categoria_soa, importo, percentuale, tipo, stato_autorizzazione, documenti, subaffidatari}]}` |
| `ribasso_pct` | float | Percentuale ribasso — **widget key** (`st.number_input key="ribasso_pct"`); modificabile solo tramite `_ribasso_pendente` staging key |
| `_ribasso_pendente` | float | Valore ribasso da ripristinare al prossimo rerun (consumato prima dell'istanziazione del widget) |
| `_durc_alerts_logged` | bool | Flag: alert DURC già loggati in questa sessione (evita duplicati ad ogni rerun) |
| `registri` | dict | 5 chiavi: `riserve`, `verbali`, `non_conformita`, `ordini_servizio`, `contabilita_sal` — ognuna list[dict] |
| `log_attivita` | list[dict] | Log cronologico operazioni: `{id, timestamp, azione, dettaglio, tab}` |
| `doc_elaborati` | dict | `{"grafico": [...], "tecnico": [...], "amministrativo": [...]}` — tutti i documenti per categoria; ogni item: `{codice, titolo, is_variante, data_approvazione_variante, note_variante, path, data_upload}` |

**Chiavi rimosse:** `contract_details` (merged in `csa_data`), `_interp_result` (tab interpretazione eliminato), `_data_consegna_ck` (sostituita da `data_consegna_cantiere`), `subappalti` (sostituita da `operatori_economici`)

---

## Struttura JSON attesa da Claude

### `csa_data` (da `analyze_csa`) — unico dict con tutti i campi
```json
{
  "indirizzo_cantiere": "...",
  "comune": "...",
  "provincia": "BG",
  "regione": "...",
  "tipo_lavori": "...",
  "categorie_materiali": ["..."],
  "lavorazioni_specialistiche": ["..."],
  "importo_lavori": "€ 1.350.000,00",
  "durata_lavori_giorni": 180,
  "stazione_appaltante": "...",
  "categorie_soa": [
    {
      "codice": "OG3",
      "descrizione_categoria": "Strade, autostrade, ponti...",
      "classifica": "IV",
      "prevalente": true,
      "motivazione": "..."
    }
  ],
  "sal_intervallo_giorni": 30,
  "sal_importo_minimo_euro": 80000.0,
  "sal_tipo": "misto",
  "penale_giornaliera_permille": 1.0,
  "penale_massima_percentuale": 10.0,
  "riserve_iscrizione_giorni": 15,
  "riserve_quantificazione_giorni": 15,
  "collaudo_giorni": 180,
  "importo_oneri_sicurezza": 27000.0,
  "obblighi_appaltatore": ["..."],
  "obblighi_stazione_appaltante": ["..."],
  "checklist_prime_settimane": [{"attivita": "...", "termine_giorni": 10, "priorita": "alta"}],
  "checklist_contabilita": [{"attivita": "...", "termine_giorni": null, "priorita": "alta"}],
  "checklist_rapporti_dl": [{"attivita": "...", "termine_giorni": null, "priorita": "alta"}],
  "checklist_assicurative": [{"attivita": "...", "termine_giorni": 10, "priorita": "alta"}],
  "tipo_contratto": "A corpo|A misura|A corpo e misura",
  "prezzario_nome": "Prezzario Regionale Lombardo",
  "prezzario_regione": "Lombardia",
  "prezzario_anno": "2023",
  "elaborati": [
    {
      "codice": "TAV-01",
      "titolo": "Planimetria generale",
      "categoria": "grafico",
      "obbligatorio": true
    }
  ]
}
```

**Nota:** `clausole_penalizzanti` e `clausole_ambigue` sono state rimosse dall'app (materia legale esclusa).

---

## Avvio

```bash
pip install -r requirements.txt
streamlit run app.py
```

La modalità demo è attivabile dalla sidebar senza API Key
(dati fittizi: cantiere stradale Via Roma, Bergamo BG, € 1.350.000, 180 giorni).

---

## Nuove funzionalità — Sessione 2026-05-09 (rev. 7 — tab Documenti + chunked analysis)

| Feature | Implementazione |
|---------|----------------|
| **Tab 📄 Documenti redesign** | Repository digitale elaborati: lista estratta da CSA (`elaborati` field), card 3-colonne per categoria (grafico/tecnico/amministrativo), upload PDF per codice, ricerca testo via `_cerca_in_pdf()` PyMuPDF; Varianti approvate con form e delete; Redazione spostata in expander collassato |
| **Elaborati field in CSA** | `analyze_csa()` e `analyze_csa_chunked()` estraggono `elaborati: [{codice, titolo, categoria, obbligatorio}]`; `EXTRACTION_PROMPT`, `CHUNK_PROMPT_TEMPLATE` e `_SCHEMA_CONSOLIDATION` aggiornati |
| **Analisi chunked PDF grandi** | `conta_token_api()` (@st.cache_data) → se > 150K token: `analyze_csa_chunked()` con N chiamate Haiku (CHUNK_PROMPT, ~80K token/chunk) + CONSOLIDATION_PROMPT finale; risolve `prompt is too long: 215241 tokens > 200000 maximum` |
| **Text-only API (no PDF base64)** | `_estrai_testo_pdf()` (PyMuPDF/fitz) — mai inviato PDF base64 all'API; risolve `A maximum of 100 PDF pages may be provided` |
| **Stato elaborati/varianti salvato** | `elaborati_caricati` (dict) e `varianti` (list) persistiti in JSON via `_salva_stato_cantiere()`; ripristinati al caricamento analisi salvata |

---

## Nuove funzionalità — Sessione 2026-05-09 (rev. 6 — Operatori + ribasso + fix)

| Feature | Implementazione |
|---------|----------------|
| **Tab 🏢 Operatori Economici** | `operatori_tab.py` (725 righe) — gerarchia L0/L1/L2; appaltatore con DURC 120gg auto-scadenza + Visura + Polizza CAR/RCT; subappaltatori con 8 documenti + verifica 30%; subaffidatari collegati al subappaltatore padre |
| **Semaforo DURC** | `render_durc_semaphore(oe)` — visualizza stato DURC/Visura di tutti gli operatori; verde/giallo(≤30gg)/rosso(scaduto); espanso automaticamente se ci sono criticità; usato anche in Dashboard |
| **Ribasso d'asta salvato** | `ribasso_pct` ora persistito nel JSON (chiave `_ribasso_pct`) e ripristinato al caricamento analisi; `on_change=_on_ribasso_change` logga il cambio e salva; ripristino via pattern staging `_ribasso_pendente` |
| **Tab 📚 Registri** | `registri_tab.py` (1.289 righe) — 5 sezioni: Riserve art.120, Verbali (6 tipi), Non Conformità, Ordini di Servizio (DL/RUP/CSE), Contabilità SAL |
| **Tab 📋 Log Attività** | `log_manager.py` (278 righe) — log cronologico con filtri, export PDF (landscape A4), cancellazione; `aggiungi_log()` integrato in tutti i tab |
| **Doc viewer unificato** | `doc_viewer.py` (137 righe) — `render_doc_buttons(path, key)`: PDF via blob URL JavaScript (non data: URL), immagini thumbnail cliccabile, Office → download; applicato a Checklist, Operatori, tutti i registri |
| **Dashboard 2a fila KPI** | Quando operatori/registri non vuoti: metriche subappalti % / riserve / NC aperte / SAL contabilità pagati + semaforo DURC |
| **Tipo contratto + prezzario** | Dashboard e Sintesi CSA mostrano tipo contratto (A corpo/misura) e prezzario adottato; estratti da `analyze_csa()` |
| **Data consegna condivisa** | `data_consegna_cantiere` in session state condivisa tra Calendario e Checklist; log automatico su cambio data |
| **Salvataggio stato esteso** | `_salva_stato_cantiere()` persiste anche `operatori_economici`, `ribasso_pct`, `registri`, `log_attivita`, `data_consegna_cantiere` nel JSON |

---

## Nuove funzionalità — Sessione 2026-05-07

| Feature | Implementazione |
|---------|----------------|
| **Architettura unificata** | Una sola chiamata Haiku all'upload; `csa_data` contiene tutti i campi; eliminati tab legali e Sonnet |
| **Token counting pre-analisi** | `conta_pagine_pdf()` + `stima_token_pdf()` in `csa_analyzer.py`; stima costo Haiku prima del caricamento; un solo pulsante "Avvia analisi" con costo stimato |
| **Barra progresso animata** | Step 10%→40%→75%→95% con `st.progress()` + `st.empty()` durante `analyze_csa()` |
| **Retry 429 migliorato** | `_chiama_con_rate_limit` ora accetta `**kwargs`; barra progresso countdown visualizza avanzamento attesa |
| **Dashboard tab** | Tab iniziale con metriche chiave (4 KPI) + 3 azioni rapide + riepilogo penale/collaudo |
| **📂 Analisi salvate sidebar** | Expander sempre visibile; fix bug visibilità (era nascosta se `results/` assente o vuota); badge ✅ su analisi attiva; eliminazione con reset sessione; cartella `results/` creata |

---

## Bug corretti — Sessione 2026-05-03

| Bug | Causa | Fix |
|-----|-------|-----|
| `FPDFUnicodeEncodingException` su caratteri "—" nel PDF | Font Helvetica non supporta Unicode | Sostituito con DejaVu Sans TTF scaricato in `fonts/` |
| Testo sovrapposto in "Dati cantiere" del PDF | Celle affiancate con `ln=False` overflow su testo lungo | Riscritta con righe separate label/valore (50mm + larghezza residua) |
| `_parse_importo()` restituisce 0 su testo letterale | Nessun parser per italiano | Aggiunta `_parse_importo_italiano()` con supporto "un milione trecentocinquantamila euro" |
| `analyze_contract_details()` fallisce silenziosamente su PDF grandi | Nessun retry né timeout | Retry 3x backoff (2s, 4s, 8s) + `timeout=120s` + errore esplicito |
| Calendario non supportava SAL a importo o misto | Logica solo temporale | `calendar_manager.py` riscritto con 3 modalità + avanzamento lineare |
| Penali e revisione prezzi ignoravano il ribasso d'asta | Campo ribasso non esisteva | Aggiunto campo sidebar; `importo_netto` propagato a tutti i tab |

---

## Bug corretti — Sessione 2026-05-09 (post-deploy)

| Bug | Causa | Fix |
|-----|-------|-----|
| **`prompt is too long: 215241 tokens > 200000 maximum`** su CSA > 80 pagine | `analyze_csa()` inviava il PDF intero come base64 senza limite di token | Implementata modalità chunked: `conta_token_api()` conta i token esatti; se > 150 000 → `analyze_csa_chunked()` estrae testo con PyMuPDF, divide in chunk da ~80 000 token, analizza ciascuno con `CHUNK_PROMPT`, consolida con chiamata finale |
| **`SyntaxError: no binding for nonlocal '_n_chunks_usati'`** | `nonlocal` non funziona al livello module di Streamlit (non c'è funzione esterna) | Rimosso `nonlocal` dalla callback `_on_chunk_progress`; il valore finale di `_n_chunks_usati` viene già dal return di `analyze_csa_chunked()` |
| **`A maximum of 100 PDF pages may be provided`** | `analyze_csa()` e `conta_token_api()` inviavano il PDF come `base64` document — limite API Anthropic di 100 pagine | Eliminato completamente il PDF base64 da tutte le funzioni; ora usano sempre `_estrai_testo_pdf()` (PyMuPDF) e inviano solo testo all'API |

## Bug corretti — Sessione 2026-05-09

| Bug | Causa | Fix |
|-----|-------|-----|
| **`StreamlitAPIException: ribasso_pct cannot be modified after widget instantiation`** | Il widget `st.number_input(key="ribasso_pct")` viene istanziato nella sidebar (riga ~598); i pulsanti "carica analisi" (riga ~718) sono nella stessa sidebar ma dopo il widget — Streamlit vieta di impostare `st.session_state[widget_key]` dopo l'istanziazione | Pattern staging: i load button scrivono in `st.session_state._ribasso_pendente`; all'inizio della sidebar (prima del widget) si controlla `if "_ribasso_pendente" in st.session_state:` e si trasferisce il valore — così al rerun successivo il widget nasce già con il valore corretto |
| **`NameError: comune`** in `operatori_tab.py` | Variabile assegnata come `common = csa_data.get("comune", "")` ma poi referenziata come `comune` nell'if-condition | Rinominato il riferimento da `comune` a `common` in `render_operatori_tab()` |
| **Loop infinito upload documenti** (bloccava l'app) | `st.file_uploader` mantiene il file in session state tra i rerun; ogni rerun riprocessava l'upload indefinitamente | Guard idempotency `if nome_file_calcolato != nome_file_corrente:` prima di scrivere su disco e `st.rerun()` — applicato a tutti e 4 gli handler upload (Checklist, Subappalti standard, Registri verbali, Registri OS) |
| **`AttributeError: 'NoneType' object has no attribute 'isoformat'`** in tutti i tab | `dict.get(key, default)` restituisce `None` (non il default) se la chiave esiste con valore None esplicito; `st.date_input(value=None)` può restituire None | Fix con `or date.today()` dopo sia il `session_state.get()` che il widget; pattern uniforme in Calendario e Checklist |
| **Data consegna non sincronizzata** tra Calendario e Checklist | Ogni tab usava una chiave separata | Chiave unificata `data_consegna_cantiere` in session state; entrambi i tab leggono e scrivono nella stessa chiave |

---

## Bug corretti — Sessione 2026-05-05

| Bug | Causa | Fix |
|-----|-------|-----|
| `'ascii' codec can't encode character '\xe0'` in notifiche email | `smtplib.sendmail()` chiama `.encode('ascii')` internamente su caratteri italiani | Sostituito con `server.send_message(msg)`; oggetto sanitizzato con `.encode("ascii", errors="replace")`; nomi file Excel con soli caratteri ASCII |
| JSON troncato: `Unterminated string starting at: line 96` | `max_tokens=4096` insufficiente per CSA grandi; modello troncava a metà JSON | `max_tokens` → 8192; aggiunto `_ripara_json_troncato()` con bracket-stack; check su `stop_reason == "max_tokens"` |
| Costo API ~$0.70 per PDF da 0.8MB | Sonnet usato per tutte le chiamate senza caching | Split Haiku/Sonnet + prompt caching `cache_control: ephemeral` + limite 50 pagine PDF |
| Rate limit 429 senza feedback utente | Nessuna gestione `RateLimitError` | `_chiama_con_rate_limit()` con countdown live e retry automatico x2 |
| Mappa fornitori trova 0 risultati OSM | Query solo su `node`, tag troppo restrittivi, raggio 30km | Prefisso `nwr`, tag estesi (hardware, steelconstruction, woodworker, timber), raggio default 50km |
| Link fornitori assenti quando OSM restituisce 0 risultati | Link mostrati solo in presenza di risultati | Google Maps e Pagine Gialle sempre visibili per categoria, indipendentemente dai risultati OSM |

---

## Roadmap — Prossime fasi

### ✅ FASE COMPLETATA — UX + Ottimizzazioni (2026-05-09)

Tutte le feature implementate (barra progresso, token counting, retry 429, architettura Haiku, analisi salvate, Operatori L0/L1/L2, Registri, Log attività, doc viewer, ribasso salvato). Dettagli in "Decisioni implementative chiave".

**Backlog:**
- `client.beta.files.upload()` — evita ricodifica base64 ad ogni analisi
- Indicatore costo post-analisi basato su token reali input/output

---

### FASE TESTING — giugno 2026

**Obiettivo:** validare l'app su CSA reali di tipologie diverse prima del deploy.

**CSA da testare (5 tipologie):**
- [ ] **Stradale**: rifacimento manto, segnaletica — verifica OG3, importo km-based
- [ ] **Edilizia civile**: ristrutturazione/costruzione edificio — verifica OG1, OG2
- [ ] **Impianti**: impianti meccanici/elettrici — verifica OS3, OS28, OS30
- [ ] **Manutenzione**: manutenzione ordinaria multi-anno — verifica SAL periodici brevi
- [ ] **Opere idrauliche**: fognature, acquedotti — verifica OG6

**Checklist di verifica per ogni CSA:**
- [ ] Importo estratto corretto (± 5% rispetto al contratto)
- [ ] Durata giorni corretta
- [ ] Penali giornaliere estratte correttamente
- [ ] Categorie SOA pertinenti e classifica coerente con importo
- [ ] `sal_tipo` rilevato correttamente (tempo/importo/misto)
- [ ] Calendario SAL generato senza errori
- [ ] Export Excel completo (4 fogli)
- [ ] Export PDF senza errori Unicode
- [ ] Notifiche email inviate correttamente su Gmail

**Criteri di successo:** almeno 4/5 CSA analizzati correttamente senza interventi manuali sui dati.

---

### FASE DEPLOY — luglio 2026

**Obiettivo:** rendere l'app accessibile via browser senza installazione locale per i beta tester.

**Stack previsto:**
- **Streamlit Community Cloud** (streamlit.io/cloud) — repository GitHub privato
- Secrets management per API keys via `st.secrets` (non variabili d'ambiente)
- Dominio custom opzionale (es. `dtcantiere.it`)

**Checklist pre-deploy:**
- [ ] Creare repository GitHub privato e push del codice
- [ ] Configurare `secrets.toml` su Streamlit Cloud (API key demo condivisa)
- [ ] Creare `.env.example` e `secrets.toml.example` per documentazione
- [ ] Verificare che i font DejaVu siano inclusi nel repository (`fonts/`)
- [ ] Testare su Python 3.11+ (Streamlit Cloud usa 3.11 di default)
- [ ] Aggiungere test pytest su `calendar_manager.py` e `penalties.py`
- [ ] Aggiungere rate limiting per API key condivisa (max N richieste/ora per sessione)

---

### FASE 2 — Agente email fornitori (human-in-the-loop)

- Nuovo tab "📧 Contatto Fornitori": Claude API seleziona fornitori pertinenti (OSM vs categoria CSA) → Sonnet redige email personalizzata → `st.text_area` revisione bozza → invio Gmail OAuth2 / SMTP
- Vincoli: nessun invio senza conferma; OAuth2 non in chiaro; log email con timestamp; bozze non approvate mantenute in sessione

---

### FASE 3 — Import computi metrici

- Upload computo metrico (Excel/PDF) → Claude API spacchetta voci per categoria SOA (OG/OS)
- SAL a importo su avanzamento reale per categoria (non stima lineare); confronto computo vs avanzamento dichiarato; verifica coerenza importi/classifica SOA

---

### FASE COMMERCIALE — Piano beta tester

Beta giugno 2026: 3-5 DTC a € 20/mese con API Key condivisa; pricing post-beta: Base €49 / Pro €99 / Azienda €199/mese. Vedi [BUSINESS_PLAN.md](BUSINESS_PLAN.md) per dettagli completi.

---

## Business Plan

Mercato ~45.000 DTC/studi tecnici italiani (D.Lgs. 36/2023). Pricing: Base €49 / Pro €99 / Azienda €199 / White Label €500+/mese. Break-even ~6 clienti Pro. Vedi [BUSINESS_PLAN.md](BUSINESS_PLAN.md) per proiezioni, costi, canali acquisizione e analisi rischi.

---

## Sviluppi Futuri (backlog non prioritario)

- **Struttura cartelle per analisi**: ad ogni nuova analisi CSA creare automaticamente in `results/` una cartella nominata `{data}_{NomeAppalto}` con sottocartelle: `01_Contratto/CSA`, `01_Contratto/Varianti`, `02_Contabilita/SAL`, `02_Contabilita/Riserve`, `03_Documenti_Ufficiali/Verbali`, `03_Documenti_Ufficiali/Ordini_di_Servizio`, `03_Documenti_Ufficiali/Corrispondenza`, `04_Operatori_Economici/Appaltatore`, `04_Operatori_Economici/Subappaltatori`, `05_Qualita/Non_Conformita`, `05_Qualita/Checklist`, `06_Export/PDF`, `06_Export/Excel`. Gli allegati checklist e operatori vanno nelle sottocartelle corrispondenti. Da definire: nome cartella automatico da CSA (slug di `tipo_lavori`+`comune`) o inserito manualmente dall'utente.
- **Gestione multi-CSA**: confronto parametri tra appalti (penali, durata, SAL)
- **Test unitari**: pytest per `calendar_manager.py` e `penalties.py` (logica pura)
- **`.env.example`**: file di esempio per variabili d'ambiente
- **Demo data da CSA reale**: sostituire i dati Bergamo con un CSA pubblico anonimizzato
- **Notifiche scadenze automatiche**: cron job o webhook che invia email senza intervento utente
- **Import SAL da contabilità DL**: caricare i SAL già emessi per aggiornare il calendario reale
