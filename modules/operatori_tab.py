"""
operatori_tab.py — Gestione operatori economici per l'app DTC.

Struttura gerarchica a tre livelli:
  L0 — Appaltatore principale (dati + documenti)
  L1 — Subappaltatori (dipendono dall'appaltatore; nessun limite fisso di legge — art.119 D.Lgs.36/2023; limite definito dal CSA)
  L2 — Subaffidatari (dipendono da un subappaltatore specifico)

Funzione pubblica: render_operatori_tab(csa_data, importo_base, salva_fn, results_dir)
"""

import streamlit as st
import pathlib
from datetime import date, timedelta

from modules.log_manager import aggiungi_log, aggiungi_al_diario
from modules.doc_viewer import render_doc_buttons


_TAB_NOME = "Operatori Economici"
_DURC_VALIDITA_GG = 120
_DURC_ALERT_GG = 30
_SOGLIA_ATTENZIONE = 25.0  # soglia avviso se presente limite CSA
_SOGLIA_LIMITE = 30.0      # usata solo se il CSA indica un limite (default conservativo)
_TIPI_FILE = ["pdf", "docx", "doc", "xlsx", "jpg", "png"]
_STATI_AUT = ["in_attesa", "autorizzato", "negato"]
_STATI_LABEL = {
    "in_attesa": "⏳ In attesa",
    "autorizzato": "✅ Autorizzato",
    "negato": "❌ Negato",
}
_SEM = {"verde": "🟢", "giallo": "🟡", "rosso": "🔴", "grigio": "⚪"}


# ── Strutture dati di default ──────────────────────────────────────────────────

def _docs_appaltatore() -> dict:
    return {
        "durc": {"filename": "", "data_emissione": ""},
        "visura": {"filename": "", "data_scadenza": ""},
        "polizza_car": {"filename": ""},
        "polizza_rct": {"filename": ""},
        "altri": [],
    }


def _docs_suboperatore() -> dict:
    return {
        "durc": {"filename": "", "data_emissione": ""},
        "visura": {"filename": "", "data_scadenza": ""},
        "contratto": {"filename": ""},
        "pos": {"filename": ""},
        "polizza": {"filename": ""},
        "cciaa": {"filename": ""},
        "soa": {"filename": ""},
        "autorizzazione_sa": {"filename": ""},
    }


def _operatori_default() -> dict:
    return {
        "appaltatore": {
            "ragione_sociale": "",
            "piva": "",
            "documenti": _docs_appaltatore(),
        },
        "subappaltatori": [],
    }


# ── Inizializzazione session state ─────────────────────────────────────────────

def _init() -> None:
    if "operatori_economici" not in st.session_state or not isinstance(
        st.session_state.operatori_economici, dict
    ):
        st.session_state.operatori_economici = _operatori_default()

    oe = st.session_state.operatori_economici
    oe.setdefault("appaltatore", _operatori_default()["appaltatore"])
    oe.setdefault("subappaltatori", [])

    app = oe["appaltatore"]
    app.setdefault("ragione_sociale", "")
    app.setdefault("piva", "")
    docs_app = app.setdefault("documenti", {})
    for k, v in _docs_appaltatore().items():
        docs_app.setdefault(k, v)

    for sub in oe["subappaltatori"]:
        sub.setdefault("subaffidatari", [])
        sub_docs = sub.setdefault("documenti", {})
        for k, v in _docs_suboperatore().items():
            sub_docs.setdefault(k, v)
        for saff in sub["subaffidatari"]:
            saff_docs = saff.setdefault("documenti", {})
            for k, v in _docs_suboperatore().items():
                saff_docs.setdefault(k, v)


# ── Helper DURC ────────────────────────────────────────────────────────────────

