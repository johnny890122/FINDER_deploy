from otree.api import *
import sys, os, random, json, io
import networkx as nx
import numpy as np

doc = """
Your app description
"""

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
    degree = {node: degree for (node, degree) in G.degree()}

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

def remove_from_G(player, G):
    removed = [n for n in G.neighbors(player.to_be_removed)]
    removed.append(player.to_be_removed)
    
    player.num_removed = len(removed)
    player.original_size = len(G.nodes())
    for n in removed:
        G.remove_node(n)
    player.node_remain = len(G.nodes())
    
    for p in player.group.get_players():
        if p.id_in_group in G.nodes():
            p.survive = True
        else:
            p.survive = False

def hider_payoff(player, G):
    constant =C()
    c = constant.c
    delta = constant.delta

    nodes = { node["id"]: {"degree": node["degree"], "geo_d": node["geo_d"]} for node in G_nodes(G, player) }

    payoff = 0
    geo_d = [node["geo_d"] for node in nodes.values()]
    for i, d in enumerate(geo_d):
        if d == 0 or i+1 == player.id_in_group:
            pass
        else:
            payoff += delta**d

    payoff -= c*nodes[player.id_in_group]["degree"]

    return payoff

def getRobustness(G, sol):
    G = G.copy()
    GCCsize = len(max(nx.connected_components(G), key=len))
    G.remove_node(sol)
    newGCCsize = len(max(nx.connected_components(G), key=len))

    print(GCCsize, newGCCsize)

    return (GCCsize - newGCCsize) / ((G.number_of_nodes() * G.number_of_nodes()))


def generate_ba_graph_with_density(n, density):
    total_possible_edges = (n * (n - 1)) / 2
    desired_num_edges = density * total_possible_edges
    avg_edges_per_node = round(desired_num_edges / n)
    m = max(avg_edges_per_node, 1)  # Ensure m is at least 1
    ba_graph = nx.barabasi_albert_graph(n, m)

    return ba_graph

class C(BaseConstants):
    NAME_IN_URL = 'actual_rounds'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 3 # 理論上，設定成一個很大的數字即可。或是試試看動態決定。
    c = 0.1
    delta = 0.9

class Subsession(BaseSubsession):
    pass

class Group(BaseGroup):
    G = nx.Graph()
    G_hider_practice = nx.Graph()
    G_seeker_practice = nx.Graph()
    now_survive = models.IntegerField(initial=0)

# 在有 human seeker 的情況下，P1 為 seeker
class Player(BasePlayer):
    # 實驗的參數
    cons = C()
    original_size = models.IntegerField()
    role_type = models.StringField()

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
    invitation = models.StringField(initial="", label="您選擇的節點為：")
    survive = models.BooleanField(initial=False)

    G_nodes = models.StringField()
    hider_payoff = models.FloatField()

