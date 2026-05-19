import math
from typing import Optional


def calcola_penale_giornaliera(importo_contratto: float, permille: float) -> float:
    return importo_contratto * permille / 1000.0


def calcola_penale_cumulativa(
    importo_contratto: float,
    permille: float,
    giorni_ritardo: int,
    penale_massima_percent: float = 10.0,
) -> dict:
    penale_giornaliera = calcola_penale_giornaliera(importo_contratto, permille)
    penale_massima = importo_contratto * penale_massima_percent / 100.0
    penale_raw = penale_giornaliera * giorni_ritardo
    penale_applicata = min(penale_raw, penale_massima)
    giorni_al_cap = (
        math.ceil(penale_massima / penale_giornaliera) if penale_giornaliera > 0 else None
    )
    return {
        "penale_giornaliera_euro": penale_giornaliera,
        "giorni_ritardo": giorni_ritardo,
        "penale_cumulativa_euro": penale_applicata,
        "penale_massima_euro": penale_massima,
        "penale_massima_percent": penale_massima_percent,
        "cap_raggiunto": penale_raw >= penale_massima,
        "giorni_al_cap": giorni_al_cap,
    }


def simula_revisione_prezzi(
    importo_contratto: float,
    oneri_sicurezza: float,
    indice_istat_offerta: float,
    indice_istat_aggiornamento: float,
    soglia_franchigia_percent: float = 5.0,
) -> dict:
    """
    Price revision per art.60 D.Lgs.36/2023.
    Security costs are excluded. 90% of the variation exceeding the threshold
    is compensated (or deducted if negative).
    """
    importo_revisabile = importo_contratto - oneri_sicurezza
    if importo_revisabile <= 0 or indice_istat_offerta <= 0:
        return {"error": "Dati non validi per il calcolo"}

    variazione_percent = (
        (indice_istat_aggiornamento - indice_istat_offerta) / indice_istat_offerta
    ) * 100

    eccedenza = abs(variazione_percent) - soglia_franchigia_percent
    if eccedenza <= 0:
        compensazione_percent = 0.0
        compensazione_euro = 0.0
        note = (
            f"La variazione ({variazione_percent:+.2f}%) rientra nella franchigia "
            f"del {soglia_franchigia_percent:.1f}%: nessuna compensazione."
        )
    else:
        # Art.60: 90% of variation beyond threshold, sign follows the direction
        segno = 1 if variazione_percent > 0 else -1
        compensazione_percent = segno * eccedenza * 0.90
        compensazione_euro = importo_revisabile * compensazione_percent / 100
        direzione = "aumento" if variazione_percent > 0 else "riduzione"
        note = (
            f"Variazione indice: {variazione_percent:+.2f}%. "
            f"Eccedenza sulla franchigia {soglia_franchigia_percent:.1f}%: "
            f"{eccedenza:.2f}%. Compensazione al 90% ({direzione} prezzi)."
        )

    return {
        "importo_contratto": importo_contratto,
        "oneri_sicurezza": oneri_sicurezza,
        "importo_revisabile": importo_revisabile,
        "indice_offerta": indice_istat_offerta,
        "indice_aggiornamento": indice_istat_aggiornamento,
        "variazione_totale_percent": variazione_percent,
        "soglia_franchigia_percent": soglia_franchigia_percent,
        "eccedenza_percent": max(0.0, eccedenza),
        "compensazione_applicabile_percent": compensazione_percent,
        "compensazione_euro": compensazione_euro,
        "a_favore_appaltatore": variazione_percent > soglia_franchigia_percent,
        "note": note,
    }
