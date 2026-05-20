"""
registri_tab.py — Gestione registri ufficiali di cantiere per l'app DTC.

Registri implementati:
  1. Riserve (art.120 D.Lgs.36/2023)
  2. Verbali (consegna, sospensione, ripresa, sopralluogo, contestazione, collaudo)
  3. Non Conformità
  4. Ordini di Servizio (DL / RUP / CSE)
  5. Contabilità SAL

Ogni sezione gestisce inserimento, visualizzazione, modifica, eliminazione e
upload documenti allegati. Tutte le variazioni vengono persistite tramite
salva_fn() e registrate nel log attività.
"""

import io
import time
import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
import pathlib

from modules.log_manager import aggiungi_log, aggiungi_al_diario
from modules.doc_viewer import render_doc_buttons


# ---------------------------------------------------------------------------
# Tipi e costanti
# ---------------------------------------------------------------------------

_STATI_RISERVA = ["iscritta", "confermata", "quantificata", "definita", "respinta"]

_TIPI_RISERVA = [
    "Maggiori quantità CME",
    "Lavorazione/onere non previsto",
    "Sospensione lavori",
    "Variazione progettuale",
    "Ritardo imputabile a SA",
    "Interferenze impreviste",
    "Altro",
]

_ATTI_CONTABILI = [
    "Registro di contabilità",
    "SAL (Stato Avanzamento Lavori)",
    "Verbale di consegna",
    "Verbale di sospensione",
    "Verbale di ripresa",
    "Ordine di Servizio",
]

_STATI_RISERVA_WIZARD = [
    "Iscritta",
    "Esplicitata",
    "Accettata",
    "Rigettata",
    "In accordo bonario",
    "Arbitrato",
]
_TIPI_VERBALE = [
    "consegna_lavori",
    "sospensione",
    "ripresa",
    "sopralluogo",
    "contestazione",
    "collaudo",
]
_ETICHETTE_VERBALE = {
    "consegna_lavori": "Consegna Lavori",
    "sospensione": "Sospensione",
    "ripresa": "Ripresa",
    "sopralluogo": "Sopralluogo",
    "contestazione": "Contestazione",
    "collaudo": "Collaudo",
}
_STATI_NC = ["aperta", "in_lavorazione", "chiusa"]
_EMITTENTI_OS = ["DL", "RUP", "CSE"]
_STATI_OS = ["ricevuto", "in_esecuzione", "evaso", "contestato"]
_STATI_SAL = ["emesso", "in_verifica", "pagato"]

_TIPI_FILE = ["pdf", "docx", "doc", "xlsx", "jpg", "png"]


# ---------------------------------------------------------------------------
# Inizializzazione session state
# ---------------------------------------------------------------------------

def _init_registri() -> None:
    """Inizializza st.session_state.registri se mancante."""
    if "registri" not in st.session_state or st.session_state.registri is None:
        st.session_state.registri = {
            "riserve": [],
            "verbali": [],
            "non_conformita": [],
            "ordini_servizio": [],
            "contabilita_sal": [],
            "schede_accettazione": [],
        }
    # Assicura che tutte le chiavi siano presenti (backward-compat)
    for chiave in ("riserve", "verbali", "non_conformita", "ordini_servizio", "contabilita_sal", "schede_accettazione"):
        if chiave not in st.session_state.registri:
            st.session_state.registri[chiave] = []


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _prossimo_id(lista: list) -> int:
    """Restituisce il prossimo ID incrementale (max esistente + 1, minimo 1)."""
    if not lista:
        return 1
    return max(item.get("id", 0) for item in lista) + 1


def _numero_progressivo(prefisso: str, lista: list, campo: str = "numero") -> str:
    """Genera un numero progressivo es. R001, V003, NC002."""
    n = len(lista) + 1
    return f"{prefisso}{n:03d}"


