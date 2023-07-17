import networkx as nx
import numpy as np

def get_current_graph(player):
    return player.group.G

# Utility: 用來將 G 的 link 轉換成前端接受的格式
def G_links(G, Full_G):
    links = []
    for (i, j) in Full_G.edges():
        if i in list(G.nodes()) and j in list(G.nodes):
            links.append({"source": i, "target": j, 'dashed': "False", "display": "True"})
            # links.append({"source": j, "target": i, 'dashed': "False", "display": "True"})
        else:
            links.append({"source": i, "target": j, 'dashed': "False", "display": "False"})
            # links.append({"source": j, "target": i, 'dashed': "False", "display": "False"})
    return links

# Utility: 用來將 G 的 node attributes 轉換成前端接受的格式
def G_nodes(G, Full_G):

    degree = {node: degree for (node, degree) in G.degree()}
    closeness = {node: closeness for (node, closeness) in nx.closeness_centrality(G).items()}
    betweenness = {node: betweenness for (node, betweenness) in nx.betweenness_centrality(G).items()}
    pagerank = {node: pagerank for (node, pagerank) in nx.pagerank(G).items()}

    nodes = []
    for n in Full_G.nodes():
        if n in list(G.nodes()):
            nodes.append({
                "id": n, "degree": round(degree[n], 2), "closeness": round(closeness[n], 2), "betweenness": round(betweenness[n], 2), "pagerank": round(pagerank[n], 2), "display": "True", 
                })
        else:
            nodes.append({
                "id": n, "degree": -1, "closeness": -1, "betweenness": -1, "pagerank": -1, "display": "False"
                })

    return nodes


def node_centrality_criteria(G, Full_G):
    degree, closeness, betweenness, pagerank = [], [], [], []
    for node in G_nodes(G, Full_G):
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
def to_list(string, dytpe="int"):
    if string == "":
        return []
    if dytpe == "int":
        return [int(n) for n in string.split(",")]
    else:
        return [float(n) for n in string.split(",")]
        
def remove_node_and_neighbor(to_be_removed, G):
    removed = [n for n in G.neighbors(to_be_removed)] + [to_be_removed]
    for n in removed:
        G.remove_node(n)
    return G

def remove_node(to_be_removed, G, auto_clean=True):
    G.remove_node(to_be_removed)

    if auto_clean:
        for n in dict(G.nodes()).copy():
            if G.degree(n) == 0:
                G.remove_node(n)

    return G

def to_dash_G(to_be_removed, G):
    G.nodes[to_be_removed]['display'] = False

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

def converter(dct):
    tmp_dct = dict()
    cnt = 0
    for node in dct["nodes"]:
        node["label"] = node["id"]
        tmp_dct["node_"+str(cnt)]= node
        cnt += 1

    for edge in dct["links"]:
        tmp_dct["edge_"+str(cnt)] = edge
        cnt += 1

    str_ = str(json.dumps(tmp_dct, indent=2, ensure_ascii=False))

    for idx in range(cnt, -1, -1):
        str_ = str_.replace("_"+str(idx), "")
    str_ = "graph [" + str_[1:]
    str_ = str_.replace('\"', '').replace(',', '').replace(':', '').replace('{', '[').replace('}', ']')

    return str_

def convert_to_FINDER_format(file_name, input_dir, output_dir):
    G = nx.read_edgelist(f"{input_dir}/{file_name}.txt")
    data = json_graph.node_link_data(G)

    with io.open(f"{output_dir}/{file_name}.txt", 'w', encoding='utf8') as outfile:
        str_ = converter(data)
        outfile.write(str_)

