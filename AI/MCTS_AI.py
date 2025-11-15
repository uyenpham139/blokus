import random
import math
import copy
import board
import pieces
import time

class MCTSNode:
    def __init__(self, game_state, player, opponent, parent=None, move=None):
        self.game_state = game_state # The Board object
        self.player = player         # The player whose *turn it is* at this node
        self.opponent = opponent     # The other player
        self.parent = parent
        self.move = move             # The move that led to this state
        self.children = []
        self.wins = 0
        self.visits = 0
        # A list of players for game_over/fit_piece checks
        self.players_list = [player, opponent] 
        self.untried_moves = self.get_all_moves()

    def get_all_moves(self):
        # Get all possible moves for the current player
        return board.return_all_pending_moves(self.game_state, self.player)

    def uct_select_child(self, exploration_constant=1.414):
        # Select child with highest UCT value (Upper Confidence Bound for Trees)
        best_child = None
        best_score = -float('inf')
        
        for child in self.children:
            if child.visits == 0:
                # Prioritize unvisited nodes
                score = float('inf')
            else:
                exploit_term = child.wins / child.visits
                explore_term = exploration_constant * math.sqrt(math.log(self.visits) / child.visits)
                score = exploit_term + explore_term
            
            if score > best_score:
                best_score = score
                best_child = child
        return best_child

    def expand(self):
        # Expand one untried move
        if not self.untried_moves:
            return None # Fully expanded
            
        move = self.untried_moves.pop()
        
        # Create a new state by applying the move
        new_board = copy.deepcopy(self.game_state)
        new_player = copy.deepcopy(self.player)
        new_opponent = copy.deepcopy(self.opponent)
        
        # Apply the move
        new_board.fit_piece(move, new_player, [new_player, new_opponent])
        
        # Create the child node.
        # The "player" for the child is the *opponent* because it's their turn next.
        child_node = MCTSNode(new_board, new_opponent, new_player, parent=self, move=move)
        self.children.append(child_node)
        return child_node

    def simulate(self):
        # Simulate a random playout ("rollout") from this node's state
        current_board = copy.deepcopy(self.game_state)
        sim_player = copy.deepcopy(self.player) 
        sim_opponent = copy.deepcopy(self.opponent) 
        
        current_turn_player = sim_player
        other_player = sim_opponent
        players_list = [current_turn_player, other_player]

        # Limit simulation depth to avoid long rollouts
        for _ in range(40): # Max 40 moves (20 per player)
            
            if board.is_game_over(current_board, players_list):
                break

            possible_moves = board.return_all_pending_moves(current_board, current_turn_player)
            
            if not possible_moves:
                # Player has no moves, skip turn
                current_turn_player, other_player = other_player, current_turn_player
                continue

            # Play a random move
            move = random.choice(possible_moves)
            current_board.fit_piece(move, current_turn_player, players_list)
            
            # Swap turns
            current_turn_player, other_player = other_player, current_turn_player

        # Game is over or depth limit reached, determine winner
        # We must evaluate from the perspective of the player who *made the move to get here*
        # which is self.parent.player
        return self.get_simulation_result(current_board, self.parent.player, self.player)

    def get_simulation_result(self, final_board, original_player, opponent_player):
        # Check the score from the perspective of the *original* player
        winners = board.get_winners([original_player, opponent_player])
        
        if len(winners) == 1:
            if winners[0].number == original_player.number:
                return 1.0 # Win
            else:
                return 0.0 # Loss
        else:
            return 0.5 # Draw
            
    def backpropagate(self, result):
        # Update wins/visits up the tree
        current_node = self
        current_result = result
        while current_node is not None:
            current_node.visits += 1
            # The result is from the perspective of the *parent's* move.
            # We add the result to the parent's wins.
            # The child's "win" is (1 - parent_win).
            current_node.wins += current_result
            current_result = 1.0 - current_result # Invert result for parent
            current_node = current_node.parent

class MCTS:
    def __init__(self, player_color, player_number, iterations=100):
        self.color = player_color
        self.number = player_number
        self.iterations = iterations # Number of simulations

    def find_best_move(self, gameboard, player, opponent):
        # Create root node (it's the AI's turn)
        root = MCTSNode(gameboard, player, opponent)
        
        # Set a time limit for MCTS (e.g., 2 seconds)
        # end_time = time.time() + 2.0 
        # while time.time() < end_time:
        
        for _ in range(self.iterations):
            node = root
            
            # 1. Select
            while not node.untried_moves and node.children:
                node = node.uct_select_child()
            
            # 2. Expand
            if node.untried_moves:
                node = node.expand()
                if node is None: 
                    node = root

            # 3. Simulate
            if node: 
                result = node.simulate()
                # 4. Backpropagate
                node.backpropagate(result)
            
        # After iterations, choose the move that led to the most visited child
        if not root.children:
            return None # No possible moves
            
        best_child = max(root.children, key=lambda c: c.visits)
        return best_child.move