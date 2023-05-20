from otree.api import *
import sys, os, random, json, io
import networkx as nx
import numpy as np

from seeker_game.utility import G_links, G_nodes, to_list, remove_from_G, getRobustness, generate_ba_graph_with_density

doc = """
human seeker 單機版 
"""

class C(BaseConstants):
    NAME_IN_URL = 'seeker_game'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 20 # 理論上，設定成一個很大的數字即可。或是試試看動態決定。
    c = 0.1
    delta = 0.9

class Subsession(BaseSubsession):
    pass

class Group(BaseGroup):
    G = nx.Graph()
    G_seeker_practice = nx.Graph()

# 在有 human seeker 的情況下，P1 為 seeker
class Player(BasePlayer):
    # 實驗的參數
    cons = C()
    original_size = models.IntegerField()
    role_type = models.StringField(initial="seeker")

    # seeker 需要的 field
    to_be_removed = models.IntegerField(
        initial=-1, 
    )
    num_removed = models.IntegerField(initial=-1)
    node_remain = models.IntegerField(initial=-1)
    edge_remain = models.IntegerField(initial=-1)
    confirm = models.BooleanField()

    sub_practice_end = models.BooleanField(initial=False)
    seeker_payoff = models.FloatField(initial=0)

    # hider 需要的 field
    # invitation = models.StringField(initial="", label="您選擇的節點為：")
    survive = models.BooleanField(initial=False)

    G_nodes = models.StringField()
    # hider_payoff = models.FloatField()

def creating_session(subsession: Subsession):
    is_practice = subsession.session.config['practice']
    num_demo_participants = subsession.session.config['num_demo_participants']
    players = subsession.get_players()

    # # grouping
    # if is_practice and is_human_seeker and is_human_hider:
    #     group_matrix = [[1], [i for i in range(2, num_demo_participants+1)]]
    # else:
    #     group_matrix = [[i for i in range(1, num_demo_participants+1)]]
    # subsession.set_group_matrix(group_matrix)

    # player role。
    for player in players:
        player.invitation = str(player.id_in_group)

        if player.round_number == 1:
            player.original_size = player.session.config["size"]
        else:
            player.original_size = player.in_round(1).original_size

    # 初始化 graph
    if is_practice:
        if subsession.session.config["generating_process"]:
            G = generate_ba_graph_with_density(
                n=subsession.session.config["size"], 
                density=subsession.session.config["density"]
            )

            G = nx.relabel_nodes(G, lambda x: x + 2)
            for n in G.nodes():
                subsession.get_groups()[0].G.add_node(n)
            for e in G.edges():
                subsession.get_groups()[0].G.add_edge(e[0], e[1])

            G_seeker_practice = generate_ba_graph_with_density(
                n=subsession.session.config["size"], 
                density=subsession.session.config["density"]
            )

            G_seeker_practice = nx.relabel_nodes(G, lambda x: x + 2)
            for n in G_seeker_practice.nodes():
                subsession.get_groups()[0].G_seeker_practice.add_node(n)
            for e in G_seeker_practice.edges():
                subsession.get_groups()[0].G_seeker_practice.add_edge(e[0], e[1])
    else:
        # subsession.get_groups()[0].G = 
        G = generate_ba_graph_with_density(
            n=subsession.session.config["size"], 
            density=subsession.session.config["density"]
        )

        G = nx.relabel_nodes(G, lambda x: x + 2)
        for n in G.nodes():
            subsession.get_groups()[0].G.add_node(n)
        for e in G.edges():
            subsession.get_groups()[0].G.add_edge(e[0], e[1])

