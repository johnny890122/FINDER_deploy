import networkx as nx
import numpy as np
import pygsheets, json, requests
from networkx.readwrite import json_graph
from typing import Type
import os
from io import BytesIO

def compute_finder_payoff(G, dqn, model_file):
    hist_G = G.copy()
    content = BytesIO(convert_to_FINDER_format(G).encode('utf-8'))
    _, sol = dqn.Evaluate(content, model_file)

    payoff_finder_lst = [0]
    for node in sol:
        payoff_finder_lst.append(getRobustness(G, hist_G, node))
    for _ in range(G.number_of_nodes() - len(payoff_finder_lst)):
        GCCsize = len(max(nx.connected_components(G), key=len))
        payoff_finder_lst.append(1 - 1/GCCsize)
    
    payoff_finder_lst = (np.cumsum(payoff_finder_lst) / G.number_of_nodes()).tolist()

    return payoff_finder_lst

def copy_G(source_G, target_G):
    for n in source_G.nodes():
        target_G.add_node(n)
    for e in source_G.edges():
        target_G.add_edge(e[0], e[1])

def read_sample(sample):
    assert sample in [
        "911", "everett", "borgatti", "potts", "DOMESTICTERRORWEB", 
        "HEROIN_DEALING", "MAIL",  "suicide", "SWINGERS_club", "HAMBURG_TIE_YEAR"
    ]

    if sample == "911":
        G = nx.read_gml("./sample_data/911.gml")
    elif sample in ["everett", "potts", "borgatti"]:
        G = nx.read_gml(f"./sample_data/{sample}.gml")
    else:
        G = nx.read_gml(f"./empirical_data/{sample}.gml")

    map_dct = {node: int(idx) for idx, node in enumerate(G.nodes())}
    return nx.relabel_nodes(G, map_dct, copy=True)
    
def current_dismantle_stage(player):
    basic_full_nodes = read_sample(player.session.config["basic_sample_data"]).number_of_nodes()
    HXA_full_nodes = read_sample(player.session.config["HXA_sample_data"]).number_of_nodes()
    
    if player.group.basic_G.number_of_nodes() == basic_full_nodes:
        stage = "basic"
    elif player.group.HDA_G.number_of_nodes() == HXA_full_nodes:
        stage = "HDA"
    elif player.group.HCA_G.number_of_nodes() == HXA_full_nodes:
        stage = "HCA"
    elif player.group.HBA_G.number_of_nodes() == HXA_full_nodes:
        stage = "HBA"
    elif player.group.HPRA_G.number_of_nodes() == HXA_full_nodes:
        stage = "HPRA"
    else:
        stage = "official"

    return stage

def current_dismantle_G(player, stage):
    if stage == "basic":
        return player.group.basic_G
    elif stage == "HDA":
        return player.group.HDA_G
    elif stage == "HCA":
        return player.group.HCA_G
    elif stage == "HBA":
        return player.group.HBA_G
    elif stage == "HPRA":
        return player.group.HPRA_G   
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
def G_nodes(G, graph_layout={}):

    degree = {node: degree for (node, degree) in G.degree()}
    closeness = {node: closeness for (node, closeness) in nx.closeness_centrality(G).items()}
    betweenness = {node: betweenness for (node, betweenness) in nx.betweenness_centrality(G).items()}
    pagerank = {node: pagerank for (node, pagerank) in nx.pagerank(G).items()}

    nodes = []
    # graph_layout[dct["id"]] = {"x": dct["x"], "y": dct["y"]}
    for n, data in list(G.nodes(data=True)):
        dct = {
            "id": n, "degree": degree[n], "closeness": closeness[n], 
            "betweenness": betweenness[n], "page_rank": pagerank[n], "display": "True"
        }
        if graph_layout != {}:
            dct["x"] = graph_layout[n]["x"]
            dct["y"] = graph_layout[n]["y"]
        nodes.append(dct)

    # add a pesudo node as center node
    if len(list(nx.connected_components(G))) > 1:
        nodes.append({
            "id": "source", "degree": -1, "closeness": -1, "betweenness": -1, "page_rank": -1, "display": "False"
        })

    return nodes

def node_centrality_criteria(G):

    centrality = {
        "degree": {"node":[], "value":[]}, "closeness": {"node":[], "value":[]}, "betweenness": {"node":[], "value":[]}, "page_rank": {"node":[], "value":[]}
    }
    for metric in ["degree", "closeness", "betweenness", "page_rank"]:
        node_lst = []
        for node in G_nodes(G):
            node_lst.append((node["id"], node[metric]))
        
        hxa = sorted(node_lst, key=lambda x: x[1], reverse=True)
        rank = 1
        now_score = hxa[0][1]
        for idx, (node, score) in enumerate(hxa): 
            if now_score > score:
                now_score = score
                rank += 1
            centrality[metric]["node"].append(node)
            centrality[metric]["value"].append(rank)

    return centrality

def relabel_G(G):
    map_dct = {node: idx for idx, node in enumerate(G.nodes())}
    reverse_map_dct = {val: key for key, val in map_dct.items()}
    return nx.relabel_nodes(G, map_dct, copy=True), reverse_map_dct

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

def getRobustness(full_g: Type[nx.classes.graph.Graph], G: Type[nx.classes.graph.Graph], sol: int):    
    fullGCCsize = len(max(nx.connected_components(full_g), key=len))

    G.remove_node(sol)

    remainGCC = nx.connected_components(G)

    if len(list(remainGCC)) != 0:
        remainGCCsize = len(max(nx.connected_components(G), key=len))
    else:
        remainGCCsize = 1
    return 1 - remainGCCsize/fullGCCsize

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

def convert_to_FINDER_format(G):
    data = json_graph.node_link_data(G)
    str_ = converter(data)

    return str_


def complete_genertor(n=20):
    return nx.complete_graph(n)

