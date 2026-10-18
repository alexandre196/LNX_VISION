import networkx as nx
from app.core.graph_builder import load_graph, get_entity_dict, load_events
from fastapi import HTTPException


def _get_graph() -> nx.Graph:
    return load_graph()


def shortest_path(start: str, end: str) -> dict:
    G = _get_graph()
    if start not in G:
        raise HTTPException(status_code=404, detail=f"Entité '{start}' introuvable.")
    if end not in G:
        raise HTTPException(status_code=404, detail=f"Entité '{end}' introuvable.")
    try:
        path_ids = nx.shortest_path(G, source=start, target=end, weight="weight")
        length   = nx.shortest_path_length(G, source=start, target=end, weight="weight")
    except nx.NetworkXNoPath:
        raise HTTPException(status_code=404, detail=f"Aucun chemin entre '{start}' et '{end}'.")

    entities = get_entity_dict(G)
    path_detail = [{"id": nid, "name": entities.get(nid, {}).get("name", nid)} for nid in path_ids]
    edges_detail = []
    for i in range(len(path_ids) - 1):
        edge = G.get_edge_data(path_ids[i], path_ids[i+1], default={})
        edges_detail.append({"de": path_ids[i], "vers": path_ids[i+1],
                              "relation": edge.get("relation","—"), "force": edge.get("force",0)})
    return {"path": path_detail, "edges": edges_detail,
            "nb_etapes": len(path_ids)-1, "score_chemin": round(length,4),
            "message": f"Chemin de {start} à {end} — {len(path_ids)-1} étape(s)."}


def get_all_entities() -> list:
    G = _get_graph()
    return [{"id": nid, **data} for nid, data in G.nodes(data=True)]


def get_entity(entity_id: str) -> dict:
    G = _get_graph()
    if entity_id not in G:
        raise HTTPException(status_code=404, detail=f"Entité '{entity_id}' introuvable.")
    data = dict(G.nodes[entity_id])
    neighbors = []
    for neighbor in G.neighbors(entity_id):
        edge = G.get_edge_data(entity_id, neighbor, default={})
        neighbors.append({"id": neighbor, "name": G.nodes[neighbor].get("name", neighbor),
                          "relation": edge.get("relation","—"), "force": edge.get("force",0)})
    return {"id": entity_id, **data, "connexions": neighbors}


def get_entity_events(entity_id: str) -> list:
    events = load_events()
    return events.get(entity_id, [])


def get_high_risk(threshold: int = 75) -> list:
    G = _get_graph()
    return [{"id": nid, **data} for nid, data in G.nodes(data=True) if data.get("risk",0) >= threshold]


def get_graph_stats() -> dict:
    G = _get_graph()
    risks = [d.get("risk",0) for _, d in G.nodes(data=True)]
    return {"nb_entites": G.number_of_nodes(), "nb_liens": G.number_of_edges(),
            "densite": round(nx.density(G),4),
            "risk_moyen": round(sum(risks)/len(risks),1) if risks else 0,
            "risk_max": max(risks) if risks else 0, "connexe": nx.is_connected(G)}


def get_communities() -> dict:
    """Détecte les communautés avec l'algorithme de Louvain."""
    import community as community_louvain
    G = _get_graph()
    partition = community_louvain.best_partition(G, weight='force')
    # Groupe par communauté
    communities = {}
    for node, comm_id in partition.items():
        if comm_id not in communities:
            communities[comm_id] = []
        node_data = dict(G.nodes[node])
        communities[comm_id].append({
            "id": node,
            "name": node_data.get("name", node),
            "risk": node_data.get("risk", 0),
        })
    # Stats par communauté
    result = []
    for comm_id, members in sorted(communities.items()):
        risks = [m["risk"] for m in members]
        result.append({
            "community_id": comm_id,
            "size": len(members),
            "risk_moyen": round(sum(risks)/len(risks), 1) if risks else 0,
            "members": members,
        })
    # Partition complète pour le frontend
    return {
        "nb_communities": len(result),
        "partition": partition,
        "communities": result,
    }



    G = _get_graph()
    risks = [d.get("risk",0) for _, d in G.nodes(data=True)]
    return {"nb_entites": G.number_of_nodes(), "nb_liens": G.number_of_edges(),
            "densite": round(nx.density(G),4),
            "risk_moyen": round(sum(risks)/len(risks),1) if risks else 0,
            "risk_max": max(risks) if risks else 0, "connexe": nx.is_connected(G)}