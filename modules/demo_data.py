"""
Dati fittizi ma realistici per la modalità demo dell'app.
Cantiere: Rifacimento manto stradale Via Roma e strade limitrofe — Comune di Bergamo (BG)
"""
import pandas as pd


DEMO_CSA_DATA = {
    # ── Dati generali ─────────────────────────────────────────────────────────
    "stazione_appaltante": "Comune di Bergamo — Settore Lavori Pubblici e Manutenzioni",
    "tipo_lavori": "Rifacimento manto stradale, marciapiedi e sottoservizi in Via Roma e vie limitrofe",
    "importo_lavori": "€ 1.350.000,00",
    "durata_lavori_giorni": 180,
    "cig": "8E33B74813",
    "cup": "J37H21000190004",
    "indirizzo_cantiere": "Via Roma e strade limitrofe (Via Torquato Tasso, Via Sant'Alessandro)",
    "comune": "Bergamo",
    "provincia": "BG",
    "regione": "Lombardia",
    "categorie_materiali": [
        "Conglomerato bituminoso (binder e tappeto d'usura)",
        "Calcestruzzo Rck 25 per fondazioni e cordoli",
        "Cubetti di porfido e masselli autobloccanti",
        "Tubazioni in PEAD PE100 per fognatura e acquedotto",
        "Segnaletica orizzontale termoplastica",
        "Inerti e tout-venant per sottofondo",
        "Ghisa sferoidale per chiusini e caditoie",
        "Cordonature in granito",
    ],
    "lavorazioni_specialistiche": [
        "Fresatura meccanica del manto bituminoso esistente",
        "Demolizione e rifacimento marciapiedi e cordoli",
        "Scavi e posa tubazioni fognarie DN 300-500",
        "Ripristino allacci idrici e fognari privati",
        "Impianti di illuminazione pubblica LED",
        "Segnaletica stradale orizzontale e verticale",
    ],
    "categorie_soa": [
        {
            "codice": "OG3",
            "descrizione_categoria": "Strade, autostrade, ponti, viadotti, ferrovie, metropolitane",
            "classifica": "IV",
            "prevalente": True,
            "motivazione": "Lavori stradali prevalenti (fresatura, rifacimento manto, marciapiedi) — importo € 1.350.000",
        },
        {
            "codice": "OG6",
            "descrizione_categoria": "Acquedotti, gasdotti, oleodotti, opere di irrigazione e di evacuazione",
            "classifica": "II",
            "prevalente": False,
            "motivazione": "Posa tubazioni fognarie e ripristino allacci idrici — importo stimato € 200.000",
        },
        {
            "codice": "OS10",
            "descrizione_categoria": "Segnaletica stradale non luminosa",
            "classifica": "I",
            "prevalente": False,
            "motivazione": "Segnaletica orizzontale termoplastica e verticale — importo stimato € 80.000",
        },
    ],
    # ── Parametri contrattuali ────────────────────────────────────────────────
    "sal_intervallo_giorni": 30,
    "sal_importo_minimo_euro": 80000.0,
    "sal_tipo": "misto",
    "penale_giornaliera_permille": 1.0,
    "penale_massima_percentuale": 10.0,
    "riserve_iscrizione_giorni": 10,
    "riserve_quantificazione_giorni": 15,
    "collaudo_giorni": 180,
    "importo_oneri_sicurezza": 27000.0,
    # ── Subappalto & Subaffidamento ───────────────────────────────────────────
    "subappalto_percentuale_massima": 30.0,
    "subappalto_categorie_vietate": ["OG3 — categoria prevalente"],
    "subappalto_autorizzazione_richiesta": True,
    "subappalto_qualificazione_richiesta": True,
    "subaffidamento_percentuale_massima": None,
    "subappalto_note": "Comunicare nominativi subappaltatori almeno 20 giorni prima dell'inizio lavori. DURC del subappaltatore obbligatorio prima dell'autorizzazione.",
    # ── Obblighi ──────────────────────────────────────────────────────────────
    "obblighi_appaltatore": [
        "Predisporre e consegnare il POS entro 10 giorni dalla consegna cantiere",
        "Nominare il DTC iscritto all'albo professionale competente",
        "Aprire e tenere aggiornato il registro di contabilità (DM 49/2018)",
        "Garantire la presenza del DTC in cantiere nelle ore di lavorazione",
        "Comunicare eventuali subappalti alla SA con almeno 20 giorni di anticipo",
        "Installare cartello di cantiere conforme entro 5 giorni dalla consegna",
        "Stipulare polizza CAR con massimale pari all'importo contrattuale",
        "Stipulare polizza RCT con massimale minimo € 2.000.000,00",
        "Consegnare campioni dei materiali alla DL prima della posa in opera",
        "Smaltire i rifiuti da demolizione secondo D.Lgs. 152/2006",
        "Ripristinare la segnaletica stradale provvisoria entro 24 ore da ogni intervento",
        "Presentare cronoprogramma dettagliato entro 10 giorni dalla consegna",
        "Comunicare quotidianamente alla DL l'avanzamento delle lavorazioni",
    ],
    "obblighi_stazione_appaltante": [
        "Emettere il certificato di pagamento entro 45 giorni dalla data SAL",
        "Procedere al pagamento entro 30 giorni dall'emissione del certificato",
        "Fornire all'appaltatore tutta la documentazione tecnica disponibile sui sottoservizi",
        "Designare il DL e comunicarne i riferimenti entro la consegna cantiere",
        "Autorizzare varianti entro 30 giorni dalla richiesta motivata dell'appaltatore",
        "Emettere il certificato di collaudo entro 180 giorni dall'ultimazione lavori",
        "Restituire la cauzione definitiva entro 90 giorni dall'approvazione del collaudo",
    ],
    # ── Checklist ─────────────────────────────────────────────────────────────
    "checklist_prime_settimane": [
        {"attivita": "Richiedere e firmare verbale di consegna cantiere con eventuali riserve sullo stato dei luoghi", "termine_giorni": 1, "priorita": "alta"},
        {"attivita": "Installare recinzione perimetrale e segnaletica di cantiere conforme al CdS", "termine_giorni": 2, "priorita": "alta"},
        {"attivita": "Aprire giornale dei lavori e registro di contabilità", "termine_giorni": 1, "priorita": "alta"},
        {"attivita": "Comunicare nominativo DTC alla SA e alla DL con copia del patentino/iscrizione albo", "termine_giorni": 1, "priorita": "alta"},
        {"attivita": "Consegnare POS aggiornato alla DL e al Coordinatore per la Sicurezza in Esecuzione (CSE)", "termine_giorni": 10, "priorita": "alta"},
        {"attivita": "Installare cartello di cantiere conforme alle prescrizioni SA", "termine_giorni": 5, "priorita": "alta"},
        {"attivita": "Attivare polizza CAR e consegnare copia quietanza alla SA", "termine_giorni": 10, "priorita": "alta"},
        {"attivita": "Attivare polizza RCT (min. € 2M) e consegnare copia alla SA", "termine_giorni": 10, "priorita": "alta"},
        {"attivita": "Richiedere per PEC ai gestori (A2A, Italgas, TIM, Enel) mappatura aggiornata sottoservizi", "termine_giorni": 3, "priorita": "alta"},
        {"attivita": "Consegnare cronoprogramma esecutivo dettagliato alla DL", "termine_giorni": 10, "priorita": "alta"},
        {"attivita": "Eseguire rilievo fotografico completo dello stato dei luoghi prima degli scavi", "termine_giorni": 2, "priorita": "alta"},
        {"attivita": "Verificare con il Comune la necessità di SCIA o autorizzazioni per occupazione suolo pubblico", "termine_giorni": 3, "priorita": "alta"},
        {"attivita": "Concordare con DL e PM del Comune il calendario di avanzamento settimanale", "termine_giorni": 7, "priorita": "media"},
        {"attivita": "Allestire area di deposito materiali e macchinari con recinzione e cartellonistica", "termine_giorni": 3, "priorita": "media"},
    ],
    "checklist_accettazione_materiali": [
        {"attivita": "Richiedere approvazione scritta della DL per ogni materiale prima della posa in opera", "termine_giorni": None, "priorita": "alta"},
        {"attivita": "Presentare campioni dei materiali con 7 gg di anticipo rispetto alla posa per approvazione DL", "termine_giorni": None, "priorita": "alta"},
        {"attivita": "Verificare marcatura CE e Dichiarazione di Prestazione (DoP) per ogni materiale da costruzione", "termine_giorni": None, "priorita": "alta"},
        {"attivita": "Controllare bolle di consegna (DDT): quantità, qualità e corrispondenza con le voci di elenco prezzi", "termine_giorni": None, "priorita": "alta"},
        {"attivita": "Registrare lotto, provenienza e data di arrivo di ogni fornitura sul giornale dei lavori", "termine_giorni": None, "priorita": "alta"},
        {"attivita": "Eseguire campionamento e inviare a laboratorio accreditato i provini di cls (Rck, slump, Cl)", "termine_giorni": None, "priorita": "alta"},
        {"attivita": "Verificare certificati mill test degli acciai da armatura (Fe 450C): heat number + marcatura", "termine_giorni": None, "priorita": "alta"},
        {"attivita": "Controllare granulometria e provenienza degli inerti (conforme a CSA e NTC 2018)", "termine_giorni": None, "priorita": "media"},
        {"attivita": "Verificare temperatura e ricevuta di pesatura del conglomerato bituminoso (bolla da impianto)", "termine_giorni": None, "priorita": "alta"},
        {"attivita": "Conservare DDT e certificati di prova per tutta la durata del contratto e collaudo", "termine_giorni": None, "priorita": "alta"},
        {"attivita": "Documentare con foto i materiali rifiutati e trasmettere comunicazione scritta al fornitore e alla DL", "termine_giorni": None, "priorita": "media"},
    ],
    "checklist_sicurezza": [
        {"attivita": "Inviare notifica preliminare all'ASL e all'Ispettorato del Lavoro prima dell'inizio dei lavori", "termine_giorni": 1, "priorita": "alta"},
        {"attivita": "Redigere e consegnare POS (Piano Operativo di Sicurezza) alla DL e al CSE entro 10 giorni dalla consegna", "termine_giorni": 10, "priorita": "alta"},
        {"attivita": "Verificare che recinzioni, segnaletica stradale e cartellonistica siano conformi al D.Lgs. 81/2008", "termine_giorni": 2, "priorita": "alta"},
        {"attivita": "Dotare tutti i lavoratori dei DPI previsti nel POS (elmetti, guanti, imbracature, scarpe antinfortunistiche)", "termine_giorni": None, "priorita": "alta"},
        {"attivita": "Verificare attestati di formazione obbligatoria di tutti i lavoratori (D.Lgs. 81/2008, Accordo Stato-Regioni)", "termine_giorni": None, "priorita": "alta"},
        {"attivita": "Tenere aggiornato il registro presenze giornaliero in cantiere (nominativo, mansione, orario)", "termine_giorni": None, "priorita": "alta"},
        {"attivita": "Partecipare alla riunione di coordinamento con il CSE prima dell'inizio delle lavorazioni", "termine_giorni": 3, "priorita": "alta"},
        {"attivita": "Verificare scadenza sorveglianza sanitaria (visite mediche) di tutti i lavoratori esposti a rischi specifici", "termine_giorni": None, "priorita": "alta"},
        {"attivita": "Aggiornare il POS prima di ogni nuova fase lavorativa o cambio di lavorazioni", "termine_giorni": None, "priorita": "media"},
        {"attivita": "Tenere aggiornato il registro infortuni e segnalare immediatamente all'INAIL ogni infortunio > 3 gg", "termine_giorni": None, "priorita": "alta"},
        {"attivita": "Verificare idoneità tecnico-professionale dei subappaltatori (DURC, organico, attrezzature) prima dell'accesso", "termine_giorni": None, "priorita": "alta"},
    ],
    "checklist_assicurative": [
        {"attivita": "Polizza CAR (All Risks) — massimale pari all'importo contrattuale (€ 1.350.000)", "termine_giorni": 10, "priorita": "alta"},
        {"attivita": "Polizza RCT — massimale minimo € 2.000.000 per sinistro (richiesto dal CSA)", "termine_giorni": 10, "priorita": "alta"},
        {"attivita": "Assicurazione infortuni operai conforme al CCNL Edile e Genio Civile", "termine_giorni": 10, "priorita": "alta"},
        {"attivita": "Verificare che ogni subappaltatore abbia polizze equivalenti prima di iniziare le lavorazioni", "termine_giorni": None, "priorita": "alta"},
        {"attivita": "Consegnare quietanze di pagamento premi assicurativi alla SA prima dell'inizio lavori", "termine_giorni": 10, "priorita": "alta"},
        {"attivita": "Verificare copertura polizza CAR per danni accidentali a sottoservizi di terzi durante gli scavi", "termine_giorni": 10, "priorita": "alta"},
        {"attivita": "Aggiornare le polizze in caso di variante che aumenti l'importo contrattuale", "termine_giorni": None, "priorita": "media"},
        {"attivita": "Comunicare immediatamente alla compagnia assicurativa qualsiasi sinistro o danneggiamento", "termine_giorni": None, "priorita": "alta"},
    ],
    # ── Subaffidamenti & Ordini di Servizio ───────────────────────────────────
    "subaffidamenti": {
        "importo_totale": "15000",
        "numero_subaffidatari": 2,
        "lista_subaffidatari": [
            {
                "nome": "Ditta XYZ Scavi s.r.l.",
                "importo": "10000",
                "descrizione_lavori": "Scavi e movimentazione terra",
            },
            {
                "nome": "Azienda ABC Impianti s.n.c.",
                "importo": "5000",
                "descrizione_lavori": "Installazione tubazioni",
            },
        ],
    },
    "ordini_servizio": {
        "numero_totale": 3,
        "lista_ordini": [
            {
                "data": "2026-05-01",
                "numero": "OS-001/2026",
                "descrizione": "Realizzazione scavi preliminari",
                "importo": "5000",
            },
            {
                "data": "2026-05-10",
                "numero": "OS-002/2026",
                "descrizione": "Posa tubazioni acque bianche",
                "importo": "3500",
            },
            {
                "data": "2026-05-15",
                "numero": "OS-003/2026",
                "descrizione": "Controllo e collaudo parziale",
                "importo": "0",
            },
        ],
    },
    # Campi flat derivati (pre-calcolati per la demo)
    "subaffidamenti_importo": 15000.0,
    "subaffidamenti_numero": 2,
    "ordini_servizio_numero": 3,
    "ordini_servizio_lista": [
        {
            "data": "2026-05-01",
            "numero": "OS-001/2026",
            "descrizione": "Realizzazione scavi preliminari",
            "importo": "5000",
        },
        {
            "data": "2026-05-10",
            "numero": "OS-002/2026",
            "descrizione": "Posa tubazioni acque bianche",
            "importo": "3500",
        },
        {
            "data": "2026-05-15",
            "numero": "OS-003/2026",
            "descrizione": "Controllo e collaudo parziale",
            "importo": "0",
        },
    ],
}