def _durc_info(data_emissione_str: str) -> dict:
    """Calcola stato DURC da data emissione (validità 120 gg)."""
    if not data_emissione_str:
        return {"colore": "grigio", "testo": "Nessuna data emissione"}
    try:
        dt_em = date.fromisoformat(data_emissione_str)
        dt_sc = dt_em + timedelta(days=_DURC_VALIDITA_GG)
        giorni = (dt_sc - date.today()).days
        if giorni < 0:
            return {"colore": "rosso", "testo": f"SCADUTO da {-giorni} gg ({dt_sc.strftime('%d/%m/%Y')})"}
        if giorni <= _DURC_ALERT_GG:
            return {"colore": "giallo", "testo": f"Scade tra {giorni} gg ({dt_sc.strftime('%d/%m/%Y')})"}
        return {"colore": "verde", "testo": f"Valido fino al {dt_sc.strftime('%d/%m/%Y')}"}
    except (ValueError, TypeError):
        return {"colore": "grigio", "testo": "Data non valida"}


def _visura_info(data_scadenza_str: str) -> dict:
    """Calcola stato Visura Camerale da data scadenza."""
    if not data_scadenza_str:
        return {"colore": "grigio", "testo": "Nessuna data scadenza"}
    try:
        dt_sc = date.fromisoformat(data_scadenza_str)
        giorni = (dt_sc - date.today()).days
        if giorni < 0:
            return {"colore": "rosso", "testo": f"SCADUTA da {-giorni} gg ({dt_sc.strftime('%d/%m/%Y')})"}
        if giorni <= _DURC_ALERT_GG:
            return {"colore": "giallo", "testo": f"Scade tra {giorni} gg ({dt_sc.strftime('%d/%m/%Y')})"}
        return {"colore": "verde", "testo": f"Valida fino al {dt_sc.strftime('%d/%m/%Y')}"}
    except (ValueError, TypeError):
        return {"colore": "grigio", "testo": "Data non valida"}


def _collect_durc_info(oe: dict) -> list[tuple[str, str, dict]]:
    """Raccoglie info DURC per tutti gli operatori: (nome, livello, info_dict)."""
    result = []
    app = oe.get("appaltatore", {})
    rs_app = app.get("ragione_sociale", "") or "Appaltatore"
    result.append((rs_app, "L0", _durc_info(app.get("documenti", {}).get("durc", {}).get("data_emissione", ""))))

    for sub in oe.get("subappaltatori", []):
        result.append((
            sub.get("ragione_sociale", "—"), "L1",
            _durc_info(sub.get("documenti", {}).get("durc", {}).get("data_emissione", "")),
        ))
        for saff in sub.get("subaffidatari", []):
            result.append((
                saff.get("ragione_sociale", "—"), "L2",
                _durc_info(saff.get("documenti", {}).get("durc", {}).get("data_emissione", "")),
            ))
    return result


# ── Rendering documenti ────────────────────────────────────────────────────────

def _render_durc(doc: dict, dir_path: pathlib.Path, obj_key: str, salva_fn) -> None:
    """Riga DURC: data emissione → auto-scadenza → semaforo → viewer → upload."""
    filename = doc.get("filename", "")
    data_em_str = doc.get("data_emissione", "")
    data_em_val = None
    if data_em_str:
        try:
            data_em_val = date.fromisoformat(data_em_str)
        except (ValueError, TypeError):
            pass

    c1, c2 = st.columns([3, 2])
    with c1:
        nuova = st.date_input(
            "Data emissione DURC",
            value=data_em_val,
            key=f"{obj_key}_durc_em",
            format="DD/MM/YYYY",
            help=f"Validità automatica {_DURC_VALIDITA_GG} giorni dalla data di emissione",
        )
        if nuova is not None:
            ns = nuova.isoformat()
            if ns != data_em_str:
                doc["data_emissione"] = ns
                salva_fn()
                st.rerun()
        info = _durc_info(doc.get("data_emissione", ""))
        st.caption(f"{_SEM[info['colore']]} {info['testo']}")

    with c2:
        if filename:
            render_doc_buttons(dir_path / filename, key=f"{obj_key}_durc_doc")
        else:
            st.caption("Nessun file")
        up = st.file_uploader(
            "Carica DURC", type=_TIPI_FILE,
            key=f"{obj_key}_durc_up", label_visibility="collapsed",
        )
        if up is not None and up.name != filename:
            dir_path.mkdir(parents=True, exist_ok=True)
            (dir_path / up.name).write_bytes(up.getvalue())
            doc["filename"] = up.name
            aggiungi_log("DURC caricato", up.name, tab=_TAB_NOME)
            salva_fn()
            st.rerun()


