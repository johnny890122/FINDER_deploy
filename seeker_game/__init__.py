from otree.api import *
import sys, os, random, json, io
import networkx as nx
import numpy as np

from seeker_game.utility import G_links, G_nodes, to_list, remove_node, getRobustness, generate_ba_graph_with_density, node_centrality_criteria, GCC_size, complete_genertor, read_911, current_dismantle_G, current_dismantle_stage

sys.path.append(os.path.dirname(__file__) + os.sep + './')
from FINDER import FINDER

doc = """
human seeker 單機版 
"""

randint = np.random.randint(5)

class C(BaseConstants):
    NAME_IN_URL = 'seeker_game'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 100 # TODO: 理論上，設定成一個很大的數字即可（size+1）。

class Subsession(BaseSubsession):
    pass

class Group(BaseGroup):
    basic_911 = read_911()
    HDA_911 = basic_911.copy()
    HCA_911 = basic_911.copy()
    HBA_911 = basic_911.copy()
    HPRA_911 = basic_911.copy()
    G = nx.Graph()

class Player(BasePlayer):
    # 實驗的參數
    cons = C()
    role_type = models.StringField(initial="seeker")

    # seeker 需要的 field
    seeker_payoff = models.FloatField(initial=0)
    confirm = models.BooleanField()
    sub_practice_end = models.BooleanField(initial=False)

    # Graph 需要的 field 
    num_edge = models.IntegerField(initial=-1)
    num_node = models.IntegerField(initial=-1)
    to_be_removed = models.IntegerField(initial=-1)
    num_edge_removed = models.IntegerField(initial=-1)
    edge_remain = models.IntegerField(initial=-1)

    GCC_size = models.IntegerField(initial=-1)
    remainGCC_size = models.IntegerField(initial=-1)
    finder_hist = models.StringField(initial="2,3,4,5,6,7,8,9,10")
    node_plot_finder = models.StringField(initial="")
    payoff_finder = models.StringField(initial="")

def creating_session(subsession: Subsession):
    is_pre_computed = subsession.session.config['pre_computed']
    generating_process = subsession.session.config["generating_process"]
    assert generating_process in ["ba", "covert", "dark"]

    if not is_pre_computed:
        size = subsession.session.config["size"]
        density = subsession.session.config["density"]
        initial_G = generate_ba_graph_with_density(size, density)
        initial_G = nx.relabel_nodes(initial_G, lambda x: str(x+2))
    else:
        file_name = f"./data/{generating_process}/g_{randint}"
        initial_G = nx.read_gml(file_name)
        initial_G = nx.relabel_nodes(initial_G, lambda x: int(x) + 2)

        hist = np.loadtxt(f"./data/{generating_process}/finder_node_hist/g_{randint}.txt", delimiter=",").tolist()
        hist = [h[1] for h in hist]
        
        hist_G = initial_G.copy()
        full_GCCsize = GCC_size(hist_G)
        full_G_size = hist_G.number_of_nodes()
        GCC_hist_lst, payoff_finder_lst = [full_GCCsize], [0]
        for n in hist:
            payoff = getRobustness(hist_G, int(n)+2, full_GCCsize, full_G_size)
            payoff_finder_lst.append(payoff)
            GCC_hist_lst.append(GCC_size(hist_G))

    for player in subsession.get_players():
        player.num_node = initial_G.number_of_nodes()
        player.node_plot_finder = ",".join([str(n) for n in GCC_hist_lst])
        player.payoff_finder = ",".join([str(p) for p in payoff_finder_lst])

        if player.round_number == 1:

            G = subsession.get_groups()[0].G

            for n in initial_G.nodes():
                G.add_node(int(n))

            for e in initial_G.edges():
                G.add_edge(int(e[0]), int(e[1]))

class WelcomePage(Page):
    @staticmethod
    def is_displayed(player: Player):
        if  player.group.basic_911.number_of_edges() == read_911().number_of_edges():
            return True
        return False

class _911_intro(Page):
    @staticmethod
    def is_displayed(player: Player):
        if  player.group.basic_911.number_of_edges() == read_911().number_of_edges():
            return True
        return False

class HXA_IntroPage(Page):
    @staticmethod
    def is_displayed(player: Player):
        if  player.group.basic_911.number_of_edges() == 0 and player.group.HDA_911.number_of_edges() == read_911().number_of_edges():
            return True
        return False

class _911_HDA(Page):
    @staticmethod
    def is_displayed(player: Player):
        if player.group.basic_911.number_of_edges() == 0 and player.group.HDA_911.number_of_edges() == read_911().number_of_edges():
            return True
        return False

class _911_HCA(Page):
    @staticmethod
    def is_displayed(player: Player):
        if player.group.HDA_911.number_of_edges() == 0 and player.group.HCA_911.number_of_edges() == read_911().number_of_edges():
            return True
        return False

class _911_HBA(Page):
    @staticmethod
    def is_displayed(player: Player):
        if player.group.HCA_911.number_of_edges() == 0 and player.group.HBA_911.number_of_edges() == read_911().number_of_edges():
            return True
        return False


class _911_HPRA(Page):
    @staticmethod
    def is_displayed(player: Player):
        if player.group.HBA_911.number_of_edges() == 0 and player.group.HPRA_911.number_of_edges() == read_911().number_of_edges():
            return True
        return False

