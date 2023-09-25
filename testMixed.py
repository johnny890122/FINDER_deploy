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
from io import BytesIO
from networkx.readwrite import json_graph

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

def read_gml(data_dir: str, file_name: str) -> Type[nx.classes.graph.Graph]:
    G = nx.read_gml(data_dir + file_name, destringizer=int)
    map_dct = {node: int(idx) for idx, node in enumerate(G.nodes())}
    return nx.relabel_nodes(G, map_dct)

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

def main(dqn, g_name, h_method):

    g = read_gml(data_dir="./empirical_data/", file_name=f"{g_name}.gml")
    G = g.copy()

    reward_lst = []

    if method == "FINDER":
        content = BytesIO(convert_to_FINDER_format(G).encode('utf-8'))
        model_file = f"./models/Model_EMPIRICAL/{g_name}.ckpt"
        _, sol = dqn.Evaluate(content, model_file)
        for node in sol:
            reward = getRobustness(g, G, node)
            reward_lst.append(reward)

    while (nx.number_of_edges(G)>0):
        if method == "RAND":

            node = np.random.choice(list(G.nodes()))
            reward = getRobustness(g, G, node)
            reward_lst.append(reward)

        elif method in ["HDA", "HBA", "HCA", "HPRA"]: # use HXA
            node = hxa(G, h_method)
            reward = getRobustness(g, G, node)
            reward_lst.append(reward)
    
    for _ in range(g.number_of_nodes() - len(reward_lst)):
        GCCsize = len(max(nx.connected_components(g), key=len))
        reward_lst.append(1 - 1/GCCsize)
    
    reward_lst = (np.cumsum(reward_lst) / g.number_of_nodes()).tolist()

    return reward_lst[-1]    

if __name__=="__main__":
    dqn = FINDER()
    graphs_name = ["DOMESTICTERRORWEB", "HEROIN_DEALING", "MAIL", "SWINGERS_club", "HAMBURG_TIE_YEAR", "suicide",]

    for g_name in graphs_name:
        print(g_name)
        for method in ["RAND"]:
            score_lst = []
            for i in range(100):
                score = main(dqn, g_name, method)
                score_lst.append(score)
            print(method, np.mean(score_lst))

        print("="*20)