def _render_visura(doc: dict, dir_path: pathlib.Path, obj_key: str, salva_fn) -> None:
    """Riga Visura Camerale: data scadenza → semaforo → viewer → upload."""
    filename = doc.get("filename", "")
    data_sc_str = doc.get("data_scadenza", "")
    data_sc_val = None
    if data_sc_str:
        try:
            data_sc_val = date.fromisoformat(data_sc_str)
        except (ValueError, TypeError):
            pass

    c1, c2 = st.columns([3, 2])
    with c1:
        nuova = st.date_input(
            "Data scadenza Visura",
            value=data_sc_val,
            key=f"{obj_key}_visura_sc",
            format="DD/MM/YYYY",
            help="Data di scadenza della visura camerale",
        )
        if nuova is not None:
            ns = nuova.isoformat()
            if ns != data_sc_str:
                doc["data_scadenza"] = ns
                salva_fn()
                st.rerun()
        info = _visura_info(doc.get("data_scadenza", ""))
        st.caption(f"{_SEM[info['colore']]} {info['testo']}")

    with c2:
        if filename:
            render_doc_buttons(dir_path / filename, key=f"{obj_key}_visura_doc")
        else:
            st.caption("Nessun file")
        up = st.file_uploader(
            "Carica Visura", type=_TIPI_FILE,
            key=f"{obj_key}_visura_up", label_visibility="collapsed",
        )
        if up is not None and up.name != filename:
            dir_path.mkdir(parents=True, exist_ok=True)
            (dir_path / up.name).write_bytes(up.getvalue())
            doc["filename"] = up.name
            aggiungi_log("Visura Camerale caricata", up.name, tab=_TAB_NOME)
            salva_fn()
            st.rerun()


def _render_doc_semplice(doc: dict, doc_key: str, label: str, dir_path: pathlib.Path, obj_key: str, salva_fn) -> None:
    """Riga documento semplice: viewer + upload."""
    filename = doc.get("filename", "")
    if filename:
        render_doc_buttons(dir_path / filename, key=f"{obj_key}_{doc_key}_doc")
    else:
        st.caption("Nessun file")
    up = st.file_uploader(
        f"Carica {label}", type=_TIPI_FILE,
        key=f"{obj_key}_{doc_key}_up", label_visibility="collapsed",
    )
    if up is not None and up.name != filename:
        dir_path.mkdir(parents=True, exist_ok=True)
        (dir_path / up.name).write_bytes(up.getvalue())
        doc["filename"] = up.name
        aggiungi_log(f"Documento: {label}", up.name, tab=_TAB_NOME)
        salva_fn()
        st.rerun()


def _render_altri(altri: list, dir_path: pathlib.Path, obj_key: str, salva_fn) -> None:
    """Sezione documenti aggiuntivi con add/remove."""
    for idx, doc_extra in enumerate(altri):
        nome_doc = doc_extra.get("nome", f"Doc {idx + 1}")
        filename = doc_extra.get("filename", "")
        c1, c2, c3 = st.columns([3, 3, 1])
        with c1:
            st.markdown(f"**{nome_doc}**")
            if filename:
                render_doc_buttons(dir_path / filename, key=f"{obj_key}_altro_{idx}_doc")
            else:
                st.caption("Nessun file")
        with c2:
            up = st.file_uploader(
                "Carica", type=_TIPI_FILE,
                key=f"{obj_key}_altro_{idx}_up", label_visibility="collapsed",
            )
            if up is not None and up.name != filename:
                dir_path.mkdir(parents=True, exist_ok=True)
                (dir_path / up.name).write_bytes(up.getvalue())
                altri[idx]["filename"] = up.name
                aggiungi_log(f"Documento aggiuntivo: {nome_doc}", up.name, tab=_TAB_NOME)
                salva_fn()
                st.rerun()
        with c3:
            if st.button("🗑️", key=f"{obj_key}_altro_{idx}_del", help="Rimuovi"):
                altri.pop(idx)
                salva_fn()
                st.rerun()

    st.divider()
    nome_nuovo = st.text_input(
        "Nome documento aggiuntivo", key=f"{obj_key}_altro_new_nome",
        placeholder="es. Dichiarazione antimafia",
    )
    if st.button("➕ Aggiungi documento", key=f"{obj_key}_altro_new_btn"):
        if nome_nuovo.strip():
            altri.append({"nome": nome_nuovo.strip(), "filename": ""})
            salva_fn()
            st.rerun()
        else:
            st.warning("Inserire il nome del documento.")


