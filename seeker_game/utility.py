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
def G_nodes(G):

    degree = {node: degree for (node, degree) in G.degree()}
    closeness = {node: closeness for (node, closeness) in nx.closeness_centrality(G).items()}
    betweenness = {node: betweenness for (node, betweenness) in nx.betweenness_centrality(G).items()}
    pagerank = {node: pagerank for (node, pagerank) in nx.pagerank(G).items()}

    nodes = [
        {"id": n, "degree": round(degree[n], 2), "closeness": round(closeness[n], 2), "betweenness": round(betweenness[n], 2), "pagerank": round(pagerank[n], 2)}
            for n in G.nodes()
    ]
    return nodes

def node_centrality_criteria(G):
    degree, closeness, betweenness, pagerank = [], [], [], []
    for node in G_nodes(G):
        degree.append((node["id"], node["degree"]))
        closeness.append((node["id"], node["closeness"]))
        betweenness.append((node["id"], node["betweenness"]))
        pagerank.append((node["id"], node["pagerank"]))

    highest_degree_id, _ = sorted(degree, key=lambda x: x[1], reverse=True)[0]
    highest_closeness_id, _ = sorted(closeness, key=lambda x: x[1], reverse=True)[0]
    highest_betweenness_id, _ = sorted(betweenness, key=lambda x: x[1], reverse=True)[0]
    highest_page_rank_id, _ = sorted(pagerank, key=lambda x: x[1], reverse=True)[0]
    return {
        "degree": highest_degree_id, 
        "closeness": highest_closeness_id,
        "betweenness": highest_betweenness_id, 
        "page_rank": highest_page_rank_id, 
    }

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
    avg_edges_per_node = int(desired_num_edges / n)
    m = max(avg_edges_per_node, 1)  # Ensure m is at least 1
    ba_graph = nx.barabasi_albert_graph(n, m)
    return ba_graph
