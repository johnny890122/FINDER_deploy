from os import environ

SESSION_CONFIGS = [
    dict(
        name='seeker_game', 
        app_sequence=['seeker_game'], 
        num_demo_participants=1, 
        seeker='human', 

        size=100,
        density=0.01, 
        pre_computed=True, 
        generating_process='ba', 
        randint=0, 
    ),
    dict(
        name="seeker_instruction", 
        app_sequence=["seeker_instruction"],
        num_demo_participants=1, 
    )

    # dict(
    #     name='seeker_game_size_density', 
    #     # app_sequence=['seeker_instruction', 'seeker_game'], 
    #     app_sequence=['seeker_game'], 
    #     num_demo_participants=1, 
    #     seeker='human', 
    #     pre_computed=False,

    #     size=50,
    #     density=0.1, 
        
    #     degree_distribution=None,
    #     generating_process='ba_graph', 
    #     visualization=None,
    #     # graph_config = "density_low", 
    #     randint=1, 
    # ),

    # dict(
    #     name='only_human_seeker',
    #     # app_sequence=['seeker_instruction', 'hider_instruction', 'actual_rounds', 'payoff'],
    #     app_sequence=['actual_rounds'],
    #     num_demo_participants=1, 
    #     hider='not_human',
    #     seeker='human',
    #     practice=False,

    #     num_sythetic_hider=20, 
    #     density=0.1, 
    #     degree_distribution=None,
    #     generating_process="ba_graph",
    #     visualization=None,
    # ),

    # dict(
    #     name='only_human_seeker_no_practice',
    #     # app_sequence=['seeker_instruction', 'hider_instruction', 'actual_rounds', 'payoff'],
    #     app_sequence=['actual_rounds'],
    #     num_demo_participants=1,
    #     hider='not_human',
    #     seeker='human',
    #     num_demo=8,
    #     practice=False,
    # ),

    # dict(
    #     name='only_human_hider',
    #     # app_sequence=['seeker_instruction', 'hider_instruction', 'actual_rounds', 'payoff'],
    #     app_sequence=['actual_rounds'],
    #     num_demo_participants=4,
    #     hider='human',
    #     seeker='not_human',
    #     practice=True,
    # ),

    # dict(
    #     name='only_human_hider_no_practice',
    #     # app_sequence=['seeker_instruction', 'hider_instruction', 'actual_rounds', 'payoff'],
    #     app_sequence=['actual_rounds'],
    #     num_demo_participants=4,
    #     hider='human',
    #     seeker='not_human',
    #     practice=False,
    # ),
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
