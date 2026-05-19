"""
doc_viewer.py — Visualizzatore/downloader unificato per documenti allegati.

Esporta:
  render_doc_buttons(file_path, key) — mostra 👁️ Visualizza + ⬇️ Scarica affiancati.

PDF: apre in nuova scheda via blob URL creato da JS (i data: URL sono bloccati dai
browser moderni; i blob: URL non lo sono perché nascono in-browser da un click diretto).

Immagini: thumbnail inline via st.image (con expand nativo Streamlit) + download.
Office:   due download button (i browser non possono aprirli inline).
"""

import base64
import pathlib
import streamlit as st
import streamlit.components.v1 as components


_MIME: dict[str, str] = {
    ".pdf":  "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".doc":  "application/msword",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".xls":  "application/vnd.ms-excel",
    ".jpg":  "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png":  "image/png",
}

_IMG_EXTS = frozenset({".jpg", ".jpeg", ".png"})

# Stile pulsante blu che imita i bottoni Streamlit
_BTN_CSS = (
    "background:#0e76a8;color:#fff;border:none;border-radius:6px;"
    "padding:8px 0;cursor:pointer;font-size:14px;width:100%;"
    "font-family:sans-serif;letter-spacing:.3px;"
)


def _js_fn_name(key: str) -> str:
    """Converte una chiave Streamlit arbitraria in un nome funzione JS valido."""
    return "dtc_" + "".join(c if c.isalnum() else "_" for c in key)


def _render_pdf_blob_button(encoded: str, fn: str) -> None:
    """Inietta tramite components.html() un pulsante che apre il PDF via blob URL.

    I blob: URL sono creati in-browser a partire dai byte base64 e aperti con
    window.open(..., '_blank'). Questo metodo funziona in tutti i browser moderni
    e non è soggetto al blocco dei data: URL in nuove schede.
    """
    html = f"""
<button onclick="{fn}()" style="{_BTN_CSS}">
  &#128065;&#65039;&nbsp;Visualizza
</button>
<script>
function {fn}() {{
  var s = atob("{encoded}");
  var u = new Uint8Array(s.length);
  for (var i = 0; i < s.length; i++) u[i] = s.charCodeAt(i);
  var blob = new Blob([u], {{type: "application/pdf"}});
  window.open(URL.createObjectURL(blob), "_blank");
}}
</script>
"""
    components.html(html, height=46)


def render_doc_buttons(file_path, key: str) -> None:
    """Mostra 👁️ Visualizza + ⬇️ Scarica affiancati per un documento allegato.

    Args:
        file_path: percorso al file su disco (str o pathlib.Path).
        key:       prefisso univoco per tutti i widget Streamlit generati internamente.
    """
    fp = pathlib.Path(file_path)
    nome = fp.name
    ext = fp.suffix.lower()
    mime = _MIME.get(ext, "application/octet-stream")

    if not fp.exists():
        st.caption(f"📎 {nome} *(file non trovato su disco)*")
        return

    file_bytes = fp.read_bytes()

    if ext in _IMG_EXTS:
        # st.image mostra la thumbnail con il pulsante ⛶ nativo di Streamlit per
        # la visualizzazione a schermo intero — nessun blob URL necessario.
        st.image(file_bytes, caption=nome, width=120)
        st.download_button(
            "⬇️ Scarica",
            data=file_bytes,
            file_name=nome,
            mime=mime,
            key=f"{key}_dl",
            use_container_width=True,
        )

    elif ext == ".pdf":
        encoded = base64.b64encode(file_bytes).decode()
        fn = _js_fn_name(key)
        col_vis, col_dl = st.columns(2)
        with col_vis:
            _render_pdf_blob_button(encoded, fn)
        with col_dl:
            st.download_button(
                "⬇️ Scarica",
                data=file_bytes,
                file_name=nome,
                mime=mime,
                key=f"{key}_dl",
                use_container_width=True,
            )

    else:
        # Office e altri: due download button (non apribili inline dal browser)
        col_vis, col_dl = st.columns(2)
        with col_vis:
            st.download_button(
                "👁️ Apri",
                data=file_bytes,
                file_name=nome,
                mime=mime,
                key=f"{key}_view",
                use_container_width=True,
            )
        with col_dl:
            st.download_button(
                "⬇️ Scarica",
                data=file_bytes,
                file_name=nome,
                mime=mime,
                key=f"{key}_dl",
                use_container_width=True,
            )