def _render_docs_sub(docs: dict, dir_path: pathlib.Path, obj_key: str, salva_fn) -> None:
    """Render tutti i documenti per un suboperatore (L1 o L2)."""
    c1, c2 = st.columns(2)
    with c1:
        with st.expander("📄 DURC"):
            _render_durc(docs.setdefault("durc", {"filename": "", "data_emissione": ""}),
                         dir_path, obj_key, salva_fn)
    with c2:
        with st.expander("📄 Visura Camerale"):
            _render_visura(docs.setdefault("visura", {"filename": "", "data_scadenza": ""}),
                           dir_path, obj_key, salva_fn)

    altri_docs = [
        ("contratto", "Contratto subappalto"),
        ("pos", "POS — Piano Operativo Sicurezza"),
        ("polizza", "Polizza assicurativa"),
        ("cciaa", "Visura CCIAA"),
        ("soa", "Certificazione SOA"),
        ("autorizzazione_sa", "Autorizzazione SA"),
    ]
    for i in range(0, len(altri_docs), 2):
        ca, cb = st.columns(2)
        dk1, dl1 = altri_docs[i]
        with ca:
            with st.expander(f"📄 {dl1}"):
                _render_doc_semplice(docs.setdefault(dk1, {"filename": ""}),
                                     dk1, dl1, dir_path, obj_key, salva_fn)
        if i + 1 < len(altri_docs):
            dk2, dl2 = altri_docs[i + 1]
            with cb:
                with st.expander(f"📄 {dl2}"):
                    _render_doc_semplice(docs.setdefault(dk2, {"filename": ""}),
                                         dk2, dl2, dir_path, obj_key, salva_fn)


# ── Sezione DURC dashboard ─────────────────────────────────────────────────────

def _log_durc_alerts(oe: dict) -> None:
    """Logga alert DURC una volta per sessione (non ad ogni rerun)."""
    alert_key = "_durc_alerts_logged"
    if st.session_state.get(alert_key):
        return
    st.session_state[alert_key] = True
    for nome, livello, info in _collect_durc_info(oe):
        if info["colore"] in ("rosso", "giallo"):
            aggiungi_log(
                f"⚠️ DURC {info['colore'].upper()}: {nome}",
                f"({livello}) {info['testo']}",
                tab=_TAB_NOME,
            )


def render_durc_semaphore(oe: dict) -> None:
    """Sezione semaforo DURC — utilizzabile anche dalla Dashboard principale."""
    tutti = _collect_durc_info(oe)
    con_data = [(n, l, i) for n, l, i in tutti if i["colore"] != "grigio"]
    critici = [x for x in con_data if x[2]["colore"] in ("rosso", "giallo")]

    if not con_data:
        return

    expanded = bool(critici)
    icon = "⚠️" if critici else "🟢"
    with st.expander(f"{icon} Scadenze DURC / Visure — {len(con_data)} operatori con data", expanded=expanded):
        for nome, livello, info in tutti:
            if info["colore"] == "grigio":
                continue
            sem = _SEM[info["colore"]]
            lev_label = {"L0": "Appaltatore", "L1": "Subappaltatore", "L2": "Subaffidatario"}.get(livello, livello)
            st.markdown(f"{sem} **{nome}** _{lev_label}_ — {info['testo']}")


# ── Livello 0 — Appaltatore ────────────────────────────────────────────────────

