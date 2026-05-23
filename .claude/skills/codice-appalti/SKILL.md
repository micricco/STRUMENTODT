---
name: codice-appalti
description: "D.Lgs. 36/2023 (Codice dei Contratti Pubblici) + Correttivo D.Lgs. 209/2024. Usa quando devi rispondere a domande su appalti pubblici italiani: anticipazione contrattuale (Art.125), riserve (Art.120), subappalto (Art.119), revisione prezzi (Art.60), SAL, penali, collaudo, consegna lavori. Normativa di riferimento per il Direttore Tecnico di Cantiere (DTC)."
argument-hint: [articolo, tema, es. "Art.125" o "anticipazione" o "riserve"]
---

# D.Lgs. 36/2023 — Codice dei Contratti Pubblici
**Fonte**: D.Lgs. 31 marzo 2023 n. 36 + Correttivo D.Lgs. 31 dicembre 2024 n. 209
**Ambito**: Lavori, servizi, forniture — appalti pubblici italiani

## Come usare questa skill

- Chiedi di un articolo specifico → rispondo con il testo normativo esatto
- Chiedi di un tema → indico gli articoli applicabili e le regole operative
- Devo redigere un documento → applico la norma alla fattispecie concreta

---

## Articoli critici per il DTC

### Art. 125 — Anticipazione del prezzo
**Soggetto**: Stazione Appaltante (SA) eroga / Appaltatore riceve

