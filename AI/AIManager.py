from RandomMovesBot.RandomMovesBot import return_random_move
from board import is_game_over

def main(gameboard, ai_player, opponent_player):
    best_move = None
    ai_name = ai_player.ai_name

    if ai_name == "MinimaxAI":
        if hasattr(ai_player, 'ai_class') and ai_player.ai_class:
            best_move = ai_player.ai_class.find_best_move(gameboard, ai_player, opponent_player)
        else:
            raise TypeError("MinimaxAI is not properly initialized on the player object.")

    elif ai_name == "RandomMovesBot":
        best_move = return_random_move(gameboard, ai_player)

    elif ai_name == "ReinforcementLearningAI":
        if hasattr(ai_player, 'ai_class') and ai_player.ai_class:
            best_move = ai_player.ai_class.explore_or_exploit(gameboard, ai_player, opponent_player)
        else:
            from AI import ReinforcementLearningAI
            best_move = ReinforcementLearningAI.main(gameboard, ai_player, opponent_player)
    
    else:
        print(f"Warning: AI '{ai_name}' not recognized. Falling back to random moves.")
        best_move = return_random_move(gameboard, ai_player)

    if best_move is not None:
        if not gameboard.fit_piece(best_move, ai_player, opponent_player, mode="ai"):
            print(f"CRITICAL ERROR: For player {ai_player.ai_name}, the following move failed:\n {best_move}")
            print(f"The state of the gameboard is: \n{gameboard.board}")
            raise Exception("Piece selected by AI was not fit")
    
    return best_move
