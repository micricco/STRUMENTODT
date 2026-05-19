from datetime import date, timedelta
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Sospensione:
    id: int
    data_inizio: date
    data_fine: Optional[date]
    tipo: str  # "totale" | "parziale"
    motivo: str
    percentuale: float = 100.0


def _giorni_sospesi_totali(sospensioni: List[Sospensione]) -> int:
    return sum(
        (s.data_fine - s.data_inizio).days
        for s in sospensioni
        if s.tipo == "totale" and s.data_fine is not None
    )


def _genera_milestones_sal(
    durata_giorni: int,
    importo_contratto: float,
    sal_tipo: str,
    sal_intervallo_giorni: Optional[int],
    sal_importo_soglia: Optional[float],
) -> list:
    """
    Restituisce lista di {giorno, importo_sal, trigger} per i SAL previsti.

    - tempo:   SAL ogni sal_intervallo_giorni giorni di calendario
    - importo: SAL quando l'avanzamento lineare raggiunge sal_importo_soglia
    - misto:   unione dei due trigger (rimuove date a meno di 7 gg)
    """

    def _tempo() -> list:
        if not sal_intervallo_giorni or sal_intervallo_giorni <= 0:
            return []
        res = []
        n = 1
        while True:
            g = n * sal_intervallo_giorni
            if g >= durata_giorni:
                break
            imp = importo_contratto * g / durata_giorni if importo_contratto > 0 else None
            res.append({"giorno": g, "importo_sal": imp, "trigger": "tempo"})
            n += 1
            if n > 500:
                break
        return res

    def _importo() -> list:
        if not sal_importo_soglia or sal_importo_soglia <= 0 or importo_contratto <= 0:
            return []
        res = []
        n = 1
        while True:
            imp_cum = n * sal_importo_soglia
            if imp_cum >= importo_contratto:
                break
            g = round(imp_cum / importo_contratto * durata_giorni)
            res.append({"giorno": g, "importo_sal": imp_cum, "trigger": "importo"})
            n += 1
            if n > 500:
                break
        return res

    if sal_tipo == "tempo":
        return _tempo()

    if sal_tipo == "importo":
        return _importo()

    if sal_tipo == "misto":
        t_map = {m["giorno"]: m for m in _tempo()}
        a_map = {m["giorno"]: m for m in _importo()}
        merged: dict = {}
        for g, m in t_map.items():
            merged[g] = m.copy()
        for g, m in a_map.items():
            if g in merged:
                merged[g]["trigger"] = "misto"
            else:
                merged[g] = m.copy()
        sorted_ms = sorted(merged.values(), key=lambda x: x["giorno"])
        # rimuove milestone troppo vicine (< 7 gg)
        deduped: list = []
        prev_g = -8
        for m in sorted_ms:
            if m["giorno"] - prev_g > 7:
                deduped.append(m)
                prev_g = m["giorno"]
        return deduped

    return []


def calcola_calendario(
    data_consegna: date,
    durata_giorni: int,
    importo_contratto: float = 0.0,
    sal_tipo: str = "tempo",
    sal_intervallo_giorni: Optional[int] = None,
    sal_importo_soglia: Optional[float] = None,
    sospensioni: Optional[List[Sospensione]] = None,
) -> dict:
    """
    Calcola tutte le date contrattuali.

    sal_tipo: "tempo" | "importo" | "misto"
    Solo le sospensioni totali completate estendono data_fine_lavori.
    I SAL sono calcolati su giorni di calendario (anche durante sospensioni).
    """
    if sospensioni is None:
        sospensioni = []

    giorni_sospesi = _giorni_sospesi_totali(sospensioni)
    durata_eff = durata_giorni + giorni_sospesi
    data_fine_lavori = data_consegna + timedelta(days=durata_eff)

    eventi: list[dict] = []

    eventi.append({
        "data": data_consegna,
        "tipo": "Consegna",
        "descrizione": "Consegna cantiere — inizio tempo utile",
        "giorno_contratto": 0,
        "critico": True,
    })

    milestones = _genera_milestones_sal(
        durata_giorni=durata_eff,
        importo_contratto=importo_contratto,
        sal_tipo=sal_tipo,
        sal_intervallo_giorni=sal_intervallo_giorni,
        sal_importo_soglia=sal_importo_soglia,
    )

    for n, ms in enumerate(milestones, 1):
        sal_date = data_consegna + timedelta(days=ms["giorno"])
        if sal_date >= data_fine_lavori:
            break

        trigger = ms["trigger"]
        imp_sal = ms.get("importo_sal")

        if trigger == "tempo":
            desc = f"SAL n.{n} — intervallo temporale (giorno {ms['giorno']})"
        elif trigger == "importo":
            imp_str = f"€ {imp_sal:,.0f}" if imp_sal else ""
            desc = f"SAL n.{n} — soglia importo {imp_str} (giorno {ms['giorno']})"
        else:
            imp_str = f" / € {imp_sal:,.0f}" if imp_sal else ""
            desc = f"SAL n.{n} — tempo + importo (giorno {ms['giorno']}{imp_str})"

        eventi.append({
            "data": sal_date,
            "tipo": f"SAL n.{n}",
            "descrizione": desc,
            "giorno_contratto": ms["giorno"],
            "importo_sal": imp_sal,
            "trigger_sal": trigger,
            "critico": True,
        })

    for sosp in sorted(sospensioni, key=lambda s: s.data_inizio):
        tipo_label = (
            "Sospensione totale"
            if sosp.tipo == "totale"
            else f"Sospensione parziale ({sosp.percentuale:.0f}%)"
        )
        eventi.append({
            "data": sosp.data_inizio,
            "tipo": "Sospensione inizio",
            "descrizione": f"{tipo_label}: {sosp.motivo}",
            "giorno_contratto": (sosp.data_inizio - data_consegna).days,
            "critico": False,
        })
        if sosp.data_fine:
            eventi.append({
                "data": sosp.data_fine,
                "tipo": "Ripresa lavori",
                "descrizione": f"Fine sospensione: {sosp.motivo}",
                "giorno_contratto": (sosp.data_fine - data_consegna).days,
                "critico": False,
            })

    eventi.append({
        "data": data_fine_lavori,
        "tipo": "Fine lavori",
        "descrizione": (
            f"Scadenza tempo utile ({durata_giorni} gg contratto"
            + (f" + {giorni_sospesi} gg sospensioni" if giorni_sospesi else "")
            + ")"
        ),
        "giorno_contratto": durata_eff,
        "critico": True,
    })

    eventi.append({
        "data": data_fine_lavori + timedelta(days=1),
        "tipo": "Inizio penali",
        "descrizione": "Inizio maturazione penali per ritardo (se non ultimati i lavori)",
        "giorno_contratto": durata_eff + 1,
        "critico": True,
    })

    eventi.sort(key=lambda e: e["data"])

    return {
        "data_consegna": data_consegna,
        "data_fine_lavori": data_fine_lavori,
        "giorni_sospesi_totali": giorni_sospesi,
        "durata_originale_giorni": durata_giorni,
        "durata_effettiva_giorni": durata_eff,
        "sal_tipo": sal_tipo,
        "eventi": eventi,
    }
