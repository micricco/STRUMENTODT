# MAPPA SOFTWARE — Strumento DT Cantiere

> Generato il 2026-05-07 — D.Lgs. 36/2023

---

## 1. Struttura file

```
claudeai/
├── app.py                      # Entry point Streamlit (~1.500 righe)
├── CLAUDE.md                   # Istruzioni e stato progetto per Claude Code
├── MAPPA_SOFTWARE.md           # Questo file
├── requirements.txt            # Dipendenze Python
├── fonts/
│   ├── DejaVuSans.ttf          # Font Unicode per export PDF
│   └── DejaVuSans-Bold.ttf
└── modules/
    ├── __init__.py
    ├── csa_analyzer.py         # Analisi base CSA via Claude Haiku
    ├── contract_analyzer.py    # Analisi contrattuale + redazione documenti
    ├── calendar_manager.py     # Calcolo calendario scadenze e SAL
    ├── penalties.py            # Calcolo penali e revisione prezzi art.60
    ├── demo_data.py            # Dati demo cantiere Bergamo BG
    ├── geocoder.py             # Geocoding Nominatim (OSM)
    ├── supplier_search.py      # Ricerca fornitori Overpass API
    └── map_renderer.py         # Mappa interattiva Folium
```

---

## 2. Descrizione moduli e funzioni principali

### `app.py` — Entry point principale

| Funzione / Sezione | Descrizione |
|--------------------|-------------|
| `_chiama_con_rate_limit(fn, *args)` | Wrapper per chiamate API con retry automatico su RateLimitError 429; countdown live con `st.empty()` |
| `_genera_pdf_calendario(cal, csa_data)` | Genera PDF del calendario scadenze con tabella colorata (fpdf2 + font DejaVu) |
| `_genera_excel_multifoglio(csa_data, details, cal)` | Genera Excel con 4 fogli: Sintesi CSA, Scadenze, Checklist, Calendario |
| `_invia_notifica_email(...)` | Invia email HTML con scadenze imminenti via SMTP/STARTTLS |
| `_parse_importo(val)` | Parser importi: numerico, formato italiano (€ 1.350.000,00), testo letterale |
| `_parse_importo_italiano(testo)` | Parser testo italiano: "un milione trecentocinquantamila euro" |
| `_load_demo_into_session()` | Carica dati demo in session_state senza API call |
| **Sidebar** | API key, ribasso d'asta, raggio fornitori, categorie, export Excel, notifiche email, demo |
| **Tab 1–9** | Vedi sezione 3 |

---

### `modules/csa_analyzer.py` — Analisi base CSA

| Funzione | Descrizione |
|----------|-------------|
| `analyze_csa(pdf_bytes, api_key)` | Chiamata Claude Haiku con `@st.cache_data`; estrae dati base + categorie SOA; usa prompt caching `cache_control: ephemeral` |
| `_limita_pagine(pdf_bytes, max_pagine)` | Tronca PDF alle prime N pagine via pypdf (default: 50) per limitare i token |

**Modello:** `claude-haiku-4-5-20251001`
**Max tokens output:** 2048
**Cache:** `@st.cache_data` — sopravvive ai rerun se stesso PDF + stessa key

---

### `modules/contract_analyzer.py` — Analisi contrattuale

| Funzione | Descrizione |
|----------|-------------|
| `analyze_contract_details(pdf_bytes, api_key)` | 2 chiamate API: Haiku (parametri meccanici + checklist) + Sonnet (analisi legale); retry 3x con backoff; timeout 150s |
| `_chiama_con_pdf(client, model, pdf_base64, prompt, max_tokens, max_tentativi)` | Chiamata API con PDF e cache_control; gestisce RateLimitError, APITimeoutError, JSONDecodeError |
| `_ripara_json_troncato(raw)` | Bracket-stack scanner che chiude parentesi aperte se `stop_reason == "max_tokens"` |
| `_limita_pagine(pdf_bytes, max_pagine)` | Identica a quella in csa_analyzer.py (default: 50) |
| `interpret_clause(clause_text, contract_context, api_key)` | Analisi legale strutturata di clausola libera via Sonnet |
| `generate_document(doc_type, context, params, api_key)` | Genera documento legale (riserva / verbale_consegna / proroga / contestazione) via Haiku |

**Modelli:** Haiku per estrazione meccanica; Sonnet per analisi legale qualitativa
**Max tokens output:** 8192 (per entrambe le chiamate di analisi)
**Prompt caching:** il PDF viene pagato una sola volta (Haiku); Sonnet legge dalla cache a ~10% del costo

---

### `modules/calendar_manager.py` — Calendario scadenze

| Funzione | Descrizione |
|----------|-------------|
| `calcola_calendario(data_consegna, durata_giorni, importo_contratto, sal_tipo, ...)` | Genera lista eventi contrattuali con 3 modalità SAL + sospensioni |
| `_genera_milestones_sal(...)` | Calcola date SAL: tempo (ogni X giorni), importo (avanzamento lineare), misto (unione deduplicata < 7 gg) |
| `_giorni_sospesi_totali(sospensioni)` | Somma giorni sospensioni totali per proroga scadenza |
| `Sospensione` | Dataclass: id, data_inizio, data_fine, tipo (totale/parziale), motivo, percentuale |

