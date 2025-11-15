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

# Default 2 Player settings
ROW_COUNT_2P = 14
COLUMN_COUNT_2P = 14

# Default 4 Player settings
ROW_COUNT_4P = 20
COLUMN_COUNT_4P = 20

STARTING_SCORE = 89

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_SIZE = [WINDOW_WIDTH, WINDOW_HEIGHT]

BOARD_FILL_VALUE = 0
PLAYER1_VALUE = 1
PLAYER2_VALUE = 2
PLAYER3_VALUE = 3
PLAYER4_VALUE = 4

STARTING_SCORE = 89

def get_start_points(rows, cols):
    return {
        1: [0, 0],             
        2: [0, cols-1],        
        3: [rows-1, cols-1],    
        4: [rows-1, 0]
    }

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5555

INFINITY = 10000
M_INFINITY = -10000

def write_to_log(msg):
    log_folder = os.path.abspath(os.path.dirname(sys.argv[0]))
    log_file = os.path.join(log_folder, "log.txt")
    with open(log_file, "a+") as f:
        f.write("\n\n\n"+msg)
        f.close()

from AI.MinimaxAI import Minimax
from AI.MCTS_AI import MCTS 

HUMAN_PARAMS = {"default_p1" : {"is_ai" : False, "color" : PURPLE, "name_if_ai" : None, "ai_class": None},
                "default_p2" : {"is_ai" : False, "color" : ORANGE, "name_if_ai" : None, "ai_class": None}}
AI_PARAMS = {"randombot_p2" : {"is_ai" : True, "color" : ORANGE, "name_if_ai" : "RandomMovesBot", "ai_class" : None},
             "rlkeras_p2" : {"is_ai" : True, "color" : ORANGE, "name_if_ai" : "ReinforcementLearningAI", "ai_class": get_model("tf_keras")},
             "rltorch_p2" : {"is_ai" : True, "color" : ORANGE, "name_if_ai" : "ReinforcementLearningAI", "ai_class": get_model("torch")},
             "alphabeta_easy_p2": {"is_ai": True, "color": ORANGE, "name_if_ai": "MinimaxAI", "ai_class": Minimax(ORANGE, 2, depth=1)},
             "alphabeta_hard_p2": {"is_ai": True, "color": ORANGE, "name_if_ai": "MinimaxAI", "ai_class": Minimax(ORANGE, 2, depth=2)},
             "mcts_easy_p2": {"is_ai": True, "color": ORANGE, "name_if_ai": "MCTS_AI", "ai_class": MCTS(ORANGE, 2, iterations=100)},
             "mcts_hard_p2": {"is_ai": True, "color": ORANGE, "name_if_ai": "MCTS_AI", "ai_class": MCTS(ORANGE, 2, iterations=500)}
            }