def creating_session(subsession: Subsession):
    is_practice = subsession.session.config['practice']
    is_human_seeker = (subsession.session.config['seeker'] == 'human')
    is_human_hider = (subsession.session.config['hider'] == 'human')
    num_demo_participants = subsession.session.config['num_demo_participants']
    players = subsession.get_players()

    # grouping
    if is_practice and is_human_seeker and is_human_hider:
        group_matrix = [[1], [i for i in range(2, num_demo_participants+1)]]
    else:
        group_matrix = [[i for i in range(1, num_demo_participants+1)]]
    subsession.set_group_matrix(group_matrix)

    # player role。
    for player in players:
        player.invitation = str(player.id_in_group)

        if player.round_number == 1:
            if is_human_seeker and player.id_in_group == 1 and player.group.id_in_subsession == 1:
                player.role_type = 'seeker'
            else:
                player.role_type = 'hider'
            player.original_size = 20
        else:
            player.role_type = player.in_round(1).role_type
            player.original_size = player.in_round(1).original_size

    # 初始化 graph
    if is_practice:
        if is_human_seeker and is_human_hider:  
            for n in range(2, len(players)+1):
                subsession.get_groups()[0].G_seeker_practice.add_node(n)
            for n in range(1, len(players)):
                subsession.get_groups()[1].G_hider_practice.add_node(n)
        elif is_human_seeker and not is_human_hider:
            # for n in range(2, subsession.session.config["num_sythetic_hider"]+2):
            #     subsession.get_groups()[0].G_seeker_practice.add_node(n)
            if subsession.session.config["generating_process"]:
                G = generate_ba_graph_with_density(
                    n=subsession.session.config["num_sythetic_hider"], 
                    density=subsession.session.config["density"]
                )

                G = nx.relabel_nodes(G, lambda x: x + 2)
                for n in G.nodes():
                    subsession.get_groups()[0].G.add_node(n)
                for e in G.edges():
                    subsession.get_groups()[0].G.add_edge(e[0], e[1])

                G_seeker_practice = generate_ba_graph_with_density(
                    n=subsession.session.config["num_sythetic_hider"], 
                    density=subsession.session.config["density"]
                )

                G_seeker_practice = nx.relabel_nodes(G, lambda x: x + 2)
                for n in G_seeker_practice.nodes():
                    subsession.get_groups()[0].G_seeker_practice.add_node(n)
                for e in G_seeker_practice.edges():
                    subsession.get_groups()[0].G_seeker_practice.add_edge(e[0], e[1])

        elif not is_human_seeker and is_human_hider:
            for n in range(1, len(players)+1):
                subsession.get_groups()[0].G_hider_practice.add_node(n)
    else:
        if is_human_seeker and is_human_hider: 
            for n in range(2, len(players)+1):
                subsession.get_groups()[0].G.add_node(n)
        elif is_human_seeker and not is_human_hider:
            # subsession.get_groups()[0].G = 
            G = generate_ba_graph_with_density(
                n=subsession.session.config["num_sythetic_hider"], 
                density=subsession.session.config["density"]
            )

            G = nx.relabel_nodes(G, lambda x: x + 2)
            for n in G.nodes():
                subsession.get_groups()[0].G.add_node(n)
            for e in G.edges():
                subsession.get_groups()[0].G.add_edge(e[0], e[1])

        elif not is_human_seeker and is_human_hider:
            for n in range(1, len(players)+1):
                subsession.get_groups()[0].G.add_node(n)


class Hider_build(Page):
    form_model = 'player'
    form_fields = ['invitation']

    # 此畫面只顯示給：Hider & (上回合 survive or 第一回合）
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
        if player.session.config['practice']:
            G = player.group.G_hider_practice
        else:
            G = player.group.G

        return {
            "nodes": G_nodes(G, player),
            "neighbors": list(G.neighbors(player.id_in_group)), 
            "links": G_links(G),
            "which_round": player.round_number,
            "me": player.id_in_group
        }

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        # 這裡是為了測試方便，隨機向其他玩家發出邀請。
        if player.session.config['seeker'] == 'human':
            start_index = 2
        else:
            start_index = 1

        invitation = []
        for i in range(start_index, player.session.config["num_demo_participants"]):
            # if i != player.id_in_group and random.random() > 17/18:
            invitation.append(str(i))

        player.invitation = ",".join(invitation)

class Hider_wait_matching(WaitPage):
    title_text = "等待 hider 配對"
    body_text = ""

    def is_displayed(player: Player):
        if player.session.config['practice']:
            G = player.group.G_hider_practice
        else:
            G = player.group.G

        if len(G.nodes()) != 0 and player.role_type == 'seeker':
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
        if group.session.config['practice']:
            G = group.G_hider_practice
        else:
            G = group.G

        for player in group.get_players():
            if player.role_type == 'hider':
                if player.round_number != 1:
                    if not player.in_round(player.round_number-1).survive:
                        continue
                for n in to_list(player.invitation):
                    invitation = to_list(group.get_player_by_id(n).invitation)
                    if player.id_in_group in invitation and n != player.id_in_group:
                        G.add_edge(player.id_in_group, n)

                # 計算報酬
                if player.round_number == 1:
                    player.hider_payoff = hider_payoff(player, G)
                    print("round1")
                elif player.in_round(player.round_number-1).survive:
                    player.hider_payoff = hider_payoff(player, G)
                    print("survive")
                else:
                    player.hider_payoff = 0
                    print("die")