def _formatta_importo(valore: float) -> str:
    """Formatta un float come importo in euro (es. € 12.345,67)."""
    if valore is None or valore == 0:
        return "€ 0,00"
    return f"€ {valore:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _salva_file_allegato(
    uploaded_file,
    sottocartella: str,
    prefisso: str,
    record_id: int,
    results_dir: pathlib.Path,
) -> str | None:
    """
    Salva un file caricato dall'utente nella sottocartella appropriata.
    Restituisce il nome file salvato, oppure None se fallisce.
    """
    if uploaded_file is None:
        return None
    try:
        dest_dir = results_dir / "registri" / sottocartella
        dest_dir.mkdir(parents=True, exist_ok=True)
        nome_file = f"{prefisso}{record_id}_{uploaded_file.name}"
        dest_path = dest_dir / nome_file
        with open(dest_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return nome_file
    except Exception as exc:
        st.error(f"Errore nel salvataggio del file: {exc}")
        return None


def _scarica_file_allegato(
    nome_file: str,
    sottocartella: str,
    results_dir: pathlib.Path,
) -> bytes | None:
    """Restituisce i byte di un file allegato, oppure None se non trovato."""
    percorso = results_dir / "registri" / sottocartella / nome_file
    if percorso.exists():
        return percorso.read_bytes()
    return None


def _parse_data_sicura(valore: str) -> date | None:
    """Converte una stringa ISO in date, restituisce None se non valida."""
    if not valore:
        return None
    try:
        return date.fromisoformat(valore)
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Funzione principale (entry point)
# ---------------------------------------------------------------------------

def render_registri_tab(
    csa_data: dict,
    details: dict,
    results_dir: pathlib.Path,
    salva_fn,
    importo_netto: float = 0.0,
    include_verbali: bool = True,
    include_contabilita: bool = True,
    include_schede_accettazione: bool = False,
) -> None:
    _init_registri()

    st.header("🗂️ Registri di Cantiere")
    st.caption(
        "Gestione registri ufficiali ai sensi del D.Lgs. 36/2023 e DM 49/2018."
    )

    # Build tab list dynamically
    tab_names = ["📋 Riserve"]
    if include_verbali:
        tab_names.append("📝 Verbali")
    tab_names.extend(["⚠️ Non Conformità", "📨 Ordini di Servizio"])
    if include_schede_accettazione:
        tab_names.append("✅ Schede Accettazione")

    tabs = st.tabs(tab_names)
    idx = 0

    with tabs[idx]:
        _render_riserve(csa_data, details, importo_netto, results_dir, salva_fn)
    idx += 1

    if include_verbali:
        with tabs[idx]:
            _render_verbali(csa_data, details, results_dir, salva_fn)
        idx += 1

    with tabs[idx]:
        _render_non_conformita(csa_data, details, results_dir, salva_fn)
    idx += 1

    with tabs[idx]:
        _render_ordini_servizio(csa_data, details, results_dir, salva_fn)
    idx += 1

    if include_schede_accettazione:
        with tabs[idx]:
            _render_schede_accettazione(csa_data, salva_fn, results_dir)

    if include_contabilita:
        st.divider()
        _render_contabilita_sal(csa_data, details, importo_netto, results_dir, salva_fn)


# ===========================================================================
# SEZIONE A — RISERVE (wizard 4-step Art. 120 D.Lgs. 36/2023)
# ===========================================================================

def _genera_pdf_riserva(riserva: dict, csa_data: dict) -> bytes | None:
    """Genera PDF della riserva con stile carta intestata."""
    try:
        from fpdf import FPDF
        FONT_REG  = str(pathlib.Path("fonts") / "DejaVuSans.ttf")
        FONT_BOLD = str(pathlib.Path("fonts") / "DejaVuSans-Bold.ttf")

        pdf = FPDF()
        pdf.add_page()
        pdf.add_font("DejaVu", "",  FONT_REG,  uni=True)
        pdf.add_font("DejaVu", "B", FONT_BOLD, uni=True)

        def _sezione(titolo: str) -> None:
            pdf.set_font("DejaVu", "B", 10)
            pdf.set_fill_color(30, 80, 160)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(0, 7, titolo, ln=True, fill=True)
            pdf.set_text_color(0, 0, 0)

        def _riga(label: str, valore: str) -> None:
            pdf.set_font("DejaVu", "B", 9)
            pdf.cell(60, 6, f"  {label}:", border=0)
            pdf.set_font("DejaVu", "", 9)
            pdf.cell(0, 6, str(valore or "—"), ln=True)

        # Titolo
        pdf.set_font("DejaVu", "B", 13)
        pdf.set_fill_color(30, 80, 160)
        pdf.set_text_color(255, 255, 255)
        rid = riserva.get("id", "—")
        pdf.cell(0, 9, f"RISERVA {rid} — Art. 120 D.Lgs. 36/2023", ln=True, align="C", fill=True)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(4)

        _sezione("DATI APPALTO")
        _riga("Oggetto lavori", csa_data.get("tipo_lavori", "—"))
        _riga("Stazione Appaltante", csa_data.get("stazione_appaltante", "—"))
        _riga("Comune", f"{csa_data.get('comune', '—')} ({csa_data.get('provincia', '—')})")
        _riga("CIG", csa_data.get("cig", "—"))
        pdf.ln(3)

        _sezione("EVENTO SCATENANTE")
        _riga("Tipo riserva", riserva.get("tipo", riserva.get("causale", "—")))
        _riga("Lavorazione interessata", riserva.get("lavorazione", "—"))
        _riga("Data evento", riserva.get("data_evento", riserva.get("data_fatto_generatore", "—")))
        pdf.set_font("DejaVu", "B", 9)
        pdf.cell(0, 6, "  Descrizione:", ln=True)
        pdf.set_font("DejaVu", "", 9)
        desc = riserva.get("descrizione_evento", riserva.get("causale", "—"))
        pdf.multi_cell(0, 5, f"  {desc}")
        pdf.ln(3)

        _sezione("ATTO CONTABILE")
        _riga("Atto", riserva.get("atto_contabile", "—"))
        _riga("Numero/riferimento", riserva.get("numero_atto", riserva.get("numero", "—")))
        _riga("Data atto", riserva.get("data_atto", riserva.get("data_iscrizione", "—")))
        _riga("Scadenza esplicitazione (15 gg)", riserva.get("scadenza_esplicitazione", "—"))
        _riga("Scadenza risposta DL (30 gg)", riserva.get("scadenza_risposta_dl", "—"))
        pdf.ln(3)

        _sezione("QUANTIFICAZIONE")
        importo = riserva.get("importo_indicativo") or riserva.get("importo_richiesto") or 0.0
        _riga("Importo indicativo", f"€ {float(importo):,.2f}")
        pdf.set_font("DejaVu", "B", 9)
        pdf.cell(0, 6, "  Base di calcolo:", ln=True)
        pdf.set_font("DejaVu", "", 9)
        pdf.multi_cell(0, 5, f"  {riserva.get('base_calcolo', '—')}")
        pdf.set_font("DejaVu", "B", 9)
        pdf.cell(0, 6, "  Causa:", ln=True)
        pdf.set_font("DejaVu", "", 9)
        pdf.multi_cell(0, 5, f"  {riserva.get('causa', riserva.get('causale', '—'))}")
        pdf.ln(3)

        if riserva.get("testo_riserva"):
            _sezione("TESTO FORMALE DELLA RISERVA")
            pdf.set_font("DejaVu", "", 8)
            pdf.multi_cell(0, 5, riserva["testo_riserva"])
            pdf.ln(3)

        _sezione("STATO")
        _riga("Stato attuale", riserva.get("stato", "—"))
        _riga("Data creazione", riserva.get("data_creazione", "—"))

        pdf.ln(12)
        pdf.set_font("DejaVu", "B", 9)
        pdf.cell(90, 6, "Il Direttore dei Lavori", align="C")
        pdf.cell(0, 6, "Il Rappresentante dell'Impresa", align="C", ln=True)
        pdf.ln(14)
        pdf.set_font("DejaVu", "", 9)
        pdf.cell(90, 6, "_" * 35, align="C")
        pdf.cell(0, 6, "_" * 35, align="C", ln=True)

        buf = io.BytesIO()
        pdf.output(buf)
        buf.seek(0)
        return buf.read()
    except Exception as exc:
        st.error(f"Errore generazione PDF riserva: {exc}")
        return None


def _wizard_nuova_riserva(riserve: list, results_dir: pathlib.Path, salva_fn) -> None:
    """Wizard 4-step per iscrizione riserva Art. 120 D.Lgs. 36/2023."""

    if "_wiz_ris_step" not in st.session_state:
        st.session_state["_wiz_ris_step"] = 1
    if "_wiz_ris_data" not in st.session_state:
        st.session_state["_wiz_ris_data"] = {}

    step = st.session_state["_wiz_ris_step"]
    wdata = st.session_state["_wiz_ris_data"]

    st.progress(step / 4, text=f"Step {step} di 4 — Iscrizione riserva Art. 120")
    st.divider()

    # ── STEP 1 — Evento scatenante ─────────────────────────────────────────────
    if step == 1:
        st.markdown("### 📋 Step 1: Identifica l'evento")
        with st.form("wiz_ris_step1", clear_on_submit=False):
            tipo_riserva = st.selectbox(
                "Tipo riserva",
                _TIPI_RISERVA,
                index=_TIPI_RISERVA.index(wdata.get("tipo", _TIPI_RISERVA[0]))
                      if wdata.get("tipo") in _TIPI_RISERVA else 0,
            )
            data_evento = st.date_input(
                "Data in cui si è verificato l'evento",
                value=_parse_data_sicura(wdata.get("data_evento")) or date.today(),
            )
            descrizione_evento = st.text_area(
                "Descrizione evento",
                value=wdata.get("descrizione_evento", ""),
                placeholder="Descrivere cosa è successo...",
                height=100,
            )
            lavorazione = st.text_input(
                "Lavorazione interessata",
                value=wdata.get("lavorazione", ""),
                placeholder="Es. Copertura tetto in legno lamellare",
            )
            avanti = st.form_submit_button("Avanti →", type="primary")
            if avanti:
                if not lavorazione.strip():
                    st.error("Indicare la lavorazione interessata.")
                elif not descrizione_evento.strip():
                    st.error("Descrivere l'evento scatenante.")
                else:
                    wdata.update({
                        "tipo": tipo_riserva,
                        "data_evento": data_evento.isoformat(),
                        "descrizione_evento": descrizione_evento.strip(),
                        "lavorazione": lavorazione.strip(),
                    })
                    st.session_state["_wiz_ris_step"] = 2
                    st.rerun()

    # ── STEP 2 — Atto contabile ────────────────────────────────────────────────
    elif step == 2:
        st.markdown("### 📄 Step 2: Atto contabile su cui iscrivere")
        st.warning(
            "⚠️ La riserva va iscritta sul **PRIMO atto contabile utile** successivo all'evento. "
            "Non aspettare SAL successivi!"
        )
        with st.form("wiz_ris_step2", clear_on_submit=False):
            atto_contabile = st.selectbox(
                "Atto contabile",
                _ATTI_CONTABILI,
                index=_ATTI_CONTABILI.index(wdata.get("atto_contabile", _ATTI_CONTABILI[0]))
                      if wdata.get("atto_contabile") in _ATTI_CONTABILI else 0,
            )
            numero_atto = st.text_input(
                "Numero/riferimento atto",
                value=wdata.get("numero_atto", ""),
                placeholder="Es. SAL n.3, V-2024-05",
            )
            data_atto = st.date_input(
                "Data atto contabile",
                value=_parse_data_sicura(wdata.get("data_atto")) or date.today(),
            )

            scad_espl = data_atto + timedelta(days=15)
            st.info(f"📅 Devi esplicitare e quantificare entro: **{scad_espl.strftime('%d/%m/%Y')}** (15 giorni dall'atto)")

            col_b, col_n = st.columns(2)
            with col_b:
                indietro = st.form_submit_button("← Indietro")
            with col_n:
                avanti = st.form_submit_button("Avanti →", type="primary")

            if indietro:
                st.session_state["_wiz_ris_step"] = 1
                st.rerun()
            if avanti:
                if not numero_atto.strip():
                    st.error("Indicare il numero/riferimento dell'atto contabile.")
                else:
                    wdata.update({
                        "atto_contabile": atto_contabile,
                        "numero_atto": numero_atto.strip(),
                        "data_atto": data_atto.isoformat(),
                        "scadenza_esplicitazione": scad_espl.isoformat(),
                        "scadenza_risposta_dl": (data_atto + timedelta(days=30)).isoformat(),
                    })
                    st.session_state["_wiz_ris_step"] = 3
                    st.rerun()

    # ── STEP 3 — Quantificazione ───────────────────────────────────────────────
    elif step == 3:
        st.markdown("### 💶 Step 3: Quantifica la riserva")

        importo_indicativo = st.number_input(
            "Importo indicativo € (da esplicitare entro 15 gg)",
            min_value=0.0,
            value=float(wdata.get("importo_indicativo", 0.0)),
            step=100.0,
            format="%.2f",
            key="wiz_ris_importo",
        )
        base_calcolo = st.text_area(
            "Base di calcolo",
            value=wdata.get("base_calcolo", ""),
            placeholder="Es: m³ 20,00 legname x € 450/m³ = € 9.000\noppure: nolo gru € 350/gg x 15gg = € 5.250",
            height=80,
            key="wiz_ris_base_calcolo",
        )
        causa = st.text_area(
            "Causa della riserva (errore progettuale, carenza CME, ecc.)",
            value=wdata.get("causa", ""),
            height=80,
            key="wiz_ris_causa",
        )

        # Testo riserva generato automaticamente
        st.subheader("📝 Testo riserva generato automaticamente")
        tipo_r  = wdata.get("tipo", "—")
        lav_r   = wdata.get("lavorazione", "—")
        dev_r   = wdata.get("data_evento", "—")
        desc_r  = wdata.get("descrizione_evento", "—")
        testo = (
            f"Si iscrive riserva ai sensi dell'Art. 120 D.Lgs. 36/2023 per {tipo_r.lower()} "
            f"relativa alla lavorazione: {lav_r}.\n"
            f"Evento verificatosi in data {dev_r}.\n"
            f"{desc_r}\n"
            f"Importo indicativo: € {importo_indicativo:,.2f}\n"
            f"Base di calcolo: {base_calcolo}\n"
            f"Causa: {causa}\n"
            f"Documentazione a supporto: allegata."
        )
        st.code(testo, language=None)

        file_allegati = st.file_uploader(
            "Allega documentazione (rilievi, preventivi, foto, DDT)",
            accept_multiple_files=True,
            type=_TIPI_FILE,
            key="wiz_ris_allegati",
        )

        col_b, col_n = st.columns(2)
        with col_b:
            if st.button("← Indietro", key="wiz_ris_back3"):
                wdata.update({
                    "importo_indicativo": importo_indicativo,
                    "base_calcolo": base_calcolo,
                    "causa": causa,
                    "testo_riserva": testo,
                })
                st.session_state["_wiz_ris_step"] = 2
                st.rerun()
        with col_n:
            if st.button("Avanti →", type="primary", key="wiz_ris_next3"):
                # Salva file allegati: leggi bytes ora, prima del rerun
                allegati_salvati = []
                if file_allegati:
                    dest_dir = results_dir / "registri" / "riserve"
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    rid_temp = _prossimo_id(riserve)
                    for f in file_allegati:
                        nome = f"r{rid_temp}_{f.name}"
                        (dest_dir / nome).write_bytes(f.getbuffer())
                        allegati_salvati.append(nome)
                wdata.update({
                    "importo_indicativo": importo_indicativo,
                    "base_calcolo": base_calcolo,
                    "causa": causa,
                    "testo_riserva": testo,
                    "file_allegati": allegati_salvati,
                })
                st.session_state["_wiz_ris_step"] = 4
                st.rerun()

    # ── STEP 4 — Riepilogo e salvataggio ──────────────────────────────────────
    elif step == 4:
        st.markdown("### ✅ Step 4: Conferma e salva")

        scad_espl_str = wdata.get("scadenza_esplicitazione", "")
        scad_dl_str   = wdata.get("scadenza_risposta_dl", "")
        scad_espl     = _parse_data_sicura(scad_espl_str)
        giorni_espl   = (scad_espl - date.today()).days if scad_espl else None

        with st.container(border=True):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**Tipo riserva:** {wdata.get('tipo', '—')}")
                st.markdown(f"**Lavorazione:** {wdata.get('lavorazione', '—')}")
                st.markdown(f"**Data evento:** {wdata.get('data_evento', '—')}")
                st.markdown(f"**Atto contabile:** {wdata.get('atto_contabile', '—')} — {wdata.get('numero_atto', '—')}")
                st.markdown(f"**Data atto:** {wdata.get('data_atto', '—')}")
            with c2:
                importo_val = float(wdata.get("importo_indicativo") or 0.0)
                st.markdown(f"**Importo indicativo:** {_formatta_importo(importo_val)}")
                st.markdown(f"**Stato:** Iscritta")
                if giorni_espl is not None:
                    if giorni_espl <= 0:
                        st.error(f"❌ Scadenza esplicitazione: **{scad_espl_str}** — SCADUTA")
                    elif giorni_espl <= 5:
                        st.error(f"🚨 Scadenza esplicitazione: **{scad_espl_str}** (tra {giorni_espl} gg)")
                    else:
                        st.markdown(f"⚠️ **Scadenza esplicitazione:** {scad_espl_str}")
                st.markdown(f"⚠️ **Scadenza risposta DL:** {scad_dl_str}")

            allegati = wdata.get("file_allegati", [])
            if allegati:
                st.markdown(f"**Allegati:** {', '.join(allegati)}")

        col_b, col_s = st.columns(2)
        with col_b:
            if st.button("← Indietro", key="wiz_ris_back4"):
                st.session_state["_wiz_ris_step"] = 3
                st.rerun()
        with col_s:
            if st.button("💾 Salva Riserva", type="primary", key="wiz_ris_salva"):
                nuova_id = _prossimo_id(riserve)
                nuova = {
                    "id": f"RIS-{len(riserve)+1:03d}",
                    "tipo": wdata.get("tipo", ""),
                    "lavorazione": wdata.get("lavorazione", ""),
                    "data_evento": wdata.get("data_evento", ""),
                    "descrizione_evento": wdata.get("descrizione_evento", ""),
                    "atto_contabile": wdata.get("atto_contabile", ""),
                    "numero_atto": wdata.get("numero_atto", ""),
                    "data_atto": wdata.get("data_atto", ""),
                    "scadenza_esplicitazione": wdata.get("scadenza_esplicitazione", ""),
                    "scadenza_risposta_dl": wdata.get("scadenza_risposta_dl", ""),
                    "importo_indicativo": float(wdata.get("importo_indicativo") or 0.0),
                    "base_calcolo": wdata.get("base_calcolo", ""),
                    "causa": wdata.get("causa", ""),
                    "testo_riserva": wdata.get("testo_riserva", ""),
                    "stato": "Iscritta",
                    "file_allegati": wdata.get("file_allegati", []),
                    "data_creazione": date.today().isoformat(),
                    # Campi legacy per compatibilità con vecchia lista
                    "numero": f"RIS-{len(riserve)+1:03d}",
                    "causale": wdata.get("descrizione_evento", ""),
                    "importo_richiesto": float(wdata.get("importo_indicativo") or 0.0),
                    "importo_riconosciuto": 0.0,
                    "data_iscrizione": wdata.get("data_atto", date.today().isoformat()),
                    "data_fatto_generatore": wdata.get("data_evento", date.today().isoformat()),
                    "documenti": wdata.get("file_allegati", []),
                }
                st.session_state.registri["riserve"].append(nuova)
                aggiungi_log(
                    "Riserva iscritta",
                    f"{nuova['id']} — {nuova['tipo']} — {nuova['lavorazione'][:50]}",
                    tab="Registri",
                )
                aggiungi_al_diario(
                    f"Riserva {nuova['id']} iscritta: {nuova['tipo']} su {nuova['lavorazione'][:60]}",
                    "📄 Documento / Verbale",
                )
                salva_fn()
                # Reset wizard
                st.session_state["_wiz_ris_step"] = 1
                st.session_state["_wiz_ris_data"] = {}
                st.success(f"✅ Riserva {nuova['id']} salvata con successo.")
                st.rerun()

        col_ann, _ = st.columns([1, 3])
        with col_ann:
            if st.button("✖ Annulla wizard", key="wiz_ris_annulla"):
                st.session_state["_wiz_ris_step"] = 1
                st.session_state["_wiz_ris_data"] = {}
                st.rerun()


def _render_riserve(csa_data, details, importo_netto, results_dir, salva_fn):
    st.subheader("📋 Registro Riserve")
    st.caption("Riserve iscritte ai sensi dell'art.120 D.Lgs.36/2023.")

    riserve: list = st.session_state.registri["riserve"]

    # ── Riepilogo metriche ────────────────────────────────────────────────────
    totale_importo = sum(
        float(r.get("importo_indicativo") or r.get("importo_richiesto") or 0.0)
        for r in riserve
    )
    totale_riconosciuto = sum(r.get("importo_riconosciuto", 0.0) or 0.0 for r in riserve)
    iscritte = [r for r in riserve if r.get("stato", "").lower() == "iscritta"]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Totale riserve", len(riserve))
    col2.metric("Iscritte (aperte)", len(iscritte))
    col3.metric("Importo richiesto", _formatta_importo(totale_importo))
    col4.metric("Importo riconosciuto", _formatta_importo(totale_riconosciuto))

    # Alert scadenze imminenti
    oggi = date.today()
    for r in riserve:
        if r.get("stato", "").lower() != "iscritta":
            continue
        scad = _parse_data_sicura(r.get("scadenza_esplicitazione", ""))
        if scad is None:
            continue
        gg = (scad - oggi).days
        rid = r.get("id", r.get("numero", "—"))
        lav = r.get("lavorazione", r.get("causale", "—"))[:40]
        if gg <= 0:
            st.error(f"❌ Riserva **{rid}** ({lav}): termine esplicitazione **SCADUTO** ({scad})")
        elif gg <= 3:
            st.error(f"🚨 Riserva **{rid}** ({lav}): esplicitare entro **{gg} giorni** ({scad})")
        elif gg <= 7:
            st.warning(f"⚠️ Riserva **{rid}** ({lav}): esplicitare entro **{gg} giorni** ({scad})")

    st.divider()

    # ── Wizard nuova riserva ──────────────────────────────────────────────────
    step_corrente = st.session_state.get("_wiz_ris_step", 1)
    label_exp = "➕ Nuova riserva — Wizard guidato" if step_corrente == 1 else f"🔄 Wizard in corso — Step {step_corrente}/4"
    with st.expander(label_exp, expanded=(step_corrente > 1)):
        _wizard_nuova_riserva(riserve, results_dir, salva_fn)

    st.divider()

    # ── Lista riserve ─────────────────────────────────────────────────────────
    if not riserve:
        st.info("Nessuna riserva registrata. Usare il wizard sopra per iscrivere una riserva.")
        return

    st.markdown(f"**{len(riserve)} riserve registrate**")

    for idx, riserva in enumerate(riserve):
        rid = riserva.get("id", f"#{idx+1}")
        stato_r = riserva.get("stato", "iscritta")
        importo_r = float(riserva.get("importo_indicativo") or riserva.get("importo_richiesto") or 0.0)
        lav_r = riserva.get("lavorazione", riserva.get("causale", "—"))[:45]

        # Badge scadenza
        scad_espl = _parse_data_sicura(riserva.get("scadenza_esplicitazione", ""))
        badge_scad = ""
        if scad_espl and stato_r.lower() == "iscritta":
            gg_scad = (scad_espl - date.today()).days
            if gg_scad <= 0:
                badge_scad = " ❌SCADUTA"
            elif gg_scad <= 3:
                badge_scad = f" 🚨{gg_scad}gg"
            elif gg_scad <= 7:
                badge_scad = f" ⚠️{gg_scad}gg"

        badge_stato = {
            "iscritta": "🟡", "Iscritta": "🟡",
            "esplicitata": "🔵", "Esplicitata": "🔵",
            "accettata": "🟢", "Accettata": "🟢",
            "rigettata": "🔴", "Rigettata": "🔴",
            "In accordo bonario": "🟠",
            "Arbitrato": "🟣",
            "confermata": "🔵", "quantificata": "🟠",
            "definita": "🟢", "respinta": "🔴",
        }.get(stato_r, "⚪")

        titolo_exp = f"{badge_stato} {rid} — {stato_r}{badge_scad} — {lav_r} — {_formatta_importo(importo_r)}"

        with st.expander(titolo_exp, expanded=False):
            # Cambio stato inline
            tutti_stati = _STATI_RISERVA_WIZARD + [s for s in _STATI_RISERVA if s not in [x.lower() for x in _STATI_RISERVA_WIZARD]]
            idx_stato_cur = next((i for i, s in enumerate(tutti_stati) if s.lower() == stato_r.lower()), 0)
            nuovo_stato = st.selectbox(
                "Stato",
                tutti_stati,
                index=idx_stato_cur,
                key=f"reg_ris_stato_{rid}_{idx}",
            )
            if nuovo_stato != stato_r:
                if st.button("💾 Aggiorna stato", key=f"reg_ris_upd_stato_{rid}_{idx}"):
                    st.session_state.registri["riserve"][idx]["stato"] = nuovo_stato
                    aggiungi_log("Riserva — cambio stato", f"{rid} → {nuovo_stato}", tab="Registri")
                    salva_fn()
                    st.rerun()

            st.markdown("---")

            # Dettagli wizard
            col_vis1, col_vis2 = st.columns(2)
            with col_vis1:
                st.markdown(f"**ID:** {rid}")
                if riserva.get("tipo"):
                    st.markdown(f"**Tipo:** {riserva['tipo']}")
                if riserva.get("lavorazione"):
                    st.markdown(f"**Lavorazione:** {riserva['lavorazione']}")
                if riserva.get("data_evento"):
                    st.markdown(f"**Data evento:** {riserva['data_evento']}")
                if riserva.get("atto_contabile"):
                    st.markdown(f"**Atto:** {riserva['atto_contabile']} — {riserva.get('numero_atto','—')}")
                if riserva.get("data_atto"):
                    st.markdown(f"**Data atto:** {riserva['data_atto']}")
                # Legacy
                if not riserva.get("tipo") and riserva.get("causale"):
                    st.markdown(f"**Causale:** {riserva['causale']}")
            with col_vis2:
                st.markdown(f"**Importo:** {_formatta_importo(importo_r)}")
                if riserva.get("scadenza_esplicitazione"):
                    scad_str = riserva["scadenza_esplicitazione"]
                    scad_d = _parse_data_sicura(scad_str)
                    if scad_d:
                        gg_r = (scad_d - date.today()).days
                        if gg_r <= 0:
                            st.error(f"❌ Esplicitazione scaduta il {scad_str}")
                        elif gg_r <= 3:
                            st.error(f"🚨 Esplicitare entro {gg_r} giorni ({scad_str})")
                        elif gg_r <= 7:
                            st.warning(f"⚠️ Esplicitare entro {gg_r} giorni ({scad_str})")
                        else:
                            st.success(f"✅ Scadenza esplicitazione: {scad_str}")
                if riserva.get("scadenza_risposta_dl"):
                    st.markdown(f"⚠️ **Scadenza risposta DL:** {riserva['scadenza_risposta_dl']}")
                if riserva.get("data_creazione"):
                    st.markdown(f"**Creata il:** {riserva['data_creazione']}")

            if riserva.get("causa"):
                st.markdown(f"**Causa:** {riserva['causa']}")
            if riserva.get("base_calcolo"):
                with st.expander("Base di calcolo"):
                    st.text(riserva["base_calcolo"])
            if riserva.get("testo_riserva"):
                with st.expander("📝 Testo formale riserva"):
                    st.code(riserva["testo_riserva"], language=None)

            # Pulsante PDF
            col_pdf, col_del = st.columns([2, 1])
            with col_pdf:
                if st.button("📄 Genera PDF riserva", key=f"reg_ris_pdf_{rid}_{idx}"):
                    pdf_bytes = _genera_pdf_riserva(riserva, csa_data)
                    if pdf_bytes:
                        st.download_button(
                            "⬇️ Scarica PDF",
                            data=pdf_bytes,
                            file_name=f"riserva_{rid}.pdf",
                            mime="application/pdf",
                            key=f"reg_ris_pdf_dl_{rid}_{idx}",
                        )

            # Documenti allegati
            docs_esistenti = list(riserva.get("file_allegati", []) or riserva.get("documenti", []))
            if docs_esistenti:
                st.markdown("**Documenti allegati:**")
                for nome_doc in docs_esistenti:
                    render_doc_buttons(
                        results_dir / "registri" / "riserve" / nome_doc,
                        key=f"reg_riserve_{rid}_doc_{nome_doc}",
                    )

            # Upload aggiuntivo
            nuovo_doc = st.file_uploader(
                "Allega altro documento",
                type=_TIPI_FILE,
                key=f"reg_riserve_{rid}_upload",
            )
            if nuovo_doc is not None:
                nome_salvato = _salva_file_allegato(nuovo_doc, "riserve", "r", rid, results_dir)
                campo_docs = "file_allegati" if "file_allegati" in riserva else "documenti"
                if nome_salvato and nome_salvato not in docs_esistenti:
                    st.session_state.registri["riserve"][idx].setdefault(campo_docs, []).append(nome_salvato)
                    if campo_docs == "file_allegati":
                        st.session_state.registri["riserve"][idx].setdefault("documenti", []).append(nome_salvato)
                    aggiungi_log("Documento allegato a riserva", f"{rid} — {nome_salvato}", tab="Registri")
                    salva_fn()
                    st.success(f"Documento '{nome_salvato}' allegato.")
                    st.rerun()

            st.markdown("---")
            with col_del:
                if st.button(f"🗑️ Elimina", key=f"reg_riserve_{rid}_del"):
                    st.session_state.registri["riserve"].pop(idx)
                    aggiungi_log("Riserva eliminata", f"{rid}", tab="Registri")
                    salva_fn()
                    st.success(f"Riserva {rid} eliminata.")
                    st.rerun()


# ===========================================================================
# SEZIONE B — VERBALI
# ===========================================================================

def _render_verbali(csa_data, details, results_dir, salva_fn):
    st.subheader("📝 Registro Verbali")
    st.caption("Verbali ufficiali di cantiere: consegna lavori, sospensioni, riprese, sopralluoghi, contestazioni, collaudo.")

    verbali: list = st.session_state.registri["verbali"]

    # ── Riepilogo per tipo ────────────────────────────────────────────────────
    conteggio_tipo: dict = {}
    for v in verbali:
        t = v.get("tipo", "altro")
        conteggio_tipo[t] = conteggio_tipo.get(t, 0) + 1

    if verbali:
        col_metr = st.columns(min(len(conteggio_tipo) + 1, 6))
        col_metr[0].metric("Totale verbali", len(verbali))
        for i, (tipo_v, cnt) in enumerate(conteggio_tipo.items(), 1):
            if i < len(col_metr):
                col_metr[i].metric(_ETICHETTE_VERBALE.get(tipo_v, tipo_v), cnt)
    else:
        st.info("Nessun verbale registrato.")

    st.divider()

    # ── Form nuovo verbale ────────────────────────────────────────────────────
    with st.expander("➕ Nuovo verbale", expanded=False):
        numero_auto_v = _numero_progressivo("V", verbali)
        with st.form("form_nuovo_verbale", clear_on_submit=True):
            st.markdown("**Dati del verbale**")
            col_v1, col_v2 = st.columns(2)
            with col_v1:
                numero_verbale = st.text_input(
                    "Numero verbale",
                    value=numero_auto_v,
                    key="reg_verbali_new_numero",
                )
                data_verbale = st.date_input(
                    "Data verbale",
                    value=date.today(),
                    key="reg_verbali_new_data",
                )
                tipo_verbale = st.selectbox(
                    "Tipo verbale",
                    options=_TIPI_VERBALE,
                    format_func=lambda x: _ETICHETTE_VERBALE.get(x, x),
                    key="reg_verbali_new_tipo",
                )
            with col_v2:
                oggetto_verbale = st.text_input(
                    "Oggetto",
                    placeholder="Es. Verbale di consegna lavori - Lotto 1",
                    key="reg_verbali_new_oggetto",
                )
                presenti_verbale = st.text_input(
                    "Presenti (Nome (Ruolo), ...)",
                    placeholder="Es. Mario Rossi (DL), Luigi Bianchi (Appaltatore)",
                    key="reg_verbali_new_presenti",
                )
            note_verbale = st.text_area(
                "Note e contenuto verbale",
                placeholder="Contenuto del verbale, osservazioni, riserve apposte...",
                height=120,
                key="reg_verbali_new_note",
            )
            submitted_v = st.form_submit_button("💾 Aggiungi verbale", type="primary")
            if submitted_v:
                if not oggetto_verbale.strip():
                    st.error("L'oggetto del verbale è obbligatorio.")
                else:
                    nuovo_v = {
                        "id": _prossimo_id(verbali),
                        "numero": numero_verbale.strip() or numero_auto_v,
                        "data": data_verbale.isoformat(),
                        "tipo": tipo_verbale,
                        "presenti": presenti_verbale.strip(),
                        "oggetto": oggetto_verbale.strip(),
                        "note": note_verbale.strip(),
                        "filename": "",
                    }
                    st.session_state.registri["verbali"].append(nuovo_v)
                    aggiungi_log(
                        "Verbale aggiunto",
                        f"Verbale {nuovo_v['numero']} — {_ETICHETTE_VERBALE.get(tipo_verbale, tipo_verbale)} — {oggetto_verbale[:50]}",
                        tab="Registri",
                    )
                    aggiungi_al_diario(
                        f"Verbale {nuovo_v['numero']} — {_ETICHETTE_VERBALE.get(tipo_verbale, tipo_verbale)}: {oggetto_verbale[:60]}",
                        "📄 Documento / Verbale",
                    )
                    salva_fn()
                    st.success(f"Verbale {nuovo_v['numero']} aggiunto con successo.")
                    st.rerun()

    st.divider()

    # ── Lista verbali ─────────────────────────────────────────────────────────
    if not verbali:
        return

    st.markdown(f"**{len(verbali)} verbali registrati**")

    verbali_ordinati = sorted(verbali, key=lambda x: x.get("data", ""), reverse=True)

    for verbale in verbali_ordinati:
        vid = verbale.get("id", 0)
        numero_v = verbale.get("numero", f"#{vid}")
        tipo_v = verbale.get("tipo", "—")
        data_v = verbale.get("data", "—")
        oggetto_v = verbale.get("oggetto", "—")
        idx_v = next((i for i, x in enumerate(verbali) if x.get("id") == vid), None)

        titolo_v = (
            f"📝 {numero_v} — {_ETICHETTE_VERBALE.get(tipo_v, tipo_v).upper()} "
            f"— {data_v} — {oggetto_v[:50]}"
        )

        with st.expander(titolo_v, expanded=False):
            col_vv1, col_vv2 = st.columns(2)
            with col_vv1:
                st.markdown(f"**Numero:** {numero_v}")
                st.markdown(f"**Data:** {data_v}")
                st.markdown(f"**Tipo:** {_ETICHETTE_VERBALE.get(tipo_v, tipo_v)}")
            with col_vv2:
                st.markdown(f"**Oggetto:** {oggetto_v}")
                st.markdown(f"**Presenti:** {verbale.get('presenti', '—') or '—'}")
            if verbale.get("note"):
                st.markdown(f"**Note:** {verbale.get('note')}")

            # Documento allegato
            filename_v = verbale.get("filename", "")
            if filename_v:
                render_doc_buttons(
                    results_dir / "registri" / "verbali" / filename_v,
                    key=f"reg_verbali_{vid}_doc",
                )

            # Upload verbale scansionato
            upload_v = st.file_uploader(
                "Allega verbale scansionato",
                type=_TIPI_FILE,
                key=f"reg_verbali_{vid}_upload",
            )
            if upload_v is not None:
                nome_sal_v = _salva_file_allegato(upload_v, "verbali", "v", vid, results_dir)
                if nome_sal_v and idx_v is not None and nome_sal_v != filename_v:
                    st.session_state.registri["verbali"][idx_v]["filename"] = nome_sal_v
                    aggiungi_log("Documento allegato a verbale", f"Verbale {numero_v} — {nome_sal_v}", tab="Registri")
                    aggiungi_al_diario(f"Documento allegato a verbale {numero_v}: {nome_sal_v}", "🔵 Adempimento Amministrativo")
                    salva_fn()
                    st.success(f"Documento '{nome_sal_v}' allegato.")
                    st.rerun()

            st.markdown("---")

            # Form modifica
            if idx_v is not None:
                with st.expander("✏️ Modifica verbale", expanded=False):
                    with st.form(f"form_edit_verbale_{vid}"):
                        col_ev1, col_ev2 = st.columns(2)
                        with col_ev1:
                            new_num_v = st.text_input("Numero", value=numero_v, key=f"reg_verbali_{vid}_e_num")
                            data_v_cur = _parse_data_sicura(data_v) or date.today()
                            new_data_v = st.date_input("Data", value=data_v_cur, key=f"reg_verbali_{vid}_e_data")
                            idx_tipo_v = _TIPI_VERBALE.index(tipo_v) if tipo_v in _TIPI_VERBALE else 0
                            new_tipo_v = st.selectbox(
                                "Tipo",
                                _TIPI_VERBALE,
                                index=idx_tipo_v,
                                format_func=lambda x: _ETICHETTE_VERBALE.get(x, x),
                                key=f"reg_verbali_{vid}_e_tipo",
                            )
                        with col_ev2:
                            new_ogg_v = st.text_input("Oggetto", value=oggetto_v, key=f"reg_verbali_{vid}_e_ogg")
                            new_pres_v = st.text_input("Presenti", value=verbale.get("presenti", ""), key=f"reg_verbali_{vid}_e_pres")
                        new_note_v = st.text_area("Note", value=verbale.get("note", ""), height=80, key=f"reg_verbali_{vid}_e_note")
                        if st.form_submit_button("💾 Salva modifiche"):
                            st.session_state.registri["verbali"][idx_v].update({
                                "numero": new_num_v.strip(),
                                "data": new_data_v.isoformat(),
                                "tipo": new_tipo_v,
                                "oggetto": new_ogg_v.strip(),
                                "presenti": new_pres_v.strip(),
                                "note": new_note_v.strip(),
                            })
                            aggiungi_log("Verbale modificato", f"Verbale {new_num_v}", tab="Registri")
                            salva_fn()
                            st.success("Verbale aggiornato.")
                            st.rerun()

                # Elimina
                if st.button(f"🗑️ Elimina verbale {numero_v}", key=f"reg_verbali_{vid}_del"):
                    st.session_state.registri["verbali"].pop(idx_v)
                    aggiungi_log("Verbale eliminato", f"Verbale {numero_v}", tab="Registri")
                    salva_fn()
                    st.success(f"Verbale {numero_v} eliminato.")
                    st.rerun()


# ===========================================================================
# SEZIONE C — NON CONFORMITÀ
# ===========================================================================

def _render_non_conformita(csa_data, details, results_dir, salva_fn):
    st.subheader("⚠️ Registro Non Conformità")
    st.caption("Rilevazioni di non conformità durante l'esecuzione dei lavori.")

    nc_list: list = st.session_state.registri["non_conformita"]

    # ── Metriche colorate ─────────────────────────────────────────────────────
    aperte = [x for x in nc_list if x.get("stato") == "aperta"]
    in_lav = [x for x in nc_list if x.get("stato") == "in_lavorazione"]
    chiuse = [x for x in nc_list if x.get("stato") == "chiusa"]

    col_nc1, col_nc2, col_nc3, col_nc4 = st.columns(4)
    col_nc1.metric("Totale NC", len(nc_list))
    col_nc2.metric("🔴 Aperte", len(aperte))
    col_nc3.metric("🟡 In lavorazione", len(in_lav))
    col_nc4.metric("🟢 Chiuse", len(chiuse))

    if aperte:
        st.warning(f"⚠️ **{len(aperte)} non conformità aperte** — richiedono azioni correttive.")

    st.divider()

    # ── Form nuova NC ─────────────────────────────────────────────────────────
    with st.expander("➕ Nuova non conformità", expanded=False):
        numero_auto_nc = _numero_progressivo("NC", nc_list)
        with st.form("form_nuova_nc", clear_on_submit=True):
            st.markdown("**Dati della non conformità**")
            col_nc_a, col_nc_b = st.columns(2)
            with col_nc_a:
                numero_nc = st.text_input("Numero NC", value=numero_auto_nc, key="reg_nc_new_numero")
                data_rilev = st.date_input("Data rilevazione", value=date.today(), key="reg_nc_new_data")
                lavorazione_nc = st.text_input(
                    "Lavorazione interessata",
                    placeholder="Es. Opere di fondazione - Pali trivellati",
                    key="reg_nc_new_lavorazione",
                )
            with col_nc_b:
                responsabile_nc = st.text_input(
                    "Responsabile",
                    placeholder="Es. Subappaltatore Bianchi Srl",
                    key="reg_nc_new_responsabile",
                )
                stato_nc = st.selectbox("Stato", _STATI_NC, key="reg_nc_new_stato")
                data_chiusura_nc = st.date_input(
                    "Data chiusura (se chiusa)",
                    value=None,
                    key="reg_nc_new_data_chiusura",
                )
            descrizione_nc = st.text_area(
                "Descrizione non conformità",
                placeholder="Descrivere la non conformità rilevata, i riferimenti normativi o contrattuali violati...",
                height=100,
                key="reg_nc_new_descr",
            )
            azioni_nc = st.text_area(
                "Azioni correttive prescritte",
                placeholder="Indicare le azioni correttive richieste all'appaltatore...",
                height=80,
                key="reg_nc_new_azioni",
            )
            submitted_nc = st.form_submit_button("💾 Aggiungi NC", type="primary")
            if submitted_nc:
                if not descrizione_nc.strip():
                    st.error("La descrizione della non conformità è obbligatoria.")
                else:
                    nuova_nc = {
                        "id": _prossimo_id(nc_list),
                        "numero": numero_nc.strip() or numero_auto_nc,
                        "data_rilevazione": data_rilev.isoformat(),
                        "descrizione": descrizione_nc.strip(),
                        "lavorazione": lavorazione_nc.strip(),
                        "responsabile": responsabile_nc.strip(),
                        "stato": stato_nc,
                        "azioni_correttive": azioni_nc.strip(),
                        "data_chiusura": data_chiusura_nc.isoformat() if data_chiusura_nc else "",
                        "documenti": [],
                    }
                    st.session_state.registri["non_conformita"].append(nuova_nc)
                    aggiungi_log(
                        "Non conformità aggiunta",
                        f"NC {nuova_nc['numero']} — {descrizione_nc[:60]}",
                        tab="Registri",
                    )
                    aggiungi_al_diario(
                        f"Non conformità {nuova_nc['numero']} rilevata: {descrizione_nc[:80]}",
                        "⚠️ Problema / NC",
                    )
                    salva_fn()
                    st.success(f"Non conformità {nuova_nc['numero']} aggiunta.")
                    st.rerun()

    st.divider()

    # ── Lista NC ──────────────────────────────────────────────────────────────
    if not nc_list:
        return

    st.markdown(f"**{len(nc_list)} non conformità registrate**")

    nc_ordinata = sorted(nc_list, key=lambda x: x.get("data_rilevazione", ""), reverse=True)

    for nc in nc_ordinata:
        ncid = nc.get("id", 0)
        numero_nc_vis = nc.get("numero", f"#{ncid}")
        stato_nc_vis = nc.get("stato", "aperta")
        idx_nc = next((i for i, x in enumerate(nc_list) if x.get("id") == ncid), None)

        badge_nc = {"aperta": "🔴", "in_lavorazione": "🟡", "chiusa": "🟢"}.get(stato_nc_vis, "⚪")
        titolo_nc = (
            f"{badge_nc} {numero_nc_vis} — {stato_nc_vis.upper()} — "
            f"{nc.get('data_rilevazione', '—')} — {nc.get('descrizione', '')[:50]}"
        )

        with st.expander(titolo_nc, expanded=False):
            col_ncv1, col_ncv2 = st.columns(2)
            with col_ncv1:
                st.markdown(f"**Numero:** {numero_nc_vis}")
                st.markdown(f"**Data rilevazione:** {nc.get('data_rilevazione', '—')}")
                st.markdown(f"**Lavorazione:** {nc.get('lavorazione', '—') or '—'}")
                st.markdown(f"**Responsabile:** {nc.get('responsabile', '—') or '—'}")
            with col_ncv2:
                st.markdown(f"**Stato:** {stato_nc_vis}")
                if nc.get("data_chiusura"):
                    st.markdown(f"**Data chiusura:** {nc.get('data_chiusura')}")
            st.markdown(f"**Descrizione:** {nc.get('descrizione', '—')}")
            if nc.get("azioni_correttive"):
                st.markdown(f"**Azioni correttive:** {nc.get('azioni_correttive')}")

            # Documenti
            docs_nc = nc.get("documenti", [])
            if docs_nc:
                st.markdown("**Documenti allegati:**")
                for doc_nc in docs_nc:
                    render_doc_buttons(
                        results_dir / "registri" / "nc" / doc_nc,
                        key=f"reg_nc_{ncid}_doc_{doc_nc}",
                    )

            upload_nc = st.file_uploader("Allega documento NC", type=_TIPI_FILE, key=f"reg_nc_{ncid}_upload")
            if upload_nc is not None:
                nome_sal_nc = _salva_file_allegato(upload_nc, "nc", "nc", ncid, results_dir)
                if nome_sal_nc and idx_nc is not None and nome_sal_nc not in docs_nc:
                    st.session_state.registri["non_conformita"][idx_nc]["documenti"].append(nome_sal_nc)
                    aggiungi_log("Documento allegato a NC", f"NC {numero_nc_vis} — {nome_sal_nc}", tab="Registri")
                    aggiungi_al_diario(f"Documento allegato a NC {numero_nc_vis}: {nome_sal_nc}", "🔵 Adempimento Amministrativo")
                    salva_fn()
                    st.success(f"Documento '{nome_sal_nc}' allegato.")
                    st.rerun()

            st.markdown("---")

            if idx_nc is not None:
                with st.expander("✏️ Modifica NC", expanded=False):
                    with st.form(f"form_edit_nc_{ncid}"):
                        col_enc1, col_enc2 = st.columns(2)
                        with col_enc1:
                            new_num_nc = st.text_input("Numero", value=numero_nc_vis, key=f"reg_nc_{ncid}_e_num")
                            data_ril_cur = _parse_data_sicura(nc.get("data_rilevazione", "")) or date.today()
                            new_data_ril = st.date_input("Data rilevazione", value=data_ril_cur, key=f"reg_nc_{ncid}_e_data")
                            new_lav_nc = st.text_input("Lavorazione", value=nc.get("lavorazione", ""), key=f"reg_nc_{ncid}_e_lav")
                            new_resp_nc = st.text_input("Responsabile", value=nc.get("responsabile", ""), key=f"reg_nc_{ncid}_e_resp")
                        with col_enc2:
                            idx_st_nc = _STATI_NC.index(stato_nc_vis) if stato_nc_vis in _STATI_NC else 0
                            new_stato_nc = st.selectbox("Stato", _STATI_NC, index=idx_st_nc, key=f"reg_nc_{ncid}_e_stato")
                            data_ch_cur = _parse_data_sicura(nc.get("data_chiusura", ""))
                            new_data_ch = st.date_input("Data chiusura", value=data_ch_cur, key=f"reg_nc_{ncid}_e_data_ch")
                        new_descr_nc = st.text_area("Descrizione", value=nc.get("descrizione", ""), height=80, key=f"reg_nc_{ncid}_e_descr")
                        new_azioni_nc = st.text_area("Azioni correttive", value=nc.get("azioni_correttive", ""), height=60, key=f"reg_nc_{ncid}_e_azioni")
                        if st.form_submit_button("💾 Salva modifiche"):
                            st.session_state.registri["non_conformita"][idx_nc].update({
                                "numero": new_num_nc.strip(),
                                "data_rilevazione": new_data_ril.isoformat(),
                                "lavorazione": new_lav_nc.strip(),
                                "responsabile": new_resp_nc.strip(),
                                "stato": new_stato_nc,
                                "data_chiusura": new_data_ch.isoformat() if new_data_ch else "",
                                "descrizione": new_descr_nc.strip(),
                                "azioni_correttive": new_azioni_nc.strip(),
                            })
                            aggiungi_log("NC modificata", f"NC {new_num_nc} → stato: {new_stato_nc}", tab="Registri")
                            salva_fn()
                            st.success("Non conformità aggiornata.")
                            st.rerun()

                if st.button(f"🗑️ Elimina NC {numero_nc_vis}", key=f"reg_nc_{ncid}_del"):
                    st.session_state.registri["non_conformita"].pop(idx_nc)
                    aggiungi_log("NC eliminata", f"NC {numero_nc_vis}", tab="Registri")
                    salva_fn()
                    st.success(f"Non conformità {numero_nc_vis} eliminata.")
                    st.rerun()


# ===========================================================================
# SEZIONE D — ORDINI DI SERVIZIO
# ===========================================================================

def _render_ordini_servizio(csa_data, details, results_dir, salva_fn):
    st.subheader("📨 Registro Ordini di Servizio")
    st.caption("Ordini di servizio emessi da DL, RUP o CSE ai sensi del DM 49/2018.")

    os_list: list = st.session_state.registri["ordini_servizio"]
    oggi_os = date.today()

    # ── Metriche e scaduti ────────────────────────────────────────────────────
    conteggio_os: dict = {}
    for o in os_list:
        s = o.get("stato", "ricevuto")
        conteggio_os[s] = conteggio_os.get(s, 0) + 1

    scaduti = [
        o for o in os_list
        if o.get("termine_adempimento")
        and o.get("stato") not in ("evaso",)
        and _parse_data_sicura(o.get("termine_adempimento", "")) is not None
        and _parse_data_sicura(o.get("termine_adempimento", "")) < oggi_os
    ]

    col_os_m = st.columns(5)
    col_os_m[0].metric("Totale OS", len(os_list))
    for i, stato_os_k in enumerate(["ricevuto", "in_esecuzione", "evaso", "contestato"]):
        col_os_m[i + 1].metric(stato_os_k.replace("_", " ").title(), conteggio_os.get(stato_os_k, 0))

    if scaduti:
        numeri_scad = [o.get("numero", f"#{o.get('id')}") for o in scaduti]
        st.error(
            f"⚠️ **{len(scaduti)} ordini di servizio scaduti non evasi:** "
            f"**{', '.join(numeri_scad)}** — Il termine di adempimento è superato."
        )

    st.divider()

    # ── Form nuovo OS ─────────────────────────────────────────────────────────
    with st.expander("➕ Nuovo ordine di servizio", expanded=False):
        numero_auto_os = _numero_progressivo("OS", os_list)
        with st.form("form_nuovo_os", clear_on_submit=True):
            st.markdown("**Dati dell'ordine di servizio**")
            col_os_a, col_os_b = st.columns(2)
            with col_os_a:
                numero_os = st.text_input("Numero OS", value=numero_auto_os, key="reg_os_new_numero")
                data_em_os = st.date_input("Data emissione", value=date.today(), key="reg_os_new_data_em")
                emittente_os = st.selectbox("Emittente", _EMITTENTI_OS, key="reg_os_new_emittente")
                termine_os = st.date_input(
                    "Termine adempimento (opzionale)",
                    value=None,
                    key="reg_os_new_termine",
                )
            with col_os_b:
                destinatario_os = st.text_input(
                    "Destinatario",
                    placeholder="Es. Impresa Costruzioni SpA",
                    key="reg_os_new_dest",
                )
                oggetto_os = st.text_input(
                    "Oggetto",
                    placeholder="Es. Ripristino giunti di dilatazione ponte",
                    key="reg_os_new_oggetto",
                )
                stato_os_new = st.selectbox("Stato", _STATI_OS, key="reg_os_new_stato")
            descrizione_os = st.text_area(
                "Descrizione e prescrizioni",
                placeholder="Descrivere le prescrizioni, le modalità di adempimento, i riferimenti contrattuali...",
                height=100,
                key="reg_os_new_descr",
            )
            note_os_new = st.text_area("Note", height=60, key="reg_os_new_note")
            submitted_os = st.form_submit_button("💾 Aggiungi ordine di servizio", type="primary")
            if submitted_os:
                if not oggetto_os.strip():
                    st.error("L'oggetto dell'ordine di servizio è obbligatorio.")
                else:
                    nuovo_os = {
                        "id": _prossimo_id(os_list),
                        "numero": numero_os.strip() or numero_auto_os,
                        "data_emissione": data_em_os.isoformat(),
                        "emittente": emittente_os,
                        "destinatario": destinatario_os.strip(),
                        "oggetto": oggetto_os.strip(),
                        "descrizione": descrizione_os.strip(),
                        "termine_adempimento": termine_os.isoformat() if termine_os else "",
                        "stato": stato_os_new,
                        "filename_os": "",
                        "filename_risposta": "",
                        "note": note_os_new.strip(),
                    }
                    st.session_state.registri["ordini_servizio"].append(nuovo_os)
                    aggiungi_log(
                        "Ordine di servizio aggiunto",
                        f"OS {nuovo_os['numero']} da {emittente_os} — {oggetto_os[:60]}",
                        tab="Registri",
                    )
                    aggiungi_al_diario(
                        f"Ordine di Servizio {nuovo_os['numero']} ({emittente_os}): {oggetto_os[:80]}",
                        "🔵 Adempimento Amministrativo",
                    )
                    salva_fn()
                    st.success(f"Ordine di servizio {nuovo_os['numero']} aggiunto.")
                    st.rerun()

    st.divider()

    # ── Lista OS ──────────────────────────────────────────────────────────────
    if not os_list:
        return

    st.markdown(f"**{len(os_list)} ordini di servizio registrati**")

    os_ordinati = sorted(os_list, key=lambda x: x.get("data_emissione", ""), reverse=True)

    for ordine in os_ordinati:
        osid = ordine.get("id", 0)
        numero_os_vis = ordine.get("numero", f"#{osid}")
        stato_os_vis = ordine.get("stato", "ricevuto")
        termine_os_vis = ordine.get("termine_adempimento", "")
        idx_os = next((i for i, x in enumerate(os_list) if x.get("id") == osid), None)

        # Verifica scadenza
        is_scaduto_os = False
        if termine_os_vis and stato_os_vis != "evaso":
            data_t = _parse_data_sicura(termine_os_vis)
            if data_t and data_t < oggi_os:
                is_scaduto_os = True

        badge_os = {
            "ricevuto": "📩",
            "in_esecuzione": "🔄",
            "evaso": "✅",
            "contestato": "⚡",
        }.get(stato_os_vis, "📨")
        scad_label = " ⚠️ SCADUTO" if is_scaduto_os else ""
        titolo_os = (
            f"{badge_os} {numero_os_vis} — {ordine.get('emittente', '—')} — "
            f"{ordine.get('data_emissione', '—')} — {ordine.get('oggetto', '')[:45]}{scad_label}"
        )

        with st.expander(titolo_os, expanded=is_scaduto_os):
            if is_scaduto_os:
                st.error(f"⚠️ Termine adempimento **{termine_os_vis}** superato — OS non ancora evaso.")

            col_osv1, col_osv2 = st.columns(2)
            with col_osv1:
                st.markdown(f"**Numero:** {numero_os_vis}")
                st.markdown(f"**Data emissione:** {ordine.get('data_emissione', '—')}")
                st.markdown(f"**Emittente:** {ordine.get('emittente', '—')}")
                st.markdown(f"**Destinatario:** {ordine.get('destinatario', '—') or '—'}")
            with col_osv2:
                st.markdown(f"**Oggetto:** {ordine.get('oggetto', '—')}")
                st.markdown(f"**Termine adempimento:** {termine_os_vis or 'Non specificato'}")
                st.markdown(f"**Stato:** {stato_os_vis}")
            if ordine.get("descrizione"):
                st.markdown(f"**Descrizione:** {ordine.get('descrizione')}")
            if ordine.get("note"):
                st.markdown(f"**Note:** {ordine.get('note')}")

            # File OS e risposta
            for file_campo, label_campo, sottoc_campo, prefisso_campo in [
                ("filename_os", "Documento OS", "os", "os"),
                ("filename_risposta", "Risposta appaltatore", "os", "os_risp"),
            ]:
                fname = ordine.get(file_campo, "")
                if fname:
                    st.caption(f"📎 {label_campo}")
                    render_doc_buttons(
                        results_dir / "registri" / sottoc_campo / fname,
                        key=f"reg_os_{osid}_doc_{file_campo}",
                    )

                upload_os_f = st.file_uploader(
                    f"Allega {label_campo}",
                    type=_TIPI_FILE,
                    key=f"reg_os_{osid}_upload_{file_campo}",
                )
                if upload_os_f is not None and idx_os is not None:
                    nome_sal_os = _salva_file_allegato(upload_os_f, sottoc_campo, prefisso_campo, osid, results_dir)
                    if nome_sal_os and nome_sal_os != fname:
                        st.session_state.registri["ordini_servizio"][idx_os][file_campo] = nome_sal_os
                        aggiungi_log(f"{label_campo} allegato a OS", f"OS {numero_os_vis} — {nome_sal_os}", tab="Registri")
                        aggiungi_al_diario(f"{label_campo} allegato a OS {numero_os_vis}: {nome_sal_os}", "🔵 Adempimento Amministrativo")
                        salva_fn()
                        st.success(f"'{nome_sal_os}' allegato.")
                        st.rerun()

            st.markdown("---")

            if idx_os is not None:
                with st.expander("✏️ Modifica OS", expanded=False):
                    with st.form(f"form_edit_os_{osid}"):
                        col_eos1, col_eos2 = st.columns(2)
                        with col_eos1:
                            new_num_os = st.text_input("Numero", value=numero_os_vis, key=f"reg_os_{osid}_e_num")
                            data_em_cur = _parse_data_sicura(ordine.get("data_emissione", "")) or date.today()
                            new_data_em = st.date_input("Data emissione", value=data_em_cur, key=f"reg_os_{osid}_e_data")
                            idx_em = _EMITTENTI_OS.index(ordine.get("emittente", "DL")) if ordine.get("emittente") in _EMITTENTI_OS else 0
                            new_emit = st.selectbox("Emittente", _EMITTENTI_OS, index=idx_em, key=f"reg_os_{osid}_e_emit")
                            data_term_cur = _parse_data_sicura(ordine.get("termine_adempimento", ""))
                            new_termine = st.date_input("Termine adempimento", value=data_term_cur, key=f"reg_os_{osid}_e_termine")
                        with col_eos2:
                            new_dest_os = st.text_input("Destinatario", value=ordine.get("destinatario", ""), key=f"reg_os_{osid}_e_dest")
                            new_ogg_os = st.text_input("Oggetto", value=ordine.get("oggetto", ""), key=f"reg_os_{osid}_e_ogg")
                            idx_st_os = _STATI_OS.index(stato_os_vis) if stato_os_vis in _STATI_OS else 0
                            new_stato_os = st.selectbox("Stato", _STATI_OS, index=idx_st_os, key=f"reg_os_{osid}_e_stato")
                        new_descr_os = st.text_area("Descrizione", value=ordine.get("descrizione", ""), height=80, key=f"reg_os_{osid}_e_descr")
                        new_note_os = st.text_area("Note", value=ordine.get("note", ""), height=60, key=f"reg_os_{osid}_e_note")
                        if st.form_submit_button("💾 Salva modifiche"):
                            st.session_state.registri["ordini_servizio"][idx_os].update({
                                "numero": new_num_os.strip(),
                                "data_emissione": new_data_em.isoformat(),
                                "emittente": new_emit,
                                "destinatario": new_dest_os.strip(),
                                "oggetto": new_ogg_os.strip(),
                                "descrizione": new_descr_os.strip(),
                                "termine_adempimento": new_termine.isoformat() if new_termine else "",
                                "stato": new_stato_os,
                                "note": new_note_os.strip(),
                            })
                            aggiungi_log("OS modificato", f"OS {new_num_os} → stato: {new_stato_os}", tab="Registri")
                            salva_fn()
                            st.success("Ordine di servizio aggiornato.")
                            st.rerun()

                if st.button(f"🗑️ Elimina OS {numero_os_vis}", key=f"reg_os_{osid}_del"):
                    st.session_state.registri["ordini_servizio"].pop(idx_os)
                    aggiungi_log("OS eliminato", f"OS {numero_os_vis}", tab="Registri")
                    salva_fn()
                    st.success(f"Ordine di servizio {numero_os_vis} eliminato.")
                    st.rerun()


# ===========================================================================
# SEZIONE E — SCHEDE DI ACCETTAZIONE MATERIALI
# ===========================================================================

def _render_schede_accettazione(csa_data: dict, salva_fn, results_dir) -> None:
    _init_registri()
    registri = st.session_state.registri
    schede: list = registri.get("schede_accettazione", [])

    # ── SEZIONE DOCUMENTI AZIENDALI — caricati una volta, validi per tutte le schede ──
    has_carta = bool(st.session_state.get("dtc_carta_intestata_bytes"))
    has_timbro = bool(st.session_state.get("dtc_timbro_bytes"))
    has_firma = bool(st.session_state.get("dtc_firma_bytes"))
    with st.expander("🏢 Documenti Aziendali (carta intestata, timbro, firma)", expanded=not has_carta):
        st.caption("Caricali una volta sola — verranno usati automaticamente in tutte le schede")
        col1_az, col2_az, col3_az = st.columns(3)
        with col1_az:
            if has_carta:
                st.success(f"✅ Carta intestata: {st.session_state.get('dtc_carta_intestata_nome', 'caricata')}")
            else:
                st.warning("⚠️ Nessuna carta intestata")
            up_carta = st.file_uploader("Carta intestata", type=["jpg", "png", "pdf"], key="up_carta_glob")
            if up_carta:
                st.session_state["dtc_carta_intestata_bytes"] = up_carta.read()
                st.session_state["dtc_carta_intestata_nome"] = up_carta.name
                st.success("✅ Salvata")
        with col2_az:
            if has_timbro:
                st.success("✅ Timbro caricato")
            else:
                st.warning("⚠️ Nessun timbro")
            up_timbro = st.file_uploader("Timbro", type=["jpg", "png"], key="up_timbro_glob")
            if up_timbro:
                st.session_state["dtc_timbro_bytes"] = up_timbro.read()
                st.success("✅ Salvato")
        with col3_az:
            if has_firma:
                st.success("✅ Firma caricata")
            else:
                st.warning("⚠️ Nessuna firma")
            up_firma = st.file_uploader("Firma", type=["jpg", "png"], key="up_firma_glob")
            if up_firma:
                st.session_state["dtc_firma_bytes"] = up_firma.read()
                st.success("✅ Salvata")

    with st.expander("➕ Nuova Scheda di Accettazione", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            data_acc = st.date_input("Data accettazione", value=date.today(), key="acc_data")
            materiale = st.text_input("Materiale / Descrizione", key="acc_materiale", placeholder="Es: Cemento, Acciaio, Laterizi…")
        with col2:
            fornitore = st.text_input("Fornitore", key="acc_fornitore", placeholder="Nome azienda")
            quantita = st.text_input("Quantità", key="acc_quantita", placeholder="Es: 100 sacchi, 5 tonnellate")

        note = st.text_area("Note / Difetti rilevati", key="acc_note", height=80)

        col3, col4 = st.columns(2)
        with col3:
            stato = st.selectbox(
                "Stato accettazione",
                ["Accettato", "Accettato con difetti", "Rifiutato"],
                key="acc_stato",
            )
        with col4:
            is_cam = st.checkbox("🌿 Prodotto CAM (D.M. 23/06/2022)", key="acc_is_cam")

        st.markdown("**📎 Certificati prodotto**")
        cert_links = st.text_area("Link certificati (uno per riga)", key="acc_cert_links", placeholder="https://produttore.it/certificato-ce.pdf", height=80)
        cert_files = st.file_uploader("PDF certificati", type=["pdf"], key="acc_cert_files", accept_multiple_files=True)

        if st.button("💾 Salva Scheda", key="btn_salva_scheda_acc"):
            scheda_id = f"sch_{int(time.time() * 1000)}"
            numero_progressivo = len(schede) + 1
            nuova_scheda = {
                "id": scheda_id,
                "numero": numero_progressivo,
                "anno": date.today().year,
                "numero_label": f"n. {numero_progressivo} del {date.today().strftime('%d/%m/%Y')}",
                "data": str(data_acc),
                "materiale": materiale,
                "fornitore": fornitore,
                "quantita": quantita,
                "note": note,
                "stato": stato,
                "is_cam": is_cam,
                "cert_links": [l.strip() for l in cert_links.splitlines() if l.strip()],
                "cert_files_nomi": [f.name for f in cert_files] if cert_files else [],
                "file_allegati": [],
            }
            # Bytes in session_state separato — NON nel JSON salvato su disco
            st.session_state[f"_scheda_media_{scheda_id}"] = {
                "carta_intestata_bytes": st.session_state.get("dtc_carta_intestata_bytes"),
                "timbro_bytes": st.session_state.get("dtc_timbro_bytes"),
                "firma_bytes": st.session_state.get("dtc_firma_bytes"),
            }
            schede.append(nuova_scheda)
            registri["schede_accettazione"] = schede
            st.session_state.registri = registri
            salva_fn()
            aggiungi_log("Scheda accettazione registrata", f"{materiale} — {stato}", tab="Registri")
            st.success(f"✅ Scheda '{materiale}' registrata ({nuova_scheda['numero_label']})")
            st.rerun()

        if st.button("📄 Crea Scheda di Accettazione", key="btn_crea_scheda_form", help="Genera PDF dai dati inseriti senza salvare"):
            numero_temp = len(schede) + 1
            scheda_temp = {
                "numero": numero_temp,
                "numero_label": f"n. {numero_temp} del {date.today().strftime('%d/%m/%Y')}",
                "data": str(data_acc),
                "materiale": materiale,
                "fornitore": fornitore,
                "quantita": quantita,
                "note": note,
                "stato": stato,
                "is_cam": is_cam,
                "cert_links": [l.strip() for l in cert_links.splitlines() if l.strip()],
                "cert_files_nomi": [f.name for f in cert_files] if cert_files else [],
            }
            pdf_bytes = _genera_pdf_scheda_accettazione(scheda_temp, csa_data)
            if pdf_bytes:
                nome_file = f"Scheda_Accettazione_{materiale.replace(' ', '_')}_{data_acc}.pdf"
                st.download_button(
                    label="⬇️ Scarica PDF",
                    data=pdf_bytes,
                    file_name=nome_file,
                    mime="application/pdf",
                    key="download_scheda_form",
                )

    if schede:
        st.markdown("### Schede registrate")
        for idx, scheda in enumerate(schede):
            with st.container(border=True):
                col_a, col_b, col_c = st.columns([2, 2, 1])
                with col_a:
                    stato_emoji = {
                        "Accettato": "✅",
                        "Accettato con difetti": "⚠️",
                        "Rifiutato": "❌",
                    }.get(scheda.get("stato", ""), "—")
                    num_label = scheda.get("numero_label", f"n. {idx + 1}")
                    st.markdown(f"**{stato_emoji} [{num_label}] {scheda.get('materiale', '—')}**")
                    st.caption(f"Fornitore: {scheda.get('fornitore', '—')}")
                    st.caption(f"Quantità: {scheda.get('quantita', '—')}")
                    if scheda.get("is_cam"):
                        st.caption("🌿 Prodotto CAM")
                with col_b:
                    st.caption(f"📅 {scheda.get('data', '—')}")
                    nota = scheda.get("note", "—") or "—"
                    st.caption(f"Note: {nota[:100]}")
                    if scheda.get("cert_links"):
                        st.caption(f"🔗 {len(scheda['cert_links'])} certificati")
                with col_c:
                    if st.button("📄 Crea Scheda", key=f"crea_scheda_{idx}"):
                        st.session_state[f"show_pdf_{idx}"] = True

                    if st.session_state.get(f"show_pdf_{idx}"):
                        scheda_id = scheda.get("id")
                        media = st.session_state.get(f"_scheda_media_{scheda_id}", {})
                        scheda_con_media = {**scheda, **media}
                        pdf_bytes = _genera_pdf_scheda_accettazione(scheda_con_media, csa_data)
                        if pdf_bytes:
                            nome_file = (
                                f"Scheda_Accettazione_"
                                f"{scheda.get('materiale', '').replace(' ', '_')}_"
                                f"{scheda.get('data', '')}.pdf"
                            )
                            st.download_button(
                                label="⬇️ Scarica PDF",
                                data=pdf_bytes,
                                file_name=nome_file,
                                mime="application/pdf",
                                key=f"download_scheda_{idx}",
                            )

                    if st.button("🗑️", key=f"del_scheda_{idx}", help="Elimina scheda"):
                        scheda_id = scheda.get("id")
                        st.session_state.pop(f"_scheda_media_{scheda_id}", None)
                        st.session_state.pop(f"show_pdf_{idx}", None)
                        schede.pop(idx)
                        registri["schede_accettazione"] = schede
                        st.session_state.registri = registri
                        salva_fn()
                        st.rerun()
    else:
        st.info("Nessuna scheda di accettazione registrata.")


def _genera_pdf_scheda_accettazione(scheda: dict, csa_data: dict) -> bytes | None:
    try:
        from fpdf import FPDF
        from PIL import Image

        FONT_REG  = str(pathlib.Path("fonts") / "DejaVuSans.ttf")
        FONT_BOLD = str(pathlib.Path("fonts") / "DejaVuSans-Bold.ttf")

        def _img_to_buf(raw_bytes: bytes) -> io.BytesIO:
            img = Image.open(io.BytesIO(raw_bytes)).convert("RGBA")
            bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
            bg.paste(img, mask=img.split()[3] if img.mode == "RGBA" else None)
            buf = io.BytesIO()
            bg.convert("RGB").save(buf, format="PNG")
            buf.seek(0)
            return buf

        pdf = FPDF()
        pdf.add_page()
        pdf.add_font("DejaVu", "",  FONT_REG,  uni=True)
        pdf.add_font("DejaVu", "B", FONT_BOLD, uni=True)

        # HEADER — carta intestata (prima di qualsiasi ln/cell)
        carta_bytes = (
            scheda.get("carta_intestata_bytes")
            or st.session_state.get("dtc_carta_intestata_bytes")
        )
        if carta_bytes:
            try:
                img_c = Image.open(io.BytesIO(carta_bytes)).convert("RGB")
                buf_c = io.BytesIO()
                img_c.save(buf_c, format="PNG")
                buf_c.seek(0)
                pdf.image(buf_c, x=10, y=8, w=190, h=40)
                pdf.set_y(52)
            except Exception:
                pdf.set_font("DejaVu", "B", 11)
                pdf.cell(0, 8, "[ Carta intestata ]", ln=True, align="C")
        else:
            pdf.set_font("DejaVu", "B", 11)
            ditta = csa_data.get("appaltatore", csa_data.get("stazione_appaltante", "Impresa Appaltatrice"))
            pdf.cell(0, 8, ditta, ln=True, align="C")
            pdf.ln(4)

        # TITOLO
        pdf.set_font("DejaVu", "B", 13)
        pdf.set_fill_color(30, 80, 160)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 9, "SCHEDA DI ACCETTAZIONE MATERIALI", ln=True, align="C", fill=True)
        pdf.set_text_color(0, 0, 0)

        # NUMERAZIONE CRONOLOGICA
        num_label = scheda.get("numero_label", "")
        if not num_label and scheda.get("numero"):
            data_str = scheda.get("data", "")
            try:
                from datetime import datetime as _dt
                data_fmt = _dt.strptime(data_str, "%Y-%m-%d").strftime("%d/%m/%Y")
            except Exception:
                data_fmt = data_str
            num_label = f"n. {scheda['numero']} del {data_fmt}"
        if num_label:
            pdf.set_font("DejaVu", "B", 11)
            pdf.cell(0, 7, num_label, ln=True, align="C")
        pdf.ln(5)

        # BADGE CAM
        if scheda.get("is_cam"):
            pdf.set_font("DejaVu", "B", 10)
            pdf.set_fill_color(0, 150, 80)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(0, 7, "PRODOTTO CAM — Criteri Ambientali Minimi (D.M. 23/06/2022)", ln=True, align="C", fill=True)
            pdf.set_text_color(0, 0, 0)
            pdf.ln(4)

        def _sezione(titolo: str) -> None:
            pdf.set_font("DejaVu", "B", 10)
            pdf.set_fill_color(220, 228, 245)
            pdf.cell(0, 7, titolo, ln=True, fill=True)

        def _riga(label: str, valore: str) -> None:
            pdf.set_font("DejaVu", "B", 9)
            pdf.cell(55, 6, f"  {label}:", border=0)
            pdf.set_font("DejaVu", "", 9)
            pdf.cell(0, 6, str(valore or "—"), ln=True)

        # DATI APPALTO
        _sezione("DATI APPALTO")
        _riga("Oggetto lavori",      csa_data.get("tipo_lavori", "—"))
        _riga("Stazione Appaltante", csa_data.get("stazione_appaltante", "—"))
        _riga("Comune",              f"{csa_data.get('comune', '—')} ({csa_data.get('provincia', '—')})")
        _riga("CIG",                 csa_data.get("cig", "—"))
        _riga("CUP",                 csa_data.get("cup", "—"))
        pdf.ln(4)

        # DATI MATERIALE
        _sezione("DATI MATERIALE")
        _riga("Materiale / Descrizione", scheda.get("materiale", "—"))
        _riga("Fornitore",               scheda.get("fornitore", "—"))
        _riga("Quantità",                scheda.get("quantita", "—"))
        _riga("Data accettazione",       scheda.get("data", "—"))
        _riga("Esito",                   scheda.get("stato", "—"))
        pdf.ln(4)

        # NOTE
        if scheda.get("note"):
            _sezione("NOTE")
            pdf.set_font("DejaVu", "", 9)
            pdf.multi_cell(0, 6, scheda["note"])
            pdf.ln(4)

        # CERTIFICATI
        cert_links = scheda.get("cert_links", [])
        cert_files_nomi = scheda.get("cert_files_nomi", [])
        if cert_links or cert_files_nomi:
            _sezione("CERTIFICATI E DOCUMENTAZIONE PRODOTTO")
            pdf.set_font("DejaVu", "", 9)
            for link in cert_links:
                pdf.cell(0, 6, f"  Link: {link}", ln=True)
            for nome in cert_files_nomi:
                pdf.cell(0, 6, f"  Allegato: {nome}", ln=True)
            pdf.ln(4)

        # APPROVAZIONE — timbro + firma affiancati
        pdf.ln(8)
        y_before_app = pdf.get_y()
        if y_before_app > 240:
            pdf.add_page()
        _sezione("APPROVAZIONE")
        pdf.ln(4)
        y_footer = pdf.get_y()

        timbro_bytes = (
            scheda.get("timbro_bytes")
            or st.session_state.get("dtc_timbro_bytes")
        )
        firma_bytes = (
            scheda.get("firma_bytes")
            or st.session_state.get("dtc_firma_bytes")
        )
        if timbro_bytes:
            try:
                pdf.image(_img_to_buf(timbro_bytes), x=15, y=y_footer, w=75, h=35)
            except Exception:
                pass
        if firma_bytes:
            try:
                pdf.image(_img_to_buf(firma_bytes), x=115, y=y_footer, w=75, h=35)
            except Exception:
                pass

        pdf.set_y(y_footer + 38)
        pdf.set_font("DejaVu", "", 8)
        pdf.cell(95, 5, "Timbro Impresa Appaltatrice", align="C")
        pdf.cell(95, 5, "Firma Responsabile", align="C", ln=True)
        pdf.ln(14)
        pdf.set_draw_color(100, 100, 100)
        pdf.line(110, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(2)
        pdf.set_font("DejaVu", "B", 9)
        pdf.cell(0, 5, "Il Direttore dei Lavori", ln=True, align="R")
        pdf.set_font("DejaVu", "", 8)
        pdf.cell(0, 5, "Data: _______________", ln=True, align="R")
        pdf.cell(0, 5, "Firma: _______________", ln=True, align="R")

        return bytes(pdf.output())

    except Exception as e:
        st.error(f"Errore generazione PDF scheda: {e}")
        return None


# ===========================================================================
# SEZIONE F — CONTABILITÀ SAL
# ===========================================================================

def _render_contabilita_sal(csa_data, details, importo_netto, results_dir, salva_fn):
    _init_registri()
    st.subheader("💰 Contabilità SAL")
    st.caption("Registro degli Stati di Avanzamento Lavori emessi e dei relativi pagamenti.")

    sal_list: list = st.session_state.registri["contabilita_sal"]

    # ── Collegamento al calendario contrattuale ───────────────────────────────
    sal_intervallo = details.get("sal_intervallo_giorni")
    sal_tipo = details.get("sal_tipo", "")
    sal_importo_min = details.get("sal_importo_minimo_euro")
    durata_gg = details.get("durata_lavori_giorni")

    if sal_intervallo or sal_importo_min:
        info_parts = []
        if sal_tipo:
            info_parts.append(f"Modalità SAL: **{sal_tipo}**")
        if sal_intervallo:
            info_parts.append(f"Intervallo: **{sal_intervallo} giorni**")
        if sal_importo_min:
            info_parts.append(f"Importo minimo: **{_formatta_importo(sal_importo_min)}**")
        if durata_gg and sal_intervallo:
            n_sal_prev = max(1, int(durata_gg) // int(sal_intervallo))
            info_parts.append(f"SAL previsti dal contratto: **{n_sal_prev}**")
        st.info("📅 " + " — ".join(info_parts))

    # ── Metriche ──────────────────────────────────────────────────────────────
    totale_lordo = sum(s.get("importo_lordo", 0.0) or 0.0 for s in sal_list)
    totale_netto = sum(s.get("importo_netto", 0.0) or 0.0 for s in sal_list)
    totale_ritenute = sum(s.get("ritenute", 0.0) or 0.0 for s in sal_list)
    pagati = [s for s in sal_list if s.get("stato_pagamento") == "pagato"]
    totale_pagato = sum(s.get("importo_netto", 0.0) or 0.0 for s in pagati)
    residuo_pagamento = totale_netto - totale_pagato

    col_sal1, col_sal2, col_sal3, col_sal4 = st.columns(4)
    col_sal1.metric("SAL emessi", len(sal_list))
    col_sal2.metric("Importo lordo totale", _formatta_importo(totale_lordo))
    col_sal3.metric("Totale pagato (netto)", _formatta_importo(totale_pagato))
    col_sal4.metric("Residuo da pagare", _formatta_importo(residuo_pagamento))

    if importo_netto > 0 and totale_lordo > 0:
        perc_avanz = min(100.0, (totale_lordo / importo_netto) * 100)
        st.progress(perc_avanz / 100, text=f"Avanzamento lavori: {perc_avanz:.1f}% dell'importo contrattuale netto")

    st.divider()

    # ── Form nuovo SAL ────────────────────────────────────────────────────────
    with st.expander("➕ Nuovo SAL", expanded=False):
        prossimo_num_sal = len(sal_list) + 1
        with st.form("form_nuovo_sal", clear_on_submit=True):
            st.markdown("**Dati del SAL**")
            col_sal_a, col_sal_b = st.columns(2)
            with col_sal_a:
                numero_sal = st.number_input(
                    "Numero SAL",
                    min_value=1,
                    value=prossimo_num_sal,
                    step=1,
                    key="reg_sal_new_numero",
                )
                data_em_sal = st.date_input("Data emissione", value=date.today(), key="reg_sal_new_data")
                importo_lordo_sal = st.number_input(
                    "Importo lordo SAL (€)",
                    min_value=0.0,
                    value=0.0,
                    step=1000.0,
                    format="%.2f",
                    key="reg_sal_new_lordo",
                )
            with col_sal_b:
                ritenute_sal = st.number_input(
                    "Ritenute (€)",
                    min_value=0.0,
                    value=0.0,
                    step=100.0,
                    format="%.2f",
                    help="Ritenuta di garanzia e altre trattenute. Importo netto = Lordo − Ritenute.",
                    key="reg_sal_new_ritenute",
                )
                stato_pag_sal = st.selectbox("Stato pagamento", _STATI_SAL, key="reg_sal_new_stato")
                data_pag_sal = st.date_input(
                    "Data pagamento (se pagato)",
                    value=None,
                    key="reg_sal_new_data_pag",
                )
            note_sal_new = st.text_area("Note", height=60, key="reg_sal_new_note")

            # Preview importo netto calcolato
            importo_netto_sal_calc = max(0.0, importo_lordo_sal - ritenute_sal)
            st.info(
                f"**Importo netto calcolato:** {_formatta_importo(importo_netto_sal_calc)} "
                f"(lordo {_formatta_importo(importo_lordo_sal)} − ritenute {_formatta_importo(ritenute_sal)})"
            )

            submitted_sal = st.form_submit_button("💾 Aggiungi SAL", type="primary")
            if submitted_sal:
                if importo_lordo_sal <= 0:
                    st.error("L'importo lordo del SAL deve essere maggiore di zero.")
                else:
                    nuovo_sal = {
                        "id": _prossimo_id(sal_list),
                        "numero": int(numero_sal),
                        "data_emissione": data_em_sal.isoformat(),
                        "importo_lordo": importo_lordo_sal,
                        "importo_netto": importo_netto_sal_calc,
                        "ritenute": ritenute_sal,
                        "stato_pagamento": stato_pag_sal,
                        "data_pagamento": data_pag_sal.isoformat() if data_pag_sal else "",
                        "note": note_sal_new.strip(),
                    }
                    st.session_state.registri["contabilita_sal"].append(nuovo_sal)
                    aggiungi_log(
                        "SAL aggiunto",
                        f"SAL n.{numero_sal} — lordo {_formatta_importo(importo_lordo_sal)} — {stato_pag_sal}",
                        tab="Registri",
                    )
                    aggiungi_al_diario(
                        f"SAL n.{int(numero_sal)} aggiunto: {_formatta_importo(importo_lordo_sal)} lordo ({stato_pag_sal})",
                        "🟢 Contabilità",
                    )
                    salva_fn()
                    st.success(f"SAL n.{numero_sal} aggiunto con successo.")
                    st.rerun()

    st.divider()

    # ── Lista SAL ─────────────────────────────────────────────────────────────
    if not sal_list:
        return

    st.markdown(f"**{len(sal_list)} SAL registrati**")

    sal_ordinati = sorted(sal_list, key=lambda x: x.get("numero", 0))

    for sal in sal_ordinati:
        salid = sal.get("id", 0)
        numero_sal_vis = sal.get("numero", salid)
        stato_pag_vis = sal.get("stato_pagamento", "emesso")
        lordo_vis = sal.get("importo_lordo", 0.0) or 0.0
        netto_vis = sal.get("importo_netto", 0.0) or 0.0
        idx_sal = next((i for i, x in enumerate(sal_list) if x.get("id") == salid), None)

        badge_sal = {"emesso": "📄", "in_verifica": "🔍", "pagato": "✅"}.get(stato_pag_vis, "💰")
        titolo_sal = (
            f"{badge_sal} SAL n.{numero_sal_vis} — {sal.get('data_emissione', '—')} — "
            f"Lordo: {_formatta_importo(lordo_vis)} — {stato_pag_vis.upper()}"
        )

        with st.expander(titolo_sal, expanded=False):
            col_salv1, col_salv2 = st.columns(2)
            with col_salv1:
                st.markdown(f"**Numero SAL:** {numero_sal_vis}")
                st.markdown(f"**Data emissione:** {sal.get('data_emissione', '—')}")
                st.markdown(f"**Importo lordo:** {_formatta_importo(lordo_vis)}")
                st.markdown(f"**Ritenute:** {_formatta_importo(sal.get('ritenute', 0.0) or 0.0)}")
            with col_salv2:
                st.markdown(f"**Importo netto:** {_formatta_importo(netto_vis)}")
                st.markdown(f"**Stato pagamento:** {stato_pag_vis}")
                if sal.get("data_pagamento"):
                    st.markdown(f"**Data pagamento:** {sal.get('data_pagamento')}")
            if sal.get("note"):
                st.markdown(f"**Note:** {sal.get('note')}")

            st.markdown("---")

            if idx_sal is not None:
                with st.expander("✏️ Modifica SAL", expanded=False):
                    with st.form(f"form_edit_sal_{salid}"):
                        col_esal1, col_esal2 = st.columns(2)
                        with col_esal1:
                            new_num_sal = st.number_input("Numero SAL", min_value=1, value=int(numero_sal_vis), step=1, key=f"reg_sal_{salid}_e_num")
                            data_em_sal_cur = _parse_data_sicura(sal.get("data_emissione", "")) or date.today()
                            new_data_em_sal = st.date_input("Data emissione", value=data_em_sal_cur, key=f"reg_sal_{salid}_e_data")
                            new_lordo_sal = st.number_input(
                                "Importo lordo (€)",
                                min_value=0.0,
                                value=float(lordo_vis),
                                step=1000.0,
                                format="%.2f",
                                key=f"reg_sal_{salid}_e_lordo",
                            )
                            new_ritenute_sal = st.number_input(
                                "Ritenute (€)",
                                min_value=0.0,
                                value=float(sal.get("ritenute", 0.0) or 0.0),
                                step=100.0,
                                format="%.2f",
                                key=f"reg_sal_{salid}_e_ritenute",
                            )
                        with col_esal2:
                            idx_st_sal = _STATI_SAL.index(stato_pag_vis) if stato_pag_vis in _STATI_SAL else 0
                            new_stato_sal = st.selectbox("Stato pagamento", _STATI_SAL, index=idx_st_sal, key=f"reg_sal_{salid}_e_stato")
                            data_pag_sal_cur = _parse_data_sicura(sal.get("data_pagamento", ""))
                            new_data_pag_sal = st.date_input("Data pagamento", value=data_pag_sal_cur, key=f"reg_sal_{salid}_e_data_pag")
                        new_note_sal = st.text_area("Note", value=sal.get("note", ""), height=60, key=f"reg_sal_{salid}_e_note")
                        if st.form_submit_button("💾 Salva modifiche"):
                            new_netto_sal = max(0.0, new_lordo_sal - new_ritenute_sal)
                            st.session_state.registri["contabilita_sal"][idx_sal].update({
                                "numero": int(new_num_sal),
                                "data_emissione": new_data_em_sal.isoformat(),
                                "importo_lordo": new_lordo_sal,
                                "importo_netto": new_netto_sal,
                                "ritenute": new_ritenute_sal,
                                "stato_pagamento": new_stato_sal,
                                "data_pagamento": new_data_pag_sal.isoformat() if new_data_pag_sal else "",
                                "note": new_note_sal.strip(),
                            })
                            aggiungi_log(
                                "SAL modificato",
                                f"SAL n.{new_num_sal} → stato: {new_stato_sal}",
                                tab="Registri",
                            )
                            salva_fn()
                            st.success("SAL aggiornato.")
                            st.rerun()

                if st.button(f"🗑️ Elimina SAL n.{numero_sal_vis}", key=f"reg_sal_{salid}_del"):
                    st.session_state.registri["contabilita_sal"].pop(idx_sal)
                    aggiungi_log("SAL eliminato", f"SAL n.{numero_sal_vis}", tab="Registri")
                    salva_fn()
                    st.success(f"SAL n.{numero_sal_vis} eliminato.")
                    st.rerun()