def _render_appaltatore(app: dict, csa_data: dict, results_dir: pathlib.Path, salva_fn) -> None:
    dir_path = results_dir / "operatori" / "appaltatore"

    with st.expander("📋 Dati e documenti appaltatore", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            rs = st.text_input("Ragione Sociale", value=app.get("ragione_sociale", ""), key="oe_app_rs")
            if rs != app.get("ragione_sociale", ""):
                app["ragione_sociale"] = rs
                salva_fn()
        with c2:
            piva = st.text_input("P.IVA / C.F.", value=app.get("piva", ""), key="oe_app_piva")
            if piva != app.get("piva", ""):
                app["piva"] = piva
                salva_fn()

        soa_list = csa_data.get("categorie_soa", [])
        if soa_list:
            st.caption(
                "Categorie SOA (da CSA): "
                + ", ".join(f"{s.get('codice','')}/{s.get('classifica','')}" for s in soa_list)
            )

        st.divider()
        st.markdown("##### Documenti")

        docs = app.setdefault("documenti", _docs_appaltatore())

        c1, c2 = st.columns(2)
        with c1:
            with st.expander("📄 DURC"):
                _render_durc(docs.setdefault("durc", {"filename": "", "data_emissione": ""}),
                             dir_path, "oe_app", salva_fn)
        with c2:
            with st.expander("📄 Visura Camerale"):
                _render_visura(docs.setdefault("visura", {"filename": "", "data_scadenza": ""}),
                               dir_path, "oe_app", salva_fn)

        c3, c4 = st.columns(2)
        with c3:
            with st.expander("📄 Polizza CAR"):
                _render_doc_semplice(docs.setdefault("polizza_car", {"filename": ""}),
                                     "polizza_car", "Polizza CAR", dir_path, "oe_app", salva_fn)
        with c4:
            with st.expander("📄 Polizza RCT"):
                _render_doc_semplice(docs.setdefault("polizza_rct", {"filename": ""}),
                                     "polizza_rct", "Polizza RCT", dir_path, "oe_app", salva_fn)

        with st.expander("📎 Altri documenti"):
            _render_altri(docs.setdefault("altri", []), dir_path, "oe_app", salva_fn)


# ── Livello 1 — Subappaltatori ─────────────────────────────────────────────────

def _render_limite(subs: list, importo_base: float, csa_data: dict | None = None) -> None:
    # Art. 119 D.Lgs. 36/2023 — nessun limite fisso; usa valore CSA se presente
    limite_csa = float((csa_data or {}).get("subappalto_percentuale_massima") or 0)
    ha_limite = limite_csa > 0

    tot_sub = sum(
        float(s.get("importo", 0) or 0) for s in subs if s.get("tipo") == "subappalto"
    )
    perc = (tot_sub / importo_base * 100) if importo_base > 0 else 0
    n_sub = len([s for s in subs if s.get("tipo") == "subappalto"])
    n_saff = sum(len(s.get("subaffidatari", [])) for s in subs)

    c1, c2, c3 = st.columns(3)
    with c1:
        if importo_base > 0:
            if ha_limite:
                delta_label = f"{perc:.1f}% / {limite_csa:.0f}% (CSA)"
                delta_col = "inverse" if perc > limite_csa else ("off" if perc > limite_csa * 0.85 else "normal")
            else:
                delta_label = f"{perc:.1f}% — nessun limite (Art. 119)"
                delta_col = "normal"
        else:
            delta_label = None
            delta_col = "off"
        st.metric(
            "💶 Totale subappaltato", f"€ {tot_sub:,.0f}",
            delta=delta_label,
            delta_color=delta_col,
        )
    with c2:
        st.metric(
            "🏗️ Subappaltatori", str(n_sub),
            delta=f"{n_saff} subaffidatari" if n_saff else None,
            delta_color="off",
        )
    with c3:
        if importo_base > 0 and ha_limite:
            residuo = importo_base * (limite_csa / 100) - tot_sub
            st.metric(
                "📊 Residuo consentito (CSA)", f"€ {max(residuo, 0):,.0f}",
                delta="LIMITE SUPERATO" if residuo < 0 else None,
                delta_color="inverse" if residuo < 0 else "off",
            )

    if ha_limite:
        if perc > limite_csa:
            st.error(
                f"🚨 LIMITE SUPERATO: {perc:.1f}% > {limite_csa:.0f}% (limite CSA — art.119 D.Lgs.36/2023)"
            )
        elif perc > limite_csa * (_SOGLIA_ATTENZIONE / _SOGLIA_LIMITE):
            st.warning(
                f"⚠️ Attenzione: {perc:.1f}% — vicino al limite CSA del {limite_csa:.0f}%"
            )
    else:
        st.info(
            f"ℹ️ Subappalto {perc:.1f}% — nessun limite percentuale nel CSA (art.119 D.Lgs.36/2023)"
        )


def _render_form_sub(oe: dict, importo_base: float, salva_fn) -> None:
    with st.expander("➕ Aggiungi subappaltatore"):
        c1, c2 = st.columns(2)
        with c1:
            rs = st.text_input("Ragione Sociale *", key="oe_new_sub_rs")
            piva = st.text_input("P.IVA / C.F.", key="oe_new_sub_piva")
            soa = st.text_input("Categoria SOA (es. OG3/II)", key="oe_new_sub_soa")
        with c2:
            importo = st.number_input("Importo (€)", min_value=0.0, step=1000.0, key="oe_new_sub_importo")
            tipo = st.selectbox("Tipo", ["subappalto", "subaffidamento"], key="oe_new_sub_tipo")
            stato = st.selectbox(
                "Stato autorizzazione SA", _STATI_AUT,
                format_func=lambda x: _STATI_LABEL[x], key="oe_new_sub_stato",
            )
        perc = (importo / importo_base * 100) if importo_base > 0 else 0
        if importo_base > 0:
            st.caption(f"Percentuale contrattuale: {perc:.2f}%")
        if st.button("✅ Aggiungi", type="primary", key="oe_btn_add_sub"):
            if not rs.strip():
                st.error("Inserire la ragione sociale.")
            else:
                subs = oe["subappaltatori"]
                new_id = max((s.get("id", 0) for s in subs), default=0) + 1
                subs.append({
                    "id": new_id,
                    "ragione_sociale": rs.strip(),
                    "piva": piva.strip(),
                    "categoria_soa": soa.strip(),
                    "importo": float(importo),
                    "percentuale": perc,
                    "tipo": tipo,
                    "stato_autorizzazione": stato,
                    "documenti": _docs_suboperatore(),
                    "subaffidatari": [],
                })
                aggiungi_log("Subappaltatore aggiunto", rs.strip(), tab=_TAB_NOME)
                aggiungi_al_diario(
                    f"Operatore aggiunto: {rs.strip()} (SOA {soa.strip() or 'n.d.'}, {tipo})",
                    "🔵 Adempimento Amministrativo",
                )
                salva_fn()
                st.rerun()


def _render_sub(sub: dict, oe: dict, importo_base: float, results_dir: pathlib.Path, salva_fn) -> None:
    sid = sub.get("id", 0)
    rs = sub.get("ragione_sociale", "—")
    tipo = sub.get("tipo", "subappalto")
    stato = sub.get("stato_autorizzazione", "in_attesa")
    importo = float(sub.get("importo", 0) or 0)
    dir_path = results_dir / "operatori" / f"sub_{sid}"

    durc_i = _durc_info(sub.get("documenti", {}).get("durc", {}).get("data_emissione", ""))
    tipo_ico = "🏗️" if tipo == "subappalto" else "🔗"
    label = (
        f"{tipo_ico} {rs} — {_STATI_LABEL.get(stato, stato)} — "
        f"€ {importo:,.0f} — DURC {_SEM[durc_i['colore']]}"
    )

    with st.expander(label):
        # Info
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"**Ragione Sociale:** {rs}")
            st.markdown(f"**P.IVA:** {sub.get('piva', '—') or '—'}")
        with c2:
            st.markdown(f"**SOA:** {sub.get('categoria_soa', '—') or '—'}")
            st.markdown(f"**Tipo:** {'Subappalto' if tipo == 'subappalto' else 'Subaffidamento'}")
        with c3:
            perc = (importo / importo_base * 100) if importo_base > 0 else sub.get("percentuale", 0)
            st.markdown(f"**Importo:** € {importo:,.2f}")
            st.markdown(f"**% contrattuale:** {perc:.2f}%")

        nuovo_stato = st.selectbox(
            "Stato autorizzazione SA",
            _STATI_AUT,
            index=_STATI_AUT.index(stato) if stato in _STATI_AUT else 0,
            format_func=lambda x: _STATI_LABEL[x],
            key=f"oe_sub_{sid}_stato",
        )
        if nuovo_stato != stato:
            sub["stato_autorizzazione"] = nuovo_stato
            aggiungi_log(
                "Stato subappaltatore aggiornato",
                f"{rs}: {_STATI_LABEL[nuovo_stato]}",
                tab=_TAB_NOME,
            )
            salva_fn()

        st.divider()
        st.markdown("##### Documenti")
        docs = sub.setdefault("documenti", _docs_suboperatore())
        _render_docs_sub(docs, dir_path, f"oe_sub_{sid}", salva_fn)

        st.divider()

        # ── Subaffidatari ─────────────────────────────────────────────────────
        st.markdown(f"##### 🔗 Subaffidatari di {rs}")
        _render_form_saff(sub, importo_base, results_dir, salva_fn, sid)

        for saff in sub.get("subaffidatari", []):
            _render_saff(saff, sub, importo_base, results_dir, salva_fn, sid)

        st.divider()
        if st.button(f"🗑️ Elimina subappaltatore: {rs}", key=f"oe_sub_{sid}_del"):
            oe["subappaltatori"] = [s for s in oe["subappaltatori"] if s.get("id") != sid]
            aggiungi_log("Subappaltatore eliminato", rs, tab=_TAB_NOME)
            salva_fn()
            st.rerun()