# Hider 配對後的結果
class Hider_matched(Page):
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
        if player.session.config['practice']:
            G = player.group.G_hider_practice
        else:
            G = player.group.G

        return {
            "nodes": G_nodes(G, player),
            "links": G_links(G),
            "which_round": player.round_number,
            "me": player.id_in_group, 
            "payoff": player.hider_payoff,
            "accumlative_payoff": np.sum([p.hider_payoff for p in player.in_previous_rounds() ]) + player.hider_payoff, 
        }

class Pesudo_dismantle(WaitPage):
    title_text = "等待 seeker dismantle"
    body_text = ""
    @staticmethod
    def is_displayed(player: Player):
        if not player.session.config["practice"] or player.role_type == 'seeker':
            return False

        G = player.group.G_hider_practice

        if player.round_number == 1:
            return True
        else:
            return player.in_round(player.round_number-1).survive

    @staticmethod
    def after_all_players_arrive(group: Group):
        G = group.G_hider_practice
        to_be_removed = random.choice(list(G.nodes()))
        for i, player in enumerate(group.get_players()):
            player.to_be_removed = to_be_removed
            if i == 0:
                remove_from_G(player, G)

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
            print(G.nodes(), "ss")

        if len(G.nodes()) != 0 and player.role_type == 'seeker':
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

class Wait_dismantle(WaitPage):
    title_text = "等待 seeker dismantle"
    body_text = ""
    def is_displayed(player: Player):
        if player.role_type == 'hider' and not player.session.config['practice']:
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
                hiders = player.in_round(player.round_number).get_others_in_group()
                if player.session.config['practice']:
                    if len(player.group.G_seeker_practice) >0: 
                        return True
                    elif len(player.group.G_seeker_practice) == 0 and len(player.group.G_hider_practice) != 0:
                        return True 
                else:
                    for hider in hiders:
                        if hider.survive:
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
            "current_size": len(player.group.G_seeker_practice), 
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
        is_human_seeker = player.session.config['seeker'] == 'human'
        is_human_hider = player.session.config['hider'] == 'human'
        if player.session.config['practice']:
            if len(player.group.G_seeker_practice) == 0:
                player.sub_practice_end = True

        if is_human_seeker and not is_human_hider and player.session.config['practice']:
            # TODO : "人工添加 edge"
            pass

        if is_human_seeker and not is_human_hider and not player.session.config['practice']:
            # TODO : "人工添加 edge" 
            pass 


# Hider 確認是否存活
class Hider_confirm(Page):
    @staticmethod
    def is_displayed(player: Player):
        if player.role_type == 'hider':

            if player.round_number == 1:
                return True 
            else:
                return (player.in_round(player.round_number-1).survive and not player.survive)
        return False

    @staticmethod
    def vars_for_template(player: Player):
        return {
            "which_round": player.round_number, 
            "survive": player.survive, 
        }

class Seeker_new_round(Page):
    @staticmethod
    def is_displayed(player: Player):
        if player.role_type == 'seeker' and player.session.config['practice'] and len(player.group.G_seeker_practice.nodes) == 0:
            
            hiders = player.get_others_in_subsession()
            if len(hiders[0].group.G_hider_practice.nodes()) == 0:
                return False
            return True
        return False

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

class Wait_All_finished(WaitPage):
    title_text = "等待所有人進入下一階段"
    body_text = ""

    @staticmethod
    def is_displayed(player: Player):
        if not player.session.config['practice']:
            return False

        if player.role_type == 'seeker':
            hiders = player.get_others_in_subsession()
            if len(hiders[0].group.G_hider_practice.nodes()) == 0 and len(player.group.G_seeker_practice.nodes()) == 0:
                return True
        else:
            if not player.survive:
                return True 
        return False

page_sequence = [Hider_build, Hider_wait_matching, Hider_matched, Pesudo_dismantle, 
    Seeker_dismantle, Wait_dismantle, Seeker_confirm, Hider_confirm, Seeker_new_round, Wait_All_finished]

