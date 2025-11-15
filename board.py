import numpy as np
import constants, pieces

empty = constants.BOARD_FILL_VALUE
rows = constants.ROW_COUNT
cols = constants.COLUMN_COUNT

class Board:

    def __init__(self):
        self.board = np.array([[empty for i in range(rows)] for j in range(cols)])
        self.turn_number = 1
    
    def fit_piece(self, piece, player, opponent_player, mode="player"):
        piece_x_rng = range(piece["arr"].shape[0])
        piece_y_rng = range(piece["arr"].shape[1])
        board_x_rng = range(piece["place_on_board_at"][0], rows)
        board_y_rng = range(piece["place_on_board_at"][1], cols)
        
        if player.is_1st_move:
            if player.number == constants.PLAYER1_VALUE:
                pos = constants.STARTING_PTS["player1"]
            elif player.number == constants.PLAYER2_VALUE:
                pos = constants.STARTING_PTS["player2"]
            
            is_within_starting_pos = False
            for i, x in zip(piece_x_rng, board_x_rng):
                for j, y in zip(piece_y_rng, board_y_rng):
                    if [x, y] == pos and piece["arr"][i][j] == 1:
                        is_within_starting_pos = True
            if is_within_starting_pos:
                for i, x in zip(piece_x_rng, board_x_rng):
                    for j, y in zip(piece_y_rng, board_y_rng):
                        if piece["arr"][i][j] == 1 and self.board[x][y] == empty:
                            self.board[x][y] = player.number * piece["arr"][i][j]
            else:
                if constants.VERBOSITY > 0:
                    print("Piece %s placed at %s wasn't fit in the 1st turn" \
                         % (piece["piece"], piece["place_on_board_at"]))
                return False    
            if mode=="player":
                player.is_1st_move = False
        else:
            if self.check_is_move_valid(piece["arr"], player, piece["place_on_board_at"]):
                for i, x in zip(piece_x_rng, board_x_rng):
                    for j, y in zip(piece_y_rng, board_y_rng):
                        if piece["arr"][i][j] == 1:
                            self.board[x][y] = player.number * piece["arr"][i][j]
            else:
                if constants.VERBOSITY > 0:
                    print("In fit_piece, a move with piece %s turned out to be invalid" % (piece))
                return False
        if constants.VERBOSITY > 0 and not player.is_ai:
            print("Piece that was successfully fit:", piece)
        player.discard_piece(piece)
        player.empty_current_piece()
        self.turn_number += 1
        player.turn_number += 1
        player.update_score()
        if constants.VERBOSITY > 0:
            print("After turn number %s board is:\n %s" % (self.turn_number - 1, self.board))
            print("Current player's (Player %s) score is: %s and opponent's (Player %s) score is: %s" % \
                 (player.number, player.score, opponent_player.number, opponent_player.score))
        #self.update_board_corners(player, opponent_player)
        self.optimised_update_board_corners(piece, player, opponent_player)
        return True
    
    def unfit_last_piece(self, player, opponent_player):
        piece = player.retrieve_last_piece()

        piece_x_rng = range(piece["arr"].shape[0])
        piece_y_rng = range(piece["arr"].shape[1])
        board_x_rng = range(piece["place_on_board_at"][0], rows)
        board_y_rng = range(piece["place_on_board_at"][1], cols)

        for i, x in zip(piece_x_rng, board_x_rng):
            for j, y in zip(piece_y_rng, board_y_rng):
                if piece["arr"][i][j] == 1:
                    self.board[x][y] = empty
        self.turn_number -= 1
        player.turn_number -= 1
        player.update_score()
        self.update_board_corners(player, opponent_player)
        if constants.VERBOSITY > 1:
            print("Piece %s has been removed from the board" % (piece["piece_name"]))
    
    """We check the corners of a certain coordinate on the board as such:
    tl   0   tr
    0  (x,y) 0
    bl   0   br
    """
    def update_board_corners(self, player, opponent_player):
        player.board_corners = {"bl":[],"br":[],"tl":[],"tr":[]}
        opponent_player.board_corners = {"bl":[],"br":[],"tl":[],"tr":[]}
        for p in [player, opponent_player]:
            for x in range(self.board.shape[0]):
                for y in range(self.board.shape[1]):
                    if self.board[x][y] == p.number:
                        tl, tr, bl, br = self.check_surrounding_piece_coords(x, y, p.number)
                        if tl and x-1 >= 0 and y-1 >= 0:
                            p.board_corners["tl"].append([x-1, y-1])
                        if bl and x+1 < rows and y-1 >= 0:
                            p.board_corners["bl"].append([x+1, y-1])
                        if tr and x-1 >= 0 and y+1 < cols:
                            p.board_corners["tr"].append([x-1, y+1])
                        if br and x+1 < rows and y+1 < cols:
                            p.board_corners["br"].append([x+1,y+1])
        if constants.VERBOSITY > 0:
            print("Board corners for current player (Player %s): %s" % (player.number, player.board_corners))
            print("Board corners for opponent player (Player %s): %s" % (opponent_player.number, opponent_player.board_corners))
    
    def optimised_update_board_corners(self, piece_played, player, opponent_player):
        b_x_low, b_y_low = piece_played["place_on_board_at"][0], piece_played["place_on_board_at"][1]
        b_x_high, b_y_high = b_x_low + piece_played["arr"].shape[0], b_y_low + piece_played["arr"].shape[1]
        x_low = 0 if b_x_low == 0 else b_x_low - 1
        y_low = 0 if b_y_low == 0 else b_y_low - 1
        x_high = rows if b_x_high >= rows else b_x_high + 1
        y_high = cols if b_y_high >= cols else b_y_high + 1

        for p in [player, opponent_player]:
            for x in range(x_low, x_high):
                for y in range(y_low, y_high):
                    if self.board[x][y] == p.number:
                        tl, tr, bl, br = self.check_surrounding_piece_coords(x, y, p.number)
                        if tl and x-1 >= 0 and y-1 >= 0:
                            if [x-1, y-1] not in p.board_corners["tl"]:
                                p.board_corners["tl"].append([x-1, y-1])
                        elif not tl and x-1 >= 0 and y-1 >= 0:
                            if [x-1, y-1] in p.board_corners["tl"]:
                                p.board_corners["tl"].remove([x-1, y-1])
                        
                        if bl and x+1 < rows and y-1 >= 0:
                            if [x+1, y-1] not in p.board_corners["bl"]:
                                p.board_corners["bl"].append([x+1, y-1])
                        elif not bl and x+1 < rows and y-1 >= 0:
                            if [x+1, y-1] in p.board_corners["bl"]:
                                p.board_corners["bl"].remove([x+1, y-1])
                        
                        if tr and x-1 >= 0 and y+1 < cols:
                            if [x-1, y+1] not in p.board_corners["tr"]:
                                p.board_corners["tr"].append([x-1, y+1])
                        elif not tr and x-1 >= 0 and y+1 < cols:
                            if [x-1, y+1] in p.board_corners["tr"]:
                                p.board_corners["tr"].remove([x-1, y+1])
                        
                        if br and x+1 < rows and y+1 < cols:
                            if [x+1, y+1] not in p.board_corners["br"]:
                                p.board_corners["br"].append([x+1,y+1])
                        elif not br and x+1 < rows and y+1 < cols:
                            if [x+1, y+1] in p.board_corners["br"]:
                                p.board_corners["br"].remove([x+1,y+1])
        if constants.VERBOSITY > 0:
            print("Board corners for current player (Player %s): %s" % (player.number, player.board_corners))
            print("Board corners for opponent player (Player %s): %s" % (opponent_player.number, opponent_player.board_corners))
    
    def check_surrounding_piece_coords(self, x, y, p_num):
        tl, tr, bl, br = True, True, True, True
        try:
            if x-1 >= 0 and self.board[x-1][y+1] != empty: tr = False
        except IndexError: tr = False
        try:
            if self.board[x+1][y+1] != empty: br = False
        except IndexError: br = False
        try:
            if y-1 >= 0 and self.board[x+1][y-1] != empty: bl = False
        except IndexError: bl = False
        try:
            if x-1 >= 0 and y-1 >= 0 and self.board[x-1][y-1] != empty: tl = False
        except IndexError: tl = False
        try:
            if self.board[x][y+1] == p_num: tr, br = False, False
        except IndexError: tr, br = False, False
        try:
            if self.board[x+1][y] == p_num: bl, br = False, False
        except IndexError: bl, br = False, False
        try:
            if y-1 >= 0 and self.board[x][y-1] == p_num: tl, bl = False, False
        except IndexError: tl, bl = False, False
        try:
            if x-1 >= 0 and self.board[x-1][y] == p_num: tl, tr = False, False
        except IndexError: tl, tr = False, False
        return tl, tr, bl, br
    
    def check_is_move_valid(self, piece_arr, player, coords):
        is_there_a_pc_on_the_side = False
        is_corner_exists = False
        
        piece_x_rng = range(piece_arr.shape[0])
        piece_y_rng = range(piece_arr.shape[1])
        board_x_rng = range(coords[0], rows)
        board_y_rng = range(coords[1], cols)
        if piece_arr.shape[0] + coords[0] > rows\
           or piece_arr.shape[1] + coords[1] > cols:
           return False

        for i, x in zip(piece_x_rng, board_x_rng):
            for j, y in zip(piece_y_rng, board_y_rng):
                if piece_arr[i][j] == 1 and self.board[x][y] == empty:
                    tl, tr, bl, br = get_corners_of_piece(piece_arr, i, j)
                    for p, b in zip([tl,tr,bl,br],["br","bl","tr","tl"]):
                        if p:
                            if [x, y] in player.board_corners[b]:
                                is_corner_exists = True
                    for a, b in zip([x, x, x-1, x+1], [y-1, y+1, y, y]):
                        if a < 0 or b < 0 or a >= rows or b >= cols:
                            pass
                        else:
                            if self.board[a][b] == player.number:
                                is_there_a_pc_on_the_side = True
                elif piece_arr[i][j] == 1 and self.board[x][y] != empty:
                    return False
        if is_corner_exists and not is_there_a_pc_on_the_side:
            return True
        return False
    
    def validate_and_return_move_positions(self, piece_arr, player):
        place_on_board_at = []
        for x in range(self.board.shape[0]):
            for y in range(self.board.shape[1]):
                if self.board[x][y] == empty:
                    if self.check_is_move_valid(piece_arr, player, [x,y]):
                        place_on_board_at.append([x,y])
        return place_on_board_at

