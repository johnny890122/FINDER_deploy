import networkx as nx
import numpy as np

def get_current_graph(player):
    return player.group.G_seeker_practice if player.session.config['practice'] else player.group.G


# Utility: 用來將 G 的 link 轉換成前端接受的格式
def G_links(G):
    links = []
    for (i, j) in G.edges():
        links.append({"source": i, "target": j, 'dashed': "False"})
        links.append({"source": j, "target": i, 'dashed': "False"})

    return links

# Utility: 用來將 G 的 node attributes 轉換成前端接受的格式
def G_nodes(G, player):

    degree = {node: degree for (node, degree) in G.degree()}
    closeness = {node: closeness for (node, closeness) in nx.closeness_centrality(G).items()}
    betweenness = {node: betweenness for (node, betweenness) in nx.betweenness_centrality(G).items()}
    pagerank = {node: pagerank for (node, pagerank) in nx.pagerank(G).items()}

    nodes = [
        {"id": n, "degree": degree[n], "closeness": closeness[n], "betweenness": betweenness[n], "pagerank": pagerank[n]} 
            for n in G.nodes()
    ]
    return nodes

# Utility
def to_list(string):
    if string == "":
        return []
    return [int(n) for n in string.split(",")]

def remove_node_and_neighbor(player, G):
    removed = [n for n in G.neighbors(player.to_be_removed)] + [player.to_be_removed]
    for n in removed:
        G.remove_node(n)
    return G

def getRobustness(G, sol):
    G = G.copy()
    GCCsize = len(max(nx.connected_components(G), key=len))
    G.remove_node(sol)
    newGCCsize = len(max(nx.connected_components(G), key=len))

    return (GCCsize - newGCCsize) / ((G.number_of_nodes() * G.number_of_nodes()))


def generate_ba_graph_with_density(n, density):
    total_possible_edges = (n * (n - 1)) / 2
    desired_num_edges = density * total_possible_edges
    avg_edges_per_node = round(desired_num_edges / n)
    m = max(avg_edges_per_node, 1)  # Ensure m is at least 1

    ba_graph = nx.barabasi_albert_graph(n, m)

    return ba_graph