**Nota:** usa giorni di calendario (non lavorativi); sospensioni totali estendono data_fine_lavori

---

### `modules/penalties.py` — Penali e revisione prezzi

| Funzione | Descrizione |
|----------|-------------|
| `calcola_penale_cumulativa(importo_contratto, permille, giorni_ritardo, penale_massima_percent)` | Calcola penale giornaliera, cumulativa, cap massimo e giorno al cap |
| `simula_revisione_prezzi(importo_contratto, oneri_sicurezza, indice_istat_offerta, indice_istat_aggiornamento, soglia_franchigia_percent)` | Revisione prezzi art.60 D.Lgs.36/2023: compensazione 90% per parte eccedente franchigia 5% |

---

### `modules/geocoder.py` — Geocoding

| Funzione | Descrizione |
|----------|-------------|
| `geocode_site(csa_data)` | Nominatim OSM: risolve indirizzo/comune/provincia in (lat, lon) |

---

### `modules/supplier_search.py` — Ricerca fornitori

| Costante/Funzione | Descrizione |
|-------------------|-------------|
| `CATEGORY_QUERIES` | Dict categoria → query Overpass API (prefisso `nwr` per node+way+relation) |
| `CATEGORY_KEYWORDS` | Dict categoria → parola chiave per Google Maps / Pagine Gialle |
| `search_suppliers(lat, lon, radius_km, categories)` | Query Overpass API; raggio default 50 km; restituisce DataFrame |

---

### `modules/map_renderer.py` — Mappa Folium

| Funzione | Descrizione |
|----------|-------------|
| `build_map(lat, lon, suppliers_df, radius_km)` | Mappa Folium con marker cantiere, cerchio raggio, pin fornitori per categoria |

---

### `modules/demo_data.py` — Dati demo

Contiene costanti: `DEMO_CSA_DATA`, `DEMO_CONTRACT_DETAILS`, `DEMO_COORDS`, `DEMO_SUPPLIERS`, `DEMO_DOCUMENTS`, `DEMO_INTERPRETATION` — cantiere stradale Via Roma, Bergamo BG, € 1.350.000, 180 giorni.

---

## 3. Tab — funzionalità e file coinvolti

| # | Tab | Funzionalità | File |
|---|-----|-------------|------|
| 1 | 📋 Sintesi CSA | Dati generali, materiali, lavorazioni, categorie SOA con classifica e classifica soglie | `csa_analyzer.py`, `app.py` |
| 2 | ⚖️ Analisi Contrattuale | Scadenze critiche, obblighi parti, clausole penalizzanti vs DM 49/2018, clausole ambigue | `contract_analyzer.py`, `app.py` |
| 3 | ✅ Checklist | 4 checklist operative: Prime Settimane / Contabilità SAL / Rapporti DL / Assicurazioni | `contract_analyzer.py`, `app.py` |
| 4 | 📄 Documenti | Redazione: Riserva art.120, Verbale Consegna, Proroga, Contestazione | `contract_analyzer.py`, `app.py` |
| 5 | 🔍 Interpretazione | Analisi legale strutturata di clausole ambigue (input libero) | `contract_analyzer.py`, `app.py` |
| 6 | 📅 Calendario | 3 modalità SAL (tempo/importo/misto), sospensioni, ribasso applicato, export CSV/PDF | `calendar_manager.py`, `app.py` |
| 7 | 💰 Penali & Revisione | Calcolo penali con cap, tabella progressiva, revisione prezzi art.60 | `penalties.py`, `app.py` |
| 8 | 🗺️ Mappa Fornitori | Geocoding, ricerca Overpass, mappa Folium, link Google Maps / Pagine Gialle | `geocoder.py`, `supplier_search.py`, `map_renderer.py`, `app.py` |
| 9 | ❓ Guida | Documentazione integrata: introduzione, guida passo per passo, FAQ, note legali | `app.py` |
| — | 🎮 Demo | Dati fittizi cantiere Bergamo BG senza API Key | `demo_data.py`, `app.py` |

---

## 4. Dipendenze esterne

| Libreria | Versione min | Uso |
|----------|-------------|-----|
| `streamlit` | ≥ 1.35 | UI web, session_state, widget, cache |
| `anthropic` | ≥ 0.40 | Claude API (Haiku + Sonnet), prompt caching |
| `folium` | ≥ 0.16 | Mappa interattiva fornitori |
| `streamlit-folium` | ≥ 0.20 | Embedding mappa Folium in Streamlit |
| `requests` | ≥ 2.31 | Query Overpass API (fornitori) |
| `geopy` | ≥ 2.4.1 | Nominatim geocoding |
| `pandas` | ≥ 2.0 | Tabelle dati (fornitori, eventi calendario) |
| `fpdf2` | ≥ 2.7 | Export PDF calendario con font DejaVu Unicode |
| `openpyxl` | ≥ 3.1 | Export Excel multi-foglio |
| `pypdf` | ≥ 3.0 | Limitazione pagine PDF prima dell'invio ad API |
| `smtplib` | stdlib | Notifiche email SMTP/STARTTLS |