DEMO_COORDS = (45.6983, 9.6773)  # Bergamo, Via Roma (centro)

_DEMO_SUPPLIERS_RAW = [
    {
        "Categoria": "Materiali Edili",
        "Nome": "Edilizia Rota S.r.l.",
        "Indirizzo": "Via Autostrada 42, Seriate (BG)",
        "Telefono": "+39 035 294115",
        "Email": "info@ediliziarota.it",
        "Sito Web": "www.ediliziarota.it",
        "lat": 45.6870, "lon": 9.7220,
    },
    {
        "Categoria": "Materiali Edili",
        "Nome": "Fratelli Colombo Materiali Edili",
        "Indirizzo": "Via per Osio Sotto 18, Dalmine (BG)",
        "Telefono": "+39 035 561038",
        "Email": "ordini@colombomateriali.it",
        "Sito Web": "www.colombomateriali.it",
        "lat": 45.6510, "lon": 9.6020,
    },
    {
        "Categoria": "Calcestruzzo e Prefabbricati",
        "Nome": "Bergamo Calcestruzzi S.p.A.",
        "Indirizzo": "Via Zanica 6, Stezzano (BG)",
        "Telefono": "+39 035 592211",
        "Email": "produzione@bgcalcestruzzi.it",
        "Sito Web": "www.bgcalcestruzzi.it",
        "lat": 45.6700, "lon": 9.6530,
    },
    {
        "Categoria": "Calcestruzzo e Prefabbricati",
        "Nome": "Predalbe Prefabbricati S.r.l.",
        "Indirizzo": "Via dell'Artigianato 8, Treviolo (BG)",
        "Telefono": "+39 035 200450",
        "Email": "info@predalbe.it",
        "Sito Web": "www.predalbe.it",
        "lat": 45.6760, "lon": 9.6410,
    },
    {
        "Categoria": "Noleggio Attrezzature",
        "Nome": "Nolo Macchinari Gotti S.r.l.",
        "Indirizzo": "Via Industriale 22, Stezzano (BG)",
        "Telefono": "+39 035 591780",
        "Email": "noleggio@gottimacchinari.it",
        "Sito Web": "www.gottimacchinari.it",
        "lat": 45.6680, "lon": 9.6550,
    },
    {
        "Categoria": "Noleggio Attrezzature",
        "Nome": "Edilnolo Orobica S.r.l.",
        "Indirizzo": "Viale Giulio Cesare 44, Bergamo",
        "Telefono": "+39 035 247300",
        "Email": "info@edilnoloorobica.it",
        "Sito Web": "www.edilnoloorobica.it",
        "lat": 45.7010, "lon": 9.6600,
    },
    {
        "Categoria": "Carpenteria Metallica",
        "Nome": "Officine Metalliche Bergamasche S.r.l.",
        "Indirizzo": "Via Gavazzeni 10, Seriate (BG)",
        "Telefono": "+39 035 301940",
        "Email": "officine@ombseriate.it",
        "Sito Web": "www.ombseriate.it",
        "lat": 45.6860, "lon": 9.7190,
    },
    {
        "Categoria": "Impianti Elettrici",
        "Nome": "Elettrica Bergamasca S.r.l.",
        "Indirizzo": "Via San Giorgio 15, Bergamo",
        "Telefono": "+39 035 318250",
        "Email": "info@elettricabergamasca.it",
        "Sito Web": "www.elettricabergamasca.it",
        "lat": 45.6990, "lon": 9.6710,
    },
    {
        "Categoria": "Impianti Elettrici",
        "Nome": "Impianti Valota di Valota Marco",
        "Indirizzo": "Via Roma 88, Alzano Lombardo (BG)",
        "Telefono": "+39 035 513422",
        "Email": "impianti.valota@gmail.com",
        "Sito Web": "",
        "lat": 45.7290, "lon": 9.7270,
    },
    {
        "Categoria": "Impianti Idraulici e Termici",
        "Nome": "Termoidraulica Corti S.n.c.",
        "Indirizzo": "Via delle Rose 4, Alzano Lombardo (BG)",
        "Telefono": "+39 035 511890",
        "Email": "info@termoidraulicacorti.it",
        "Sito Web": "www.termoidraulicacorti.it",
        "lat": 45.7280, "lon": 9.7250,
    },
    {
        "Categoria": "Impianti Idraulici e Termici",
        "Nome": "Idrotecnica Orobica S.r.l.",
        "Indirizzo": "Via Borgo Palazzo 120, Bergamo",
        "Telefono": "+39 035 236780",
        "Email": "info@idrotecnicaorobica.it",
        "Sito Web": "www.idrotecnicaorobica.it",
        "lat": 45.6940, "lon": 9.6880,
    },
    {
        "Categoria": "Trasporti e Logistica",
        "Nome": "Autotrasporti Radici S.r.l.",
        "Indirizzo": "Via Autostrada 55, Pedrengo (BG)",
        "Telefono": "+39 035 659110",
        "Email": "trasporti@radicilogistica.it",
        "Sito Web": "www.radicilogistica.it",
        "lat": 45.7060, "lon": 9.7540,
    },
    {
        "Categoria": "Trasporti e Logistica",
        "Nome": "Logistica Orobica S.p.A.",
        "Indirizzo": "Via dell'Industria 18, Osio Sopra (BG)",
        "Telefono": "+39 035 881700",
        "Email": "info@logisticaorobica.it",
        "Sito Web": "www.logisticaorobica.it",
        "lat": 45.6440, "lon": 9.5980,
    },
    {
        "Categoria": "Cave e Inerti",
        "Nome": "Cava Stezzano — Inerti Bruni S.r.l.",
        "Indirizzo": "Via Briantea 8, Stezzano (BG)",
        "Telefono": "+39 035 592055",
        "Email": "cava@inertibruni.it",
        "Sito Web": "www.inertibruni.it",
        "lat": 45.6710, "lon": 9.6490,
    },
    {
        "Categoria": "Cave e Inerti",
        "Nome": "Sabbie e Ghiaie Bergamasche S.r.l.",
        "Indirizzo": "Via Fiume 33, Dalmine (BG)",
        "Telefono": "+39 035 564020",
        "Email": "vendite@sabbiehgiaiebergamo.it",
        "Sito Web": "",
        "lat": 45.6530, "lon": 9.5970,
    },
]