# Seeker 破壞的頁面
class Seeker_dismantle(Page):
    form_model = 'player'
    form_fields = ['to_be_removed']

    @staticmethod
    def is_displayed(player: Player):
        if player.session.config['practice']:
            G = player.group.G_seeker_practice
        else:
            G = player.group.G

        if len(G.nodes()) != 0:
            return True
        return False

    @staticmethod
    def vars_for_template(player: Player):
        if player.session.config['practice']:
            G = player.group.G_seeker_practice
        else:
            G = player.group.G

        num_past_practice_round = 0
        if player.session.config['practice']:
            for p in player.in_previous_rounds():
                if p.sub_practice_end:
                    num_past_practice_round = p.round_number

        return {
            "num_past_practice_round": num_past_practice_round, 
            "practice": int(player.session.config['practice']), 
            "nodes": G_nodes(G, player),
            "links": G_links(G), 
            "which_round": player.round_number - num_past_practice_round,
        }

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        # for test
        if player.session.config['practice']:
            G = player.group.G_seeker_practice
        else:
            G = player.group.G


        player.to_be_removed = random.choice(list(G.nodes()))

        # 計算 reward
        player.seeker_payoff = getRobustness(G, player.to_be_removed)

        remove_from_G(player, G)

        # if player.session.config['practice']:
        #     nodes = player.group.G_seeker_practice.nodes()

        #     for _ in range(random.randint(0, len(nodes))):
        #         try:
        #             [node1, node2] = random.sample(nodes, 2)
        #             player.group.G_seeker_practice.add_edge(node1, node2)
        #         except:
        #             pass

# Seeker 確認該回合的破壞成果
class Seeker_confirm(Page):
    @staticmethod
    def is_displayed(player: Player):
        if player.round_number == 1:
            return True
        else:
            hiders = player.in_round(player.round_number).get_others_in_group()
            if player.session.config['practice']:
                if len(player.group.G_seeker_practice,nodes()) > 0:
                    return True
            else:
                if len(player.group.G.nodes()) > 0: 
                    return True
        return False

    @staticmethod
    def vars_for_template(player: Player):
        num_past_practice_round = 0
        if player.session.config['practice']:
            for p in player.in_previous_rounds(): 
                if p.sub_practice_end:
                    num_past_practice_round = p.round_number

        node_line_plot = [[0, player.in_round(1).original_size]]
        for (x, p) in zip(
                range(1, player.round_number-num_past_practice_round), player.in_previous_rounds()[num_past_practice_round:]
            ):
            node_line_plot.append([x, p.node_remain])

        node_line_plot.append([player.round_number- num_past_practice_round, player.node_remain])

        payoff_line_plot = [[0, 0]]
        for (x, p) in zip(
                range(1, player.round_number-num_past_practice_round), player.in_previous_rounds()[num_past_practice_round:]
            ):
            payoff_line_plot.append([x, p.seeker_payoff])

        payoff_line_plot.append([player.round_number- num_past_practice_round, player.seeker_payoff])

        return {
            "num_past_practice_round": num_past_practice_round, 
            "current_size": len(player.group.G_seeker_practice) if player.session.config['practice'] else len(player.group.G), 
            "original_size": player.in_round(1).original_size, 
            "practice": int(player.session.config['practice']),
            "node_line_plot": node_line_plot, 
            "payoff_line_plot": payoff_line_plot, 
            "which_round": player.round_number - num_past_practice_round, 
            "caught": player.to_be_removed, 
            "num_removed": player.num_removed,
            "node_remain": player.node_remain, 
        }

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if player.session.config['practice']:
            if len(player.group.G_seeker_practice) == 0:
                player.sub_practice_end = True

        # if is_human_seeker and not is_human_hider and player.session.config['practice']:
        #     # TODO : "人工添加 edge"
        #     pass

        # if is_human_seeker and not is_human_hider and not player.session.config['practice']:
        #     # TODO : "人工添加 edge" 
        #     pass 

class Seeker_new_round(Page):
    @staticmethod
    def is_displayed(player: Player):
        if player.session.config['practice'] and len(player.group.G_seeker_practice.nodes) == 0:
            
            hiders = player.get_others_in_subsession()
            if len(hiders[0].group.G_hider_practice.nodes()) == 0:
                return False
            return True

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        for n in range(2, player.session.config['num_demo_participants']+1):
            player.group.G_seeker_practice.add_node(n)

    @staticmethod
    def vars_for_template(player: Player):
        hiders = player.get_others_in_subsession()

        return {
            "num_hiders": len(hiders[0].group.G_hider_practice.nodes())
        }


page_sequence = [Seeker_dismantle, Seeker_confirm, Seeker_new_round]

