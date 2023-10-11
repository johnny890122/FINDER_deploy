from otree.api import *
import sys, os, json
import networkx as nx
import numpy as np
from seeker_game.utility import G_links, G_nodes, to_list, remove_node, getRobustness, generate_ba_graph_with_density, node_centrality_criteria, GCC_size, complete_genertor, read_sample, current_dismantle_G, current_dismantle_stage, copy_G, relabel_G, convert_to_FINDER_format, compute_finder_payoff

sys.path.append(os.path.dirname(__file__) + os.sep + './')
# from FINDER import FINDER
from io import BytesIO

doc = """
human seeker 單機版 
"""

HXA = ["HDA", "HCA", "HBA", "HPRA"]
# dqn = FINDER()

class C(BaseConstants):
    NAME_IN_URL = 'seeker_game'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 100 # 理論上，設定成一個很大的數字即可。

class Subsession(BaseSubsession):
    pass

class Group(BaseGroup):
    basic_G = nx.Graph()
    HDA_G = nx.Graph()
    HCA_G = nx.Graph()
    HBA_G = nx.Graph()
    HPRA_G = nx.Graph()
    G = nx.Graph()

class Player(BasePlayer):
    # seeker 需要的 field
    seeker_payoff = models.FloatField(initial=0)
    tool = models.StringField(
        choices = [
            ["no_help", "自行判斷"], 
            ["degree", "連結程度"], 
            ["closeness", "距離長短"], 
            ["betweenness", "中介程度"],
            ["page_rank", "重要程度"],
            # ["AI_FINDER", "AI_FINDER"]
        ],
        label="請選擇您要使用的輔助指標。", 
        widget=widgets.RadioSelect,
        initial="empty"
    )
    playing_graph = models.StringField(
        choices = ["911", "DOMESTICTERRORWEB", "suicide", "MAIL", "HEROIN_DEALING", "HAMBURG_TIE_YEAR", "SWINGERS_club"], 
        widget=widgets.RadioSelect,
        initial="", 
    )

    # Graph 需要的 field 
    num_edge = models.IntegerField(initial=-1)
    num_node = models.IntegerField(initial=-1)
    to_be_removed = models.IntegerField(initial=-1)
    to_be_removed_ranking = models.IntegerField(initial=0
    )
    num_edge_removed = models.IntegerField(initial=-1)
    edge_remain = models.IntegerField(initial=-1)

    GCC_size = models.IntegerField(initial=-1)
    remainGCC_size = models.IntegerField(initial=-1)
    finder_hist = models.StringField(initial="")
    # node_plot_finder = models.StringField(initial="")
    payoff_finder = models.StringField(initial="")
    stage = models.StringField(initial="")
    graph_layout = models.StringField(initial="")

def creating_session(subsession: Subsession):
    for player in subsession.get_players():
        if player.round_number == 1:

            player.playing_graph = player.session.config["first_playing_data"]
            initial_G = read_sample(player.playing_graph)

            # model_file = f'./models/Model_EMPIRICAL/{player.in_round(1).playing_graph}.ckpt'
            # payoff_finder_lst = compute_finder_payoff(initial_G, dqn, model_file)

            # player.num_node = initial_G.number_of_nodes()
            # player.payoff_finder = ",".join([str(p) for p in payoff_finder_lst])

            basic_ = read_sample(player.session.config["basic_sample_data"])
            copy_G(source_G= basic_, target_G=player.group.basic_G)

            HXA_ = read_sample(player.session.config["HXA_sample_data"])
            copy_G(source_G= HXA_, target_G=player.group.HDA_G)
            copy_G(source_G= HXA_, target_G=player.group.HCA_G)
            copy_G(source_G= HXA_, target_G=player.group.HBA_G)
            copy_G(source_G= HXA_, target_G=player.group.HPRA_G)

            playing_ = read_sample(player.playing_graph)
            copy_G(source_G= playing_, target_G=subsession.get_groups()[0].G)

class WelcomePage(Page):
    @staticmethod
    def is_displayed(player: Player):
        basic_full_nodes = read_sample(player.session.config["basic_sample_data"]).number_of_nodes()
        if player.group.basic_G.number_of_nodes() == basic_full_nodes:
            return True
        return False

class _911_intro(Page):
    @staticmethod
    def is_displayed(player: Player):
        basic_full_nodes = read_sample(player.session.config["basic_sample_data"]).number_of_nodes()
        if player.group.basic_G.number_of_nodes() == basic_full_nodes:
            return True
        return False

class HXA_IntroPage(Page):
    @staticmethod
    def is_displayed(player: Player):
        basic_full_nodes = read_sample(player.session.config["basic_sample_data"]).number_of_nodes()
        HXA_full_nodes = read_sample(player.session.config["HXA_sample_data"]).number_of_nodes()
        if player.group.basic_G.number_of_nodes() == basic_full_nodes-1 and player.group.HDA_G.number_of_nodes() == HXA_full_nodes:
            return True
        return False

