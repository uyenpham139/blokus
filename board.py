import numpy as np
import constants, pieces

empty = constants.BOARD_FILL_VALUE

class Board:
    def __init__(self, rows=constants.ROW_COUNT_2P, cols=constants.COLUMN_COUNT_2P, player_count=2):
        self.rows = rows
        self.cols = cols
        self.board = np.array([[constants.BOARD_FILL_VALUE for i in range(rows)] for j in range(cols)])
        self.turn_number = 1
        self.start_points = constants.get_start_points(rows, cols, player_count)
    
    def fit_piece(self, piece_data, player, players_list=None):
        """
        piece_data: dict containing "arr" and "place_on_board_at"
        player: the player object placing the piece
        players_list: list of all players (to update their corners)
        """
        piece_arr = piece_data["arr"]
        pos_coords = piece_data["place_on_board_at"]
        
        piece_x_rng = range(piece_arr.shape[0])
        piece_y_rng = range(piece_arr.shape[1])
        board_x_rng = range(pos_coords[0], self.rows)
        board_y_rng = range(pos_coords[1], self.cols)
        
        # 1. HANDLE FIRST MOVE (Dynamic Start Points)
        if player.is_1st_move:
            # Get start point for this specific player number (1-4)
            # This will now correctly be [0,0] for both P1 and P2 in a 2P game
            target_pos = self.start_points[player.number]
            
            is_within_starting_pos = False
            for i, x in zip(piece_x_rng, board_x_rng):
                for j, y in zip(piece_y_rng, board_y_rng):
                    if [x, y] == target_pos and piece_arr[i][j] == 1:
                        is_within_starting_pos = True
            
            if is_within_starting_pos:
                for i, x in zip(piece_x_rng, board_x_rng):
                    for j, y in zip(piece_y_rng, board_y_rng):
                        if piece_arr[i][j] == 1 and self.board[x][y] == empty:
                            self.board[x][y] = player.number * piece_arr[i][j]
            else:
                if constants.VERBOSITY > 0:
                    print(f"Piece placed at {pos_coords} didn't cover start point {target_pos}")
                return False    
            player.is_1st_move = False

        # 2. HANDLE REGULAR MOVES
        else:
            if self.check_is_move_valid(piece_arr, player, pos_coords):
                for i, x in zip(piece_x_rng, board_x_rng):
                    for j, y in zip(piece_y_rng, board_y_rng):
                        if piece_arr[i][j] == 1:
                            self.board[x][y] = player.number * piece_arr[i][j]
            else:
                if constants.VERBOSITY > 0:
                    print("Invalid move attempted in fit_piece")
                return False

        piece_name = piece_data.get("piece_name")
        if not piece_name:
            piece_name = piece_data.get("piece")

        piece_info = {"piece": piece_name, 
                      "arr": piece_arr, 
                      "place_on_board_at": pos_coords}
        
        player.discard_piece(piece_info)
        player.empty_current_piece()
        self.turn_number += 1
        player.turn_number += 1
        player.update_score()
        
        target_players = players_list if players_list else [player]
        self.optimised_update_board_corners(piece_info, target_players)
        
        return True
    
    def unfit_last_piece(self, player, players_list):
        piece = player.retrieve_last_piece()

        piece_x_rng = range(piece["arr"].shape[0])
        piece_y_rng = range(piece["arr"].shape[1])
        board_x_rng = range(piece["place_on_board_at"][0], self.rows)
        board_y_rng = range(piece["place_on_board_at"][1], self.cols)

        for i, x in zip(piece_x_rng, board_x_rng):
            for j, y in zip(piece_y_rng, board_y_rng):
                if piece["arr"][i][j] == 1:
                    self.board[x][y] = empty
        
        self.turn_number -= 1
        player.turn_number -= 1
        player.update_score()
        
        self.update_board_corners(players_list)
    
    def update_board_corners(self, players_list):
        """Full scan update for all players in list."""
        for p in players_list:
            p.board_corners = {"bl":[],"br":[],"tl":[],"tr":[]}
            for x in range(self.rows):
                for y in range(self.cols):
                    if self.board[x][y] == p.number:
                        tl, tr, bl, br = self.check_surrounding_piece_coords(x, y, p.number)
                        if tl and x-1 >= 0 and y-1 >= 0:
                            p.board_corners["tl"].append([x-1, y-1])
                        if bl and x+1 < self.rows and y-1 >= 0:
                            p.board_corners["bl"].append([x+1, y-1])
                        if tr and x-1 >= 0 and y+1 < self.cols:
                            p.board_corners["tr"].append([x-1, y+1])
                        if br and x+1 < self.rows and y+1 < self.cols:
                            p.board_corners["br"].append([x+1,y+1])
    
    def optimised_update_board_corners(self, piece_played, players_list):
        """Updates corners relative to the specific piece placed."""
        b_x_low, b_y_low = piece_played["place_on_board_at"][0], piece_played["place_on_board_at"][1]
        b_x_high = b_x_low + piece_played["arr"].shape[0]
        b_y_high = b_y_low + piece_played["arr"].shape[1]
        
        x_low = 0 if b_x_low == 0 else b_x_low - 1
        y_low = 0 if b_y_low == 0 else b_y_low - 1
        x_high = self.rows if b_x_high >= self.rows else b_x_high + 1
        y_high = self.cols if b_y_high >= self.cols else b_y_high + 1

        for p in players_list:
            for x in range(x_low, x_high):
                for y in range(y_low, y_high):
                    if self.board[x][y] == p.number:
                        tl, tr, bl, br = self.check_surrounding_piece_coords(x, y, p.number)
                        
                        def update_corner(condition, c_list, coord):
                            if condition:
                                if coord not in c_list: c_list.append(coord)
                            else:
                                if coord in c_list: c_list.remove(coord)

                        if x-1 >= 0 and y-1 >= 0:
                            update_corner(tl, p.board_corners["tl"], [x-1, y-1])
                        if x+1 < self.rows and y-1 >= 0:
                            update_corner(bl, p.board_corners["bl"], [x+1, y-1])
                        if x-1 >= 0 and y+1 < self.cols:
                            update_corner(tr, p.board_corners["tr"], [x-1, y+1])
                        if x+1 < self.rows and y+1 < self.cols:
                            update_corner(br, p.board_corners["br"], [x+1, y+1])
    
    def check_surrounding_piece_coords(self, x, y, p_num):
        tl, tr, bl, br = True, True, True, True
        try:
            if x-1 >= 0 and self.board[x-1][y+1] != empty: tr = False
        except IndexError: tr = False
        try:
            if x+1 < self.rows and y+1 < self.cols and self.board[x+1][y+1] != empty: br = False
        except IndexError: br = False
        try:
            if y-1 >= 0 and x+1 < self.rows and self.board[x+1][y-1] != empty: bl = False
        except IndexError: bl = False
        try:
            if x-1 >= 0 and y-1 >= 0 and self.board[x-1][y-1] != empty: tl = False
        except IndexError: tl = False
        
        try:
            if y+1 < self.cols and self.board[x][y+1] == p_num: tr, br = False, False
        except IndexError: tr, br = False, False
        try:
            if x+1 < self.rows and self.board[x+1][y] == p_num: bl, br = False, False
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
        board_x_rng = range(coords[0], self.rows)
        board_y_rng = range(coords[1], self.cols)
        
        if piece_arr.shape[0] + coords[0] > self.rows\
           or piece_arr.shape[1] + coords[1] > self.cols:
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
                        if a < 0 or b < 0 or a >= self.rows or b >= self.cols:
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
        for x in range(self.rows):
            for y in range(self.cols):
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
        # This will now correctly be [0,0] for both P1 and P2 in a 2P game
        start_x, start_y = gameboard.start_points[player.number]
        
        for current_piece in pieces.get_all_piece_states(player):
            for x in range(current_piece["arr"].shape[0]):
                for y in range(current_piece["arr"].shape[1]):
                    if current_piece["arr"][x][y] == 1:
                        board_x = start_x - x
                        board_y = start_y - y
                        
                        # --- Add boundary check to prevent crashes ---
                        if (board_x >= 0 and board_y >= 0 and 
                            board_x + current_piece["arr"].shape[0] <= gameboard.rows and 
                            board_y + current_piece["arr"].shape[1] <= gameboard.cols):
                        
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
    return pending_moves_list

