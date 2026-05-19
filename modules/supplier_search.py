import requests
import pandas as pd


OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Parole chiave italiane per Google Maps / Pagine Gialle (una per categoria)
CATEGORY_KEYWORDS = {
    "Materiali Edili": "materiali edili",
    "Noleggio Attrezzature": "noleggio attrezzature edili",
    "Calcestruzzo e Prefabbricati": "calcestruzzo prefabbricati",
    "Carpenteria Metallica": "carpenteria metallica",
    "Impianti Elettrici": "impianti elettrici",
    "Impianti Idraulici e Termici": "impianti idraulici termici",
    "Trasporti e Logistica": "trasporti logistica",
    "Cave e Inerti": "cave inerti sabbia ghiaia",
    "Legname e Carpenteria Legno": "legname carpenteria legno",
    "Ferramenta e Utensileria": "ferramenta utensileria",
}

# nwr = node + way + relation (copertura OSM molto più ampia)
CATEGORY_QUERIES = {
    "Materiali Edili": [
        'nwr["shop"="building_materials"]',
        'nwr["shop"="doityourself"]',
        'nwr["shop"="hardware"]',
        'nwr["shop"="trade"]',
        'nwr["craft"="builder"]',
        'nwr["craft"="construction"]',
        'nwr["industrial"="building_materials"]',
        'nwr["name"~"edil|materiali edili|costruzion|cemento|laterizi|calce",i]',
        'nwr["name"~"bricolag|brico|ferramenta",i]',
    ],
    "Noleggio Attrezzature": [
        'nwr["shop"="rental"]',
        'nwr["amenity"="rental"]',
        'nwr["name"~"noleggio|nolo|rental|autonoleggio",i]',
        'nwr["name"~"attrezzature|macchine edili|escavatori",i]',
    ],
    "Calcestruzzo e Prefabbricati": [
        'nwr["industrial"="concrete_plant"]',
        'nwr["man_made"="works"]["product"~"concrete|calcestruzzo",i]',
        'nwr["name"~"calcestruzzo|betonaggio|prefabbricati|betoniera|cls",i]',
        'nwr["name"~"stabilimento|impianto calcestruzzo",i]',
    ],
    "Carpenteria Metallica": [
        'nwr["craft"="metal_construction"]',
        'nwr["craft"="blacksmith"]',
        'nwr["craft"="steelconstruction"]',
        'nwr["industrial"="steel"]',
        'nwr["name"~"carpenteria metallica|ferro|acciaio|serramenti|infissi metal",i]',
        'nwr["name"~"officina meccanica|lavorazione metalli",i]',
    ],
    "Impianti Elettrici": [
        'nwr["craft"="electrician"]',
        'nwr["shop"="electrical"]',
        'nwr["name"~"impianti elettrici|elettricista|elettrotecnica|automazione",i]',
    ],
    "Impianti Idraulici e Termici": [
        'nwr["craft"="plumber"]',
        'nwr["craft"="hvac"]',
        'nwr["shop"="plumbing"]',
        'nwr["name"~"idraulico|termoidraulico|impianti termici|riscaldamento|condizionamento",i]',
        'nwr["name"~"climatizzazione|pompe di calore|sanitari",i]',
    ],
    "Trasporti e Logistica": [
        'nwr["office"="logistics"]',
        'nwr["amenity"="cargo"]',
        'nwr["name"~"trasporti|autotrasporti|logistica|spedizioni|movimentazione",i]',
        'nwr["name"~"trasporto terre|smaltimento|inerti|autocarri",i]',
    ],
    "Cave e Inerti": [
        'nwr["landuse"="quarry"]',
        'nwr["name"~"cava|inerti|sabbia|ghiaia|pietrisco|aggregati",i]',
        'nwr["name"~"escavazione|cave e inerti",i]',
    ],
    "Legname e Carpenteria Legno": [
        'nwr["craft"="carpenter"]',
        'nwr["craft"="woodworker"]',
        'nwr["shop"="timber"]',
        'nwr["name"~"legname|segheria|carpenteria legno|falegnameria|strutture legno",i]',
    ],
    "Ferramenta e Utensileria": [
        'nwr["shop"="hardware"]',
        'nwr["name"~"ferramenta|utensileria|utensili|minuteria|viterie|bulloneria",i]',
    ],
}


def _build_overpass_query(lat: float, lon: float, radius_m: int, tag_queries: list[str]) -> str:
    union_parts = "\n  ".join(
        [f'{q}(around:{radius_m},{lat},{lon});' for q in tag_queries]
    )
    return f"""
[out:json][timeout:45];
(
  {union_parts}
);
out center;
"""


def _parse_elements(elements: list, category: str) -> list[dict]:
    results = []
    for el in elements:
        tags = el.get("tags", {})
        name = tags.get("name") or tags.get("operator") or tags.get("brand")
        if not name:
            continue
        # way/relation hanno coordinate in "center"
        lat = el.get("lat") or el.get("center", {}).get("lat")
        lon = el.get("lon") or el.get("center", {}).get("lon")
        results.append({
            "Categoria": category,
            "Nome": name,
            "Indirizzo": _format_address(tags),
            "Telefono": tags.get("phone") or tags.get("contact:phone", ""),
            "Email": tags.get("email") or tags.get("contact:email", ""),
            "Sito Web": tags.get("website") or tags.get("contact:website", ""),
            "lat": lat,
            "lon": lon,
        })
    return results


def _format_address(tags: dict) -> str:
    parts = []
    if tags.get("addr:street"):
        parts.append(tags["addr:street"])
        if tags.get("addr:housenumber"):
            parts[-1] += f" {tags['addr:housenumber']}"
    if tags.get("addr:city"):
        parts.append(tags["addr:city"])
    return ", ".join(parts) if parts else ""


def search_suppliers(
    lat: float, lon: float, radius_km: float, categories: list[str] | None = None
) -> pd.DataFrame:
    """Query Overpass API e restituisce un DataFrame di fornitori vicino a (lat, lon)."""
    radius_m = int(radius_km * 1000)
    all_results = []

    active_categories = categories or list(CATEGORY_QUERIES.keys())

    for category in active_categories:
        tag_queries = CATEGORY_QUERIES.get(category, [])
        if not tag_queries:
            continue

        query = _build_overpass_query(lat, lon, radius_m, tag_queries)
        try:
            response = requests.post(
                OVERPASS_URL,
                data={"data": query},
                timeout=50,
            )
            response.raise_for_status()
            data = response.json()
            elements = data.get("elements", [])
            all_results.extend(_parse_elements(elements, category))
        except requests.RequestException:
            continue

    if not all_results:
        return pd.DataFrame(
            columns=["Categoria", "Nome", "Indirizzo", "Telefono", "Email", "Sito Web", "lat", "lon"]
        )

    df = pd.DataFrame(all_results)
    df = df.drop_duplicates(subset=["Nome", "lat", "lon"])
    return df.reset_index(drop=True)
