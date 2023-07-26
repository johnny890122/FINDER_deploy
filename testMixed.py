#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys,os
sys.path.append(os.path.dirname(__file__) + os.sep + '../')
from FINDER import FINDER
from tqdm import tqdm, trange
import networkx as nx
from typing import Type
import numpy as np
import pandas as pd
import json, time

def write_gml(G: Type[nx.classes.graph.Graph], data_dir: str, file_name: str) -> None:
    nx.write_gml(G, data_dir+file_name)

def read_gml(data_dir: str, file_name: str) -> Type[nx.classes.graph.Graph]:
    G = nx.read_gml(data_dir + file_name)
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

def hxa_finder_mixed(g, G, h_method, cnt):
    assert h_method in ["HDA", "HBA", "HCA", "HPRA", "ALL"]
    if h_method == "ALL":
        h_method = np.random.choice(["HDA", "HBA", "HCA", "HPRA"])
    
    method = np.random.choice(["FINDER", h_method])            
    
    if method == "FINDER":
        dqn = FINDER()
        model_file = './models/Model_barabasi_albert/nrange_200_200_iter_154500.ckpt'
        _, sol = dqn.Evaluate(f"./tmpG/g_{cnt-1}", model_file)
        node = sol[0]
    else: # use HXA
        node = hxa(G, h_method)
    
    time.sleep(1)

    reward = getRobustness(g, G, int(node))
    write_gml(G, "./tmpG/", f"g_{cnt}")
    
    return method, int(node), reward

def main():
    h_method = "HDA"
    dqn = FINDER()
    model_file = './models/Model_barabasi_albert/nrange_200_200_iter_154500.ckpt'
    for i in trange(100):
        g = read_gml(data_dir="./data/ba/", file_name=f"g_{i}")
        G = g.copy()
        write_gml(G, "./tmpG/", "g_0")
        cnt = 1
        while (nx.number_of_nodes(G)>0):
            method, node, reward = hxa_finder_mixed(g, G, h_method, cnt)
            cnt += 1
            print(nx.number_of_nodes(G))
            print(method, node, reward)
        break
    

if __name__=="__main__":
    main()