def check_if_player_can_move(gameboard, player):
    """
    A *smarter*, faster check to see if a player has *any* valid move.
    It only checks piece placements against available corner locations.
    """
    if not player.remaining_pieces:
        return False

    if player.is_1st_move:
        # Check if *any* piece can be placed on the start point
        start_x, start_y = gameboard.start_points[player.number]
        for piece_name in player.remaining_pieces.keys():
            piece_data = player.remaining_pieces[piece_name]
            # Use the helper function from pieces.py
            orientations = pieces.get_all_piece_states_for_one_piece(piece_name, piece_data)
            for state in orientations:
                arr = state["arr"]
                for x in range(arr.shape[0]):
                    for y in range(arr.shape[1]):
                        if arr[x][y] == 1:
                            board_x, board_y = start_x - x, start_y - y
                            # Check if it fits within bounds
                            if (board_x >= 0 and board_y >= 0 and 
                                board_x + arr.shape[0] <= gameboard.rows and 
                                board_y + arr.shape[1] <= gameboard.cols):
                                # This move is *possible*.
                                return True
        return False # No piece could be placed on start
    
    else:
        # This is the main performance hog.
        # Get all possible corners the player can play on.
        all_corners = []
        for corner_list in player.board_corners.values():
            all_corners.extend(corner_list)
        
        if not all_corners:
            return False # No corners, no moves.

        # Now, for each remaining piece...
        for piece_name in player.remaining_pieces.keys():
            piece_data = player.remaining_pieces[piece_name]
            orientations = pieces.get_all_piece_states_for_one_piece(piece_name, piece_data)
            
            # ...and each orientation...
            for state in orientations:
                arr = state["arr"]
                # ...find all the blocks in that piece...
                piece_blocks = []
                for r in range(arr.shape[0]):
                    for c in range(arr.shape[1]):
                        if arr[r][c] == 1:
                            piece_blocks.append((r, c))
                
                if not piece_blocks: continue

                # ...and for each corner, try to place each block on it.
                # Use a set to avoid re-checking the same placement
                checked_placements = set() 
                for corner_x, corner_y in all_corners:
                    for anchor_r, anchor_c in piece_blocks:
                        board_x = corner_x - anchor_r
                        board_y = corner_y - anchor_c
                        
                        placement_key = (board_x, board_y, state["rotated"], state["flipped"])
                        if placement_key in checked_placements:
                            continue
                        checked_placements.add(placement_key)

                        # Now check if this placement is valid
                        if gameboard.check_is_move_valid(arr, player, [board_x, board_y]):
                            return True # Found one!
        
        return False

def is_game_over(board, players_list):
    """
    Checks if game is over for a list of players (2 or 4).
    Returns True only if ALL players are unable to move.
    
    NOW USES THE FAST 'check_if_player_can_move' FUNCTION
    """
    for p in players_list:
        # Use the fast check
        if check_if_player_can_move(board, p):
            return False 
    
    return True

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

def get_winners(players_list):
    """
    Returns a list of players with the highest score.
    Handles 2-player and 4-player scenarios, including ties.
    """
    for p in players_list:
        p.score = scoring_fn(p.remaining_pieces)
        
    max_score = max(p.score for p in players_list)
    
    winners = [p for p in players_list if p.score == max_score]
    
    return winners