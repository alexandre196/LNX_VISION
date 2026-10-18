"""
icij_to_nexus.py
Convertit les données ICIJ Offshore Leaks en format NEXUS (entities.xlsx)
Placer ce script dans : LNX_Vision_V1/
Lancer avec : python icij_to_nexus.py
"""
import pandas as pd
import os
import re

# ── CONFIG ────────────────────────────────────────────────────────────────────
ICIJ_DIR    = os.path.join(os.path.dirname(__file__), "icij")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "app", "data", "entities_icij.xlsx")
MAX_ENTITIES = 500   # Nombre max d'entités à garder
MAX_RELATIONS = 1000 # Nombre max de relations

print("=" * 50)
print("  NEXUS.INTEL — Import ICIJ Offshore Leaks")
print("=" * 50)

# ── CHARGEMENT ────────────────────────────────────────────────────────────────
print("\n[1/5] Chargement des fichiers CSV...")

entities_path      = os.path.join(ICIJ_DIR, "nodes-entities.csv")
officers_path      = os.path.join(ICIJ_DIR, "nodes-officers.csv")
relationships_path = os.path.join(ICIJ_DIR, "relationships.csv")

for p in [entities_path, officers_path, relationships_path]:
    if not os.path.exists(p):
        print(f"  ERREUR : fichier introuvable : {p}")
        print("  Vérifie que le ZIP est extrait dans LNX_Vision_V1/icij/")
        exit(1)

df_entities      = pd.read_csv(entities_path,      low_memory=False)
df_officers      = pd.read_csv(officers_path,      low_memory=False)
df_relationships = pd.read_csv(relationships_path, low_memory=False)

print(f"  Entités    : {len(df_entities):,} lignes")
print(f"  Officiers  : {len(df_officers):,} lignes")
print(f"  Relations  : {len(df_relationships):,} lignes")

# ── COMPTAGE DES CONNEXIONS ───────────────────────────────────────────────────
print("\n[2/5] Calcul du nombre de connexions par entité...")

# Compter combien de fois chaque node_id apparaît dans les relations
from collections import Counter
conn_count = Counter()
for col in ["node_id_start", "node_id_end"]:
    if col in df_relationships.columns:
        conn_count.update(df_relationships[col].dropna().astype(str).tolist())

# ── SÉLECTION DES TOP ENTITÉS ─────────────────────────────────────────────────
print(f"\n[3/5] Sélection des {MAX_ENTITIES} entités les plus connectées...")

# Préparer les entités
df_ent = df_entities.copy()
df_ent["node_id"] = df_ent["node_id"].astype(str)
df_ent["connections"] = df_ent["node_id"].map(conn_count).fillna(0).astype(int)

# Préparer les officiers (personnes physiques)
df_off = df_officers.copy()
df_off["node_id"] = df_off["node_id"].astype(str)
df_off["connections"] = df_off["node_id"].map(conn_count).fillna(0).astype(int)

# Fusionner et trier par connexions
df_ent["source_type"] = "Organisation"
df_off["source_type"] = "Individu"

# Colonnes communes
common_cols = ["node_id", "name", "source_type", "connections"]
if "countries" in df_ent.columns:
    df_ent["country"] = df_ent["countries"].fillna("Unknown")
elif "country_codes" in df_ent.columns:
    df_ent["country"] = df_ent["country_codes"].fillna("Unknown")
else:
    df_ent["country"] = "Unknown"

if "countries" in df_off.columns:
    df_off["country"] = df_off["countries"].fillna("Unknown")
elif "country_codes" in df_off.columns:
    df_off["country"] = df_off["country_codes"].fillna("Unknown")
else:
    df_off["country"] = "Unknown"

df_ent = df_ent[["node_id","name","source_type","connections","country"]].copy()
df_off = df_off[["node_id","name","source_type","connections","country"]].copy()

# Top entités par connexions
df_all = pd.concat([df_ent, df_off], ignore_index=True)
df_all = df_all[df_all["connections"] > 0]
df_all = df_all.sort_values("connections", ascending=False).head(MAX_ENTITIES)
df_all = df_all.reset_index(drop=True)

print(f"  {len(df_all)} entités sélectionnées")

