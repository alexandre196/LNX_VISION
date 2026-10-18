import networkx as nx

def shortest_path(G, source, target):
    try:
        return nx.shortest_path(G, source, target)
    except nx.NetworkXNoPath:
        return None
    except nx.NodeNotFound:
        return None