class FINDER_IntroPage(Page):
    @staticmethod
    def is_displayed(player: Player):
        return False
        # if HPRA_911.number_of_edges() == 0 and G.number_of_edges() == :
        #     return True
        # return False

class ReceptionPage(Page):
    @staticmethod
    def is_displayed(player: Player):
        if player.round_number == 1:
            return True
        return False

# Seeker 破壞的頁面
class Seeker_dismantle(Page):
    form_model = 'player'
    form_fields = ['to_be_removed']
    
    @staticmethod
    def is_displayed(player: Player):
        
        G = current_dismantle_G(player)
        if G.number_of_edges() > 0:
            return True
        return False

    @staticmethod
    def vars_for_template(player: Player):
        stage = current_dismantle_stage(player)
        G = current_dismantle_G(player)
        centrality = node_centrality_criteria(G)

        gradient_color = ["#9FE2BF", "#000000", "#ffffff"]
        color_map = {}
        for h_based, nodes in centrality.items():
            color_map[h_based] = {
                node: gradient_color[int((idx)//( (len(nodes) + 1) / len(gradient_color)))] 
                    for idx, node in enumerate(nodes)
            }
            
        return {
            "stage": stage, 
            "practice": int(player.session.config['pre_computed']), 
            "which_round": player.round_number,

            "nodes": G_nodes(G), 
            "links": G_links(G), 

            "density": nx.density(G), 
            "highest_degree_id": centrality["degree"][0] if stage == "HDA" or stage == "official" else -1,
            "highest_closeness_id": centrality["closeness"][0] if stage == "HCA" or stage == "official" else -1,
            "highest_betweenness_id": centrality["betweenness"][0] if stage == "HBA" or stage == "official" else -1,
            "highest_page_rank_id": centrality["page_rank"][0] if stage == "HPRA" or stage == "official" else -1, 
            "degree_ranking": json.dumps(color_map["degree"]),
            "closeness_ranking": json.dumps(color_map["closeness"]), 
            "betweenness_ranking": json.dumps(color_map["betweenness"]), 
            "page_rank_ranking": json.dumps(color_map["page_rank"]), 

            "g_number": randint, 
        }

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        G = current_dismantle_G(player)
        # 計算 reward
        player.num_edge = G.number_of_edges()
        player.num_node = G.number_of_nodes()
        player.GCC_size = GCC_size(G)

        player.seeker_payoff = getRobustness(G, player.to_be_removed, player.in_round(1).GCC_size, player.in_round(1).num_node)
        
        player.edge_remain = G.number_of_edges()
        player.remainGCC_size = GCC_size(G)
        

# Seeker 確認該回合的破壞成果
class Seeker_confirm(Page):
    @staticmethod
    def is_displayed(player: Player):
        G = current_dismantle_G(player)
        if G.number_of_edges() > 0:
            return True
        return False

    @staticmethod
    def vars_for_template(player: Player):
        num_past_practice_round = 0
        if player.session.config['pre_computed']:
            for p in player.in_previous_rounds(): 
                if p.sub_practice_end:
                    num_past_practice_round = p.round_number

        # Remaining node
        node_plot = [[0, player.in_round(1).GCC_size]]
        for n in range(1, player.round_number+1):
            node_plot.append([n, player.in_round(n).remainGCC_size])

        # Accumulate payoff
        payoff = [0] + [p.seeker_payoff for p in player.in_previous_rounds()] + [player.seeker_payoff]
        accum_payoff = np.add.accumulate(payoff)
        payoff_plot = [[i, p] for (i, p) in enumerate(accum_payoff)]

        if player.session.config['pre_computed']:
            payoff_finder = to_list(player.payoff_finder, dytpe="float")
            node_plot_finder = to_list(player.node_plot_finder, dytpe="int")
            payoff_finder = [[i, p] for (i, p) in enumerate(np.cumsum(payoff_finder))]
            node_plot_finder = [[i, p] for (i, p) in enumerate(node_plot_finder)]
        else:
            #TODO: real-time finder 
            hist = [[i, n] for (i, n) in enumerate(to_list(player.in_round(1).finder_hist))]
            payoff_finder = [[i, p] for (i, p) in enumerate(to_list(player.in_round(1).payoff_finder, "float"))]
            node_plot_finder = [[i, p] for (i, p) in enumerate(to_list(player.in_round(1).node_plot_finder))]

        
        return {
            "original_size": player.in_round(1).GCC_size, 
            "practice": int(player.session.config['pre_computed']),
            "node_plot_finder": node_plot_finder,
            "payoff_finder": payoff_finder, 
            "node_line_plot": node_plot, 
            "payoff_line_plot": payoff_plot, 
            "which_round": player.round_number, 
            "caught": player.to_be_removed, 
            "current_GCC_size": player.remainGCC_size, 
        }

page_sequence = [WelcomePage, HXA_IntroPage, _911_HDA, _911_HCA, _911_HBA, _911_HPRA, FINDER_IntroPage, Seeker_dismantle, Seeker_confirm]
# page_sequence = [Seeker_dismantle, Seeker_confirm]

