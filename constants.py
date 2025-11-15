import sys, os
VERBOSITY = 1

BLACK = (26, 26, 26)
WHITE = (230, 230, 230)
GREEN = (67, 217, 107)
PURPLE = (75, 103, 217)
ORANGE = (217, 133, 75)
RED = (217, 75, 75)
BOARD_BACKGROUND = (46, 46, 46)
BOARD_GRID = (60, 60, 60)
ACCENT = (217, 178, 75)

def get_model(model):
    if model == "tf_keras":
        try:
            import AI.RLModelKeras as rlmk
            return rlmk.TDN(model_name = "models/test_396_1")
        except:
            pass
    elif model == "torch":
        try:
            import AI.RLModelTorch as rlmt
            return rlmt.TDN()
        except:
            pass

ROW_COUNT = 14
COLUMN_COUNT = 14

STARTING_SCORE = 89

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_SIZE = [WINDOW_WIDTH, WINDOW_HEIGHT]

BOARD_FILL_VALUE = 0
PLAYER1_VALUE = 1
PLAYER2_VALUE = 2

STARTING_PTS = \
{"player1" : [4,4],
 "player2" : [9,9]}

INFINITY = 10000
M_INFINITY = -10000

def write_to_log(msg):
    log_folder = os.path.abspath(os.path.dirname(sys.argv[0]))
    log_file = os.path.join(log_folder, "log.txt")
    with open(log_file, "a+") as f:
        f.write("\n\n\n"+msg)
        f.close()

from AI.MinimaxAI import Minimax

HUMAN_PARAMS = {"default_p1" : {"is_ai" : False, "color" : PURPLE, "name_if_ai" : None, "ai_class": None},
                "default_p2" : {"is_ai" : False, "color" : ORANGE, "name_if_ai" : None, "ai_class": None}}
AI_PARAMS = {"randombot_p2" : {"is_ai" : True, "color" : ORANGE, "name_if_ai" : "RandomMovesBot", "ai_class" : None},
             "rlkeras_p2" : {"is_ai" : True, "color" : ORANGE, "name_if_ai" : "ReinforcementLearningAI", "ai_class": get_model("tf_keras")},
             "rltorch_p2" : {"is_ai" : True, "color" : ORANGE, "name_if_ai" : "ReinforcementLearningAI", "ai_class": get_model("torch")},
             "alphabeta_easy_p2": {"is_ai": True, "color": ORANGE, "name_if_ai": "MinimaxAI", "ai_class": Minimax(ORANGE, 2, depth=1)},
             "alphabeta_hard_p2": {"is_ai": True, "color": ORANGE, "name_if_ai": "MinimaxAI", "ai_class": Minimax(ORANGE, 2, depth=2)}}