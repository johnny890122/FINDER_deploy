import random, json
import networkx as nx
from networkx.readwrite import json_graph
import io


import requests
import pygsheets
from bs4 import BeautifulSoup
import pandas as pd

url = input("Enter the link: ")
soup = BeautifulSoup(requests.get(url).text, 'html.parser')

links_text = soup.find_all('a', attrs={"class": "participant-link"})
href_lst = [ link.attrs["href"] for link in links_text ]

df = pd.DataFrame({"id": [ i+1 for i in range(len(href_lst))], "link": href_lst})

auth_file = "finderlink-381806-aa232dd1eff5.json"
gc = pygsheets.authorize(service_file = auth_file)

try:
	# setting sheet
	sheet_url = "https://docs.google.com/spreadsheets/d/15t8MjE9mLmHGQDWzGGqEPiri402DKU1Ux8EX9XyxwcA/"
	sheet = gc.open_by_url(sheet_url)
	sheet.worksheet_by_title("link").clear()
	sheet.worksheet_by_title("link").set_dataframe(df, start = "A1")
	print("成功上傳連結！")
except:
	print("失敗！")



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

# if __name__ == '__main__':
# 	for file in os.listdir("input/ba_graph/"):
# 		genRandomGraph(file)
