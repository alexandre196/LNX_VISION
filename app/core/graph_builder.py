import pandas as pd
import networkx as nx
import os

EXCEL_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "entities.xlsx")

def load_graph() -> nx.Graph:
    xls = pd.ExcelFile(EXCEL_PATH)
    df_entities  = pd.read_excel(xls, sheet_name="Entites")
    df_relations = pd.read_excel(xls, sheet_name="Relations")

    G = nx.Graph()

    for _, row in df_entities.iterrows():
        G.add_node(
            row["id"],
            name=row["name"],
            type=row["type"],
            risk=int(row["risk"]),
            statut=row["statut"],
            ville=row["ville"],
            lat=float(row["lat"]) if "lat" in row and pd.notna(row["lat"]) else None,
            lon=float(row["lon"]) if "lon" in row and pd.notna(row["lon"]) else None,
        )

    for _, row in df_relations.iterrows():
        G.add_edge(
            row["source"], row["cible"],
            relation=row["relation"],
            force=float(row["force"]),
            weight=round(1 - float(row["force"]) + 0.01, 4),
        )

    return G


def load_events() -> dict:
    xls = pd.ExcelFile(EXCEL_PATH)
    if "Evenements" not in xls.sheet_names:
        return {}
    df = pd.read_excel(xls, sheet_name="Evenements")
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    df = df.sort_values("date", ascending=False)
    events = {}
    for _, row in df.iterrows():
        eid = str(row["entity_id"])
        if eid not in events:
            events[eid] = []
        events[eid].append({
            "date": row["date"], "type": row["type"],
            "description": row["description"], "lieu": row["lieu"],
        })
    return events


def get_entity_dict(G: nx.Graph) -> dict:
    return {node: data for node, data in G.nodes(data=True)}