class _911_HDA(Page):
    @staticmethod
    def is_displayed(player: Player):
        basic_full_nodes = read_sample(player.session.config["basic_sample_data"]).number_of_nodes()
        HXA_full_nodes = read_sample(player.session.config["HXA_sample_data"]).number_of_nodes()
        if player.group.basic_G.number_of_nodes() == basic_full_nodes-1 and player.group.HDA_G.number_of_nodes() == HXA_full_nodes:
            return True
        return False

class _911_HCA(Page):
    @staticmethod
    def is_displayed(player: Player):
        HXA_full_nodes = read_sample(player.session.config["HXA_sample_data"]).number_of_nodes()
        if player.group.HDA_G.number_of_nodes() == HXA_full_nodes-1 and player.group.HCA_G.number_of_nodes() == HXA_full_nodes:
            return True
        return False

class _911_HBA(Page):
    @staticmethod
    def is_displayed(player: Player):
        HXA_full_nodes = read_sample(player.session.config["HXA_sample_data"]).number_of_nodes()
        if player.group.HCA_G.number_of_nodes() == HXA_full_nodes-1 and player.group.HBA_G.number_of_nodes() == HXA_full_nodes:
            return True
        return False

class _911_HPRA(Page):
    @staticmethod
    def is_displayed(player: Player):
        HXA_full_nodes = read_sample(player.session.config["HXA_sample_data"]).number_of_nodes()
        if player.group.HBA_G.number_of_nodes() == HXA_full_nodes-1 and player.group.HPRA_G.number_of_nodes() == HXA_full_nodes:
            return True
        return False

class FINDER_IntroPage(Page):
    @staticmethod
    def is_displayed(player: Player):
        stage = current_dismantle_stage(player)
        G = current_dismantle_G(player, stage)
        HXA_full_nodes = read_sample(player.session.config["HXA_sample_data"]).number_of_nodes()
        if player.group.HPRA_G.number_of_nodes() == HXA_full_nodes-1 and G.number_of_nodes() == read_sample(player.in_round(1).playing_graph).number_of_nodes():
            return True
        return False

class game_start(Page):
    @staticmethod
    def is_displayed(player: Player):
        stage = current_dismantle_stage(player)
        G = current_dismantle_G(player, stage)
        HXA_full_nodes = read_sample(player.session.config["HXA_sample_data"]).number_of_nodes()
        if player.group.HPRA_G.number_of_nodes() == HXA_full_nodes-1 and G.number_of_nodes() == read_sample(player.in_round(1).playing_graph).number_of_nodes():
            return True
        return False   

class Tool_Selection_Page(Page):
    form_model = "player"
    form_fields = ['tool']

    @staticmethod
    def is_displayed(player: Player):
        full_nodes = read_sample(player.session.config["HXA_sample_data"]).number_of_nodes()
        if player.group.HPRA_G.number_of_nodes() == full_nodes-1:
            return True
        return False

class ReceptionPage(Page):
    @staticmethod
    def is_displayed(player: Player):
        if player.round_number == 1:
            return True
        return False