- L'anticipazione è pari al **20% dell'importo contrattuale** (netto ribasso)
- Erogata entro **15 giorni** dalla data di effettivo inizio dei lavori (previa presentazione di fideiussione pari all'anticipazione + interessi legali)
- **Recupero graduale**: trattenuta su ogni SAL nella stessa proporzione (20% del lordo SAL); il recupero non può essere superiore all'anticipazione residua
- **Correttivo 2024**: confermato il 20% anche per contratti derivanti da accordi quadro e concessioni
- **Fideiussione**: deve essere rilasciata da banca, assicurazione o intermediario finanziario; si riduce proporzionalmente ad ogni recupero SAL
- Mancata restituzione dell'anticipazione non recuperata → escussione fideiussione + risoluzione contratto

**Applicazione pratica DTC**:
- Verificare che la fideiussione sia acquisita prima di erogare
- Applicare la trattenuta su ogni certificato di pagamento SAL: `recupero = importo_lordo_SAL × 20%`
- Aggiornare il registro anticipazione ad ogni SAL

---

### Art. 120 — Riserve e accordo bonario
**Termini perentori**:

| Adempimento | Termine | Decadenza |
|---|---|---|
| Iscrizione riserva sul registro | Entro **15 gg** dall'evento che la genera | Perdita del diritto |
| Esplicitazione/quantificazione | Entro **15 gg** dalla firma dell'atto contabile successivo | Inammissibilità |
| Istanza accordo bonario | Quando riserve superano **15% importo contrattuale** | — |

**Procedura accordo bonario (Art. 120 c.6)**:
1. Appaltatore trasmette istanza al RUP
2. Nomina esperto da parte del RUP entro 15 gg
3. Proposta di accordo entro **45 gg** dalla nomina
4. Accettazione/rifiuto entro **30 gg** dalla proposta
5. Se rifiutata → arbitrato o giurisdizione ordinaria

**Riserve inammissibili**: pretese superiori al 20% del valore del contratto (limite complessivo Art. 120 c.2)

**Applicazione pratica DTC**:
- Vigilare che il libro contratti sia firmato contestualmente alla stesura
- Controllare date e notificare all'appaltatore i termini di scadenza
- Documentare ogni evento generatore di riserva nel giornale dei lavori

---

### Art. 119 — Subappalto
**Limiti**:
- Massimo **50%** dell'importo totale del contratto (Correttivo 2024: elevato dal 30% al 50% per i lavori)
- Autorizzazione preventiva della SA obbligatoria
- Subappaltatore deve essere qualificato per la categoria SOA subappaltata

**Adempimenti obbligatori**:
- Comunicare nominativo subappaltatore **almeno 10 giorni** prima dell'inizio delle lavorazioni
- Trasmettere: contratto di subappalto, DURC subappaltatore, certificato antimafia (se importo > €150.000)
- Pagamento diretto del subappaltatore dalla SA se richiesto o in caso di inadempimento dell'appaltatore

**Categorie non subappaltabili** (regola generale): categorie SOA a qualificazione obbligatoria superspecializzata (OS 18-A, OS 21 oltre certi importi); verificare il CSA per restrizioni specifiche

**Subaffidamento (Art. 122)**: max **10% dell'importo del singolo subappalto**; soggetto alle stesse norme del subappalto

---

### Art. 60 — Revisione prezzi (ex art. 29 D.Lgs. 50/2016)
**Applicazione obbligatoria** per contratti di lavori con durata superiore a 12 mesi

**Meccanismo**:
- Variazione ≥ **5%** rispetto al prezzo originale (soglia di attivazione)
- Revisione applicata sulla quota eccedente il 5% (non sull'intera variazione)
- Indici di riferimento: ISTAT per i materiali edili, ANAC per i singoli servizi
- Il CSA deve indicare l'elenco delle voci soggette a revisione

**Formula base**:
```
Revisione = (Prezzo_attuale - Prezzo_contrattuale × 1.05) × Quantità_eseguita
```
applicata per ciascuna voce con variazione > 5%

**Correttivo 2024**: introdotto meccanismo di compensazione prezzi per le "opere in corso" — tabelle MEF aggiornate semestralmente

---

### Art. 108 — SAL e pagamenti
**Termini di pagamento**:
- SA emette il certificato di pagamento entro **30 giorni** dal SAL
- Pagamento entro **30 giorni** dal certificato di pagamento
- Ritardo → interessi legali maggiorati (tasso BCE + 8 punti)

**Ritenuta di garanzia**: 0,5% su ogni certificato di pagamento; svincolata dopo collaudo o CRE

**SAL finale**: emesso dopo ultimazione lavori; base per il calcolo del saldo

---

### Art. 115-116 — Sospensioni dei lavori
**Sospensione legittima**: cause di forza maggiore, condizioni meteo eccezionali, necessità di coordinamento con altri appalti, ordine della SA per cause non imputabili all'appaltatore

**Termini**:
- Verbale di sospensione: redatto **contestualmente** all'evento
- Sospensione massima cumulata: **1/4 della durata contrattuale** (oltre: diritto all'equo compenso o risoluzione)
- Ripresa lavori: verbale di ripresa firmato da DL e appaltatore

**Sospensione illegittima**: imputabile alla SA → risarcimento del danno + proroga del termine contrattuale

---

### Art. 1 c.2 — Collaudo / CRE
- Lavori ≤ €1.000.000: Certificato di Regolare Esecuzione (CRE) in luogo del collaudo
- Lavori > €1.000.000: collaudo tecnico-amministrativo obbligatorio
- Termine: entro **6 mesi** dall'ultimazione (prorogabile fino a 12 mesi per opere complesse)
- Collaudo statico: obbligatorio per opere in cemento armato, acciaio, prefabbricati (D.P.R. 380/2001)

---

### Art. 90 — Penali per ritardo
- Misura: definita nel contratto, normalmente **1‰ per giorno** di ritardo
- Massimale: **10% dell'importo contrattuale netto**
- Raggiunto il massimale → risoluzione contrattuale facoltativa della SA (Art. 122)
- Contabilizzazione: detratta dal certificato di pagamento SAL o dal saldo finale
- Contestazione formale: l'appaltatore deve contestare con riserva sul verbale di accertamento del ritardo

---

## Categorie SOA — Riferimento rapido

| Classifica | Importo massimo |
|---|---|
| I | fino a €258.228 |
| II | fino a €516.457 |
| III | fino a €1.032.913 |
| IV | fino a €2.582.284 |
| V | fino a €5.164.569 |
| VI | fino a €10.329.138 |
| VII | fino a €15.493.707 |
| VIII | oltre €15.493.707 |

**Categorie prevalenti più comuni lavori**:
- OG1: Edifici civili e industriali
- OG3: Strade, autostrade, ponti, viadotti
- OG6: Acquedotti, gasdotti, oleodotti, opere di irrigazione e di evacuazione
- OG8: Opere fluviali, di difesa, sistemazione idraulica
- OS18-A: Componenti strutturali in acciaio (qualificazione obbligatoria)

---

## Scadenzario tipo DTC (riferimenti normativi)

| Evento | Termine | Articolo |
|---|---|---|
| Iscrizione riserva | 15 gg dall'evento | Art. 120 |
| Esplicitazione riserva | 15 gg dalla firma atto contabile | Art. 120 |
| Emissione certificato pagamento | 30 gg dal SAL | Art. 108 |
| Pagamento SAL | 30 gg dal certificato | Art. 108 |
| Comunicazione subappaltatore | 10 gg prima inizio lavorazioni | Art. 119 |
| Collaudo/CRE | 6 mesi da ultimazione lavori | Allegato II.14 |
| Svincolo ritenuta garanzia | Dopo collaudo/CRE | Art. 108 |
