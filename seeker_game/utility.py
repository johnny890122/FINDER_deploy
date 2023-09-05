import networkx as nx
import numpy as np
import pygsheets, json
from networkx.readwrite import json_graph

def read_911(full):
    if full:
        filename = "./sample_data/full_911.json"
    else:
        filename = "./sample_data/911.json"
    with open(filename) as f:
        js_graph = json.load(f)
    G = json_graph.node_link_graph(js_graph, multigraph=False)
    map_dct = {node: int(node) for node in G.nodes()}
    return nx.relabel_nodes(G, map_dct, copy=True)

    # if full:
    #     G = nx.read_gml("../sample_data/full_911.gml")
    # else:
    #     G = nx.read_gml("../sample_data/911.gml")
    # map_dct = {
    #     node: idx + 2 for idx, node in enumerate(G.nodes())
    # }
    # return nx.relabel_nodes(G, map_dct, copy=True)

def read_everett(full):

    # G = nx.read_gml("./sample_data/everett.gml")
    # return G
    filename = "./sample_data/everett.json"
    with open(filename) as f:
        js_graph = json.load(f)
    G = json_graph.node_link_graph(js_graph, multigraph=False)
    map_dct = {node: int(node) for node in G.nodes()}
    return nx.relabel_nodes(G, map_dct, copy=True)
    
def current_dismantle_stage(player, num_911_nodes):
    if player.group.basic_911.number_of_nodes() == num_911_nodes:
        stage = "basic"
    elif player.group.HDA_911.number_of_nodes() == num_911_nodes:
        stage = "HDA"
    elif player.group.HCA_911.number_of_nodes() == num_911_nodes:
        stage = "HCA"
    elif player.group.HBA_911.number_of_nodes() == num_911_nodes:
        stage = "HBA"
    elif player.group.HPRA_911.number_of_nodes() == num_911_nodes:
        stage = "HPRA"
    else:
        stage = "official"

    return stage

def current_dismantle_G(player, stage):
    # assert stage in ["basic", "HDA", "HCA", "HBA", "HPRA", "official"]

    if stage == "basic":
        return player.group.basic_911
    elif stage == "HDA":
        return player.group.HDA_911
    elif stage == "HCA":
        return player.group.HCA_911
    elif stage == "HBA":
        return player.group.HBA_911
    elif stage == "HPRA":
        return player.group.HPRA_911   
    else:
        return player.group.G

def get_current_graph(player):
    return player.group.G

def GCC_size(G):
    if len(list(nx.connected_components(G))) != 0:
        return len(max(nx.connected_components(G), key=len))
    return 1

# Utility: 用來將 G 的 link 轉換成前端接受的格式
def G_links(G):
    links = []
    for (i, j) in G.edges():
        links.append({"source": i, "target": j, 'dashed': "False", "display": "True"})
    
    if len(list(nx.connected_components(G))) > 1:
        for CC in nx.connected_components(G):
            subgraph = G.copy().subgraph(CC)
            # find highest degree node 
            keys = list(nx.degree_centrality(subgraph).keys())
            values = list(nx.degree_centrality(subgraph).values())
            node = keys[ np.argmax(values)]
            links.append({"source": "source", "target": node, 'dashed': "False", "display": "False"})
    return links

# Utility: 用來將 G 的 node attributes 轉換成前端接受的格式
def G_nodes(G):

    degree = {node: degree for (node, degree) in G.degree()}
    closeness = {node: closeness for (node, closeness) in nx.closeness_centrality(G).items()}
    betweenness = {node: betweenness for (node, betweenness) in nx.betweenness_centrality(G).items()}
    pagerank = {node: pagerank for (node, pagerank) in nx.pagerank(G).items()}

    nodes = []
    for n, data in list(G.nodes(data=True)):
        dct = {
            "id": n, "degree": round(degree[n], 2), "closeness": round(closeness[n], 2), 
            "betweenness": round(betweenness[n], 2), "pagerank": round(pagerank[n], 2), "display": "True"
        }
        if "x" in data.keys() and "y" in data.keys():
            dct["x"] = data["x"]
            dct["y"] = data["y"]
        nodes.append(dct)

    # add a pesudo node as center node
    if len(list(nx.connected_components(G))) > 1:
        nodes.append({
            "id": "source", "degree": -1, "closeness": -1, "betweenness": -1, "pagerank": -1, "display": "False"
        })

    return nodes

def node_centrality_criteria(G):

    centrality = {
        "degree": {}, "closeness": {}, "betweenness": {}, "page_rank": {}
    }
    for metric in ["degree", "closeness", "betweenness", "page_rank"]:
        node_lst = []
        for node in G_nodes(G):
            node_lst.append((node["id"], node["degree"]))
        
        hxa = sorted(node_lst, key=lambda x: x[1], reverse=True)
        rank = 1
        now_score = hxa[0][1]
        for idx, (node, score) in enumerate(hxa): 
            if now_score > score:
                now_score = score
                rank += 1
            centrality[metric][node] = rank

    return centrality

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

def remove_node(to_be_removed, G):
    G.remove_node(to_be_removed)
    return G

def getRobustness(G, sol, fullGCCsize, N):
    G.remove_node(int(sol))
    remainGCCsize = GCC_size(G)

    return ((fullGCCsize - remainGCCsize) / fullGCCsize) / N

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

def complete_genertor(n=20):
    return nx.complete_graph(n)

def fetch_link(sheet_url, auth_file):
    buffer = 0.01
    gc = pygsheets.authorize(service_file = auth_file)
    sheet = gc.open_by_url(sheet_url)

    df = sheet.worksheet_by_title("link").get_as_df()
    df = df[df["num_used"] <= df["total_avaiable"]*(1-buffer)]

    return df["link"].iloc[0]

def upload_info(sheet_url, auth_file, link):

	gc = pygsheets.authorize(service_file = auth_file)
    
	sheet = gc.open_by_url(sheet_url)
	df = sheet.worksheet_by_title("link").get_as_df()

	df.loc[df["link"] == link, "num_used"] += 1
	sheet.worksheet_by_title("link").clear()

	sheet.worksheet_by_title("link").set_dataframe(df, start = "A1")