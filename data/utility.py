from typing import Type
import networkx as nx
import numpy as np

def star_genertor(n=20) -> Type[nx.classes.graph.Graph]:
    return nx.star_graph(n)

def complete_genertor(n=20) -> Type[nx.classes.graph.Graph]:
    return nx.complete_graph(n)

def ba_generator(n=20, m: int=2) -> Type[nx.classes.graph.Graph]:
    return nx.barabasi_albert_graph(n ,m)

def covert_generator(m=20, density: int=0.1):
    generator = CovertGenerator(min_n, max_n, density)
    generator.simulate()
    return generator.G

def dark_generator(min_n: int=20, max_n: int=30, density: int=0.1):
    generator = DarkGenerator(min_n, max_n, density)
    generator.simulate()
    return generator.G

def read_gml(data_dir: str, file_name: str) -> Type[nx.classes.graph.Graph]:
    G = nx.read_gml(data_dir + file_name)
    return nx.relabel_nodes(G, lambda x: int(x))

def write_gml(G: Type[nx.classes.graph.Graph], data_dir: str, file_name: str) -> None:
    nx.write_gml(G, data_dir+file_name)

def getRobustness(full_g: Type[nx.classes.graph.Graph], G: Type[nx.classes.graph.Graph], sol: int):    
    fullGCCsize = len(max(nx.connected_components(full_g), key=len))

    G.remove_node(int(sol))

    remainGCC = nx.connected_components(G)

    if len(list(remainGCC)) != 0:
        remainGCCsize = len(max(nx.connected_components(G), key=len))
    else:
        remainGCCsize = 1
    return 1 - remainGCCsize/fullGCCsize

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

def HXA(g: Type[nx.classes.graph.Graph], method: str) -> (list, list):
    # 'HDA', 'HBA', 'HCA', 'HPRA'
    assert method in ['HDA', 'HBA', 'HCA', 'HPRA']
    sol, reward = [], []
    G = g.copy()
    while (nx.number_of_nodes(G)>0):
        node = hxa(G, method)
        
        reward.append(getRobustness(g, G, int(node)))
        sol.append(int(node))
    
    return sol, reward


# def HXA(g: Type[nx.classes.graph.Graph], method: str) -> (list, list):
#     # 'HDA', 'HBA', 'HCA', 'HPRA'
#     sol, reward = [], []
#     G = g.copy()
#     while (nx.number_of_nodes(G)>0):
#         if method == 'HDA':
#             dc = nx.degree_centrality(G)
#         elif method == 'HBA':
#             dc = nx.betweenness_centrality(G)
#         elif method == 'HCA':
#             dc = nx.closeness_centrality(G)
#         elif method == 'HPRA':
#             dc = nx.pagerank(G)
#         keys = list(dc.keys())
#         values = list(dc.values())
#         maxTag = np.argmax(values)
#         node = keys[maxTag]
        
#         reward.append(getRobustness(g, G, int(node)))
#         sol.append(int(node))
    
#     return sol, reward