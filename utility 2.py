import random, json
import networkx as nx
from networkx.readwrite import json_graph
import io

import sys,os
# sys.path.append(os.path.dirname(__file__) + os.sep + '../')
# from FINDER import FINDER

def finder():
    dqn = FINDER()
    data_test_path = '../data/synthetic/'
    data_test_name = 'test'
    model_file = './models/nrange_30_50_iter_78000.ckpt'

    data_test = data_test_path + data_test_name
    val, sol = dqn.Evaluate(data_test, model_file)

    return val, sol

def jsFormatConverter(dct):
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

def genRandomGraph(file_name):
	G = nx.read_edgelist(f"input/ba_graph/{file_name}")
	data = json_graph.node_link_data(G)

	with io.open(f'./data/synthetic/test/{file_name}', 'w', encoding='utf8') as outfile:
		str_ = jsFormatConverter(data)
		outfile.write(str_)

if __name__ == '__main__':
	for file in os.listdir("input/ba_graph/"):
		genRandomGraph(file)
