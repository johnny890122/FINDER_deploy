from otree.api import *
import sys,os
import random, json
import networkx as nx
import io

doc = """
Your app description
"""


class C(BaseConstants):
    NAME_IN_URL = 'link_page'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1

class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    role_type = models.StringField()

def creating_session(subsession: Subsession):
    for player in subsession.get_players():
        if player.session.config['seeker'] == 'human' and player.id_in_group == 1:
            player.role_type = 'seeker'
        else:
            player.role_type = 'hider'


# PAGES
class MyPage(Page):
    @staticmethod
    def is_displayed(player: Player):
        if player.role_type == 'hider':
            return True
        return False

    @staticmethod
    def vars_for_template(player: Player):
        pass


page_sequence = [MyPage]

