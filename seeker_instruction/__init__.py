from otree.api import *
import sys,os
import io

doc = """
Introduction
"""

class C(BaseConstants):
    NAME_IN_URL = 'seeker_instruction'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1

class Subsession(BaseSubsession):
    pass

class Group(BaseGroup):
    pass


class Player(BasePlayer):
    pass 

def creating_session(subsession: Subsession):
    pass 

class WelcomePage(Page):
    @staticmethod
    def is_displayed(player: Player):
        return True

class _911_intro(Page):
    @staticmethod
    def is_displayed(player: Player):
        return True

class HXA_intro(Page):
    @staticmethod
    def is_displayed(player: Player):
        return True

class _911_HDA(Page):
    @staticmethod
    def is_displayed(player: Player):
        return True

class _911_HCA(Page):
    @staticmethod
    def is_displayed(player: Player):
        return True

class _911_HBA(Page):
    @staticmethod
    def is_displayed(player: Player):
        return True

class _911_HPRA(Page):
    @staticmethod
    def is_displayed(player: Player):
        return True

class FINDER_intro(Page):
    @staticmethod
    def is_displayed(player: Player):
        return True 

page_sequence = [WelcomePage, _911_intro, _911_HDA, _911_HCA, _911_HBA, _911_HPRA, FINDER_intro]

