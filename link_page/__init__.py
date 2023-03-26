from otree.api import *
import sys,os
import random, json
import networkx as nx
import io
import pygsheets
import pandas as pd

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
    link = models.StringField()


def getLinks():

    gc = pygsheets.authorize(service_file='finderlink-381806-aa232dd1eff5.json')
    # setting sheet
    sheet_url = "https://docs.google.com/spreadsheets/d/15t8MjE9mLmHGQDWzGGqEPiri402DKU1Ux8EX9XyxwcA/" 
    sheet = gc.open_by_url(sheet_url)
    data = sheet.worksheet_by_title("link").get_all_records()



    return [d["link"] for d in data]

def creating_session(subsession: Subsession):
    links = getLinks()
    for player in subsession.get_players():
        player.link = links[player.id_in_group-1]
        if player.session.config['seeker'] == 'human' and player.id_in_group == 1:
            player.role_type = 'seeker'
        else:
            player.role_type = 'hider'

# PAGES
class MyPage(Page):
    @staticmethod
    def vars_for_template(player: Player):

        return{
            "link": player.link
        }

page_sequence = [MyPage]

