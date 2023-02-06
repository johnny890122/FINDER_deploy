from otree.api import *
import sys,os
import random, json
import networkx as nx
import io
import numpy as np
import random

doc = """
Your app description
"""

class C(BaseConstants):
    NAME_IN_URL = 'actual_rounds'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 20 # 理論上，設定成一個很大的數字即可。或是試試看動態決定。

class Subsession(BaseSubsession):
    pass

class Group(BaseGroup):
    # G = nx.Graph()
    G = nx.path_graph(3)

# 在有 human seeker 的情況下，P1 為 seeker
class Player(BasePlayer):
    cons = C()
    to_be_removed = models.IntegerField(
        initial=-1,
        label= "您選擇的節點為："
    )
    num_removed = models.IntegerField(initial=-1)
    num_remain = models.IntegerField(initial=-1)
    confirm = models.BooleanField(
        label = "確定要刪除這個節點嗎？"
    )

    original_size = models.IntegerField()
    role_type = models.StringField()
    invitation = models.StringField(initial="-1")
    survive = models.BooleanField(initial=False)
    

def creating_session(subsession: Subsession):

    group = subsession.get_groups()[0]
    players = subsession.get_players()

    if group.session.config['seeker'] == 'human':
        for n in range(2, len(players)+1):
            group.G.add_node(n)
    else:
        for n in range(1, len(players)+1):
            group.G.add_node(n)

    for player in players:
        if player.round_number == 1:
            if player.session.config['seeker'] == 'human':
                player.original_size = len(players) - 1

                if player.id_in_group == 1:
                    player.role_type = 'seeker'
                    player.invitation = "1"
                else:
                    player.role_type = 'hider'
            else:
                player.original_size = len(players)
                player.role_type = 'hider'
        else:

            player.role_type = player.in_round(1).role_type
            if player.role_type == 'seeker':
                player.invitation = "1"
            

def G_links(G):
    links = []
    for (i, j) in G.edges():
        links.append({"source": i, "target": j})
        links.append({"source": j, "target": i})

    return links

def G_nodes(G, player):
    degree = {node: degree for (node, degree) in G.degree}

    # 每個 node 的 geo-distance
    geo_dist_dct = { 
        key: np.sum(list(val.values()))
            for key, val in dict(nx.shortest_path_length(G)).items()
    }
    
    if player.role_type == 'hider':
        # player 和其他玩家之間共同鄰居的數量
        common_neighbor = dict()
        for n in G.nodes():
            common_neighbor[n] = len(list(nx.common_neighbors(G, player.id_in_group, n)))

    nodes = []
    for i in G.nodes():
        if player.role_type == 'hider':
            nodes.append({"id": i, "degree": degree[i], "geo_d": geo_dist_dct[i], "common_neighbor": common_neighbor[i]})
        else:
            nodes.append({"id": i, "degree": degree[i], "geo_d": geo_dist_dct[i]})
    return nodes

def to_list(string):
    if string == "":
        return []
    return [int(n) for n in string.split(",")]

# PAGES
class Hider_build(Page):
    form_model = 'player'
    form_fields = ['invitation']
    @staticmethod
    def is_displayed(player: Player):
        if player.role_type == 'hider':
            if player.round_number == 1:
                return True
            else:
                return player.in_round(player.round_number-1).survive
        return False

    @staticmethod
    def vars_for_template(player: Player):
        return {
            "nodes": G_nodes(player.group.G, player),
            "neighbors": list(player.group.G.neighbors(player.id_in_group)), 
            "links": G_links(player.group.G),
            "which_round": player.round_number,
            "me": player.id_in_group, 
        }
    @staticmethod
    def before_next_page(player: Player, timeout_happened):

        # for test: 向所有人發出邀請
        if player.session.config['seeker'] == 'human':
            start_index = 2
        else:
            start_index = 1

        invitation = []
        for i in range(start_index, player.in_round(1).original_size+2):
            if i != player.id_in_group and random.random() > 15/16:
                invitation.append(str(i))

        player.invitation = ",".join(invitation)


