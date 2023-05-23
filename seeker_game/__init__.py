from otree.api import *
import sys, os, random, json, io
import networkx as nx
import numpy as np

from seeker_game.utility import get_current_graph, G_links, G_nodes, to_list, remove_node_and_neighbor, getRobustness, generate_ba_graph_with_density, node_centrality_criteria

doc = """
human seeker 單機版 
"""

class C(BaseConstants):
    NAME_IN_URL = 'seeker_game'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 20 # TODO: 理論上，設定成一個很大的數字即可（size+1）。

class Subsession(BaseSubsession):
    pass

class Group(BaseGroup):
    G = nx.Graph()
    G_seeker_practice = nx.Graph()

class Player(BasePlayer):
    # 實驗的參數
    cons = C()
    role_type = models.StringField(initial="seeker")

    # seeker 需要的 field
    seeker_payoff = models.FloatField(initial=0)
    confirm = models.BooleanField()
    sub_practice_end = models.BooleanField(initial=False)

    # Graph 需要的 field 
    num_node = models.IntegerField(initial=-1)
    num_edge = models.IntegerField(initial=-1)
    to_be_removed = models.IntegerField(initial=-1)
    num_node_removed = models.IntegerField(initial=-1)
    num_edge_removed = models.IntegerField(initial=-1)
    node_remain = models.IntegerField(initial=-1)
    edge_remain = models.IntegerField(initial=-1)

def creating_session(subsession: Subsession):
    is_practice = subsession.session.config['practice']
    generating_process = subsession.session.config["generating_process"]
    # size = subsession.session.config["size"]
    # density = subsession.session.config["density"]
    graph_config = subsession.session.config["graph_config"]

    assert graph_config in ["size_low", "size_high", "density_low", "density_high"]

    # 初始化 graph
    if generating_process == "ba_graph":
        # initial_G = generate_ba_graph_with_density(n=size, density=density)
        initial_G = nx.read_adjlist("input/ba/{}_{}.txt".format(graph_config, random.randint(0, 4)))
        size = len(initial_G.nodes())
        initial_G = nx.relabel_nodes(initial_G, lambda x: int(x) + 2)

    elif generating_process == "covert":
        file_name = 'input/covert/covert_test.txt'
        initial_G = nx.read_adjlist(file_name)
        initial_G = nx.relabel_nodes(initial_G, lambda x: x + 2)


    elif generating_process == "dark":
        file_name = 'input/dark/dark_test.txt'
        initial_G = nx.read_adjlist(file_name)
        initial_G = nx.relabel_nodes(initial_G, lambda x: x + 2)
    else:
        raise NotImplementedError("{} is not implemented.".format(generating_process))

    for player in subsession.get_players():
        player.num_node = size

        if player.round_number == 1:
            G = subsession.get_groups()[0].G_seeker_practice if is_practice else subsession.get_groups()[0].G
            for n in initial_G.nodes():
                G.add_node(n)
            for e in initial_G.edges():
                G.add_edge(e[0], e[1])

# Seeker 破壞的頁面
class Seeker_dismantle(Page):
    form_model = 'player'
    form_fields = ['to_be_removed']
    
    @staticmethod
    def is_displayed(player: Player):
        G = get_current_graph(player)
        if len(G.nodes()) != 0:
            return True
        return False

    @staticmethod
    def vars_for_template(player: Player):
        G = get_current_graph(player)        
        centrality = node_centrality_criteria(G)

        return {
            "graph_config": player.session.config['graph_config'],  
            "practice": int(player.session.config['practice']), 
            "nodes": G_nodes(G), 
            "highest_degree_id": centrality["degree"],
            "highest_closeness_id": centrality["closeness"],
            "highest_betweenness_id": centrality["betweenness"],
            "highest_page_rank_id": centrality["page_rank"], 
            "links": G_links(G), 
            "which_round": player.round_number,
            "density": nx.density(G), 
        }

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        G = get_current_graph(player)

        # 計算 reward
        player.seeker_payoff = getRobustness(G, player.to_be_removed)
        player.num_node = len(G.nodes())
        player.num_edge = len(G.edges())
        
        G = remove_node_and_neighbor(player, G)
        
        player.node_remain = len(G.nodes())
        player.edge_remain = len(G.edges())
        edge_remain = len(G.edges())

        player.num_node_removed = player.num_node - player.node_remain

# Seeker 確認該回合的破壞成果
class Seeker_confirm(Page):
    @staticmethod
    def is_displayed(player: Player):
        G = get_current_graph(player)
        if len(G.nodes()) > 0:
            return True
        return False

    @staticmethod
    def vars_for_template(player: Player):
        num_past_practice_round = 0
        if player.session.config['practice']:
            for p in player.in_previous_rounds(): 
                if p.sub_practice_end:
                    num_past_practice_round = p.round_number

        # Remaining node
        node_plot = [[0, player.in_round(1).num_node]]
        for n in range(1, player.round_number+1):
            node_plot.append([n, player.in_round(n).node_remain])

        # Accumulate payoff
        payoff = [0] + [p.seeker_payoff for p in player.in_previous_rounds()] + [player.seeker_payoff]
        accum_payoff = np.add.accumulate(payoff)
        payoff_plot = [[i, p] for (i, p) in enumerate(accum_payoff)]

        # Finder dismantle history
        # FIXIT 
        node_plot_finder = np.loadtxt("input/covert/covert_test_finder.txt", delimiter=",").tolist()
        # print(hist)
        payoff_finder = np.loadtxt("input/covert/covert_test_finder_payoff.txt", delimiter=",").tolist()

        return {
            "current_size": len(player.group.G_seeker_practice) if player.session.config['practice'] else len(player.group.G), 
            "original_size": player.in_round(1).num_node, 
            "practice": int(player.session.config['practice']),
            "node_plot_finder": node_plot_finder,
            "payoff_finder": payoff_finder,  
            "node_line_plot": node_plot, 
            "payoff_line_plot": payoff_plot, 
            "which_round": player.round_number, 
            "caught": player.to_be_removed, 
            "num_node_removed": player.num_node_removed,
            "node_remain": player.node_remain, 
        }

page_sequence = [Seeker_dismantle, Seeker_confirm]