DEMO_SUPPLIERS = pd.DataFrame(_DEMO_SUPPLIERS_RAW)


DEMO_DOCUMENTS = {
    "riserva": """\
                                                        Bergamo, 02 maggio 2025

Al Responsabile Unico del Progetto
Comune di Bergamo — Settore Lavori Pubblici e Manutenzioni
Piazza Matteotti, 27 — 24122 Bergamo

Al Direttore dei Lavori
[Nome DL] — [Indirizzo Studio]

RACCOMANDATA A.R. / PEC

OGGETTO: Iscrizione di riserva ai sensi dell'art. 120, comma 3, D.Lgs. 36/2023
          Contratto n. [XXX/2025] — Rifacimento manto stradale Via Roma e vie limitrofe, Bergamo
          Interferenze con sottoservizi non indicati nel progetto esecutivo

Con la presente, la scrivente impresa [RAGIONE SOCIALE APPALTATORE], con sede legale in [INDIRIZZO],
C.F./P.IVA [CODICE], in persona del legale rappresentante [NOME COGNOME], ai sensi e per gli effetti
dell'art. 120, comma 3, del D.Lgs. 36/2023 e dell'art. 14 del DM 49/2018,

ISCRIVE FORMALE RISERVA

per i seguenti motivi:

1. FATTO GENERATORE
   In data 29 aprile 2025, durante le operazioni di scavo per la sostituzione della tubazione
   fognaria in Via Torquato Tasso (all'intersezione con Via Roma), sono stati rinvenuti cavi
   in fibra ottica di Telecom Italia e tubazioni idriche AQST Bergamo non indicate negli
   elaborati progettuali consegnati dalla SA in sede di gara.

2. NORME VIOLATE
   Ai sensi dell'art. 41, comma 1, lett. b), D.Lgs. 36/2023, il progetto esecutivo deve contenere
   le indagini sui sottoservizi esistenti. L'omissione degli impianti rinvenuti costituisce carenza
   progettuale imputabile alla SA.

3. QUANTIFICAZIONE (IN VIA PRUDENZIALE)
   Si stima un onere aggiuntivo non inferiore a € 38.000,00 (trentottomila/00), oltre IVA.
   Si riserva la quantificazione definitiva all'esito delle lavorazioni di ripristino.

4. RICHIESTA
   Si chiede la registrazione della presente riserva nel registro di contabilità e la
   convocazione di apposita riunione con la DL e il RUP entro 10 giorni.

La scrivente riserva ogni più ampia azione a tutela dei propri diritti.

In fede,

[Luogo], lì 02 maggio 2025

Il Legale Rappresentante
____________________________
[Nome Cognome]""",

    "verbale_consegna": """\
COMUNE DI BERGAMO
Settore Lavori Pubblici e Manutenzioni

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VERBALE DI CONSEGNA DEI LAVORI n. 01/2025
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Opera:        Rifacimento manto stradale, marciapiedi e sottoservizi
              in Via Roma e strade limitrofe — Bergamo
CIG:          [DA COMPILARE]
CUP:          [DA COMPILARE]
Contratto:    Rep. n. [XXX] del [DATA STIPULA]
Importo:      € 1.350.000,00 (IVA esclusa)
Durata:       180 giorni naturali e consecutivi

Il giorno 02 maggio 2025, alle ore 09:00, presso il cantiere di Via Roma,
Bergamo (BG), si sono riuniti i sottoscritti:

- IL DIRETTORE DEI LAVORI: Ing. [Nome Cognome]
- IL RESPONSABILE UNICO DEL PROGETTO (RUP): [Nome Cognome]
- L'APPALTATORE: [Ragione Sociale], DTC [Nome Cognome]

CONSEGNA FORMALE
Il Direttore dei Lavori consegna formalmente all'Appaltatore l'area di cantiere.

TERMINE CONTRATTUALE
La data di ultimazione dei lavori è fissata al: 28 ottobre 2025 (180 gg dalla consegna).

FIRME
Il Direttore dei Lavori:  ____________________________
Il R.U.P.:                ____________________________
L'Appaltatore (DTC):      ____________________________

Bergamo, lì 02 maggio 2025""",

    "proroga": """\
                                                        Bergamo, 15 giugno 2025

Al Responsabile Unico del Progetto
Comune di Bergamo — Settore Lavori Pubblici e Manutenzioni

OGGETTO: Richiesta di proroga del termine contrattuale per eventi meteorologici eccezionali
          ex art. 107, comma 1, D.Lgs. 36/2023

Con la presente, [RAGIONE SOCIALE APPALTATORE], CHIEDE la concessione di una proroga
di 21 (ventuno) giorni naturali al termine contrattuale per i seguenti motivi:

1. EVENTI METEOROLOGICI ECCEZIONALI
   Nel periodo 28 maggio — 17 giugno 2025, precipitazioni superiori del 180% alla media storica
   (fonte: ARPA Lombardia) hanno impedito l'esecuzione delle lavorazioni bituminose per 18 giorni.

2. DOCUMENTAZIONE ALLEGATA
   - Bollettini meteorologici ARPA Lombardia (All. 1)
   - Giornale dei lavori con registrazione sospensioni (All. 2)
   - Verbali di sospensione firmati dalla DL (All. 3)

3. QUANTIFICAZIONE
   Giorni sospensione documentati: 18 gg + 3 gg riorganizzazione = proroga richiesta: 21 giorni
   Nuova data di ultimazione proposta: 18 novembre 2025

Il Legale Rappresentante
____________________________
[Nome Cognome]""",

    "contestazione": """\
                                                        Bergamo, 20 giugno 2025

Al Responsabile Unico del Progetto
Comune di Bergamo — Settore Lavori Pubblici e Manutenzioni

OGGETTO: FORMALE CONTESTAZIONE — Mancata emissione del SAL n. 1 nei termini contrattuali

La scrivente [RAGIONE SOCIALE APPALTATORE] formula FORMALE CONTESTAZIONE per:

1. PREMESSE E FATTI
   Al 02 giugno 2025, lavorazioni eseguite: € 187.450,00. Richiesta SAL n.1 inviata alla DL
   in data 02/06/2025. Ad oggi, 20 giugno 2025 — trascorsi 17 giorni dalla scadenza —
   nessun certificato di pagamento è stato emesso.

2. VIOLAZIONI
   - Art. 125 D.Lgs. 36/2023: certificato di pagamento entro 45 giorni dalla maturazione SAL
   - Art. 1282 c.c.: sulle somme dovute maturano interessi legali automaticamente

3. RICHIESTA
   a) Immediata emissione del SAL n.1 entro 5 giorni dalla ricezione
   b) Pagamento di € 187.450,00 + IVA entro 30 giorni dall'emissione certificato
   c) Corresponsione interessi di mora ex D.Lgs. 231/2002

Si riserva ogni più ampia azione a tutela dei propri diritti.

Il Legale Rappresentante
____________________________
[Nome Cognome]""",
}
