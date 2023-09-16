import sys, os, json
sys.path.append(os.path.dirname(__file__) + os.sep + './')
from FINDER import FINDER
from seeker_game.utility import read_sample
import networkx as nx

dqn = FINDER()

def relabel_G(G):
    map_dct = {node: idx for idx, node in enumerate(G.nodes())}
    reverse_map_dct = {val: key for key, val in map_dct.items()}
    return nx.relabel_nodes(G, map_dct, copy=True), reverse_map_dct

playing_graph = "HAMBURG_TIE_YEAR"
model_file = f'./models/Model_EMPIRICAL/{playing_graph}.ckpt'
g = read_sample(playing_graph)
g.remove_node(7)

print(g.nodes())
g, map_dct = relabel_G(g)
print(g.nodes())

_, sol = dqn.Evaluate(g, model_file)
print(sol)
# print(map_dct)
print([map_dct[s] for s in sol])

# [7, 8, 11, 16, 4, 6, 3, 17, 0, 1, 26, 19, 23, 9, 25, 22]
# [7, 8, 11, 16, 4, 6, 3, 17, 0, 1, 26, 19, 23, 9, 25, 22]