def get_corners_of_piece(piece_arr, i, j):
    tl, tr, bl, br = True, True, True, True
    x_lim, y_lim = piece_arr.shape[0], piece_arr.shape[1]
    try:
        if i+1 < x_lim and piece_arr[i+1][j] == 1: bl, br = False, False
    except IndexError: pass
    try:
        if i+1 < x_lim and j+1 < y_lim and piece_arr[i+1][j+1] == 1: br = False
    except IndexError: pass
    try:
        if j+1 < y_lim and piece_arr[i][j+1] == 1: tr, br = False, False
    except IndexError: pass
    try:
        if i-1 >= 0 and j+1 < y_lim and piece_arr[i-1][j+1] == 1: tr = False
    except IndexError: pass
    try:
        if i-1 >= 0 and piece_arr[i-1][j] == 1: tl, tr = False, False
    except IndexError: pass
    try:
        if i-1 >= 0 and j-1 >=0 and piece_arr[i-1][j-1] == 1: tl = False
    except IndexError: pass
    try:
        if j-1 >=0 and piece_arr[i][j-1] == 1: tl, bl = False, False
    except IndexError: pass
    try:
        if i+1 < x_lim and j-1 >=0 and piece_arr[i+1][j-1] == 1: bl = False
    except IndexError: pass
    return tl, tr, bl, br

