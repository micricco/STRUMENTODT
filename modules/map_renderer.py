import folium
import pandas as pd


CATEGORY_COLORS = {
    "Materiali Edili": "orange",
    "Noleggio Attrezzature": "blue",
    "Calcestruzzo e Prefabbricati": "gray",
    "Carpenteria Metallica": "darkred",
    "Impianti Elettrici": "yellow",
    "Impianti Idraulici e Termici": "lightblue",
    "Trasporti e Logistica": "green",
    "Cave e Inerti": "beige",
}

DEFAULT_COLOR = "purple"


def build_map(site_lat: float, site_lon: float, suppliers: pd.DataFrame, radius_km: float) -> folium.Map:
    m = folium.Map(location=[site_lat, site_lon], zoom_start=11, tiles="OpenStreetMap")

    # Site marker
    folium.Marker(
        location=[site_lat, site_lon],
        popup="<b>CANTIERE</b>",
        tooltip="Cantiere",
        icon=folium.Icon(color="red", icon="hard-hat", prefix="fa"),
    ).add_to(m)

    # Radius circle
    folium.Circle(
        location=[site_lat, site_lon],
        radius=radius_km * 1000,
        color="#e74c3c",
        fill=False,
        weight=1.5,
        dash_array="6",
        tooltip=f"Raggio {radius_km} km",
    ).add_to(m)

    if suppliers.empty:
        return m

    # Group by category with LayerControl
    layers = {}
    for category in suppliers["Categoria"].unique():
        fg = folium.FeatureGroup(name=category, show=True)
        layers[category] = fg
        m.add_child(fg)

    for _, row in suppliers.iterrows():
        if pd.isna(row.get("lat")) or pd.isna(row.get("lon")):
            continue

        color = CATEGORY_COLORS.get(row["Categoria"], DEFAULT_COLOR)

        popup_lines = [f"<b>{row['Nome']}</b>", f"<i>{row['Categoria']}</i>"]
        if row.get("Indirizzo"):
            popup_lines.append(row["Indirizzo"])
        if row.get("Telefono"):
            popup_lines.append(f"Tel: {row['Telefono']}")
        if row.get("Sito Web"):
            popup_lines.append(f'<a href="{row["Sito Web"]}" target="_blank">Sito web</a>')

        folium.Marker(
            location=[row["lat"], row["lon"]],
            popup=folium.Popup("<br>".join(popup_lines), max_width=250),
            tooltip=row["Nome"],
            icon=folium.Icon(color=color, icon="industry", prefix="fa"),
        ).add_to(layers[row["Categoria"]])

    folium.LayerControl(collapsed=False).add_to(m)
    return m