**Nessuna dipendenza a pagamento** oltre a Claude API.

---

## 5. Flusso dati — dal caricamento PDF all'output finale

```
[1. UPLOAD PDF]
  └─ st.file_uploader()
  └─ pdf_bytes → st.session_state.pdf_bytes

[2. ANALISI BASE (automatica)]
  └─ _limita_pagine(pdf_bytes, 50) → pdf_limitato
  └─ base64.encode(pdf_limitato) → pdf_base64
  └─ Claude Haiku API (prompt caching)
  └─ JSON parsed → st.session_state.csa_data
       ├── indirizzo_cantiere, comune, provincia, regione
       ├── tipo_lavori, importo_lavori, durata_lavori_giorni
       ├── stazione_appaltante
       ├── categorie_materiali[], lavorazioni_specialistiche[]
       └── categorie_soa[{codice, classifica, prevalente, motivazione}]

[3. ANALISI CONTRATTUALE (on-demand, Tab 2)]
  └─ Stessa pdf_base64 (già in cache Anthropic)
  └─ Chiamata 1: Claude Haiku → parametri meccanici + 4 checklist
  └─ Chiamata 2: Claude Sonnet → obblighi + clausole penalizzanti/ambigue
  └─ Merge {fast, deep} → st.session_state.contract_details
       ├── sal_intervallo_giorni, sal_importo_minimo_euro, sal_tipo
       ├── penale_giornaliera_permille, penale_massima_percentuale
       ├── riserve_iscrizione/quantificazione_giorni, collaudo_giorni
       ├── checklist_prime_settimane[], checklist_contabilita[]
       ├── checklist_rapporti_dl[], checklist_assicurative[]
       ├── obblighi_appaltatore[], obblighi_stazione_appaltante[]
       ├── clausole_penalizzanti[{titolo, testo_csa, problema, azione}]
       └── clausole_ambigue[{titolo, interpretazione_favorevole/sfavorevole}]

[4. PROPAGAZIONE RIBASSO]
  └─ importo_base = _parse_importo(csa_data.importo_lavori)
  └─ importo_netto = importo_base × (1 - ribasso_pct / 100)
  └─ Propagato a: Tab Calendario, Tab Penali, Tab Revisione Prezzi

[5. CALENDARIO (Tab 6)]
  └─ calcola_calendario(data_consegna, durata_giorni, importo_netto, sal_tipo, ...)
  └─ _genera_milestones_sal() → lista SAL con date e importi
  └─ Aggiunte sospensioni da st.session_state.sospensioni
  └─ Output: dict {data_consegna, data_fine_lavori, eventi[], ...}
  └─ Export: CSV (pandas), PDF (_genera_pdf_calendario via fpdf2)

[6. MAPPA FORNITORI (Tab 8)]
  └─ geocode_site(csa_data) → (lat, lon) via Nominatim
  └─ search_suppliers(lat, lon, radius_km, categories) → DataFrame via Overpass
  └─ build_map(lat, lon, suppliers, radius_km) → oggetto Folium
  └─ st_folium(fmap) → mappa interattiva in UI

[7. EXPORT]
  ├─ Excel: _genera_excel_multifoglio(csa_data, details, cal) → openpyxl BytesIO
  ├─ PDF: _genera_pdf_calendario(cal, csa_data) → fpdf2 bytes
  └─ Email: _invia_notifica_email(...) → smtplib SMTP STARTTLS
```

---

## 6. Session State — chiavi principali

| Chiave | Tipo | Contenuto |
|--------|------|-----------|
| `_file_id` | str | ID file uploadato (o `"__demo__"`) |
| `_demo_active` | bool | True se modalità demo attiva |
| `pdf_bytes` | bytes\|None | Contenuto PDF caricato |
| `csa_data` | dict | Output `analyze_csa()` |
| `contract_details` | dict | Output `analyze_contract_details()` |
| `coords` | tuple(float,float) | (lat, lon) cantiere |
| `suppliers` | DataFrame | Lista fornitori OSM |
| `sospensioni` | list[Sospensione] | Sospensioni nel tab Calendario |
| `_sosp_counter` | int | ID incrementale sospensioni |
| `_interp_result` | str | Ultimo output interpretazione clausola |
| `_doc_{type}` | str | Documento generato per tipo |

---

## 7. Chiamate Claude API — riepilogo

| Funzione | Modello | Trigger | Cache | Max tokens |
|----------|---------|---------|-------|-----------|
| `analyze_csa()` | Haiku | Upload PDF | `@st.cache_data` + `cache_control` | 2048 |
| `analyze_contract_details()` — fase 1 | Haiku | Click utente Tab 2 | `cache_control` | 8192 |
| `analyze_contract_details()` — fase 2 | Sonnet | Automatico dopo fase 1 | `cache_control` (legge cache Haiku) | 8192 |
| `interpret_clause()` | Sonnet | Click utente Tab 5 | Nessuna | 2048 |
| `generate_document()` | Haiku | Click utente Tab 4 | Nessuna | 2048 |