def return_all_pending_moves(gameboard, player, mode = "ai"):
    pending_moves_list = []

    if player.is_1st_move:
        start_x, start_y = constants.STARTING_PTS["player%s" % (player.number)]
        for current_piece in pieces.get_all_piece_states(player):
            for x in range(current_piece["arr"].shape[0]):
                for y in range(current_piece["arr"].shape[1]):
                    if current_piece["arr"][x][y] == 1:
                        board_x = start_x - x
                        board_y = start_y - y
                        pending_moves_list.append({"piece": current_piece["piece"], \
                            "flipped": current_piece["flipped"], "arr": current_piece["arr"], \
                            "rotated": current_piece["rotated"], "place_on_board_at": [board_x, board_y]})
    else:
        for current_piece in pieces.get_all_piece_states(player):
            board_positions = gameboard.validate_and_return_move_positions(current_piece["arr"], player)
            for pos in board_positions:
                pending_moves_list.append({"piece": current_piece["piece"], "flipped": current_piece["flipped"],\
                            "arr": current_piece["arr"], "rotated": current_piece["rotated"], "place_on_board_at": pos})
                if mode == "is_game_over" and len(pending_moves_list) > 0:
                    return pending_moves_list
    if constants.VERBOSITY > 0 and len(pending_moves_list) > 0:
        msg = "Pending moves are: %s" % (pending_moves_list)
        print("Number of pending moves: %s" % (len(pending_moves_list)))
    elif constants.VERBOSITY > 0 and len(pending_moves_list) == 0:
        print("No more moves remain for player %s" % (player.number))
    return pending_moves_list

def is_game_over(board, player1, player2):
    if player1.is_1st_move or player2.is_1st_move:
        return False
    if not player1.remaining_pieces and not player2.remaining_pieces:
        return True
    if len(return_all_pending_moves(board, player1, "is_game_over")) == 0 and \
       len(return_all_pending_moves(board, player2, "is_game_over")) == 0:
        return True
    return False

def scoring_fn(remaining_pieces):
    score = constants.STARTING_SCORE
    if len(remaining_pieces) == 0:
        score += 15
    else:
        for _, val in remaining_pieces.items():
            for i in range(val["arr"].shape[0]):
                for j in range(val["arr"].shape[1]):
                    if val["arr"][i][j] == 1:
                        score -= 1
    if len(remaining_pieces) == 1 and "piece1" in remaining_pieces \
       and score == 88:
        score += 5
    return score

def check_higher_score(player1, player2):
    score1 = scoring_fn(player1.remaining_pieces)
    score2 = scoring_fn(player2.remaining_pieces)

    if score1 > score2: return player1
    elif score2 > score1: return player2
    else: return None #Draw