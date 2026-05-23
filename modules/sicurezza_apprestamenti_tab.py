"""
sicurezza_apprestamenti_tab.py — Tab Sicurezza e Apprestamenti
Estrae apprestamenti dal CME, verifica minimi D.Lgs. 81/2008,
genera lista ordini pre-cantiere.
"""

import json

import streamlit as st

# ── Helper importo ─────────────────────────────────────────────────────────────

def _parse_importo(v) -> float:
    if v is None:
        return 0.0
    try:
        return float(str(v).replace("€", "").replace(".", "").replace(",", ".").strip())
    except Exception:
        return 0.0


# ── Catalogo apprestamenti tipici ──────────────────────────────────────────────

_APPRESTAMENTI_KEYWORDS = {
    "ponteggio": {
        "label": "Ponteggio",
        "keywords": ["ponteggio", "ponteggi", "impalcatura", "trabattello"],
        "um": "mq",
        "minimo_legge": None,
        "norma": "Art. 122 D.Lgs. 81/2008",
        "icona": "🏗️",
    },
    "bagni": {
        "label": "Servizi igienici",
        "keywords": ["wc", "bagno", "servizi igienici", "latrina", "gabinetto"],
        "um": "nr",
        "minimo_legge": 1,  # Art. 81/2008: 1 ogni 10 lavoratori
        "norma": "All. IV D.Lgs. 81/2008 punto 1.14",
        "icona": "🚽",
    },
    "recinzione": {
        "label": "Recinzione cantiere",
        "keywords": ["recinzione", "cancello", "barriera", "delimitazione cantiere"],
        "um": "ml",
        "minimo_legge": None,
        "norma": "Art. 96 c.1 lett.a D.Lgs. 81/2008",
        "icona": "🚧",
    },
    "baracca": {
        "label": "Baracca/Spogliatoio",
        "keywords": ["baracca", "spogliatoio", "locale spogliatoio", "container ufficio"],
        "um": "nr",
        "minimo_legge": 1,
        "norma": "All. IV D.Lgs. 81/2008 punto 1.12",
        "icona": "🏠",
    },
    "deposito": {
        "label": "Deposito materiali",
        "keywords": ["deposito", "stoccaggio materiali", "area deposito"],
        "um": "mq",
        "minimo_legge": None,
        "norma": "Art. 96 D.Lgs. 81/2008",
        "icona": "📦",
    },
    "segnaletica": {
        "label": "Segnaletica di cantiere",
        "keywords": ["segnaletica", "cartelli", "pannelli segnalazione", "coni stradali"],
        "um": "nr",
        "minimo_legge": None,
        "norma": "D.Lgs. 81/2008 Titolo V",
        "icona": "⚠️",
    },
    "illuminazione": {
        "label": "Illuminazione cantiere",
        "keywords": ["illuminazione", "faro", "lampada cantiere", "proiettore"],
        "um": "nr",
        "minimo_legge": None,
        "norma": "All. IV D.Lgs. 81/2008 punto 1.10",
        "icona": "💡",
    },
    "pronto_soccorso": {
        "label": "Pronto soccorso / Cassetta",
        "keywords": ["pronto soccorso", "cassetta pronto soccorso", "pacchetto medicazione"],
        "um": "nr",
        "minimo_legge": 1,
        "norma": "Art. 45 D.Lgs. 81/2008",
        "icona": "🚑",
    },
    "estintore": {
        "label": "Estintori",
        "keywords": ["estintore", "estintori", "antincendio"],
        "um": "nr",
        "minimo_legge": 1,
        "norma": "DM 10/03/1998",
        "icona": "🧯",
    },
    "rete_anticaduta": {
        "label": "Reti anticaduta",
        "keywords": ["rete anticaduta", "rete di protezione", "reti di sicurezza"],
        "um": "mq",
        "minimo_legge": None,
        "norma": "Art. 115 D.Lgs. 81/2008",
        "icona": "🕸️",
    },
}


# ── Estrazione automatica via Claude API ───────────────────────────────────────

def _estrai_apprestamenti_da_cme(testo_cme: str, api_key: str) -> list[dict]:
    """Analizza testo CME ed estrae voci apprestamenti via Haiku."""
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""Sei un esperto di sicurezza cantieri (D.Lgs. 81/2008).
Analizza questo Computo Metrico Estimativo e identifica TUTTE le voci
relative agli apprestamenti di sicurezza e organizzazione del cantiere.

