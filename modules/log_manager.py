"""
log_manager.py — Gestione log attività cantiere per l'app DTC.

Ogni operazione significativa dell'app viene registrata automaticamente
in st.session_state.log_attivita come lista di dizionari.
"""

import os
import streamlit as st
import pandas as pd
from datetime import datetime


# ---------------------------------------------------------------------------
# Funzione pubblica: aggiungi una voce al log
# ---------------------------------------------------------------------------

def aggiungi_log(azione: str, dettaglio: str = "", tab: str = "") -> None:
    """Aggiunge una voce al log attività in session state.

    Inizializza la lista se non esiste ancora.
    L'ID è sequenziale (len + 1), il timestamp è ISO con secondi.
    """
    if not hasattr(st.session_state, "log_attivita") or st.session_state.log_attivita is None:
        st.session_state.log_attivita = []

    nuovo_id = len(st.session_state.log_attivita) + 1
    voce = {
        "id": nuovo_id,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "azione": azione,
        "dettaglio": dettaglio,
        "tab": tab,
    }
    st.session_state.log_attivita.append(voce)


def aggiungi_al_diario(descrizione: str, categoria: str, note: str = "") -> None:
    """Aggiunge automaticamente una voce al Diario del Cantiere in session state."""
    if "diario" not in st.session_state or st.session_state.diario is None:
        st.session_state.diario = []
    if "_diario_counter" not in st.session_state:
        st.session_state._diario_counter = 0
    st.session_state._diario_counter += 1
    st.session_state.diario.append({
        "id": st.session_state._diario_counter,
        "data": datetime.now().strftime("%Y-%m-%d"),
        "ora": datetime.now().strftime("%H:%M"),
        "categoria": categoria,
        "descrizione": descrizione,
        "note": note,
        "auto": True,
    })


# ---------------------------------------------------------------------------
# Funzione pubblica: rendering tab Log Attività
# ---------------------------------------------------------------------------

def render_log_tab(csa_data: dict, salva_fn) -> None:
    """Renderizza il tab 'Log Attività Cantiere' nell'app Streamlit.

    Parametri:
        csa_data  – dizionario estratto da analyze_csa() (può essere vuoto/None).
        salva_fn  – callable senza argomenti, chiamato dopo modifiche allo stato.
    """
    st.header("📋 Log Attività Cantiere")

    # Recupera log (può non esistere ancora)
    log: list = getattr(st.session_state, "log_attivita", None) or []

    if not log:
        st.info("Nessuna attività registrata. Le operazioni effettuate nell'app appariranno qui automaticamente.")
        return

    # ------------------------------------------------------------------
    # Filtri
    # ------------------------------------------------------------------
    tab_valori = sorted({v["tab"] for v in log if v.get("tab")})
    opzioni_tab = ["Tutti"] + tab_valori

    col_filtro1, col_filtro2 = st.columns([1, 2])
    with col_filtro1:
        filtro_tab = st.selectbox("Filtra per tab", opzioni_tab, key="log_filtro_tab")
    with col_filtro2:
        testo_ricerca = st.text_input("Cerca nel log", placeholder="Es. analisi, SAL, penale...", key="log_testo_ricerca")

    # Applica filtri
    risultati = log[:]
    if filtro_tab != "Tutti":
        risultati = [r for r in risultati if r.get("tab") == filtro_tab]
    if testo_ricerca.strip():
        termine = testo_ricerca.strip().lower()
        risultati = [
            r for r in risultati
            if termine in r.get("azione", "").lower() or termine in r.get("dettaglio", "").lower()
        ]

    # Ordine: più recente prima
    risultati = list(reversed(risultati))

    st.caption(f"**{len(risultati)}** voci trovate su {len(log)} totali")

    # ------------------------------------------------------------------
    # Tabella
    # ------------------------------------------------------------------
    if risultati:
        df = pd.DataFrame(risultati)[["timestamp", "tab", "azione", "dettaglio"]]
        df.columns = ["Data/Ora", "Tab", "Azione", "Dettaglio"]
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Data/Ora": st.column_config.TextColumn("Data/Ora", width="medium"),
                "Tab": st.column_config.TextColumn("Tab", width="small"),
                "Azione": st.column_config.TextColumn("Azione", width="medium"),
                "Dettaglio": st.column_config.TextColumn("Dettaglio", width="large"),
            },
        )
    else:
        st.warning("Nessuna voce corrisponde ai filtri selezionati.")

    st.divider()

    # ------------------------------------------------------------------
    # Export PDF
    # ------------------------------------------------------------------
    if st.button("📄 Esporta log PDF", key="log_esporta_pdf"):
        try:
            pdf_bytes = _genera_pdf_log(risultati, csa_data or {})
            nome_file = f"log_attivita_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            st.download_button(
                label="⬇️ Scarica PDF log",
                data=pdf_bytes,
                file_name=nome_file,
                mime="application/pdf",
                key="log_download_pdf",
            )
        except ImportError:
            st.error("Libreria fpdf2 non disponibile. Installare con: pip install fpdf2")
        except Exception as exc:
            st.error(f"Errore nella generazione del PDF: {exc}")

    # ------------------------------------------------------------------
    # Cancella log
    # ------------------------------------------------------------------
    with st.expander("🗑️ Cancella log"):
        st.warning("Questa operazione elimina tutte le voci del log in modo irreversibile.")
        conferma = st.checkbox("Confermo di voler cancellare l'intero log attività", key="log_conferma_cancella")
        if st.button("🗑️ Cancella tutto il log", disabled=not conferma, key="log_btn_cancella"):
            st.session_state.log_attivita = []
            try:
                salva_fn()
            except Exception:
                pass
            st.success("Log cancellato con successo.")
            st.rerun()


