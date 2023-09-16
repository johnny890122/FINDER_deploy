from os import environ

ROOMS = [
    dict(
        name='game_link',
        display_name='Unified Link for Seeker Game',
    ),
]

SESSION_CONFIGS = [
    dict(
        name='seeker_game', 
        app_sequence=['seeker_game'], 
        num_demo_participants=1, 
        basic_sample_data= "911", 
        HXA_sample_data = "everett",
        first_playing_data = "PREVERE1MODE",
        size=40,
        density=0.01, 
        pre_computed=True, 
        generating_process='ba', 
        randint=0, 
    ),
]

# if you set a property in SESSION_CONFIG_DEFAULTS, it will be inherited by all configs
# in SESSION_CONFIGS, except thosea that explicitly override it.
# the session config can be accessed from methods in your apps as self.session.config,
# e.g. self.session.config['participation_fee']

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=1.00, participation_fee=100, doc=""
)

PARTICIPANT_FIELDS = []
SESSION_FIELDS = []

# ISO-639 code
# for example: de, fr, ja, ko, zh-hans
LANGUAGE_CODE = 'en'

# e.g. EUR, GBP, CNY, JPY
REAL_WORLD_CURRENCY_CODE = 'USD'
USE_POINTS = False

ADMIN_USERNAME = 'admin'
# for security, best to set admin password in an environment variable
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')

DEMO_PAGE_INTRO_HTML = """ """

SECRET_KEY = '9102800717646'
