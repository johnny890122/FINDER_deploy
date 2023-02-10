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
    G = nx.Graph() # 所有玩家在畫面中看到的 graph

# 在有 human seeker 的情況下，P1 為 seeker
class Player(BasePlayer):
    # 實驗的參數
    cons = C()
    original_size = models.IntegerField()
    role_type = models.StringField()

    # seeker 需要的 field
    to_be_removed = models.IntegerField(
        label= "您選擇的節點為："
    )
    num_removed = models.IntegerField(initial=-1)
    node_remain = models.IntegerField(initial=-1)
    edge_remain = models.IntegerField(initial=-1)
    confirm = models.BooleanField(
        label = "確定要刪除這個節點嗎？"
    )

    # hider 需要的 field
    invitation = models.StringField(initial="")
    survive = models.BooleanField(initial=False)

def creating_session(subsession: Subsession):

    # 若有 human seeker，|G| = N-1，反之，|G| = N。
    group = subsession.get_groups()[0]
    players = subsession.get_players()
    if group.session.config['seeker'] == 'human':
        for n in range(2, len(players)+1):
            group.G.add_node(n)
    else:
        for n in range(1, len(players)+1):
            group.G.add_node(n)

    # 初始化每個 player 的 role，以及其他 filed。
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
            

# Utility: 用來將 G 的 link 轉換成前端接受的格式
def G_links(G):
    links = []
    for (i, j) in G.edges():
        links.append({"source": i, "target": j, 'dashed': "False"})
        links.append({"source": j, "target": i, 'dashed': "False"})

    return links

# Utility: 用來將 G 的 node attributes 轉換成前端接受的格式
def G_nodes(G, player):
    # node degree
    degree = {node: degree for (node, degree) in G.degree}

    # node geo-distance
    geo_dist_dct = { 
        key: np.sum(list(val.values()))
            for key, val in dict(nx.shortest_path_length(G)).items()
    }
    
    # player 和其他玩家之間共同鄰居的數量
    if player.role_type == 'hider':
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

# Utility
def to_list(string):
    if string == "":
        return []
    return [int(n) for n in string.split(",")]

# PAGES: 
class Hider_build(Page):
    form_model = 'player'
    form_fields = ['invitation']

    # 此畫面只顯示給：Hider & 上回合 survive
    @staticmethod
    def is_displayed(player: Player):
        if player.role_type == 'hider':
            if player.round_number == 1:
                return True
            else:
                return player.in_round(player.round_number-1).survive
        return False

    # 傳送前端需要的資訊
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
        # 這裡是為了測試方便，隨機向其他玩家發出邀請。
        if player.session.config['seeker'] == 'human':
            start_index = 2
        else:
            start_index = 1

        invitation = []
        for i in range(start_index, player.in_round(1).original_size+2):
            if i != player.id_in_group and random.random() < 3/4:
                invitation.append(str(i))

        player.invitation = ",".join(invitation)



class Hider_wait_matching(WaitPage):
    title_text = "等待 hider 配對"
    body_text = ""


    def is_displayed(player: Player):
        if len(player.group.G.nodes()) != 0 and player.role_type == 'seeker':
            return True
        else:
            if player.round_number == 1:
                return True
            else:
                return player.in_round(player.round_number-1).survive
        return False

    # 當所有人到齊，表示所有 hider 完成 build，在此進行配對。
    @staticmethod
    def after_all_players_arrive(group: Group):
        for player in group.get_players():
            if player.role_type == 'hider':
                if player.round_number != 1:
                    if not player.in_round(player.round_number-1).survive:
                        continue
                for n in to_list(player.invitation):
                    invitation = to_list(group.get_player_by_id(n).invitation)
                    if player.id_in_group in invitation:
                        group.G.add_edge(player.id_in_group, n)

# Hider 配對後的結果
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


# Seeker 破壞的頁面
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
        player.to_be_removed = random.choice(list(player.group.G.nodes()))
        removed = [n for n in player.group.G.neighbors(player.to_be_removed)]
        removed.append(player.to_be_removed)

        player.num_removed = len(removed)
        player.original_size = len(player.group.G.nodes())
        for n in removed:
            player.group.G.remove_node(n)

        player.node_remain = len(player.group.G.nodes())

        for p in player.group.get_players():
            if p.id_in_group in player.group.G.nodes():
                p.survive = True
            else:
                p.survive = False

class Wait_dismantle(WaitPage):
    title_text = "等待 seeker dismantle"
    body_text = ""
    def is_displayed(player: Player):
        if player.role_type == 'hider':
            if player.round_number == 1:
                return True
            else:
                return player.in_round(player.round_number-1).survive
        return False

# Seeker 確認該回合的破壞成果
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
        node_line_plot = [[0, player.in_round(1).original_size]]
        for (x, p) in zip(range(1, player.round_number), player.in_previous_rounds()):
            node_line_plot.append([x, p.node_remain])

        node_line_plot.append([player.round_number, player.node_remain])

        return {
            "node_line_plot": node_line_plot, 
            "which_round": player.round_number, 
            "caught": player.to_be_removed, 
            "num_removed": player.num_removed,
            "node_remain": player.node_remain, 
        }

# Hider 確認幾是否存活
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

