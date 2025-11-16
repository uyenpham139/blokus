import numpy as np, random, board, constants, pieces

def return_random_move(gameboard, player):
    if player.is_1st_move:
        return return_first_turn_move(gameboard, player) # First turn logic is fine

    # 1. Get all available corners
    all_corners = []
    for corner_list in player.board_corners.values():
        all_corners.extend(corner_list)
    
    if not all_corners:
        if constants.VERBOSITY > 0:
            print("RandomMovesBot (FAST) has no available corners.")
        return None # No corners, no moves.

    # 2. Get a shuffled list of pieces to try
    remaining_pieces_keys = list(player.remaining_pieces.keys())
    if not remaining_pieces_keys:
        return None # No pieces left
        
    random.shuffle(remaining_pieces_keys)
    
    # 3. Loop through pieces one by one
    for piece_name in remaining_pieces_keys:
        piece_data = player.remaining_pieces[piece_name]
        
        # Get all orientations for this piece
        orientations = pieces.get_all_piece_states_for_one_piece(piece_name, piece_data)
        random.shuffle(orientations)
        
        for state in orientations:
            arr = state["arr"]
            
            # Find all the blocks in this piece
            piece_blocks = []
            for r in range(arr.shape[0]):
                for c in range(arr.shape[1]):
                    if arr[r][c] == 1:
                        piece_blocks.append((r, c))
            
            if not piece_blocks: continue
            
            # Shuffle corners and anchors for randomness
            random.shuffle(all_corners)
            random.shuffle(piece_blocks)
            
            # 4. Check this piece against the available corners
            for corner_x, corner_y in all_corners:
                for anchor_r, anchor_c in piece_blocks:
                    
                    # Calculate the potential top-left placement
                    board_x = corner_x - anchor_r
                    board_y = corner_y - anchor_c
                    
                    # Check if this move is valid
                    if gameboard.check_is_move_valid(arr, player, [board_x, board_y]):
                        # SUCCESS! Found a move.
                        move = {
                            "piece": piece_name, 
                            "flipped": state["flipped"],
                            "arr": arr, 
                            "rotated": state["rotated"], 
                            "place_on_board_at": [board_x, board_y]
                        }
                        if constants.VERBOSITY > 0:
                            print("Chosen move for RandomMovesBot (FAST): %s" % (move))
                        return move

    # 5. If we loop through everything and find no moves
    if constants.VERBOSITY > 0:
        print("RandomMovesBot (FAST) found no moves.")
    return None


def return_first_turn_move(gameboard, player):
    """
    (This function is unchanged)
    Generates a random VALID first move.
    """
    pieces_keys = list(player.remaining_pieces.keys())
    
    random.shuffle(pieces_keys)

    start_x, start_y = gameboard.start_points[player.number]

    for piece in pieces_keys:
        piece_data = player.remaining_pieces[piece]
        original_arr = piece_data["arr"]
        
        for _ in range(20): 
            flips = piece_data["flips"]
            flip = random.choice(range(flips))
            
            rots = piece_data["rots"]
            rot = random.choice(range(rots))

            current_arr = np.rot90(original_arr, k=rot)
            if flip == 1:
                current_arr = np.flipud(current_arr)
            
            valid_anchors = []
            for r in range(current_arr.shape[0]):
                for c in range(current_arr.shape[1]):
                    if current_arr[r][c] == 1:
                        valid_anchors.append((r, c))
            
            if not valid_anchors:
                continue

            anchor_r, anchor_c = random.choice(valid_anchors)
            board_x = start_x - anchor_r
            board_y = start_y - anchor_c

            if (board_x >= 0 and board_y >= 0 and 
                board_x + current_arr.shape[0] <= gameboard.rows and 
                board_y + current_arr.shape[1] <= gameboard.cols):
                
                move = {
                    "piece": piece, 
                    "arr": current_arr, 
                    "rotated": rot, 
                    "flipped": flip,
                    "place_on_board_at": [board_x, board_y]
                }
                
                if constants.VERBOSITY > 0:
                    print("Chosen first move for RandomMovesBot: %s" % (move))
                return move

    print("RandomMovesBot could not find a valid first move (unlikely).")
    return None