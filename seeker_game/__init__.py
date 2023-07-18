from otree.api import *
import sys, os, random, json, io
import networkx as nx
import numpy as np

from seeker_game.utility import G_links, G_nodes, to_list, remove_node, getRobustness, generate_ba_graph_with_density, node_centrality_criteria, GCC_size, complete_genertor

sys.path.append(os.path.dirname(__file__) + os.sep + './')
from FINDER import FINDER

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
        randint = subsession.session.config["randint"]
        file_name = f"./data/{generating_process}/g_{randint}"
        initial_G = nx.read_gml(file_name)
        initial_G = nx.relabel_nodes(initial_G, lambda x: int(x) + 2)

        hist = np.loadtxt(f"./data/{generating_process}/finder_node_hist/g_{randint}.txt", delimiter=",").tolist()
        hist = [h[1] for h in hist]
        hist_G = initial_G.copy()

        fullGCCsize = GCC_size(hist_G)
        fullG_size = hist_G.number_of_nodes()
        GCC_hist_lst, payoff_finder_lst = [fullGCCsize], [0]
        for n in hist:
            print(fullGCCsize, fullG_size)
            payoff = getRobustness(hist_G, int(n)+2, fullGCCsize, fullG_size)
            payoff_finder_lst.append(payoff)
            GCC_hist_lst.append(GCC_size(hist_G))




        # FIXIT:之後取消註解
        # dqn = FINDER()
        # model_file = './models/Model_barabasi_albert/nrange_150_250_iter_103800.ckpt'

        # _, tmp = dqn.Evaluate("input/ba_graph/size_low_0.txt", model_file)
        # # player.finder_hist = ",".join([str(i) for i in tmp])

        # lst = list()
        # cnt = 0
        # for (i, n) in hist:
        #     try: 
        #         lst.append([cnt, hist_G.size()])
        #         hist_G = remove_node_and_neighbor(str(int(n)), hist_G)
        #         cnt += 1
        #     except:
        #         pass

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

            # hist_G = G.copy()
            # if not is_pre_computed:
            #     node_plot_finder = list()
            #     payoff_finder = [0]
            #     cnt = 0
            #     for (i, n) in enumerate(to_list(player.in_round(1).finder_hist)):
            #         payoff_finder.append(getRobustness(hist_G, int(n), GCC_size(initial_G)))
            #         node_plot_finder.append(len(hist_G.nodes()))
            #         hist_G = remove_node(int(n), hist_G)
            #         cnt += 1
                
            #     payoff_finder = [p for p in np.add.accumulate(payoff_finder)]
            
            #     player.node_plot_finder = ",".join([str(n) for n in node_plot_finder])
            #     player.payoff_finder = ",".join([str(p) for p in payoff_finder])

# Seeker 破壞的頁面
class Seeker_dismantle(Page):
    form_model = 'player'
    form_fields = ['to_be_removed']
    
    @staticmethod
    def is_displayed(player: Player):
        if player.group.G.number_of_nodes() > 0:
            return True
        return False

    @staticmethod
    def vars_for_template(player: Player):
        G = player.group.G
        centrality = node_centrality_criteria(G)

        return {
            "practice": int(player.session.config['pre_computed']), 
            "which_round": player.round_number,

            "nodes": G_nodes(G), 
            "links": G_links(G), 

            "density": nx.density(G), 
            "highest_degree_id": centrality["degree"],
            "highest_closeness_id": centrality["closeness"],
            "highest_betweenness_id": centrality["betweenness"],
            "highest_page_rank_id": centrality["page_rank"], 
        }

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        G = player.group.G

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
        if player.group.G.number_of_nodes() > 0:
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

            # generating_process = player.session.config["generating_process"]
            # graph_config = player.session.config["graph_config"]
            # randint = player.session.config["randint"]

            # file_name = f"input/{generating_process}/{graph_config}_{randint}.txt"
            # hist = np.loadtxt(f"input/{generating_process}/finder_hist/{graph_config}_{randint}.txt", delimiter=",").tolist()


            # hist_G = nx.read_gml(file_name)
            # node_plot_finder = list()
            payoff_finder = to_list(player.payoff_finder, dytpe="float")
            node_plot_finder = to_list(player.node_plot_finder, dytpe="int")
            payoff_finder = [[i, p] for (i, p) in enumerate(np.cumsum(payoff_finder))]
            node_plot_finder = [[i, p] for (i, p) in enumerate(node_plot_finder)]


        else:
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

page_sequence = [Seeker_dismantle, Seeker_confirm]