Per ogni voce trovata restituisci un oggetto JSON con:
- tipo: categoria (ponteggio|bagni|recinzione|baracca|deposito|segnaletica|illuminazione|pronto_soccorso|estintore|rete_anticaduta|altro)
- descrizione: descrizione originale della voce
- quantita: numero (float)
- um: unità di misura (mq, ml, nr, mc, ecc.)
- prezzo_unitario: prezzo unitario se presente (float o null)
- importo_totale: importo totale se presente (float o null)

Restituisci SOLO un array JSON valido, senza testo aggiuntivo.
Se non trovi apprestamenti restituisci array vuoto [].

TESTO CME:
{testo_cme[:80000]}"""

    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception:
        return []


# ── Render principale ──────────────────────────────────────────────────────────

def render_sicurezza_apprestamenti_tab(
    csa_data: dict,
    api_key: str,
    salva_fn,
    results_dir,
) -> None:
    st.header("🦺 Sicurezza e Apprestamenti Pre-Cantiere")
    st.caption(
        "Estrai gli apprestamenti obbligatori dal CME, "
        "verifica i minimi D.Lgs. 81/2008 e prepara la lista ordini."
    )

    # ── Sezione 1: Caricamento CME Sicurezza ──────────────────────────────────
    st.subheader("📄 Caricamento CME Sicurezza")

    cme_sic_bytes = st.session_state.get("piano_sicurezza_bytes")
    cme_sic_nome = st.session_state.get("piano_sicurezza_nome", "")

    if cme_sic_bytes:
        st.success(f"✅ CME Sicurezza: **{cme_sic_nome}** (già caricato)")
        if st.button("🔄 Sostituisci", key="sost_cme_sic"):
            del st.session_state["piano_sicurezza_bytes"]
            st.rerun()
    else:
        up = st.file_uploader(
            "Carica CME Sicurezza (Oneri per la Sicurezza)",
            type=["pdf", "xlsx", "xls"],
            key="up_cme_sicurezza",
        )
        if up and up.name != st.session_state.get("_cme_sic_nome_caricato"):
            st.session_state["piano_sicurezza_bytes"] = up.read()
            st.session_state["piano_sicurezza_nome"] = up.name
            st.session_state["_cme_sic_nome_caricato"] = up.name
            st.rerun()

    st.divider()

    # ── Sezione 2: Estrazione Apprestamenti ───────────────────────────────────
    st.subheader("🔍 Estrazione Apprestamenti")

    apprestamenti = st.session_state.get("apprestamenti_sicurezza", [])

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button(
            "🤖 Estrai automaticamente da CME",
            key="btn_estrai_apprest",
            disabled=(not cme_sic_bytes or not api_key),
        ):
            with st.spinner("Analisi CME sicurezza in corso..."):
                from modules.csa_analyzer import _estrai_testo_pdf
                testo = _estrai_testo_pdf(cme_sic_bytes)
                apprestamenti = _estrai_apprestamenti_da_cme(testo, api_key)
                st.session_state["apprestamenti_sicurezza"] = apprestamenti
                salva_fn()
                st.success(f"✅ Estratti {len(apprestamenti)} apprestamenti")
                st.rerun()

    with col_btn2:
        if st.button("➕ Aggiungi manualmente", key="btn_add_apprest_manual"):
            st.session_state["show_form_apprest"] = True

    # Form aggiunta manuale
    if st.session_state.get("show_form_apprest"):
        with st.expander("➕ Nuovo Apprestamento", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                tipo_man = st.selectbox(
                    "Tipo",
                    list(_APPRESTAMENTI_KEYWORDS.keys()) + ["altro"],
                    key="apprest_tipo_man",
                )
                desc_man = st.text_input("Descrizione", key="apprest_desc_man")
            with col2:
                qta_man = st.number_input("Quantità", min_value=0.0, key="apprest_qta_man")
                um_man = st.text_input("U.M.", value="nr", key="apprest_um_man")
            imp_man = st.number_input("Importo totale (€)", min_value=0.0, key="apprest_imp_man")
            if st.button("💾 Aggiungi", key="btn_save_apprest_man"):
                apprestamenti.append({
                    "tipo": tipo_man,
                    "descrizione": desc_man,
                    "quantita": qta_man,
                    "um": um_man,
                    "importo_totale": imp_man,
                    "fonte": "manuale",
                })
                st.session_state["apprestamenti_sicurezza"] = apprestamenti
                st.session_state["show_form_apprest"] = False
                salva_fn()
                st.rerun()

    st.divider()

    # ── Sezione 3: Tabella con verifica minimi ────────────────────────────────
    if apprestamenti:
        st.subheader("📋 Apprestamenti identificati")

        per_tipo: dict[str, list] = {}
        for a in apprestamenti:
            t = a.get("tipo", "altro")
            per_tipo.setdefault(t, []).append(a)

        tot_importo = 0.0
        n_ok = 0
        n_warning = 0

        for tipo, voci in per_tipo.items():
            info = _APPRESTAMENTI_KEYWORDS.get(tipo, {
                "label": tipo.capitalize(),
                "icona": "📦",
                "minimo_legge": None,
                "norma": "—",
                "um": "nr",
            })

            tot_qta = sum(float(v.get("quantita", 0) or 0) for v in voci)
            tot_imp = sum(float(v.get("importo_totale", 0) or 0) for v in voci)
            tot_importo += tot_imp

            minimo = info.get("minimo_legge")
            if minimo and tot_qta < minimo:
                stato = "🔴"
                n_warning += 1
            else:
                stato = "✅"
                n_ok += 1

            with st.container(border=True):
                col_a, col_b, col_c, col_d = st.columns([3, 2, 2, 1])
                with col_a:
                    st.markdown(f"**{info['icona']} {info['label']}**")
                    st.caption(f"Norma: {info['norma']}")
                with col_b:
                    st.metric("Quantità", f"{tot_qta:.1f} {info['um']}")
                    if minimo:
                        st.caption(f"Minimo legge: {minimo} {info['um']}")
                with col_c:
                    if tot_imp > 0:
                        st.metric("Importo", f"€ {tot_imp:,.2f}")
                with col_d:
                    st.markdown(f"## {stato}")

        # Totali
        st.divider()
        col_t1, col_t2, col_t3 = st.columns(3)
        col_t1.metric("Totale oneri apprestamenti", f"€ {tot_importo:,.2f}")
        col_t2.metric("✅ Conformi", n_ok)
        col_t3.metric(
            "🔴 Sotto minimo legge",
            n_warning,
            delta_color="inverse" if n_warning > 0 else "off",
        )

        if n_warning > 0:
            st.error(
                f"❌ **{n_warning} apprestamenti sotto il minimo di legge** — "
                "verifica e integra prima dell'apertura del cantiere"
            )
        else:
            st.success("✅ Tutti gli apprestamenti rispettano i minimi D.Lgs. 81/2008")

        st.divider()

        # ── Sezione 4: Lista Ordini Pre-Cantiere ──────────────────────────────
        st.subheader("📋 Lista Ordini Pre-Cantiere")
        st.caption("Apprestamenti da ordinare prima dell'apertura del cantiere")

        for idx, a in enumerate(apprestamenti):
            tipo = a.get("tipo", "altro")
            info = _APPRESTAMENTI_KEYWORDS.get(tipo, {"icona": "📦"})
            ordinato_key = f"apprest_ordinato_{idx}"

            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.caption(f"{info.get('icona', '📦')} {a.get('descrizione', tipo)}")
            with col2:
                st.caption(
                    f"{a.get('quantita', 0)} {a.get('um', 'nr')} "
                    f"— € {float(a.get('importo_totale', 0) or 0):,.2f}"
                )
            with col3:
                st.checkbox(
                    "Ordinato",
                    key=ordinato_key,
                    value=a.get("ordinato", False),
                )

        if st.button("📄 Esporta Lista Ordini PDF", key="btn_export_apprest"):
            st.info("🔜 Export PDF lista ordini — in arrivo")

        # Pulsante cancella tutto
        if st.button("🗑️ Cancella tutti gli apprestamenti", key="btn_clear_apprest"):
            st.session_state["apprestamenti_sicurezza"] = []
            salva_fn()
            st.rerun()

    else:
        st.info(
            "Nessun apprestamento identificato. "
            "Carica il CME Sicurezza e clicca 'Estrai automaticamente', "
            "oppure aggiungi manualmente."
        )
