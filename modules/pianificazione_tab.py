"""
pianificazione_tab.py — Tab Pianificazione per app DTC.

Layout 2 colonne: Cronoprogramma (sx) + Documenti CME (dx).
KPI in cima, associazione fasi→voci, generazione Excel
tramite pianificazione_excel.genera_excel_pianificazione().
"""

import io
import json
import re
import pathlib

import pandas as pd
import streamlit as st
import anthropic

from modules.log_manager import aggiungi_log, aggiungi_al_diario
from modules.csa_analyzer import _estrai_testo_pdf
from pianificazione_excel import genera_excel_pianificazione

_MODELLO = "claude-haiku-4-5-20251001"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_json_risposta(raw: str) -> list | dict:
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        inner = lines[1:-1] if lines and lines[-1].strip() == "```" else lines[1:]
        raw = "\n".join(inner)
    try:
        return json.loads(raw)
    except Exception:
        m = re.search(r"(\[[\s\S]*\]|\{[\s\S]*\})", raw)
        if m:
            try:
                return json.loads(m.group(1))
            except Exception:
                pass
    return []


def _init_piano() -> dict:
    return {
        "fasi": [],
        "voci_cme": [],
        "voci_sicurezza": [],
        "totale_cme": 0.0,
        "totale_sicurezza": 0.0,
        "associazioni": {},
        "_gantt_file_id": None,
        "_cme_file_ids": [],
        "_sicurezza_file_id": None,
        "_associazione_auto_fatta": False,
    }


def _conta_pagine_pdf(fb: bytes) -> int:
    try:
        import fitz
        doc = fitz.open(stream=fb, filetype="pdf")
        n = doc.page_count
        doc.close()
        return n
    except Exception:
        return 0


def _get_pagine_cached(f) -> int:
    """Conta pagine di un UploadedFile, con cache per evitare riletture."""
    cache = st.session_state.setdefault("pian_pg_cache", {})
    fid = f"{f.name}_{f.size}"
    if fid not in cache:
        fb = f.read()
        f.seek(0)
        cache[fid] = _conta_pagine_pdf(fb)
    return cache[fid]


# ── Estrazione Gantt ──────────────────────────────────────────────────────────

def _estrai_fasi_gantt_excel(file_bytes: bytes) -> list[dict]:
    try:
        df = pd.read_excel(io.BytesIO(file_bytes))
    except Exception as e:
        st.error(f"Errore lettura Excel: {e}")
        return []

    col_map: dict[str, str] = {}
    for col in df.columns:
        cl = str(col).lower().strip()
        if any(k in cl for k in ("attivit", "nome", "fase", "lavoraz", "descr")):
            col_map.setdefault("nome", col)
        elif any(k in cl for k in ("durata", "duration")):
            col_map.setdefault("durata", col)
        elif any(k in cl for k in ("inizio", "start")):
            col_map.setdefault("inizio", col)
        elif any(k in cl for k in ("fine", "end", "finish")):
            col_map.setdefault("fine", col)

    nome_col = col_map.get("nome", df.columns[0] if len(df.columns) > 0 else None)
    if nome_col is None:
        return []

    fasi = []
    for _, row in df.iterrows():
        nome = str(row.get(nome_col, "") or "").strip()
        if not nome or nome.lower() in ("nan", "none", ""):
            continue

        def _int_safe(col_key):
            col = col_map.get(col_key)
            if not col:
                return None
            try:
                v = row.get(col)
                return int(v) if v is not None and str(v) not in ("nan", "None", "") else None
            except Exception:
                return None

        inizio = _int_safe("inizio")
        fine = _int_safe("fine")
        durata_gg = _int_safe("durata")

        inizio = inizio or 1
        fine = fine or inizio
        if not durata_gg:
            durata_gg = max(1, (fine - inizio + 1) * 5)

        fasi.append({
            "nome": nome,
            "durata_giorni": durata_gg,
            "settimana_inizio": inizio,
            "settimana_fine": fine,
        })
    return fasi


