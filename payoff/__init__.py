from otree.api import *
import sys,os
import random, json
import networkx as nx
import io

doc = """
Your app description
"""


class C(BaseConstants):
    NAME_IN_URL = 'payoff'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1

class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    pass

# PAGES
class MyPage(Page):
    @staticmethod
    def vars_for_template(player: Player):
        pass


page_sequence = [MyPage]