# ── Livello 2 — Subaffidatari ──────────────────────────────────────────────────

def _render_form_saff(sub: dict, importo_base: float, results_dir: pathlib.Path, salva_fn, parent_sid: int) -> None:
    with st.expander("➕ Aggiungi subaffidatario"):
        c1, c2 = st.columns(2)
        with c1:
            rs = st.text_input("Ragione Sociale *", key=f"oe_new_saff_{parent_sid}_rs")
            piva = st.text_input("P.IVA / C.F.", key=f"oe_new_saff_{parent_sid}_piva")
        with c2:
            soa = st.text_input("Categoria SOA", key=f"oe_new_saff_{parent_sid}_soa")
            importo = st.number_input("Importo (€)", min_value=0.0, step=1000.0,
                                       key=f"oe_new_saff_{parent_sid}_importo")
            stato = st.selectbox("Stato", _STATI_AUT, format_func=lambda x: _STATI_LABEL[x],
                                  key=f"oe_new_saff_{parent_sid}_stato")
        if st.button("✅ Aggiungi subaffidatario", key=f"oe_btn_add_saff_{parent_sid}"):
            if not rs.strip():
                st.error("Inserire la ragione sociale.")
            else:
                saffs = sub.setdefault("subaffidatari", [])
                new_id = max((s.get("id", 0) for s in saffs), default=0) + 1
                saffs.append({
                    "id": new_id,
                    "ragione_sociale": rs.strip(),
                    "piva": piva.strip(),
                    "categoria_soa": soa.strip(),
                    "importo": float(importo),
                    "tipo": "subaffidamento",
                    "stato_autorizzazione": stato,
                    "documenti": _docs_suboperatore(),
                })
                aggiungi_log(
                    "Subaffidatario aggiunto",
                    f"{rs} → {sub.get('ragione_sociale', '')}",
                    tab=_TAB_NOME,
                )
                salva_fn()
                st.rerun()