class Hider_wait_matching(WaitPage):
    title_text = "等待 hider 配對"
    body_text = "Custom body text"

    def is_displayed(player: Player):
        if len(player.group.G.nodes()) != 0 and player.role_type == 'seeker':
            return True
        else:
            if player.round_number == 1:
                return True
            else:
                return player.in_round(player.round_number-1).survive
        return False

    @staticmethod
    def after_all_players_arrive(group: Group):
        for player in group.get_players():
            if player.role_type == 'hider':
                if player.round_number != 1:
                    print(player.round_number, player.in_round(player.round_number-1))
                    if not player.in_round(player.round_number-1).survive:
                        continue
                for n in to_list(player.invitation):
                    invitation = to_list(group.get_player_by_id(n).invitation)
                    if player.id_in_group in invitation:
                        group.G.add_edge(player.id_in_group, n)

        print(group.G)

class Hider_matched(Page):

    @staticmethod
    def is_displayed(player: Player):
        if player.role_type == 'hider':
            if player.round_number == 1:
                return True
            else:
                print("wait", player.in_round(player.round_number-1))
                return player.in_round(player.round_number-1).survive
        return False

    @staticmethod
    def vars_for_template(player: Player):
        return {
            "nodes": G_nodes(player.group.G, player),
            "links": G_links(player.group.G),
            "which_round": player.round_number,
            "me": player.id_in_group, 
        }


class Seeker_dismantle(Page):
    form_model = 'player'
    form_fields = ['to_be_removed']

    @staticmethod
    def is_displayed(player: Player):
        if len(player.group.G.nodes()) != 0 and player.role_type == 'seeker':
            return True
        return False

    @staticmethod
    def vars_for_template(player: Player):
        return {
            "nodes": G_nodes(player.group.G, player),
            "links": G_links(player.group.G), 
            "which_round": player.round_number,
        }

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        print(list(player.group.G.nodes()))
        player.to_be_removed = random.choice(list(player.group.G.nodes()))
        print("G", player.group.G.nodes(), player.to_be_removed)
        removed = [n for n in player.group.G.neighbors(player.to_be_removed)]
        removed.append(player.to_be_removed)

        player.num_removed = len(removed)
        player.original_size = len(player.group.G.nodes())
        for n in removed:
            player.group.G.remove_node(n)

        player.num_remain = len(player.group.G.nodes())

        for p in player.group.get_players():
            if p.id_in_group in player.group.G.nodes():
                p.survive = True
            else:
                p.survive = False

class Wait_dismantle(WaitPage):
    title_text = "等待 seeker dismantle"
    body_text = "Custom body text"
    def is_displayed(player: Player):
        if player.role_type == 'hider':
            if player.round_number == 1:
                return True
            else:
                return player.in_round(player.round_number-1).survive
        return False

class Seeker_confirm(Page):
    @staticmethod
    def is_displayed(player: Player):
        if player.role_type == 'seeker':
            if player.round_number == 1:
                return True
            else:
                hiders = player.in_round(player.round_number-1).get_others_in_group()
                for hider in hiders:
                    if hider.survive:
                        return True
        return False

    @staticmethod
    def vars_for_template(player: Player):
        line_plot = [[0, player.in_round(1).original_size]]
        for (x, p) in zip(range(1, player.round_number), player.in_previous_rounds()):
            line_plot.append([x, p.num_remain])

        line_plot.append([player.round_number, player.num_remain])

        return {
            "line_plot": line_plot, 
            "which_round": player.round_number, 
            "caught": player.to_be_removed, 
            "num_removed": player.num_removed,
            "num_remain": player.num_remain, 
        }

class Hider_confirm(Page):
    @staticmethod
    def is_displayed(player: Player):
        if player.role_type == 'hider':
            return player.survive
        return False

    @staticmethod
    def vars_for_template(player: Player):
        return {
            "which_round": player.round_number, 
            "survive": player.survive, 
        }

page_sequence = [Hider_build, Hider_wait_matching, Hider_matched, Seeker_dismantle, Wait_dismantle, Seeker_confirm, Hider_confirm]

