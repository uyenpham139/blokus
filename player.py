import pieces, constants, board, numpy as np

class Player:
    
    def __init__(self, player_number: int, color: list, is_ai: bool, ai_name = None, ai_class = None):
        self.number = player_number
        self.remaining_pieces = pieces.get_pieces()
        self.discarded_pieces = []
        self.current_piece = {"piece": "", "arr": [], "rotated": 0, "flipped": 0, "rects": [], "place_on_board_at": []}
        self.color = color
        self.score = board.scoring_fn(self.remaining_pieces)
        self.turn_number = 1
        self.board_corners = {"bl":[], "br":[], "tl":[], "tr":[]}
        self.is_1st_move = True
        self.is_ai = is_ai
        self.ai_name = ai_name
        self.ai_class = ai_class

    def update_score(self):
        self.score = board.scoring_fn(self.remaining_pieces)
    
    def empty_current_piece(self):
        self.current_piece = {"piece": "", "arr": [], "rotated": 0, "flipped": 0, "rects": [], "place_on_board_at": []}
    
    def rotate_current_piece(self, clockwise = True):
        max_rots = pieces.get_pieces()[self.current_piece["piece"]]["rots"]
        current_state = self.current_piece["rotated"]
    
        if clockwise:
            if current_state == max_rots - 1:
                current_state = 0
            else:
                current_state += 1
            self.current_piece["rotated"] = current_state
            self.current_piece["arr"] = np.rot90(self.current_piece["arr"], k = 1)
        else:
            if current_state == 0:
                current_state = max_rots - 1
            else:
                current_state -= 1
            self.current_piece["rotated"] = current_state
            self.current_piece["arr"] = np.rot90(self.current_piece["arr"], k = -1)
        if constants.VERBOSITY > 1:
            print("New piece array for %s is %s" % (self.current_piece["piece"], self.current_piece["arr"]))

    def flip_current_piece(self):
        if not pieces.get_pieces()[self.current_piece["piece"]]["flips"] == 1:
            if self.current_piece["flipped"] == 1:
                self.current_piece["flipped"] = 0
            else:
                self.current_piece["flipped"] += 1
            self.current_piece["arr"] = np.flipud(self.current_piece["arr"])
    
    def discard_piece(self, piece):
        del self.remaining_pieces[piece["piece"]]
        self.discarded_pieces.append(piece)
    
    def retrieve_last_piece(self):
        piece = self.discarded_pieces[-1]
        self.remaining_pieces[piece["piece"]] = pieces.get_pieces()[piece["piece"]]
        return piece

    def get_state(self):
        """Returns a serializable dictionary of the player's state."""
        return {
            "score": self.score,
            "is_1st_move": self.is_1st_move,
            "is_ai": self.is_ai,
            "ai_name": self.ai_name,
            "remaining_pieces": list(self.remaining_pieces.keys())
        }

    def load_state(self, state):
        """Loads the player's state from a dictionary."""
        self.score = state["score"]
        self.is_1st_move = state["is_1st_move"]
        
        all_pieces = pieces.get_pieces()
        self.remaining_pieces = {}
        for piece_name in state["remaining_pieces"]:
            if piece_name in all_pieces:
                self.remaining_pieces[piece_name] = {
                    "arr": np.array(all_pieces[piece_name]["arr"]),
                    "rots": all_pieces[piece_name]["rots"],
                    "flips": all_pieces[piece_name]["flips"],
                    "rects": []
                }
        
        self.discarded_pieces = []
        initial_piece_names = list(pieces.get_pieces().keys())
        for piece_name in initial_piece_names:
            if piece_name not in self.remaining_pieces:
                self.discarded_pieces.append({"piece": piece_name})
                