# ── CONSTRUCTION DU FORMAT NEXUS ──────────────────────────────────────────────
print("\n[4/5] Construction du format NEXUS...")

def clean_name(name):
    if pd.isna(name): return "Unknown"
    return str(name).strip()[:50]

def make_id(name, idx):
    if pd.isna(name): return f"E{idx:04d}"
    clean = re.sub(r'[^A-Z0-9]', '', str(name).upper())[:6]
    return f"{clean}{idx:02d}" if clean else f"E{idx:04d}"

def risk_score(connections, max_conn):
    """Score de risque basé sur le nombre de connexions (0-99)"""
    if max_conn == 0: return 30
    ratio = connections / max_conn
    return max(10, min(99, int(ratio * 99)))

def get_statut(connections, max_conn):
    ratio = connections / max_conn if max_conn > 0 else 0
    if ratio > 0.7: return "Critique"
    if ratio > 0.4: return "Surveillance"
    if ratio > 0.2: return "Enquete"
    return "Interet"

max_conn = df_all["connections"].max()

nexus_entities = []
id_map = {}  # node_id original -> id NEXUS

for idx, row in df_all.iterrows():
    nexus_id = make_id(row["name"], idx)
    id_map[row["node_id"]] = nexus_id
    risk = risk_score(row["connections"], max_conn)
    nexus_entities.append({
        "id":     nexus_id,
        "name":   clean_name(row["name"]),
        "type":   row["source_type"],
        "risk":   risk,
        "statut": get_statut(row["connections"], max_conn),
        "ville":  str(row["country"])[:20] if row["country"] else "Unknown",
        "lat":    None,
        "lon":    None,
        "connexions": int(row["connections"]),
    })

df_nexus_entities = pd.DataFrame(nexus_entities)
print(f"  {len(df_nexus_entities)} entités converties")

# ── RELATIONS ─────────────────────────────────────────────────────────────────
# Filtrer uniquement les relations entre entités sélectionnées
selected_ids = set(df_all["node_id"].astype(str).tolist())

df_rel = df_relationships.copy()
df_rel["node_id_start"] = df_rel["node_id_start"].astype(str)
df_rel["node_id_end"]   = df_rel["node_id_end"].astype(str)

df_rel_filtered = df_rel[
    df_rel["node_id_start"].isin(selected_ids) &
    df_rel["node_id_end"].isin(selected_ids)
].copy()

# Convertir les IDs
df_rel_filtered["source"] = df_rel_filtered["node_id_start"].map(id_map)
df_rel_filtered["cible"]  = df_rel_filtered["node_id_end"].map(id_map)
df_rel_filtered = df_rel_filtered.dropna(subset=["source","cible"])

# Type de relation
rel_col = "rel_type" if "rel_type" in df_rel_filtered.columns else \
          "type" if "type" in df_rel_filtered.columns else None

if rel_col:
    df_rel_filtered["relation"] = df_rel_filtered[rel_col].fillna("Lien")
else:
    df_rel_filtered["relation"] = "Lien offshore"

df_rel_filtered["force"] = 0.7  # Force par défaut

df_nexus_relations = df_rel_filtered[["source","cible","relation","force"]].drop_duplicates()
df_nexus_relations = df_nexus_relations.head(MAX_RELATIONS)
print(f"  {len(df_nexus_relations)} relations converties")

# ── EXPORT ────────────────────────────────────────────────────────────────────
print(f"\n[5/5] Export vers {OUTPUT_FILE}...")

with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
    df_nexus_entities.to_excel(writer, sheet_name="Entites", index=False)
    df_nexus_relations.to_excel(writer, sheet_name="Relations", index=False)

print("\n" + "=" * 50)
print(f"  Terminé !")
print(f"  Fichier : {OUTPUT_FILE}")
print(f"  Entités : {len(df_nexus_entities)}")
print(f"  Relations : {len(df_nexus_relations)}")
print("=" * 50)
print("\n  Maintenant dans NEXUS :")
print("  1. Modifie graph_builder.py pour pointer vers entities_icij.xlsx")
print("  2. Redémarre le serveur")
print("  3. Clique Sync dans l'interface")