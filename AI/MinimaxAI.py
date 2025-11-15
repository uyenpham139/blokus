import copy
import board, pieces, constants
from .cost_function.GreedyEvaluate import main as GreedyEvaluate

class Minimax:
    def __init__(self, player_color, player_number, depth=2):
        self.color = player_color
        self.number = player_number
        self.depth = depth

    def find_best_move(self, gameboard, player, opponent):
        _, best_move = self.minimax_alpha_beta(gameboard, player, opponent, self.depth, constants.M_INFINITY, constants.INFINITY, True)
        return best_move

    def minimax_alpha_beta(self, gameboard, player, opponent, depth, alpha, beta, maximizing_player):
        players_list = [player, opponent]
        if depth == 0 or board.is_game_over(gameboard, players_list):
            return GreedyEvaluate(gameboard, player, opponent), None

        if maximizing_player:
            max_eval = constants.M_INFINITY
            best_move = None
            possible_moves = board.return_all_pending_moves(gameboard, player)
            
            possible_moves.sort(key=lambda m: pieces.get_piece_size(m['piece']), reverse=True)

            for move in possible_moves:
                gameboard_copy = copy.deepcopy(gameboard)
                player_copy = copy.deepcopy(player)
                opponent_copy = copy.deepcopy(opponent)
                
                if gameboard_copy.fit_piece(move, player_copy, [player_copy, opponent_copy]):
                    evaluation, _ = self.minimax_alpha_beta(gameboard_copy, player_copy, opponent_copy, depth - 1, alpha, beta, False)
                    if evaluation > max_eval:
                        max_eval = evaluation
                        best_move = move
                    alpha = max(alpha, evaluation)
                    if beta <= alpha:
                        break
            return max_eval, best_move
        else: 
            min_eval = constants.INFINITY
            best_move = None
            possible_moves = board.return_all_pending_moves(gameboard, opponent)

            possible_moves.sort(key=lambda m: pieces.get_piece_size(m['piece']), reverse=True)

            for move in possible_moves:
                gameboard_copy = copy.deepcopy(gameboard)
                player_copy = copy.deepcopy(player)
                opponent_copy = copy.deepcopy(opponent)

                if gameboard_copy.fit_piece(move, opponent_copy, [player_copy, opponent_copy]):
                    evaluation, _ = self.minimax_alpha_beta(gameboard_copy, player_copy, opponent_copy, depth - 1, alpha, beta, True)
                    if evaluation < min_eval:
                        min_eval = evaluation
                        best_move = move
                    beta = min(beta, evaluation)
                    if beta <= alpha:
                        break
            return min_eval, best_move