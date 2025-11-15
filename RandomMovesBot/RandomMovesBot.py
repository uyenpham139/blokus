import numpy as np, random, board, constants
#This computer "player" just keeps playing random moves
#This random moves player serves as a good opponent for our actual AI

def return_random_move(gameboard, player):
    if player.is_1st_move:
        return return_first_turn_move(player)
    else:
        all_moves = board.return_all_pending_moves(gameboard, player)
        if len(all_moves) > 0:
            chosen_move = random.choice(all_moves)
            if constants.VERBOSITY > 0:
                print("Chosen move for RandomMovesBot: %s" % (chosen_move))
            return chosen_move
    return None

def return_first_turn_move(player):
    pieces = list(player.remaining_pieces.keys())
    #Lets not use the 1x1 piece in the beginning
    pieces.remove("piece1")
    piece = random.choice(pieces)
    
    piece_arr = player.remaining_pieces[piece]["arr"]
    
    flips = player.remaining_pieces[piece]["flips"]
    flip = random.choice(range(flips))

    rots = player.remaining_pieces[piece]["rots"]
    rot = random.choice(range(rots))

    start_x, start_y = constants.STARTING_PTS["player%s" % (player.number)]
    
    piece_arr = np.rot90(piece_arr, k = rot)
    if flip == 1:
        piece_arr = np.flipud(piece_arr)
    
    choice_x = random.choice(range(piece_arr.shape[0]))
    choice_y = random.choice(range(piece_arr.shape[1]))
    #The unit sq randomly selected for the piece must be a valid unit sq 
    while piece_arr[choice_x][choice_y] != 1:
        choice_x = random.choice(range(piece_arr.shape[0]))
        choice_y = random.choice(range(piece_arr.shape[1]))
    board_x = start_x - choice_x
    board_y = start_y - choice_y

    move = {"piece" : piece, "arr" : piece_arr, "rotated" : rot, "flipped" : flip, \
            "place_on_board_at" : [board_x, board_y]}
    if constants.VERBOSITY > 0:
        print("Chosen first move for RandomMovesBot: %s" % (move))
    return move