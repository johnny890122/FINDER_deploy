import networkx as nx
import numpy as np
import pygsheets, json, requests
from networkx.readwrite import json_graph
from typing import Type
from dotenv import load_dotenv
from github import Github
import os
from io import BytesIO

def copy_G(source_G, target_G):
    for n in source_G.nodes():
        target_G.add_node(n)
    for e in source_G.edges():
        target_G.add_edge(e[0], e[1])

def fetch_gml(github_file_path):
    github_user = "johnny890122"
    github_repo = "FINDER_deploy"
    github_branch = "seeker_game"
    load_dotenv()
    git_auth = os.getenv("git_auth")

    # API URL to fetch the file content
    api_url = f"https://api.github.com/repos/{github_user}/{github_repo}/contents/{github_file_path}?ref={github_branch}"

    # Headers for authentication using the PAT
    headers = {
        "Authorization": f"token {git_auth}",
        "Accept": "application/vnd.github.v3.raw"  # To get the raw content of the file
    }

    # Make a GET request to fetch the file content
    response = requests.get(api_url, headers=headers)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Print the content of the file
        G = nx.read_gml(BytesIO(response.content))
        map_dct = {node: int(idx) for idx, node in enumerate(G.nodes())}
        print("downlaod successfully")
    else:
        print(f"Failed to fetch file. Status code: {response.status_code}")
    return nx.relabel_nodes(G, map_dct, copy=True)

def upload_gml(file_path, file_content):
    github_user = os.environ.get("github_user")
    
    github_repo = os.environ.get("github_repo")
    github_branch = os.environ.get("github_branch")
    git_auth = os.environ.get("git_auth")
    print(github_user, github_branch, github_repo, git_auth)

    g = Github(git_auth)
    repo = g.get_user(github_user).get_repo(github_repo)

    branch = repo.get_branch(github_branch)
    try:
        # Get the existing file if it exists
        file = repo.get_contents(file_path, ref=branch.name)
        
        # Update the existing file
        repo.update_file(
            file.path,
            "Update file content",
            file_content,
            file.sha,
            branch=branch.name
        )

        print(f"File '{file_path}' updated successfully.")
    except Exception as e:
        # If the file does not exist, create a new one
        repo.create_file(
            file_path,
            "Create file",
            file_content,
            branch=branch.name
        )
        
        print(f"File '{file_path}' created successfully.")

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

