# Business Plan — DTC App

## Mercato target

**Dimensione mercato**: ~45.000 tra Direttori Tecnici di Cantiere (DTC) e studi tecnici italiani attivi nella gestione di appalti pubblici regolati da D.Lgs. 36/2023.

**Segmentazione:**
- DTC dipendenti di imprese appaltatrici medie (€ 2–20M fatturato), 3–10 cantieri attivi
- DTC freelance che gestiscono appalti per conto di più imprese
- Studi tecnici (ingegneria/architettura) che supportano imprese in gara e gestione contrattuale

---

## Pricing

| Piano | Prezzo/mese | Utenti | Limiti | Target |
|---|---|---|---|---|
| **Base** | € 49 | 1 | Fino a 5 CSA/mese | DTC freelance, piccole imprese |
| **Pro** | € 99 | 3 | CSA illimitati, notifiche email automatiche | Imprese medie con più cantieri |
| **Azienda** | € 199 | Illimitati | Multi-cantiere, supporto prioritario | Imprese strutturate, studi tecnici |
| **White Label** | € 500+ | Illimitati | Branding personalizzato, API dedicata | Associazioni di categoria, software house |

---

## Piano beta tester (giugno 2026)

- 3-5 DTC / imprese appaltatrici come beta tester
- Prezzo beta: **€ 20/mese** (include Claude API Key condivisa con rate limiting)
- Feedback strutturato mensile (Google Forms o Notion)
- Durata beta: 3 mesi; poi pricing definitivo basato sull'utilizzo reale

---

## Proiezione ricavi

| Anno | Clienti attivi | ARR | Note |
|---|---|---|---|
| **Anno 1** | ~10 | **€ 5.880** | Beta tester + primi paganti; mix Base/Pro |
| **Anno 2** | ~30 | **€ 21.600** | Referral + LinkedIn; prevalenza piano Pro |
| **Anno 3** | ~80 | **€ 57.600** | Prime aziende + 1-2 White Label |
| **Anno 4** | ~150 | **€ 115.200** | Crescita organica consolidata |

Ipotesi: ARPU medio € 588/anno (mix ~50% Base, ~35% Pro, ~15% Azienda).

---

## Costi fissi mensili stimati

| Voce | Costo/mese |
|---|---|
| Claude API (quota condivisa beta + supporto) | ~ € 80 |
| Streamlit Community Cloud (piano Teams, opzionale) | ~ € 30 |
| Dominio + email professionale | ~ € 5 |
| Strumenti SaaS (Notion, Stripe, Google Workspace) | ~ € 40 |
| Marketing digitale (LinkedIn Ads, contenuti) | ~ € 120 |
| **Totale** | **~ € 275/mese** |

Break-even: ~6 clienti Piano Pro o ~12 clienti Piano Base.

---

## Canali di acquisizione

1. **LinkedIn** — contenuti educativi su D.Lgs. 36/2023, DM 49/2018, errori comuni DTC; targeting per ruolo "Direttore Tecnico", "Responsabile Appalti", "Ingegnere di cantiere"
2. **Passaparola** — referral incentivato (1 mese gratis per chi porta un cliente pagante)
3. **Community di settore** — forum ANCE, Ordini degli Ingegneri, gruppi WhatsApp DTC
4. **Beta tester come ambassador** — 3–5 DTC con accesso anticipato a € 20/mese; feedback pubblico e casi d'uso reali

---

## Rischi principali e mitigazioni

| Rischio | Probabilità | Impatto | Mitigazione |
|---|---|---|---|
| **Errori AI su clausole legali** | Alta | Alto | Disclaimer esplicito in UI: *"Output AI a scopo informativo — verificare con consulente legale"* |
| Cambiamenti normativi (D.Lgs. 36/2023) | Media | Medio | Prompt aggiornabili senza deploy; monitoraggio Gazzetta Ufficiale |
| Concorrenza da ERP cantiere (Primus, Acca) | Bassa | Medio | Posizionamento su AI + semplicità vs complessità ERP; nessuna installazione locale |
| Superamento quota API Claude su piano condiviso | Media | Basso | Rate limiting per sessione + upgrade piano Anthropic su crescita |
| Resistenza culturale all'AI in ambito contrattuale | Alta | Medio | Demo gratuita, casi d'uso concreti, enfasi su "strumento di supporto" |
