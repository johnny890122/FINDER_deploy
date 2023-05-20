import networkx as nx
import numpy as np

# Utility: 用來將 G 的 link 轉換成前端接受的格式
def G_links(G):
    links = []
    for (i, j) in G.edges():
        links.append({"source": i, "target": j, 'dashed': "False"})
        links.append({"source": j, "target": i, 'dashed': "False"})

    return links

# Utility: 用來將 G 的 node attributes 轉換成前端接受的格式
def G_nodes(G, player):
    # node degree
    degree = {node: degree for (node, degree) in G.degree()}

    # node geo-distance
    geo_dist_dct = { 
        key: np.sum(list(val.values()))
            for key, val in dict(nx.shortest_path_length(G)).items()
    }
    
    # player 和其他玩家之間共同鄰居的數量
    if player.role_type == 'hider':
        common_neighbor = dict()
        for n in G.nodes():
            common_neighbor[n] = len(list(nx.common_neighbors(G, player.id_in_group, n)))

    nodes = []
    for i in G.nodes():
        if player.role_type == 'hider':
            nodes.append({"id": i, "degree": degree[i], "geo_d": geo_dist_dct[i], "common_neighbor": common_neighbor[i]})
        else:
            nodes.append({"id": i, "degree": degree[i], "geo_d": geo_dist_dct[i]})
    return nodes

# Utility
def to_list(string):
    if string == "":
        return []
    return [int(n) for n in string.split(",")]

def remove_from_G(player, G):
    removed = [n for n in G.neighbors(player.to_be_removed)]
    removed.append(player.to_be_removed)
    
    player.num_removed = len(removed)
    player.original_size = len(G.nodes())
    for n in removed:
        G.remove_node(n)
    player.node_remain = len(G.nodes())
    
    for p in player.group.get_players():
        if p.id_in_group in G.nodes():
            p.survive = True
        else:
            p.survive = False

def hider_payoff(player, G):
    constant =C()
    c = constant.c
    delta = constant.delta

    nodes = { node["id"]: {"degree": node["degree"], "geo_d": node["geo_d"]} for node in G_nodes(G, player) }

    payoff = 0
    geo_d = [node["geo_d"] for node in nodes.values()]
    for i, d in enumerate(geo_d):
        if d == 0 or i+1 == player.id_in_group:
            pass
        else:
            payoff += delta**d

    payoff -= c*nodes[player.id_in_group]["degree"]

    return payoff

def getRobustness(G, sol):
    G = G.copy()
    GCCsize = len(max(nx.connected_components(G), key=len))
    G.remove_node(sol)
    newGCCsize = len(max(nx.connected_components(G), key=len))

    print(GCCsize, newGCCsize)

    return (GCCsize - newGCCsize) / ((G.number_of_nodes() * G.number_of_nodes()))


def generate_ba_graph_with_density(n, density):
    total_possible_edges = (n * (n - 1)) / 2
    desired_num_edges = density * total_possible_edges
    avg_edges_per_node = round(desired_num_edges / n)
    m = max(avg_edges_per_node, 1)  # Ensure m is at least 1
    ba_graph = nx.barabasi_albert_graph(n, m)

    return ba_graph