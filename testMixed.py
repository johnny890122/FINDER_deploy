#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys,os, io
sys.path.append(os.path.dirname(__file__) + os.sep + '../')
from FINDER import FINDER
from tqdm import tqdm, trange
import networkx as nx
from typing import Type
import numpy as np
import pandas as pd
import json, time

def write_gml(G, path, file_name):
    
    dct = dict()
    cnt = 0

    for node in G.nodes():
        dct["node"+ "_" +str(cnt)]= {"id": node, "label": node}
        cnt += 1

    for edge in G.edges():
        dct["edge"+ "_" +str(cnt)] = {"source": edge[0], "target": edge[1]}
        cnt += 1

    str_ = str(json.dumps(dct, indent=2, ensure_ascii=False))

    for idx in range(cnt, -1, -1):
        str_ = str_.replace("_"+str(idx), "")
    str_ = "graph [" + str_[1:]
    str_ = str_.replace('\"', '').replace(',', '').replace(':', '').replace('{', '[').replace('}', ']')

    with io.open(f"{path}/{file_name}", 'w', encoding='utf8') as outfile:
        outfile.write(str_)

def read_gml(data_dir: str, file_name: str) -> Type[nx.classes.graph.Graph]:
    G = nx.read_gml(data_dir + file_name, destringizer=int)
    return nx.relabel_nodes(G, lambda x: int(x))

def hxa(g, method):
    G = g.copy()
    if method == 'HDA':
        dc = nx.degree_centrality(G)
    elif method == 'HBA':
        dc = nx.betweenness_centrality(G)
    elif method == 'HCA':
        dc = nx.closeness_centrality(G)
    elif method == 'HPRA':
        dc = nx.pagerank(G)
    keys = list(dc.keys())
    values = list(dc.values())
    maxTag = np.argmax(values)
    node = keys[maxTag]

    return node

def getRobustness(full_g: Type[nx.classes.graph.Graph], G: Type[nx.classes.graph.Graph], sol: int):
    fullGCCsize = len(max(nx.connected_components(full_g), key=len))

    G.remove_node(int(sol))

    remainGCC = nx.connected_components(G)

    if len(list(remainGCC)) != 0:
        remainGCCsize = len(max(nx.connected_components(G), key=len))
    else:
        remainGCCsize = 1
    return 1 - remainGCCsize/fullGCCsize

# def hxa_finder_mixed(g, G, h_method, cnt, model_file):
#     assert h_method in ["HDA", "HBA", "HCA", "HPRA", "ALL"]
#     if h_method == "ALL":
#         h_method = np.random.choice(["HDA", "HBA", "HCA", "HPRA"])

#     method = np.random.choice(["FINDER", h_method])

#     if method == "FINDER":
#         dqn = FINDER()
#         val, sol = dqn.Evaluate(f"tmpG/g_{cnt-1}", model_file)
#         node = sol[0]
#     else: # use HXA
#         node = hxa(G, h_method)

#     time.sleep(1)

#     reward = getRobustness(g, G, int(node))
#     write_gml(G, "./tmpG/", f"g_{cnt}")

#     return method, int(node), reward

def main(dqn, model_file, h_method):
    score_lst = []
    for i in trange(100):
        g = read_gml(data_dir="./data/ba/", file_name=f"g_{i}")
        G = g.copy()
        write_gml(G, "./tmpG/", "g_0")
        cnt = 1

        reward_lst = []
        while (nx.number_of_edges(G)>0):

            if h_method == "ALL":
                h_method = np.random.choice(["HDA", "HBA", "HCA", "HPRA"])

            method = np.random.choice(["FINDER", h_method])

            if method == "FINDER":
                _, sol = dqn.Evaluate(f"tmpG/g_{cnt-1}", model_file)
                node = sol[0]
            else: # use HXA
                node = hxa(G, h_method)

            reward = getRobustness(g, G, node)
            reward_lst.append(reward)

            node_mapping = {
                node: cnt for cnt, node in enumerate(G.nodes())
            }
            G = nx.relabel_nodes(G, node_mapping)

            write_gml(G, "./tmpG/", f"g_{cnt}")

            cnt += 1

        for _ in range(g.number_of_nodes() - len(reward_lst)):
            GCCsize = len(max(nx.connected_components(g), key=len))
            reward_lst.append(1 - 1/GCCsize)
        reward_lst = (np.cumsum(reward_lst) / g.number_of_nodes()).tolist()
        score = reward_lst[-1]
        score_lst.append(score)
    return score_lst
    



if __name__=="__main__":
    dqn = FINDER()
    model_file = './models/Model_barabasi_albert/nrange_200_200_iter_154500.ckpt'
    for h_method in ["HDA", "HBA", "HCA", "HPRA", "ALL"]:
        score_lst = main(dqn, model_file, h_method)
        print(h_method, np.mean(score_lst))
