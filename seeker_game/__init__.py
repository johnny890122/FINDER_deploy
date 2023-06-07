from otree.api import *
import sys, os, random, json, io
import networkx as nx
import numpy as np

from seeker_game.utility import get_current_graph, G_links, G_nodes, to_list, remove_node_and_neighbor, getRobustness, generate_ba_graph_with_density, node_centrality_criteria 

# sys.path.append(os.path.dirname(__file__) + os.sep + './')
# from FINDER import FINDER

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
    num_node = models.IntegerField(initial=-1)
    num_edge = models.IntegerField(initial=-1)
    to_be_removed = models.IntegerField(initial=-1)
    num_node_removed = models.IntegerField(initial=-1)
    num_edge_removed = models.IntegerField(initial=-1)
    node_remain = models.IntegerField(initial=-1)
    edge_remain = models.IntegerField(initial=-1)
    finder_hist = models.StringField(initial="2,3,4,5,6,7,8,9,10")
    node_plot_finder = models.StringField(initial="")
    payoff_finder = models.StringField(initial="")

def creating_session(subsession: Subsession):
    is_pre_computed = subsession.session.config['pre_computed']
    generating_process = subsession.session.config["generating_process"]
    assert generating_process in ["ba_graph", "covert", "dark"]
    



    if not is_pre_computed:
        size = subsession.session.config["size"]
        density = subsession.session.config["density"]
        initial_G = generate_ba_graph_with_density(size, density)
        initial_G = nx.relabel_nodes(initial_G, lambda x: str(x+2))
    else:
        graph_config = subsession.session.config["graph_config"]
        assert graph_config in ["size_low", "size_high", "density_low", "density_high"]

        randint = subsession.session.config["randint"]
    
        # 初始化 graph
        file_name = f"input/{generating_process}/{graph_config}_{randint}.txt"
        initial_G = nx.read_gml(file_name)
        initial_G = nx.relabel_nodes(initial_G, lambda x: int(x) + 2)

        # hist = np.loadtxt(f"input/{generating_process}/finder_hist/{graph_config}_{randint}.txt", delimiter=",").tolist()
        # hist_G = nx.read_adjlist(file_name)

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

        if player.round_number == 1:

            G = subsession.get_groups()[0].G
            for n in initial_G.nodes():
                G.add_node(int(n))
            for e in initial_G.edges():
                G.add_edge(int(e[0]), int(e[1]))

            hist_G = G.copy()
            if not is_pre_computed:
                node_plot_finder = list()
                payoff_finder = [0]
                cnt = 0
                for (i, n) in enumerate(to_list(player.in_round(1).finder_hist)):
                    try: 
                        payoff_finder.append(getRobustness(hist_G, int(n)))
                        node_plot_finder.append(len(hist_G.nodes()))
                        hist_G = remove_node_and_neighbor(int(n), hist_G)
                        cnt += 1

                        print("remove", n+2)
                    except:
                        print("not found", n+2)
                
                payoff_finder = [p for p in np.add.accumulate(payoff_finder)]
            
                player.node_plot_finder = ",".join([str(n) for n in node_plot_finder])
                player.payoff_finder = ",".join([str(p) for p in payoff_finder])

# Seeker 破壞的頁面
class Seeker_dismantle(Page):
    form_model = 'player'
    form_fields = ['to_be_removed']
    
    @staticmethod
    def is_displayed(player: Player):
        G = get_current_graph(player)
        if G.number_of_nodes() != 0:
            return True
        return False

    @staticmethod
    def vars_for_template(player: Player):
        G = get_current_graph(player)        
        centrality = node_centrality_criteria(G)

        return {
            "practice": int(player.session.config['pre_computed']), 
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
        player.num_node = G.number_of_nodes()
        player.num_edge = len(G.edges())
        
        G = remove_node_and_neighbor(player.to_be_removed, G)
        
        player.node_remain = G.number_of_nodes()
        player.edge_remain = len(G.edges())
        edge_remain = len(G.edges())

        player.num_node_removed = player.num_node - player.node_remain

# Seeker 確認該回合的破壞成果
class Seeker_confirm(Page):
    @staticmethod
    def is_displayed(player: Player):
        G = get_current_graph(player)
        if G.number_of_nodes() > 0:
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
        node_plot = [[0, player.in_round(1).num_node]]
        for n in range(1, player.round_number+1):
            node_plot.append([n, player.in_round(n).node_remain])

        # Accumulate payoff
        payoff = [0] + [p.seeker_payoff for p in player.in_previous_rounds()] + [player.seeker_payoff]
        accum_payoff = np.add.accumulate(payoff)
        payoff_plot = [[i, p] for (i, p) in enumerate(accum_payoff)]

        if player.session.config['pre_computed']:
            generating_process = player.session.config["generating_process"]
            graph_config = player.session.config["graph_config"]
            randint = player.session.config["randint"]

            file_name = f"input/{generating_process}/{graph_config}_{randint}.txt"
            hist = np.loadtxt(f"input/{generating_process}/finder_hist/{graph_config}_{randint}.txt", delimiter=",").tolist()


            hist_G = nx.read_gml(file_name)
            node_plot_finder = list()
            payoff_finder = [0]
            cnt = 0
            for (i, n) in hist:
                try: 
                    payoff_finder.append(getRobustness(hist_G, int(n)))
                    node_plot_finder.append([cnt, len(hist_G.nodes())])
                    hist_G = remove_node_and_neighbor(int(n), hist_G)
                    cnt += 1

                except:
                    print("not found", n+2)
            
            payoff_finder = [[i, p] for (i, p) in enumerate(np.add.accumulate(payoff_finder))]
        else:
            hist = [[i, n] for (i, n) in enumerate(to_list(player.in_round(1).finder_hist))]
            payoff_finder = [[i, p] for (i, p) in enumerate(to_list(player.in_round(1).payoff_finder, "float"))]
            node_plot_finder = [[i, p] for (i, p) in enumerate(to_list(player.in_round(1).node_plot_finder))]

        
        return {
            "current_size": len(player.group.G), 
            "original_size": player.in_round(1).num_node, 
            "practice": int(player.session.config['pre_computed']),
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