class Seeker_dismantle_result(Page):
    @staticmethod
    def is_displayed(player: Player):
        stage = player.in_round(player.round_number).stage

        G = current_dismantle_G(player, stage)

        basic_full_nodes = read_sample(player.session.config["basic_sample_data"]).number_of_nodes()
        HXA_full_nodes = read_sample(player.session.config["HXA_sample_data"]).number_of_nodes()
        if stage == "basic" and G.number_of_nodes() == basic_full_nodes - 1:
            return True
        elif stage in HXA and G.number_of_nodes() == HXA_full_nodes - 1:
            return True
        return False
        
    @staticmethod
    def vars_for_template(player: Player):
        stage = player.in_round(player.round_number).stage
        if stage == "basic":
            G = read_sample(player.session.config["basic_sample_data"])
        elif stage in HXA:
            G = read_sample(player.session.config["HXA_sample_data"])
        
        centrality = node_centrality_criteria(G)
        gradient_color = ["#000000", "#4d4d4d", "#949494", "#d6d6d6", "#ffffff"]
        color_map = {}
        to_be_removed_ranking = -1
        for h_based, node_map in centrality.items():
            nodes = [n for n in node_map["node"]]
            ranks = [v for v in node_map["value"]]

            color = gradient_color[0:ranks[-1]-1] if ranks[-1] <= len(gradient_color) else gradient_color
            color_map[h_based] = {
                node: color[int((rank-1)//( (ranks[-1]) / len(color)))] 
                    for node, rank in zip(nodes, ranks) if node != "source"
            }
        
        G.remove_node(player.to_be_removed)
        graph_layout = {}
        for dct in eval(player.graph_layout):
            graph_layout[dct["id"]] = {"x": dct["x"], "y": dct["y"]}
        tool_dct = {
            "basic": None,
            "HDA": "連結程度", 
            "HCA": "距離短的",
            "HBA": "中介程度",
            "HPRA": "重要性",
        }
        return {
            "to_be_removed_ranking": player.in_round(player.round_number).to_be_removed_ranking,
            "to_be_removed": player.to_be_removed, 
            "stage": stage, 
            "practice": int(player.session.config['pre_computed']), 
            "nodes": G_nodes(G, graph_layout), 
            "links": G_links(G), 
            "tool": player.in_round(player.round_number).tool,
            "density": nx.density(G), 
            "degree_ranking": { n: v for n, v in zip(centrality["degree"]["node"], centrality["degree"]["value"])},
            "closeness_ranking": { n: v for n, v in zip(centrality["closeness"]["node"], centrality["closeness"]["value"])},
            "betweenness_ranking": { n: v for n, v in zip(centrality["betweenness"]["node"], centrality["betweenness"]["value"])},
            "page_rank_ranking": { n: v for n, v in zip(centrality["page_rank"]["node"], centrality["page_rank"]["value"])},
            "degree_color": json.dumps(color_map["degree"]),
            "closeness_color": json.dumps(color_map["closeness"]), 
            "betweenness_color": json.dumps(color_map["betweenness"]), 
            "page_rank_color": json.dumps(color_map["page_rank"]),
            "tool_display_name": tool_dct[player.stage], 
        }

# Seeker 破壞的頁面
class Seeker_dismantle(Page):
    form_model = 'player'
    form_fields = ['to_be_removed', 'to_be_removed_ranking', 'graph_layout']
    
    @staticmethod
    def is_displayed(player: Player):
        stage = current_dismantle_stage(player)
        basic_full_nodes = read_sample(player.session.config["basic_sample_data"]).number_of_nodes()
        HXA_full_nodes = read_sample(player.session.config["HXA_sample_data"]).number_of_nodes()
        G = current_dismantle_G(player, stage)
        if stage == "official" and G.number_of_edges() > 0:
            return True
        elif stage == "basic" and G.number_of_nodes() == basic_full_nodes:
            return True
        elif stage in HXA and G.number_of_nodes() == HXA_full_nodes:
            return True
        return False

    @staticmethod
    def vars_for_template(player: Player):
        stage = current_dismantle_stage(player)
        G = current_dismantle_G(player, stage)
        centrality = node_centrality_criteria(G)
        tool = player.in_round(player.round_number).tool
        tool_selected = player.in_round(player.round_number).tool

        if player.round_number != 1:
            playing_graph = player.in_round(player.round_number-1).playing_graph
        else:
            playing_graph = player.session.config["first_playing_data"]
        if tool_selected == "AI_FINDER":
            # pass
            model_file = f'./models/Model_EMPIRICAL/{playing_graph}.ckpt'
            g = G.copy()
            g, map_dct = relabel_G(g)

            content = BytesIO(convert_to_FINDER_format(g).encode('utf-8'))
            _, sol = dqn.Evaluate(content, model_file)
            not_sol = [n for n in g.nodes() if n not in sol]
            sol = [map_dct[s] for s in sol]
            not_sol = [map_dct[s] for s in not_sol]

            value = []
            for idx in range(len(sol)):
                value.append(idx+1)
            for idx in range(len(not_sol)):
                value.append(len(sol)+1)

            centrality["AI_FINDER"] = {
                "node": sol + not_sol, 
                "value": value, 
            }

        gradient_color = ["#000000", "#4d4d4d", "#949494", "#d6d6d6", "#ffffff"]
        color_map = {}
        for base, node_map in centrality.items():
            nodes = [n for n in node_map["node"]]
            ranks = [v for v in node_map["value"]]

            color = gradient_color[0:ranks[-1]-1] if ranks[-1] <= len(gradient_color) else gradient_color
            color_map[base] = {
                node: color[int((rank-1)//( (ranks[-1]) / len(color)))] 
                    for node, rank in zip(nodes, ranks) if node != "source"
            }
        
        if stage == "basic":
            round_number = read_sample(player.session.config["basic_sample_data"]).number_of_nodes() - G.number_of_nodes() + 1
        elif stage in HXA:
            round_number = read_sample(player.session.config["HXA_sample_data"]).number_of_nodes() - G.number_of_nodes() + 1
        else:
            round_number = read_sample(playing_graph).number_of_nodes() - G.number_of_nodes() + 1
        
        return {
            "stage": stage, 
            "practice": int(player.session.config['pre_computed']), 
            "which_round": round_number, 
            "nodes": G_nodes(G), 
            "links": G_links(G), 
            "tool": tool,
            "density": nx.density(G), 
            "degree_ranking": { n: v for n, v in zip(centrality["degree"]["node"], centrality["degree"]["value"])},
            "closeness_ranking": { n: v for n, v in zip(centrality["closeness"]["node"], centrality["closeness"]["value"])},
            "betweenness_ranking": { n: v for n, v in zip(centrality["betweenness"]["node"], centrality["betweenness"]["value"])},
            "page_rank_ranking": { n: v for n, v in zip(centrality["page_rank"]["node"], centrality["page_rank"]["value"])},
            "FINDER_ranking": { n: v for n, v in zip(centrality["AI_FINDER"]["node"], centrality["AI_FINDER"]["value"])} if tool == "AI_FINDER" else {},
            
            "degree_color": json.dumps(color_map["degree"]),
            "closeness_color": json.dumps(color_map["closeness"]), 
            "betweenness_color": json.dumps(color_map["betweenness"]), 
            "page_rank_color": json.dumps(color_map["page_rank"]), 
            "FINDER_color": json.dumps(color_map["AI_FINDER"]) if tool == "AI_FINDER" else {}, 
        }

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.stage = current_dismantle_stage(player)
        G = current_dismantle_G(player, player.stage)
        if player.round_number != 1:
            player.playing_graph = player.in_round(player.round_number-1).playing_graph
        # 計算 reward
        player.num_edge = G.number_of_edges()
        player.num_node = G.number_of_nodes()
        player.GCC_size = GCC_size(G)
        original_G = read_sample(player.playing_graph)
        player.seeker_payoff = getRobustness(full_g=original_G, G=G, sol=player.to_be_removed) / original_G.number_of_nodes()
        
        player.edge_remain = G.number_of_edges()
        player.remainGCC_size = GCC_size(G)


        
# Seeker 確認該回合的破壞成果
class Seeker_confirm(Page):
    @staticmethod
    def is_displayed(player: Player):
        stage = player.in_round(player.round_number).stage
        G = current_dismantle_G(player, stage)
        
        if stage == "official" and G.number_of_edges() >= 0:
            return True
        return False

    @staticmethod
    def vars_for_template(player: Player):

        # Remaining node
        node_plot = [[0, player.in_round(1).GCC_size]]
        for n in range(1, player.round_number+1):
            node_plot.append([n, player.in_round(n).remainGCC_size])
        # stage
        stage = player.in_round(player.round_number).stage
        G = current_dismantle_G(player, stage)
        
        if stage == "basic":
            round_number = read_sample(player.session.config["basic_sample_data"]).number_of_nodes() - G.number_of_nodes()
        elif stage in HXA:
            round_number = read_sample(player.session.config["HXA_sample_data"]).number_of_nodes() - G.number_of_nodes()
        else:
            round_number = read_sample(player.playing_graph).number_of_nodes() - G.number_of_nodes()
        
        # Accumulate payoff
        payoff = [0] + [p.seeker_payoff for p in player.in_previous_rounds()[player.round_number-round_number:]] + [player.seeker_payoff]
        accum_payoff = np.add.accumulate(payoff)
        payoff_plot = [[i, p] for (i, p) in enumerate(accum_payoff)]

        # initial_G = read_sample(player.playing_graph)
        # model_file = f'./models/Model_EMPIRICAL/{player.playing_graph}.ckpt'
        # payoff_finder = [[i, p] for (i, p) in enumerate(compute_finder_payoff(initial_G, dqn, model_file))]
        payoff_finder = []
        return {
            "stage": stage, 
            "original_size": player.in_round(1).GCC_size, 
            "practice": int(player.session.config['pre_computed']),
            # "node_plot_finder": node_plot_finder if stage == "official" else [],
            "payoff_finder": payoff_finder if stage == "official" else [], 
            "node_line_plot": node_plot, 
            "payoff_line_plot": payoff_plot, 
            "which_round": round_number, 
            "caught": player.to_be_removed, 
            "current_GCC_size": player.remainGCC_size, 
        }

class Next_Link(Page):
    form_model = "player"
    form_fields = ['playing_graph']

    @staticmethod
    def is_displayed(player: Player):
        stage = player.in_round(player.round_number).stage
        G = current_dismantle_G(player, stage)
        
        if stage == "official" and G.number_of_edges() == 0:
            return True
        return False

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        
        initial_G = read_sample(player.playing_graph)
        stage = player.in_round(player.round_number).stage
        G = current_dismantle_G(player, stage)
        nodes = list(G.nodes())
        for n in nodes:
            G.remove_node(n)

        copy_G(source_G=initial_G, target_G=G)

page_sequence = [WelcomePage, HXA_IntroPage, FINDER_IntroPage, game_start, Tool_Selection_Page, Seeker_dismantle, Seeker_dismantle_result, Seeker_confirm, Next_Link]
