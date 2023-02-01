from otree.api import *
import sys,os
import io
import networkx as nx
import numpy as np

doc = """
seeker 無法看到（P1 為 seeker）。
"""

class C(BaseConstants):
    NAME_IN_URL = 'my_game'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1
    COST = 10

class Subsession(BaseSubsession):
    def participation_fee(self):
        return self.session.config['participation_fee']

class Group(BaseGroup):
    pass

class Player(BasePlayer):
    # 受試者是否同意知情同意書

    role_type = models.StringField()
    approval = models.BooleanField(
        label= "請勾選以下選項：", 
        choices = [[True, "同意"], [False, "不同意"]], 
        initial = True
    )

    # participation_fee
    participate_fee = models.IntegerField()



def creating_session(subsession: Subsession):
    constant = C()
    for player in subsession.get_players():
        if player.session.config['seeker'] == 'human' and player.id_in_group == 1:
            player.role_type = 'seeker'
        else:
            player.role_type = 'hider'

        # 車馬費
        player.participate_fee = int(subsession.participation_fee())

def gen_model(num_nodes, num_edges):
    G = nx.barabasi_albert_graph(num_nodes, num_edges)
    return G

# 歡迎頁面
class Welcome(Page):
    @staticmethod
    def is_displayed(player: Player):
        if player.role_type == 'hider':
            return True
        return False
    form_model = 'player'
    form_fields = ['approval']


# Dropout，實驗到此結束。
class DropoutPage(Page):
    @staticmethod
    def is_displayed(player: Player):
        if not player.approval and player.role_type == 'hider':
            return True
        return False

    @staticmethod
    def vars_for_template(player: Player):
        return {
            "participation_fee": player.participate_fee, 
        }


class P1(Page):

    @staticmethod
    def is_displayed(player: Player):
        if player.role_type == 'hider':
            return True
        return False

class P2(Page):
    @staticmethod
    def is_displayed(player: Player):
        if player.role_type == 'hider':
            return True
        return False

class P3_1(Page):
    @staticmethod
    def is_displayed(player: Player):
        if player.role_type == 'hider':
            return True
        return False

    @staticmethod
    def vars_for_template(player: Player):
        constant = C()

        G = nx.Graph()

        players = player.session.config['num_demo_participants']
        if player.session.config['seeker'] == 'human':
            for n in range(2, players+1):
                G.add_node(n)
        else:
            for n in range(1, players+1):
                G.add_node(n)

        # 每個 node 的 degree
        degree = {node: degree for (node, degree) in G.degree}

        # player 和其他玩家之間共同鄰居的數量
        common_neighbor = dict()
        for n in G.nodes():
            if n != player.id_in_group:
                common_neighbor[n] = (list(nx.common_neighbors(G, player.id_in_group, n)))

        # 每個 node 的 geo-distance
        geo_dist_dct = { 
            key: np.sum(list(val.values()))
                for key, val in dict(nx.shortest_path_length(G)).items()
        }

        return {
            "degree": degree,
            "common_neighbor": common_neighbor,
            "geo_dist_dct": geo_dist_dct,
            "total_rounds": constant.NUM_ROUNDS, 
            "id": player.id_in_group
        }


class P3_2(Page):
    @staticmethod
    def is_displayed(player: Player):
        if player.role_type == 'hider':
            return True
        return False
    @staticmethod
    def vars_for_template(player: Player):
        constant = C()
        return {
            "cost": constant.COST, 
        }

class P3_4(Page):
    @staticmethod
    def is_displayed(player: Player):
        if player.role_type == 'hider':
            return True
        return False
    @staticmethod
    def vars_for_template(player: Player):

        G = nx.Graph()

        players = player.session.config['num_demo_participants']
        if player.session.config['seeker'] == 'human':
            for n in range(2, players+1):
                G.add_node(n)
        else:
            for n in range(1, players+1):
                G.add_node(n)

        # 每個 node 的 degree
        degree = {node: degree for (node, degree) in G.degree}

        # player 和其他玩家之間共同鄰居的數量
        common_neighbor = dict()
        for n in G.nodes():
            # if n != player.id_in_group:
            common_neighbor[n] = len(list(nx.common_neighbors(G, player.id_in_group, n)))

        # 每個 node 的 geo-distance
        geo_dist_dct = { 
            key: np.sum(list(val.values()))
                for key, val in dict(nx.shortest_path_length(G)).items()
        }

        links = []
        for (i, j) in G.edges():
            links.append({"source": i, "target": j})
            links.append({"source": j, "target": i})


        return {
            "me": player.id_in_group, 
            "nodes": [{
                    "id": i, 
                    "degree": degree[i], 
                    "geo_d": geo_dist_dct[i], 
                    "common_neighbor": common_neighbor[i]
            } for i in G.nodes()],

            "links": links
        }

class P4(Page):
    @staticmethod
    def is_displayed(player: Player):
        if player.role_type == 'hider':
            return True
        return False

class P5_1(Page):
    @staticmethod
    def is_displayed(player: Player):
        if player.role_type == 'hider':
            return True
        return False

class P5_2(Page):
    @staticmethod
    def is_displayed(player: Player):
        if player.role_type == 'hider':
            return True
        return False

class P6(Page):
    @staticmethod
    def is_displayed(player: Player):
        if player.role_type == 'hider':
            return True
        return False

class P7_1(Page):
    @staticmethod
    def is_displayed(player: Player):
        if player.role_type == 'hider':
            return True
        return False

class P7_2(Page):
    @staticmethod
    def is_displayed(player: Player):
        if player.role_type == 'hider':
            return True
        return False

page_sequence = [Welcome, DropoutPage, P1, P2, P3_1, P3_2, P3_4, P4, P5_1, P5_2, P6, P7_1, P7_2]

