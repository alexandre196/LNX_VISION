"""
add_coordinates.py
Ajoute les coordonnées lat/lon aux entités ICIJ basées sur le pays
Lancer avec : python add_coordinates.py
"""
import pandas as pd
import os
import random

INPUT_FILE  = os.path.join(os.path.dirname(__file__), "app", "data", "entities_icij.xlsx")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "app", "data", "entities_icij.xlsx")

print("=" * 50)
print("  NEXUS — Ajout des coordonnées géographiques")
print("=" * 50)

xls = pd.ExcelFile(INPUT_FILE)
df_entities  = pd.read_excel(xls, sheet_name="Entites")
df_relations = pd.read_excel(xls, sheet_name="Relations")

print(f"\n  {len(df_entities)} entités chargées")

def get_coords(ville):
    if pd.isna(ville): return (20.0, 0.0)
    ville = str(ville).strip().upper()
    
    name_map = {
        "MALTA":              (35.9375, 14.3754),
        "BERMUDA":            (32.3078, -64.7505),
        "CAYMAN":             (19.3133, -81.2546),
        "HONG KONG":          (22.3193, 114.1694),
        "SEYCHELLES":         (-4.6796, 55.4920),
        "JERSEY":             (49.2144, -2.1312),
        "BRITISH VIRGIN":     (18.4207, -64.6400),
        "GUERNSEY":           (49.4657, -2.5853),
        "SINGAPORE":          (1.3521,  103.8198),
        "SAMOA":              (-13.7590, -172.1046),
        "PANAMA":             (8.9824,  -79.5199),
        "MALAYSIA":           (4.2105,  101.9758),
        "TURKEY":             (38.9637, 35.2433),
        "BAHAMAS":            (25.0343, -77.3963),
        "LUXEMBOURG":         (49.8153, 6.1296),
        "SWITZERLAND":        (46.8182, 8.2275),
        "UNITED KINGDOM":     (51.5074, -0.1278),
        "CANADA":             (56.1304, -106.3468),
        "UNITED STATES":      (37.0902, -95.7129),
        "U.S. VIRGIN":        (18.3358, -64.8963),
        "FRANCE":             (46.2276, 2.2137),
        "GERMANY":            (51.1657, 10.4515),
        "CHINA":              (35.8617, 104.1954),
        "RUSSIA":             (61.5240, 105.3188),
        "AUSTRALIA":          (-25.2744, 133.7751),
        "NEW ZEALAND":        (-40.9006, 174.8860),
        "ISLE OF MAN":        (54.2361, -4.5481),
        "LIECHTENSTEIN":      (47.1660, 9.5554),
        "MONACO":             (43.7384, 7.4246),
        "CYPRUS":             (35.1264, 33.4299),
        "MAURITIUS":          (-20.3484, 57.5522),
        "VANUATU":            (-15.3767, 166.9592),
        "BELIZE":             (17.1899, -88.4976),
        "MARSHALL":           (7.1315, 171.1845),
        "NIUE":               (-19.0544, -169.8672),
        "COOK ISLANDS":       (-21.2367, -159.7777),
        "NOT IDENTIFIED":     (20.0, 0.0),
        "UNKNOWN":            (20.0, 0.0),
    }
    for name, coords in name_map.items():
        if name in ville:
            return coords
    return (20.0 + random.uniform(-5, 5), random.uniform(-10, 10))

# Appliquer les coordonnées
import random
random.seed(42)

lats, lons = [], []
for _, row in df_entities.iterrows():
    lat, lon = get_coords(row.get("ville", "Unknown"))
    # Offset léger pour éviter superposition des marqueurs du même pays
    lats.append(round(lat + random.uniform(-1.5, 1.5), 4))
    lons.append(round(lon + random.uniform(-1.5, 1.5), 4))

df_entities["lat"] = lats
df_entities["lon"] = lons

print(f"  Coordonnées ajoutées")

# Améliorer le scoring basé sur les connexions
if "connexions" in df_entities.columns:
    max_conn = df_entities["connexions"].max()
    df_entities["risk"] = df_entities["connexions"].apply(
        lambda c: max(15, min(99, int((c / max_conn) * 99))) if max_conn > 0 else 30
    )
    print(f"  Scores de risque recalculés (max connexions: {max_conn})")

with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
    df_entities.to_excel(writer, sheet_name="Entites", index=False)
    df_relations.to_excel(writer, sheet_name="Relations", index=False)

print(f"\n  Fichier mis à jour : {OUTPUT_FILE}")
print("  Redémarre le serveur et clique Sync dans NEXUS !")
print("=" * 50)