def _render_saff(saff: dict, sub: dict, importo_base: float, results_dir: pathlib.Path, salva_fn, parent_sid: int) -> None:
    sfid = saff.get("id", 0)
    rs = saff.get("ragione_sociale", "—")
    stato = saff.get("stato_autorizzazione", "in_attesa")
    importo = float(saff.get("importo", 0) or 0)
    dir_path = results_dir / "operatori" / f"sub_{parent_sid}" / f"saff_{sfid}"

    durc_i = _durc_info(saff.get("documenti", {}).get("durc", {}).get("data_emissione", ""))
    label = (
        f"  🔗 {rs} — {_STATI_LABEL.get(stato, stato)} — "
        f"€ {importo:,.0f} — DURC {_SEM[durc_i['colore']]}"
    )

    with st.expander(label):
        st.caption(f"↳ Subaffidatario di: **{sub.get('ragione_sociale', '—')}**")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**Ragione Sociale:** {rs}")
            st.markdown(f"**P.IVA:** {saff.get('piva', '—') or '—'}")
            st.markdown(f"**SOA:** {saff.get('categoria_soa', '—') or '—'}")
        with c2:
            st.markdown(f"**Importo:** € {importo:,.2f}")
            nuovo_stato = st.selectbox(
                "Stato",
                _STATI_AUT,
                index=_STATI_AUT.index(stato) if stato in _STATI_AUT else 0,
                format_func=lambda x: _STATI_LABEL[x],
                key=f"oe_saff_{parent_sid}_{sfid}_stato",
            )
            if nuovo_stato != stato:
                saff["stato_autorizzazione"] = nuovo_stato
                salva_fn()

        st.divider()
        st.markdown("##### Documenti")
        docs = saff.setdefault("documenti", _docs_suboperatore())
        _render_docs_sub(docs, dir_path, f"oe_saff_{parent_sid}_{sfid}", salva_fn)

        st.divider()
        if st.button(f"🗑️ Elimina subaffidatario: {rs}", key=f"oe_saff_{parent_sid}_{sfid}_del"):
            sub["subaffidatari"] = [s for s in sub["subaffidatari"] if s.get("id") != sfid]
            aggiungi_log("Subaffidatario eliminato", rs, tab=_TAB_NOME)
            salva_fn()
            st.rerun()