def _estrai_fasi_gantt_pdf(testo: str, api_key: str) -> list[dict]:
    client = anthropic.Anthropic(api_key=api_key)
    prompt = (
        "Estrai le fasi del cronoprogramma in JSON.\n"
        "Rispondi SOLO con JSON valido.\n"
        '[{"nome": "ORGANIZZAZIONE CANTIERE",'
        '"durata_giorni": 5,'
        '"settimana_inizio": 1,'
        '"settimana_fine": 1}]\n\n'
        f"TESTO:\n{testo[:50_000]}"
    )
    try:
        resp = client.messages.create(
            model=_MODELLO, max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        result = _parse_json_risposta(resp.content[0].text)
        return result if isinstance(result, list) else []
    except Exception as e:
        st.warning(f"Errore estrazione Gantt da PDF: {e}")
        return []


# ── Estrazione CME e Sicurezza ────────────────────────────────────────────────

def _estrai_voci_cme(testo: str, api_key: str) -> list[dict]:
    client = anthropic.Anthropic(api_key=api_key)
    prompt = (
        "Estrai le voci del computo metrico in JSON.\n"
        "Rispondi SOLO con JSON valido, nessun testo.\n"
        '[{"numero": "1/1",'
        '"categoria": "DEMOLIZIONI",'
        '"descrizione": "Rimozione manto copertura...",'
        '"quantita": 180.00,'
        '"unita_misura": "mq",'
        '"prezzo_unitario": 19.66,'
        '"importo_totale": 3538.80,'
        '"tipo": "cme"}]\n\n'
        f"TESTO:\n{testo[:60_000]}"
    )
    try:
        resp = client.messages.create(
            model=_MODELLO, max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        result = _parse_json_risposta(resp.content[0].text)
        return result if isinstance(result, list) else []
    except Exception as e:
        st.warning(f"Errore estrazione CME: {e}")
        return []


def _estrai_voci_sicurezza(testo: str, api_key: str) -> list[dict]:
    client = anthropic.Anthropic(api_key=api_key)
    prompt = (
        "Estrai le voci degli oneri per la sicurezza in JSON.\n"
        "Ogni voce ha nota 'NON SOGGETTO A RIBASSO'.\n"
        "Rispondi SOLO con JSON valido, nessun testo.\n"
        '[{"numero": "1",'
        '"categoria": "SICUREZZA",'
        '"descrizione": "Ponteggio telaio prefabbricato h>10m...",'
        '"quantita": 648.0,'
        '"unita_misura": "mq",'
        '"prezzo_unitario": 21.53,'
        '"importo_totale": 13951.44,'
        '"tipo": "sicurezza",'
        '"nota": "NON SOGGETTO A RIBASSO"}]\n\n'
        f"TESTO:\n{testo[:60_000]}"
    )
    try:
        resp = client.messages.create(
            model=_MODELLO, max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        result = _parse_json_risposta(resp.content[0].text)
        return result if isinstance(result, list) else []
    except Exception as e:
        st.warning(f"Errore estrazione Oneri Sicurezza: {e}")
        return []


# ── Associazione automatica ───────────────────────────────────────────────────

def _associa_fasi_voci(fasi: list[dict], voci: list[dict], api_key: str) -> dict:
    client = anthropic.Anthropic(api_key=api_key)
    json_fasi = json.dumps(
        [{"nome": f.get("nome", ""), "durata_giorni": f.get("durata_giorni", 0)}
         for f in fasi],
        ensure_ascii=False,
    )
    json_voci = json.dumps(
        [{"id": str(i), "numero": v.get("numero", ""), "descrizione": v.get("descrizione", "")}
         for i, v in enumerate(voci[:150])],
        ensure_ascii=False,
    )
    prompt = (
        f"Hai queste fasi del cronoprogramma:\n{json_fasi}\n\n"
        f"E queste voci di computo metrico:\n{json_voci}\n\n"
        "Associa ogni voce alla fase più probabile basandoti sulla descrizione della lavorazione.\n"
        "Rispondi SOLO con JSON:\n"
        '{"FASE 1 – ORGANIZZAZIONE": ["0","1","2"],'
        '"FASE 2 – DEMOLIZIONI": ["3","4","5"]}'
    )
    try:
        resp = client.messages.create(
            model=_MODELLO, max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        result = _parse_json_risposta(resp.content[0].text)
        return result if isinstance(result, dict) else {}
    except Exception as e:
        st.warning(f"Errore associazione automatica: {e}")
        return {}


# ── Render principale ─────────────────────────────────────────────────────────

def render_pianificazione_tab(
    csa_data: dict,
    api_key: str,
    salva_fn,
    results_dir: pathlib.Path,
) -> None:

    if "pianificazione" not in st.session_state:
        st.session_state.pianificazione = _init_piano()
    piano = st.session_state.pianificazione

    nome_progetto = (
        f"{csa_data.get('tipo_lavori', 'Cantiere')} — "
        f"{csa_data.get('comune', '')} ({csa_data.get('provincia', '')})"
    )

    # ── KPI sempre visibili in cima ───────────────────────────────────────────
    voci_cme = piano.get("voci_cme", [])
    voci_sicurezza = piano.get("voci_sicurezza", [])
    fasi = piano.get("fasi", [])

    tot_cme = sum(float(v.get("importo_totale") or 0) for v in voci_cme)
    tot_sic = sum(float(v.get("importo_totale") or 0) for v in voci_sicurezza)
    tot_appalto = tot_cme + tot_sic
    durata_tot = sum(int(f.get("durata_giorni") or 0) for f in fasi)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💰 Totale CME", f"€ {tot_cme:,.2f}")
    col2.metric("🔴 Oneri Sicurezza", f"€ {tot_sic:,.2f}")
    col3.metric("📊 Totale Appalto", f"€ {tot_appalto:,.2f}")
    col4.metric("📅 Durata totale", f"{durata_tot} gg" if durata_tot else "—")

    st.divider()

    # ── 2 colonne affiancate ──────────────────────────────────────────────────
    col_sx, col_dx = st.columns([1, 1])

    # ════════════════════════════════════════════════════════════════════════
    # COLONNA SINISTRA — Cronoprogramma
    # ════════════════════════════════════════════════════════════════════════
    with col_sx:
        st.subheader("📅 Cronoprogramma")

        file_gantt = st.file_uploader(
            "Carica Cronoprogramma",
            type=["pdf", "xlsx", "xls"],
            key="upload_gantt",
        )

        if file_gantt:
            fid = f"{file_gantt.name}_{file_gantt.size}"
            if fid != piano.get("_gantt_file_id"):
                fb = file_gantt.read()
                file_gantt.seek(0)
                fasi_estratte: list[dict] = []

                if file_gantt.name.lower().endswith((".xlsx", ".xls")):
                    fasi_estratte = _estrai_fasi_gantt_excel(fb)
                else:
                    if not api_key:
                        st.error("API key mancante per analizzare PDF Gantt.")
                    else:
                        with st.spinner("Estrazione fasi da PDF…"):
                            testo = _estrai_testo_pdf(fb)
                            fasi_estratte = _estrai_fasi_gantt_pdf(testo, api_key)

                if fasi_estratte:
                    piano["fasi"] = fasi_estratte
                    piano["_gantt_file_id"] = fid
                    piano["_associazione_auto_fatta"] = False
                    aggiungi_log(
                        "Gantt caricato",
                        f"{file_gantt.name} — {len(fasi_estratte)} fasi",
                        "Pianificazione",
                    )
                    aggiungi_al_diario(
                        f"Cronoprogramma caricato: {file_gantt.name} — {len(fasi_estratte)} fasi",
                        "🟡 Adempimento Organizzativo",
                    )
                    salva_fn()
                    st.rerun()
                else:
                    st.warning("Nessuna fase estratta. Usa l'inserimento manuale.")

        if piano.get("fasi"):
            df_fasi = pd.DataFrame(piano["fasi"])
            for c in ["nome", "durata_giorni", "settimana_inizio", "settimana_fine"]:
                if c not in df_fasi.columns:
                    df_fasi[c] = "" if c == "nome" else 1
            edited = st.data_editor(
                df_fasi[["nome", "durata_giorni", "settimana_inizio", "settimana_fine"]],
                use_container_width=True,
                num_rows="dynamic",
                key="pian_fasi_de",
                column_config={
                    "nome": st.column_config.TextColumn("Nome Fase", width="large"),
                    "durata_giorni": st.column_config.NumberColumn("Durata (gg)", min_value=1),
                    "settimana_inizio": st.column_config.NumberColumn("Sett. Inizio", min_value=1),
                    "settimana_fine": st.column_config.NumberColumn("Sett. Fine", min_value=1),
                },
            )
            if edited is not None:
                aggiornate = edited.fillna("").to_dict("records")
                if aggiornate != piano["fasi"]:
                    piano["fasi"] = aggiornate
                    piano["_associazione_auto_fatta"] = False
                    salva_fn()
        else:
            st.info("Nessun cronoprogramma caricato.")
            if st.button("➕ Inserisci fasi manualmente", key="pian_gantt_manual"):
                piano["fasi"] = [
                    {"nome": "FASE 1 – ORGANIZZAZIONE CANTIERE",
                     "durata_giorni": 5, "settimana_inizio": 1, "settimana_fine": 1},
                ]
                piano["_gantt_file_id"] = "manual"
                salva_fn()
                st.rerun()

    # ════════════════════════════════════════════════════════════════════════
    # COLONNA DESTRA — Documenti di Computo
    # ════════════════════════════════════════════════════════════════════════
    with col_dx:
        st.subheader("📋 Documenti di Computo")

        files_cme = st.file_uploader(
            "Computo Metrico Estimativo (uno o più PDF)",
            type=["pdf"],
            accept_multiple_files=True,
            key="upload_cme",
        )

        file_elenco = st.file_uploader(
            "Elenco Prezzi (PDF)",
            type=["pdf"],
            key="upload_elenco",
        )

        file_sicurezza = st.file_uploader(
            "Oneri per la Sicurezza (PDF)",
            type=["pdf"],
            key="upload_sicurezza",
        )

        # Mostra stato file caricati
        for f in (files_cme or []):
            n_pag = _get_pagine_cached(f)
            st.success(f"✅ {f.name} — {n_pag} pagine caricato")

        if file_elenco:
            n_pag = _get_pagine_cached(file_elenco)
            st.success(f"✅ {file_elenco.name} — {n_pag} pagine caricato")

        if file_sicurezza:
            n_pag = _get_pagine_cached(file_sicurezza)
            st.success(f"✅ {file_sicurezza.name} — {n_pag} pagine caricato")

        if files_cme or file_sicurezza:
            if st.button("🔍 Estrai dati da tutti i documenti", type="primary", key="pian_estrai"):
                if not api_key:
                    st.error("API key mancante nella sidebar.")
                else:
                    tutte_cme: list[dict] = []
                    tutte_sic: list[dict] = []
                    ids_cme = [f"{f.name}_{f.size}" for f in (files_cme or [])]

                    if files_cme:
                        prog = st.progress(0.0, text="Analisi CME…")
                        for i, f in enumerate(files_cme):
                            prog.progress(
                                (i + 0.5) / len(files_cme),
                                text=f"Analisi {f.name}…",
                            )
                            testo = _estrai_testo_pdf(f.read())
                            f.seek(0)
                            voci = _estrai_voci_cme(testo, api_key)
                            tutte_cme.extend(voci)
                        prog.progress(1.0, text="CME completato.")

                    if file_sicurezza:
                        with st.spinner(f"Analisi {file_sicurezza.name}…"):
                            testo_sic = _estrai_testo_pdf(file_sicurezza.read())
                            file_sicurezza.seek(0)
                            tutte_sic = _estrai_voci_sicurezza(testo_sic, api_key)

                    piano["voci_cme"] = tutte_cme
                    piano["voci_sicurezza"] = tutte_sic
                    piano["totale_cme"] = sum(
                        float(v.get("importo_totale") or 0) for v in tutte_cme
                    )
                    piano["totale_sicurezza"] = sum(
                        float(v.get("importo_totale") or 0) for v in tutte_sic
                    )
                    piano["_cme_file_ids"] = ids_cme
                    piano["_sicurezza_file_id"] = (
                        f"{file_sicurezza.name}_{file_sicurezza.size}"
                        if file_sicurezza else None
                    )
                    piano["_associazione_auto_fatta"] = False
                    n_c = len(tutte_cme)
                    n_s = len(tutte_sic)
                    aggiungi_log(
                        "CME estratto",
                        f"{n_c} voci CME + {n_s} voci sicurezza",
                        "Pianificazione",
                    )
                    aggiungi_al_diario(
                        f"CME estratto: {n_c} voci CME + {n_s} voci sicurezza",
                        "🟡 Adempimento Organizzativo",
                    )
                    salva_fn()
                    st.rerun()

        # Stato estratto da sessione
        n_cme_ok = len(piano.get("voci_cme", []))
        n_sic_ok = len(piano.get("voci_sicurezza", []))
        if n_cme_ok or n_sic_ok:
            st.info(f"✅ {n_cme_ok} voci CME + {n_sic_ok} voci sicurezza estratte")

    # ════════════════════════════════════════════════════════════════════════
    # ASSOCIAZIONE FASI → VOCI
    # ════════════════════════════════════════════════════════════════════════
    voci_cme_curr = piano.get("voci_cme", [])
    voci_sic_curr = piano.get("voci_sicurezza", [])
    fasi_curr = piano.get("fasi", [])
    tutte_voci = voci_cme_curr + voci_sic_curr
    n_cme_curr = len(voci_cme_curr)

    if not (fasi_curr and tutte_voci):
        return

    st.divider()
    st.subheader("🔗 Associazione Fasi → Voci")

    if not piano.get("_associazione_auto_fatta"):
        if api_key:
            if st.button(
                "🤖 Associa automaticamente Fasi e Voci",
                type="primary",
                key="pian_auto_assoc",
            ):
                with st.spinner("Claude Haiku associa fasi ↔ voci CME…"):
                    assoc = _associa_fasi_voci(fasi_curr, tutte_voci, api_key)
                if assoc:
                    piano["associazioni"] = assoc
                    piano["_associazione_auto_fatta"] = True
                    aggiungi_log(
                        "Associazione fasi-voci",
                        f"{len(assoc)} fasi associate",
                        "Pianificazione",
                    )
                    salva_fn()
                    st.rerun()
                else:
                    st.warning("Associazione automatica non riuscita. Procedi manualmente.")
        else:
            st.info("Inserisci la API key nella sidebar per l'associazione automatica.")

    # Mappa indice → etichetta (🔴 per voci sicurezza)
    labels_voci = {
        str(i): (
            f"{'🔴 ' if i >= n_cme_curr else ''}"
            f"[{v.get('numero', str(i))}] {v.get('descrizione', '')[:55]}"
        )
        for i, v in enumerate(tutte_voci)
    }
    label_to_id = {v: k for k, v in labels_voci.items()}

    for fi, fase in enumerate(fasi_curr):
        nome_fase = str(fase.get("nome", f"Fase {fi + 1}"))
        ids_assoc = [x for x in piano["associazioni"].get(nome_fase, []) if x in labels_voci]

        voci_f = [tutte_voci[int(i)] for i in ids_assoc if int(i) < len(tutte_voci)]
        budget_cme_f = sum(
            float(v.get("importo_totale") or 0) for v in voci_f
            if v.get("tipo", "cme") != "sicurezza"
        )
        budget_sic_f = sum(
            float(v.get("importo_totale") or 0) for v in voci_f
            if v.get("tipo") == "sicurezza"
        )
        budget_tot_f = budget_cme_f + budget_sic_f

        with st.expander(
            f"📌 {nome_fase} — {fase.get('durata_giorni', '?')} gg "
            f"— S{fase.get('settimana_inizio', '?')}÷S{fase.get('settimana_fine', '?')} "
            f"— € {budget_tot_f:,.0f}",
            expanded=False,
        ):
            default_labels = [labels_voci[i] for i in ids_assoc if i in labels_voci]
            sel = st.multiselect(
                "Voci associate",
                options=list(labels_voci.values()),
                default=default_labels,
                key=f"pian_ms_{fi}",
            )
            nuovi_ids = [label_to_id[l] for l in sel if l in label_to_id]
            if set(nuovi_ids) != set(ids_assoc):
                piano["associazioni"][nome_fase] = nuovi_ids
                salva_fn()
                st.rerun()

            cb1, cb2, cb3 = st.columns(3)
            cb1.metric("💰 Budget CME", f"€ {budget_cme_f:,.2f}")
            cb2.metric("🔴 Budget Sicurezza", f"€ {budget_sic_f:,.2f}")
            cb3.metric("📊 Budget Totale", f"€ {budget_tot_f:,.2f}")

    # ════════════════════════════════════════════════════════════════════════
    # GENERAZIONE EXCEL
    # ════════════════════════════════════════════════════════════════════════
    st.divider()

    if st.button("📥 Genera Excel Pianificazione", type="primary", key="pian_genera_excel"):
        # Costruisce mappa voce_index → nome_fase
        voce_to_fase: dict[int, str] = {}
        for nome_fase, ids in piano.get("associazioni", {}).items():
            for vid in ids:
                try:
                    voce_to_fase[int(vid)] = nome_fase
                except (ValueError, TypeError):
                    pass

        # Aggiunge fase_associata alle voci CME
        voci_cme_ex = []
        for i, v in enumerate(voci_cme_curr):
            v2 = dict(v)
            v2["fase_associata"] = voce_to_fase.get(i, "")
            voci_cme_ex.append(v2)

        # Aggiunge fase_associata e non_ribassabile alle voci sicurezza
        voci_sic_ex = []
        for i, v in enumerate(voci_sic_curr):
            v2 = dict(v)
            v2["fase_associata"] = voce_to_fase.get(n_cme_curr + i, "")
            v2["non_ribassabile"] = True
            voci_sic_ex.append(v2)

        try:
            buf = genera_excel_pianificazione(
                fasi_curr, voci_cme_ex, voci_sic_ex, nome_progetto
            )
            st.session_state["_excel_pianificazione"] = buf.getvalue()
            aggiungi_log("Excel generato", f"Pianificazione {nome_progetto}", "Pianificazione")
            salva_fn()
        except Exception as e:
            st.error(f"Errore generazione Excel: {e}")

    if "_excel_pianificazione" in st.session_state:
        st.download_button(
            label="📥 Scarica Excel Pianificazione",
            data=st.session_state["_excel_pianificazione"],
            file_name=f"Pianificazione_{nome_progetto}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