# ---------------------------------------------------------------------------
# Funzione privata: generazione PDF
# ---------------------------------------------------------------------------

def _genera_pdf_log(log_entries: list, csa_data: dict) -> bytes:
    """Genera un PDF del log attività e restituisce i byte.

    Lancia ImportError se fpdf2 non è disponibile.
    Lancia qualsiasi eccezione FPDF in caso di errore di rendering.
    """
    from fpdf import FPDF  # importazione lazy per non crashare all'avvio se mancante

    # Percorsi font DejaVu (stesso schema usato nel resto dell'app)
    _base = os.path.dirname(os.path.dirname(__file__))
    font_regular = os.path.join(_base, "fonts", "DejaVuSans.ttf")
    font_bold = os.path.join(_base, "fonts", "DejaVuSans-Bold.ttf")

    # ------------------------------------------------------------------
    # Inizializzazione FPDF
    # ------------------------------------------------------------------
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()

    # Font
    if os.path.isfile(font_regular):
        pdf.add_font("DejaVu", "", font_regular)
    if os.path.isfile(font_bold):
        pdf.add_font("DejaVu", "B", font_bold)

    _font_name = "DejaVu" if os.path.isfile(font_regular) else "Helvetica"

    # ------------------------------------------------------------------
    # Intestazione
    # ------------------------------------------------------------------
    pdf.set_font(_font_name, "B", 14)
    pdf.cell(0, 8, "Registro Attività Cantiere — DTC", ln=True, align="C")

    tipo_lavori = csa_data.get("tipo_lavori", "")
    comune = csa_data.get("comune", "")
    provincia = csa_data.get("provincia", "")
    luogo = ", ".join(filter(None, [comune, provincia]))
    sottotitolo_parts = [tipo_lavori, luogo]
    sottotitolo = " — ".join(filter(None, sottotitolo_parts))
    if sottotitolo:
        pdf.set_font(_font_name, "", 10)
        pdf.cell(0, 5, sottotitolo, ln=True, align="C")

    pdf.set_font(_font_name, "", 8)
    pdf.cell(0, 4, f"Generato il: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", ln=True, align="C")
    pdf.ln(3)

    # ------------------------------------------------------------------
    # Larghezze colonne (landscape A4 = 297mm, margini ~10mm per lato)
    # ------------------------------------------------------------------
    margine_sx = pdf.l_margin
    larghezza_totale = pdf.w - margine_sx - pdf.r_margin  # ~277mm
    W_DATETIME = 38
    W_TAB = 25
    W_AZIONE = 60
    W_DETTAGLIO = larghezza_totale - W_DATETIME - W_TAB - W_AZIONE
    ALTEZZA_RIGA = 5
    ALTEZZA_HEADER = 6

    # ------------------------------------------------------------------
    # Intestazione tabella
    # ------------------------------------------------------------------
    pdf.set_fill_color(0, 70, 140)   # blu DTC
    pdf.set_text_color(255, 255, 255)
    pdf.set_font(_font_name, "B", 8)

    pdf.cell(W_DATETIME, ALTEZZA_HEADER, "Data/Ora", border=1, fill=True, align="C")
    pdf.cell(W_TAB, ALTEZZA_HEADER, "Tab", border=1, fill=True, align="C")
    pdf.cell(W_AZIONE, ALTEZZA_HEADER, "Azione", border=1, fill=True, align="C")
    pdf.cell(W_DETTAGLIO, ALTEZZA_HEADER, "Dettaglio", border=1, fill=True, align="C", ln=True)

    # ------------------------------------------------------------------
    # Righe dati
    # ------------------------------------------------------------------
    pdf.set_text_color(0, 0, 0)
    pdf.set_font(_font_name, "", 7)

    colore_pari = (245, 247, 250)   # grigio molto chiaro
    colore_dispari = (255, 255, 255)  # bianco

    for idx, voce in enumerate(log_entries):
        # Aggiungi pagina se necessario (auto_page_break gestisce la riga corrente,
        # ma vogliamo assicurarci che l'header non resti orfano)
        if pdf.get_y() + ALTEZZA_RIGA > pdf.page_break_trigger:
            pdf.add_page()
            # Ripeti intestazione sulla nuova pagina
            pdf.set_fill_color(0, 70, 140)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font(_font_name, "B", 8)
            pdf.cell(W_DATETIME, ALTEZZA_HEADER, "Data/Ora", border=1, fill=True, align="C")
            pdf.cell(W_TAB, ALTEZZA_HEADER, "Tab", border=1, fill=True, align="C")
            pdf.cell(W_AZIONE, ALTEZZA_HEADER, "Azione", border=1, fill=True, align="C")
            pdf.cell(W_DETTAGLIO, ALTEZZA_HEADER, "Dettaglio", border=1, fill=True, align="C", ln=True)
            pdf.set_text_color(0, 0, 0)
            pdf.set_font(_font_name, "", 7)

        # Colore alternato
        r, g, b = colore_pari if idx % 2 == 0 else colore_dispari
        pdf.set_fill_color(r, g, b)

        # Formatta timestamp: ISO → gg/mm/aaaa HH:MM:SS
        ts_raw = voce.get("timestamp", "")
        try:
            ts_dt = datetime.fromisoformat(ts_raw)
            ts_formattato = ts_dt.strftime("%d/%m/%Y %H:%M:%S")
        except (ValueError, TypeError):
            ts_formattato = ts_raw

        colonna_tab = str(voce.get("tab", ""))
        colonna_azione = str(voce.get("azione", ""))
        colonna_dettaglio = str(voce.get("dettaglio", ""))

        pdf.cell(W_DATETIME, ALTEZZA_RIGA, ts_formattato, border=1, fill=True, align="L")
        pdf.cell(W_TAB, ALTEZZA_RIGA, colonna_tab, border=1, fill=True, align="L")
        pdf.cell(W_AZIONE, ALTEZZA_RIGA, colonna_azione, border=1, fill=True, align="L")
        pdf.cell(W_DETTAGLIO, ALTEZZA_RIGA, colonna_dettaglio, border=1, fill=True, align="L", ln=True)

    # ------------------------------------------------------------------
    # Footer
    # ------------------------------------------------------------------
    pdf.ln(4)
    pdf.set_font(_font_name, "", 7)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(
        0, 4,
        f"Totale voci: {len(log_entries)} — DTC — Strumento gestione appalti pubblici (D.Lgs. 36/2023)",
        ln=True,
        align="C",
    )

    return bytes(pdf.output())