# ── Funzione pubblica principale ───────────────────────────────────────────────

def render_operatori_tab(
    csa_data: dict,
    importo_base: float,
    salva_fn,
    results_dir: pathlib.Path,
) -> None:
    """Renderizza il tab Operatori Economici (L0/L1/L2) nell'app DTC."""
    _init()
    oe = st.session_state.operatori_economici

    # Log alert DURC una volta per sessione
    _log_durc_alerts(oe)

    st.header("🏢 Operatori Economici")
    st.caption(
        "Struttura gerarchica: **Appaltatore** → **Subappaltatori** → **Subaffidatari**. "
        "Subappalto: nessun limite fisso di legge (art.119 D.Lgs.36/2023 — limite definito dal CSA se presente)."
    )

    common = csa_data.get("comune", "")
    tipo = csa_data.get("tipo_lavori", "")
    if common or tipo:
        st.info(
            f"Cantiere: **{tipo}** — {common} ({csa_data.get('provincia', '')})"
            if tipo and common
            else tipo or common
        )

    # Sezione DURC semaforo
    render_durc_semaphore(oe)

    st.divider()

    # L0
    st.subheader("🏛️ L0 — Appaltatore Principale")
    _render_appaltatore(oe["appaltatore"], csa_data, results_dir, salva_fn)

    st.divider()

    # L1 + L2
    st.subheader("🏗️ L1/L2 — Subappaltatori e Subaffidatari")
    _render_limite(oe["subappaltatori"], importo_base, csa_data)
    st.divider()
    _render_form_sub(oe, importo_base, salva_fn)

    if oe["subappaltatori"]:
        st.divider()
        for sub in oe["subappaltatori"]:
            _render_sub(sub, oe, importo_base, results_dir, salva_fn)
    else:
        st.info("Nessun subappaltatore registrato. Usa il form sopra per aggiungerne uno.")
