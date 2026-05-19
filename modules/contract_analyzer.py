import anthropic

MODEL_FAST = "claude-haiku-4-5-20251001"


_DOCUMENT_PROMPTS = {
    "riserva": """Sei un avvocato specializzato in appalti pubblici italiani. Redigi una lettera formale di iscrizione di riserva ai sensi dell'art.120 del D.Lgs.36/2023.

Data: {data_lettera}
Destinatario: Direzione Lavori e Responsabile Unico del Progetto

Dati del contratto:
{context}

Motivo della riserva: {motivo}
Importo indicativo: {importo}
Data dell'evento generatore: {data_evento}

Requisiti:
1. Cita espressamente art.120 comma 3 D.Lgs.36/2023
2. Descrivi il fatto generatore con precisione (chi, cosa, quando, dove)
3. Indica l'importo anche in via prudenziale, con riserva di quantificazione definitiva
4. Richiedi registrazione nel registro di contabilita
5. Cita le norme eventualmente violate dalla SA
6. Riserva ogni azione giudiziaria e stragiudiziale
7. Chiudi con formula di rito e spazio per firma del legale rappresentante

Usa linguaggio formale-legale italiano. Redigi SOLO il testo della lettera.""",

    "verbale_consegna": """Sei un esperto di appalti pubblici italiani (DM 49/2018, D.Lgs.36/2023). Redigi un verbale di consegna dei lavori.

Data consegna: {data_lettera}

Dati del contratto:
{context}

Osservazioni dell'appaltatore: {osservazioni}

Struttura del verbale:
1. INTESTAZIONE (ente, opera, CUP/CIG da compilare)
2. VERBALE DI CONSEGNA DEI LAVORI
3. Il giorno {data_lettera} si sono riuniti: DL, RUP, Appaltatore (spazi per nomi e qualifiche)
4. Descrizione dei luoghi e stato del sito
5. Consegna formale dell'area di cantiere
6. Termine per ultimazione lavori (da calcolare)
7. Osservazioni e riserve dell'appaltatore
8. Spazio firme (DL, RUP, Appaltatore)

Redigi SOLO il testo del verbale, in formato documento ufficiale.""",

    "proroga": """Sei un esperto di appalti pubblici italiani. Redigi una richiesta formale di proroga del termine contrattuale.

Data: {data_lettera}
Oggetto: Richiesta proroga termine contrattuale

Dati del contratto:
{context}

Causa della proroga: {causa}
Giorni di proroga richiesti: {giorni}
Documentazione allegata: {documentazione}

Struttura:
1. Premesse: richiamo al contratto e ai termini originari
2. Descrizione dettagliata dell'evento impeditivo con date precise
3. Nesso causale tra evento e ritardo
4. Calcolo dei giorni di proroga richiesti
5. Riferimenti normativi (art.107 D.Lgs.36/2023 per sospensioni o altra norma pertinente)
6. Elenco documentazione allegata
7. Riserva di ulteriori danni ex art.120 D.Lgs.36/2023 se del caso
8. Conclusioni con richiesta formale e termine per risposta

Usa linguaggio formale-legale. Redigi SOLO il testo della lettera.""",

    "contestazione": """Sei un esperto di appalti pubblici italiani. Redigi una nota formale di contestazione.

Data: {data_lettera}
Oggetto: Formale contestazione — {oggetto}

Dati del contratto:
{context}

Oggetto: {oggetto}
Descrizione dei fatti: {fatti}
Richiesta: {richiesta}

Struttura:
1. Premesse e richiamo al contratto
2. Esposizione cronologica dei fatti contestati
3. Violazioni contrattuali e/o normative specifiche con articoli
4. Quantificazione dei danni se applicabile
5. Richiesta formale con termine per risposta (15 giorni)
6. Avvertenza: mancata risposta come silenzio-inadempimento
7. Riserva di ogni azione giudiziaria e stragiudiziale

Usa linguaggio formale-legale. Redigi SOLO il testo della nota.""",
}


def generate_document(doc_type: str, context: dict, params: dict, api_key: str, max_tokens: int = 1500) -> str:
    """Genera un documento legale formale via Claude Haiku (template-based)."""
    client = anthropic.Anthropic(api_key=api_key)

    context_str = "\n".join(
        f"- {k.replace('_', ' ').title()}: {v}"
        for k, v in context.items()
        if v and k not in ("categorie_materiali", "lavorazioni_specialistiche",
                           "categorie_soa", "obblighi_appaltatore", "obblighi_stazione_appaltante",
                           "checklist_prime_settimane", "checklist_accettazione_materiali",
                           "checklist_sicurezza", "checklist_assicurative")
    )

    if max_tokens <= 512:
        lunghezza_hint = "\n\nIMPORTANTE: Redigi una versione BREVE ed essenziale. Includi solo gli elementi obbligatori di legge. Massimo 3-4 paragrafi."
    elif max_tokens <= 1500:
        lunghezza_hint = "\n\nRedigi un documento STANDARD: struttura completa, tono formale, tutti gli elementi richiesti senza ripetizioni inutili."
    else:
        lunghezza_hint = "\n\nRedigi un documento DETTAGLIATO: sviluppa ogni sezione in modo approfondito, aggiungi riferimenti normativi precisi (articoli, commi), argomentazioni giuridiche a sostegno e formule di stile complete."

    prompt = _DOCUMENT_PROMPTS[doc_type].format(context=context_str, **params) + lunghezza_hint

    message = client.messages.create(
        model=MODEL_FAST,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text
