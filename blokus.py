import numpy as np, pygame, os, json
from enum import Enum
import board, pieces, constants, player, drawElements
from board import Board
from AI import AIManager
from drawElements import Button
from network import Network

os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (30, 30)
SAVE_FILE = "savegame.json"

class GameState(Enum):
    MAIN_MENU = 1
    DIFFICULTY_MENU = 2
    GAMEPLAY = 3
    QUIT = 4
    ROOM_LIST = 5
    IN_LOBBY = 6

class TextInputBox:
    def __init__(self, x, y, w, h, font, text=''):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = constants.BOARD_GRID
        self.text_color = constants.WHITE
        self.text = text
        self.font = font
        self.txt_surface = self.font.render(text, True, self.text_color)
        self.active = False
        self.cursor_visible = True
        self.cursor_timer = 0

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif len(self.text) < 20: # Limit room name length
                self.text += event.unicode
            self.txt_surface = self.font.render(self.text, True, self.text_color)

    def draw(self, screen):
        # Draw the box
        pygame.draw.rect(screen, self.color, self.rect)
        pygame.draw.rect(screen, constants.WHITE, self.rect, 2)
        # Blit the text
        screen.blit(self.txt_surface, (self.rect.x + 5, self.rect.y + 5))
        # Blit the cursor
        if self.active:
            self.cursor_timer = (self.cursor_timer + 1) % 40
            if self.cursor_timer < 20:
                cursor_x = self.rect.x + 5 + self.txt_surface.get_width()
                pygame.draw.line(screen, self.text_color, (cursor_x, self.rect.y + 5), (cursor_x, self.rect.y + self.rect.h - 5), 2)

class GameSession:
    def __init__(self, player_init_params, screen, background, clock, rows=constants.ROW_COUNT_2P, cols=constants.COLUMN_COUNT_2P, saved_state=None, online_net=None, local_pid=None):
        self.screen = screen
        self.background = background
        self.clock = clock
        self.rows = rows
        self.cols = cols
        
        # Networking 
        self.online_net = online_net
        self.local_pid = local_pid # 1, 2, 3, or 4 if online
        
        # drawElements.adjust_grid_scaling(self.rows)
        
        self.offset_list = []
        self.game_over = False
        self.selected = None
        # self.board_rects = drawElements.init_gameboard(Board().board)
        self.infobox_msg_time_start = None
        self.infobox_msg_timeout = 4000  # milliseconds
        self.infobox_msg = ""
        
        self.game_over_text = ""

        if saved_state:
            self.load_from_state(saved_state, player_init_params)
        else:
            self.gameboard = Board(self.rows, self.cols) # 14x14 or 20x20
            # self.player1, self.player2 = self.init_players(player_init_params)
            # self.players = self.init_players(player_init_params)
            # self.active_player, self.opponent = self.player1, self.player2
            self.players = self.init_players(player_init_params)
            self.active_player_idx = 0
            self.active_player = self.players[0]
        
        # drawElements.init_piece_rects(self.player1.remaining_pieces, self.player2.remaining_pieces)
        self.board_rects = drawElements.init_gameboard(self.gameboard.board, self.rows, self.cols)
        drawElements.init_piece_rects(self.players)

    # def init_players(self, player_init_params):
    #     player1 = player.Player(constants.PLAYER1_VALUE, player_init_params["p1"]["color"],
    #                             player_init_params["p1"]["is_ai"], player_init_params["p1"]["name_if_ai"],
    #                             player_init_params["p1"]["ai_class"])
    #     player2 = player.Player(constants.PLAYER2_VALUE, player_init_params["p2"]["color"],
    #                             player_init_params["p2"]["is_ai"], player_init_params["p2"]["name_if_ai"],
    #                             player_init_params["p2"]["ai_class"])
    #     return player1, player2
    
    def init_players(self, params):
        players = []
        # Setup 2 or 4 players based on params length
        # colors = [constants.PURPLE, constants.ORANGE, constants.RED, constants.GREEN]
        
        count = len(params)
        for i in range(count):
            p_data = params[f"p{i+1}"]
            new_p = player.Player(i+1, p_data["color"], p_data["is_ai"], p_data["name_if_ai"], p_data["ai_class"])
            players.append(new_p)
        return players
    
    def switch_turn(self):
        self.active_player_idx = (self.active_player_idx + 1) % len(self.players)
        self.active_player = self.players[self.active_player_idx]
        opponent_idx = (self.active_player_idx + 1) % len(self.players)
        return self.players[opponent_idx]

    # def event_handler(self):
    #     for event in pygame.event.get():
    #         if event.type == pygame.QUIT:
    #             return GameState.QUIT
    #         elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
    #             if self.selected is not None:
    #                 if drawElements.are_squares_within_board(self.active_player.current_piece, self.board_rects):
    #                     rect_coords = [self.active_player.current_piece["rects"][0].centerx,
    #                                    self.active_player.current_piece["rects"][0].centery]
    #                     board_arr_coords = drawElements.grid_to_array_coords(rect_coords)
    #                     j = 0
    #                     while not self.active_player.current_piece["arr"][0][j] == 1:
    #                         j += 1
    #                     board_arr_coords[1] -= j
    #                     self.active_player.current_piece["place_on_board_at"] = board_arr_coords
    #                     if self.gameboard.fit_piece(self.active_player.current_piece, self.active_player, self.opponent):
    #                         self.selected = None
    #                         self.active_player, self.opponent = player.switch_active_player(self.active_player, self.opponent)
    #                         self.save_game_state()
    #                     else:
    #                         self.display_infobox_msg_start("not_valid_move")
    #                 else:
    #                     self.selected = None
    #             else:
    #                 self.offset_list, self.selected = drawElements.generate_element_offsets(self.active_player.remaining_pieces, event)
    #                 if self.selected is not None:
    #                     self.active_player.current_piece["piece"] = self.selected
    #                     self.active_player.current_piece["arr"] = self.active_player.remaining_pieces[self.selected]["arr"]
    #                     self.active_player.current_piece["rects"] = self.active_player.remaining_pieces[self.selected]["rects"]
    #         elif event.type == pygame.MOUSEBUTTONUP:
    #             drawElements.init_piece_rects(self.player1.remaining_pieces, self.player2.remaining_pieces)
    #         elif event.type == pygame.KEYDOWN:
    #             if event.key == pygame.K_ESCAPE:
    #                 return GameState.MAIN_MENU
    #             if self.selected is not None:
    #                 self.key_controls(event)
    #     return None
    
    # def event_handler(self):
    #     # NETWORK CHECK: If online and not my turn, lock inputs
    #     if self.online_net and self.local_pid != self.active_player.number:
    #         # Poll network for opponent move
    #         server_data = self.online_net.receive_data() 
    #         # (In real implementation, do this in a non-blocking thread or small timeout)
    #         if server_data and server_data["last_move"]:
    #             self.apply_remote_move(server_data["last_move"])
    #         return None

    #     for event in pygame.event.get():
    #         if event.type == pygame.QUIT:
    #             return GameState.QUIT
    #         elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
    #             if self.selected is not None:
    #                 if drawElements.are_squares_within_board(self.active_player.current_piece, self.board_rects):
    #                     rect_coords = [self.active_player.current_piece["rects"][0].centerx,
    #                                    self.active_player.current_piece["rects"][0].centery]
    #                     board_arr_coords = drawElements.grid_to_array_coords(rect_coords)
                        
    #                     # Align logic
    #                     j = 0
    #                     while not self.active_player.current_piece["arr"][0][j] == 1:
    #                         j += 1
    #                     board_arr_coords[1] -= j
                        
    #                     move_data = {
    #                         "piece_name": self.selected,
    #                         "arr": self.active_player.current_piece["arr"],
    #                         "place_at": board_arr_coords,
    #                         "p_num": self.active_player.number
    #                     }

    #                     if self.gameboard.fit_piece(move_data, self.active_player):
    #                         self.selected = None
                            
    #                         # If Online, Send Move to Server
    #                         if self.online_net:
    #                             self.online_net.send(move_data)
                            
    #                         self.switch_turn()
    #                         if not self.online_net:
    #                             self.save_game_state()
    #                         # self.save_game_state()
    #                     else:
    #                         self.display_infobox_msg_start("not_valid_move")
    #                 else:
    #                     self.selected = None
    #             else:
    #                 self.offset_list, self.selected = drawElements.generate_element_offsets(self.active_player.remaining_pieces, event)
    #                 if self.selected is not None:
    #                     self.active_player.current_piece["piece"] = self.selected
    #                     self.active_player.current_piece["arr"] = self.active_player.remaining_pieces[self.selected]["arr"]
    #                     self.active_player.current_piece["rects"] = self.active_player.remaining_pieces[self.selected]["rects"]
    #         elif event.type == pygame.MOUSEBUTTONUP:
    #             drawElements.init_piece_rects(self.players)
    #         elif event.type == pygame.KEYDOWN:
    #             if event.key == pygame.K_ESCAPE:
    #                 return GameState.MAIN_MENU
    #             if self.selected is not None:
    #                 self.key_controls(event)
    #     return None
    
    def event_handler_local(self):
        """ A new event handler for LOCAL (vs AI) games only. """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return GameState.QUIT
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.selected is not None:
                    if drawElements.are_squares_within_board(self.active_player.current_piece, self.board_rects):
                        rect_coords = [self.active_player.current_piece["rects"][0].centerx, self.active_player.current_piece["rects"][0].centery]
                        board_arr_coords = drawElements.grid_to_array_coords(rect_coords)
                        
                        j = 0
                        while not self.active_player.current_piece["arr"][0][j] == 1: j += 1
                        board_arr_coords[1] -= j
                        
                        move_data = {
                            "piece_name": self.selected,
                            "arr": self.active_player.current_piece["arr"],
                            "place_on_board_at": board_arr_coords,
                            "p_num": self.active_player.number
                        }
                        
                        # --- LOCAL LOGIC ---
                        # Call fit_piece directly, not fit_piece_and_send
                        if self.gameboard.fit_piece(move_data, self.active_player, self.players):
                            self.selected = None
                            self.switch_turn() # Switch turn immediately
                            self.save_game_state() # Save the local game
                        else:
                            self.display_infobox_msg_start("not_valid_move")
                        # --------------------
                        
                    else:
                        self.selected = None
                else:
                    self.offset_list, self.selected = drawElements.generate_element_offsets(self.active_player.remaining_pieces, event)
                    if self.selected is not None:
                        self.active_player.current_piece["piece"] = self.selected
                        self.active_player.current_piece["arr"] = self.active_player.remaining_pieces[self.selected]["arr"]
                        self.active_player.current_piece["rects"] = self.active_player.remaining_pieces[self.selected]["rects"]
            
            elif event.type == pygame.MOUSEBUTTONUP:
                drawElements.init_piece_rects(self.players)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return GameState.MAIN_MENU
                if self.selected is not None:
                    self.key_controls(event)
        return None

    def event_handler_online(self):
        """ A simplified event handler that only sends moves """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return GameState.QUIT
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.selected is not None:
                    if drawElements.are_squares_within_board(self.active_player.current_piece, self.board_rects):
                        rect_coords = [self.active_player.current_piece["rects"][0].centerx, self.active_player.current_piece["rects"][0].centery]
                        board_arr_coords = drawElements.grid_to_array_coords(rect_coords)
                        
                        j = 0
                        while not self.active_player.current_piece["arr"][0][j] == 1: j += 1
                        board_arr_coords[1] -= j
                        
                        move_data = {
                            "piece_name": self.selected,
                            "arr": self.active_player.current_piece["arr"],
                            "place_on_board_at": board_arr_coords,
                            "p_num": self.active_player.number
                        }
                        
                        # --- Send move to server for validation ---
                        self.fit_piece_and_send(move_data)
                        
                    else:
                        self.selected = None
                else:
                    self.offset_list, self.selected = drawElements.generate_element_offsets(self.active_player.remaining_pieces, event)
                    if self.selected is not None:
                        self.active_player.current_piece["piece"] = self.selected
                        self.active_player.current_piece["arr"] = self.active_player.remaining_pieces[self.selected]["arr"]
                        self.active_player.current_piece["rects"] = self.active_player.remaining_pieces[self.selected]["rects"]
            
            elif event.type == pygame.MOUSEBUTTONUP:
                drawElements.init_piece_rects(self.players)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return GameState.MAIN_MENU
                if self.selected is not None:
                    self.key_controls(event)
        return None
    
    def fit_piece_and_send(self, move_data):
        # This is the logic from event_handler, wrapped
        if self.gameboard.fit_piece(move_data, self.active_player, self.players):
            self.selected = None
            if self.online_net:
                # Send the validated move
                self.online_net.send({
                    "action": "game_move", 
                    # "p_num": self.active_player.number, 
                    "move_data": move_data
                })
            self.switch_turn() # NO! Wait for server to confirm
        else:
            self.display_infobox_msg_start("not_valid_move")

    def apply_remote_move(self, move_data): 
        if not move_data: return
        
        p_idx = move_data["p_num"] - 1
        # Add a safety check in case a player disconnected
        if p_idx >= len(self.players):
            return 
            
        p = self.players[p_idx]
        
        move_struct = {
             "arr": move_data["arr"], 
             "place_on_board_at": move_data["place_on_board_at"], 
             "piece": move_data["piece_name"]
        }
        
        self.gameboard.fit_piece(move_struct, p, self.players)
        self.switch_turn()
    
    def key_controls(self, event):
        if event.key == pygame.K_LEFT:
            self.active_player.rotate_current_piece()
            self.offset_list = drawElements.draw_rotated_flipped_selected_piece(self.active_player.current_piece)
        elif event.key == pygame.K_RIGHT:
            self.active_player.rotate_current_piece(False)
            self.offset_list = drawElements.draw_rotated_flipped_selected_piece(self.active_player.current_piece)
        elif event.key == pygame.K_UP:
            self.active_player.flip_current_piece()
            self.offset_list = drawElements.draw_rotated_flipped_selected_piece(self.active_player.current_piece)

    def display_infobox_msg_start(self, msg_key):
        self.infobox_msg_time_start = pygame.time.get_ticks()
        self.infobox_msg = msg_key

    def display_infobox_msg_end(self, end_now=False):
        if end_now or (self.infobox_msg_time_start and pygame.time.get_ticks() - self.infobox_msg_time_start > self.infobox_msg_timeout):
            self.infobox_msg_time_start = None

    # def run(self):
    #     if self.active_player.is_ai:
    #         self.display_infobox_msg_start("ai_turn")
    #         self.draw()
    #         pygame.time.wait(100)
    #         AIManager.main(self.gameboard, self.active_player, self.opponent)
    #         self.active_player, self.opponent = player.switch_active_player(self.active_player, self.opponent)
    #         self.save_game_state()
    #         self.display_infobox_msg_end(True)
    #     else:
    #         new_state = self.event_handler()
    #         if new_state:
    #             return new_state

    #     self.draw()
    #     if board.is_game_over(self.gameboard, self.active_player, self.opponent):
    #         self.display_infobox_msg_start("game_over")
    #     return GameState.GAMEPLAY
    
    def run(self):
        
        # 1. Check for updates from server
        # server_data = self.online_net.receive_data(blocking=False)
        # if server_data:
        #     if server_data.get("action") == "game_update":
        #         # Server is broadcasting a move. Apply it.
        #         if server_data["game_state"]["last_move"]["p_num"] != self.local_pid:
        #             self.apply_remote_move(server_data["game_state"])
        #     elif server_data.get("action") == "room_disbanded":
        #         # Kicked from game
        #         return GameState.MAIN_MENU

        # # 2. Handle local input ONLY if it's our turn
        # if self.active_player.number == self.local_pid:
        #     new_state = self.event_handler_online()
        #     if new_state: return new_state
        # else:
        #     # Not my turn, just pump events to keep window alive
        #     for event in pygame.event.get():
        #         if event.type == pygame.QUIT:
        #             return GameState.QUIT
        #         if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
        #             return GameState.MAIN_MENU
                
        # if self.online_net:
        #     # Simplified Online Loop
        #     if self.active_player.number != self.local_pid:
        #         # Wait/Poll for server update
        #         pygame.event.pump() # Keep window alive
        #         state = self.online_net.receive_data() # This blocks in this simple example
        #         if state and state["last_move"]:
        #              # Check if we already applied this move to avoid duplication
        #              if state["turn"] != self.active_player.number: 
        #                  self.apply_remote_move(state["last_move"])
        #     else:
        #         new_state = self.event_handler()
        #         if new_state: return new_state
        # else:
        #     # Standard Local Logic
        #     if self.active_player.is_ai:
        #         self.draw()
        #         pygame.time.wait(100)
        #         opponent = self.players[(self.active_player_idx + 1) % len(self.players)] # Mock opponent
        #         AIManager.main(self.gameboard, self.active_player, opponent) 
        #         self.switch_turn()
        #     else:
        #         new_state = self.event_handler()
        #         if new_state: return new_state
        
        # # Check if Game is Over
        # if not self.game_over and board.is_game_over(self.gameboard, self.players):
        #     self.game_over = True
        #     winners = board.get_winners(self.players)
            
        #     if len(winners) == 1:
        #         self.game_over_text = f"Game Over! Player {winners[0].number} Wins!"
        #     else:
        #         winner_nums = ", ".join([str(p.number) for p in winners])
        #         self.game_over_text = f"Game Over! Tie: Players {winner_nums}"
                
        #     self.display_infobox_msg_start("game_over")

        # self.draw()
        # return GameState.GAMEPLAY
        if self.online_net:
            # --- ONLINE GAME LOOP ---
            
            # 1. Check for updates from server
            server_data = self.online_net.receive_data(blocking=False)
            if server_data:
                if server_data.get("action") == "game_move_broadcast":
                    move_data = server_data.get("move_data")
                    if move_data and move_data["p_num"] != self.local_pid:
                        self.apply_remote_move(move_data)
                elif server_data.get("action") == "room_disbanded":
                    # Kicked from game
                    return GameState.MAIN_MENU

            # 2. Handle local input ONLY if it's our turn
            if self.active_player.number == self.local_pid:
                new_state = self.event_handler_online() # Use the *online* handler
                if new_state: return new_state
            else:
                # Not my turn, just pump events to keep window alive
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return GameState.QUIT
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        return GameState.MAIN_MENU
        
        else:
            # --- LOCAL (AI) GAME LOOP ---
            if self.active_player.is_ai:
                self.draw()
                pygame.time.wait(100)
                opponent = self.players[(self.active_player_idx + 1) % len(self.players)]
                AIManager.main(self.gameboard, self.active_player, opponent) 
                self.switch_turn()
                self.save_game_state() # Save after AI move
            else:
                # It's the human's turn against the AI
                new_state = self.event_handler_local() # Use the new *local* handler
                if new_state: return new_state
        
        # Check if Game is Over
        if not self.game_over and board.is_game_over(self.gameboard, self.players):
            self.game_over = True
            winners = board.get_winners(self.players)
            
            if len(winners) == 1:
                self.game_over_text = f"Game Over! Player {winners[0].number} Wins!"
            else:
                winner_nums = ", ".join([str(p.number) for p in winners])
                self.game_over_text = f"Game Over! Tie: Players {winner_nums}"
                
            self.display_infobox_msg_start("game_over")

        self.draw()
        return GameState.GAMEPLAY

    def draw(self):
        self.background.fill(constants.BLACK)
        # drawElements.draw_infobox(self.background, self.player1, self.player2, self.active_player)
        drawElements.draw_infobox(self.background, self.players, self.active_player)
        # if self.infobox_msg_time_start is not None:
        #     drawElements.draw_infobox_msg(self.background, self.player1, self.player2, self.infobox_msg)
        #     self.display_infobox_msg_end()
        # drawElements.draw_gameboard(self.background, self.board_rects, self.gameboard, self.active_player.current_piece, self.active_player)
        # drawElements.draw_pieces(self.background, self.player1, self.player2, self.active_player, self.selected)
        # if self.selected is not None:
        #     drawElements.draw_selected_piece(self.background, self.offset_list, pygame.mouse.get_pos(), self.active_player.current_piece, self.active_player.color)
        # self.screen.blit(self.background, (0, 0))
        # pygame.display.update()
        
        if self.infobox_msg_time_start is not None:
            self.display_infobox_msg_end()
            
        drawElements.draw_gameboard(self.background, self.board_rects, self.gameboard, self.active_player.current_piece, self.active_player)
        drawElements.draw_pieces(self.background, self.players, self.active_player, self.selected)
        if self.selected is not None:
             drawElements.draw_selected_piece(self.background, self.offset_list, pygame.mouse.get_pos(), self.active_player.current_piece, self.active_player.color)
             
        if self.infobox_msg == "game_over" and self.game_over_text:
            # Create a semi-transparent background box
            font = pygame.font.SysFont("Trebuchet MS", 40)
            text_surf = font.render(self.game_over_text, True, constants.GREEN)
            text_rect = text_surf.get_rect(center=(constants.WINDOW_WIDTH/2, constants.WINDOW_HEIGHT - 50))
            
            bg_rect = text_rect.inflate(40, 20)
            s = pygame.Surface((bg_rect.width, bg_rect.height))
            s.set_alpha(200)
            s.fill(constants.BLACK)
            
            self.background.blit(s, bg_rect)
            self.background.blit(text_surf, text_rect)
            
        self.screen.blit(self.background, (0, 0))
        pygame.display.update()

    def get_state_to_save(self):
        # return {
        #     "board": self.gameboard.board.tolist(),
        #     "turn_number": self.gameboard.turn_number,
        #     "active_player_num": self.active_player.number,
        #     "player1": self.player1.get_state(),
        #     "player2": self.player2.get_state(),
        # }
        """Serializes the game state for saving."""
        player_states = [p.get_state() for p in self.players]
        
        return {
            "board": self.gameboard.board.tolist(),
            "turn_number": self.gameboard.turn_number,
            "rows": self.rows,
            "cols": self.cols,
            "active_player_idx": self.active_player_idx,
            "players": player_states
        }

    def save_game_state(self):
        state = self.get_state_to_save()
        with open(SAVE_FILE, 'w') as f:
            json.dump(state, f, indent=4)

    def load_from_state(self, saved_state, player_init_params):
        # self.gameboard = Board()
        # self.gameboard.board = np.array(saved_state["board"])
        # self.gameboard.turn_number = saved_state["turn_number"]
        
        # self.player1, self.player2 = self.init_players(player_init_params)
        # self.player1.load_state(saved_state["player1"])
        # self.player2.load_state(saved_state["player2"])

        # if saved_state["active_player_num"] == 1:
        #     self.active_player, self.opponent = self.player1, self.player2
        # else:
        #     self.active_player, self.opponent = self.player2, self.player1
        
        # self.gameboard.update_board_corners(self.player1, self.player2)
        """Loads the game state from a save file dictionary."""
        self.rows = saved_state["rows"]
        self.cols = saved_state["cols"]
        
        self.gameboard = Board(self.rows, self.cols)
        self.gameboard.board = np.array(saved_state["board"])
        self.gameboard.turn_number = saved_state["turn_number"]
        
        # Re-init players with correct classes (AI vs Human)
        self.players = self.init_players(player_init_params)
        
        # Load state into each player
        for i, p_state in enumerate(saved_state["players"]):
            self.players[i].load_state(p_state)
            
        self.active_player_idx = saved_state["active_player_idx"]
        self.active_player = self.players[self.active_player_idx]
        
        # Re-calculate corners for all players
        all_players = self.players
        for p in all_players:
             self.gameboard.update_board_corners(p, all_players)


class GameManager:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(constants.WINDOW_SIZE)
        self.background = pygame.Surface(constants.WINDOW_SIZE)
        pygame.display.set_caption("Blokus")
        self.clock = pygame.time.Clock()
        self.game_state = GameState.MAIN_MENU
        self.game_session = None
        
        self.net = None
        self.local_client_id = None
        self.current_room_info = None
        self.room_list = []
        self.create_room_popup_active = False
        self.popup_text_box = TextInputBox(440, 300, 400, 50, pygame.font.SysFont("Trebuchet MS", 30))
        self.popup_create_button = Button(540, 370, 200, 50, "Create", constants.GREEN, constants.ACCENT, "create_room_confirm")
        self.popup_close_button = Button(800, 240, 40, 40, "X", constants.RED, constants.ACCENT, "create_room_close")
    
    def main_loop(self):
        while self.game_state != GameState.QUIT:
            if self.game_state == GameState.MAIN_MENU:
                self.game_state = self.main_menu_loop()
            elif self.game_state == GameState.DIFFICULTY_MENU:
                self.game_state = self.difficulty_menu_loop()
            elif self.game_state == GameState.ROOM_LIST:
                self.game_state = self.room_list_loop()
            elif self.game_state == GameState.IN_LOBBY:
                self.game_state = self.room_lobby_loop()
            elif self.game_state == GameState.GAMEPLAY:
                self.game_state = self.game_session.run()
            self.clock.tick(60)
        pygame.quit()
    
    def main_menu_loop(self):
        buttons = [
            Button(440, 200, 400, 60, "1 Player (vs AI)", constants.PURPLE, constants.ACCENT, "vs_ai"),
            Button(440, 280, 400, 60, "4 Player (Online)", constants.GREEN, constants.ACCENT, "online"),
            Button(440, 360, 400, 60, "Continue", constants.ORANGE, constants.ACCENT, "continue"),
            Button(440, 440, 400, 60, "Quit", constants.RED, constants.ACCENT, "quit")
        ]
        while True:
            mouse_pos = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT: return GameState.QUIT
                for button in buttons:
                    action = button.handle_event(event)
                    if action == "vs_ai": return GameState.DIFFICULTY_MENU
                    if action == "online": 
                        # --- Connect to server ---
                        self.net = Network(constants.DEFAULT_HOST, constants.DEFAULT_PORT)
                        self.local_client_id = self.net.connect()
                        if self.local_client_id:
                            return GameState.ROOM_LIST # Go to new room list
                        else:
                            print("Could not connect to server.")
                            self.net = None
                    if action == "continue":
                        if self.load_game_state():
                            return GameState.GAMEPLAY
                    if action == "quit": return GameState.QUIT
            drawElements.draw_menu(self.screen, "Blokus", buttons, mouse_pos)
            pygame.display.update()
            
    def room_list_loop(self):
        """ Replaces multiplayer_menu_loop. Shows server list. """
        
        # Static buttons
        create_button = Button(50, 600, 300, 60, "Create Room", constants.GREEN, constants.ACCENT, "create_room_open")
        back_button = Button(930, 600, 300, 60, "Back", constants.RED, constants.ACCENT, "back")
        
        # Dynamic room buttons
        room_buttons = []
        
        refresh_timer = 0
        
        while True:
            mouse_pos = pygame.mouse.get_pos()
            
            # --- Non-blocking receive for server updates ---
            refresh_timer += self.clock.get_time()
            if refresh_timer > 2000: # Refresh list every 2 seconds
                refresh_timer = 0
                if self.net:
                    self.net.send({"action": "get_room_list"})
            
            server_data = self.net.receive_data(blocking=False)
            if server_data:
                if server_data.get("action") == "room_list":
                    self.room_list = server_data.get("rooms", [])
                    room_buttons = []
                    for i, room in enumerate(self.room_list):
                        y_pos = 150 + i * 70
                        btn = Button(700, y_pos, 150, 50, "Join", constants.PURPLE, constants.ACCENT, f"join_{room['id']}")
                        room_buttons.append(btn)
                elif server_data.get("action") == "room_joined":
                    self.current_room_info = server_data.get("room_info")
                    return GameState.IN_LOBBY
                elif server_data.get("action") == "error":
                    print(f"Server Error: {server_data.get('message')}")
            
            # --- Event Handling ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT: return GameState.QUIT
                
                if self.create_room_popup_active:
                    self.popup_text_box.handle_event(event)
                    action = self.popup_create_button.handle_event(event)
                    if action == "create_room_confirm":
                        room_name = self.popup_text_box.text
                        if room_name:
                            self.net.send({"action": "create_room", "name": room_name})
                            self.create_room_popup_active = False # Wait for server reply
                    if self.popup_close_button.handle_event(event) == "create_room_close":
                         self.create_room_popup_active = False
                else:
                    action = create_button.handle_event(event)
                    if action == "create_room_open":
                        self.popup_text_box.text = ""
                        self.create_room_popup_active = True
                    
                    if back_button.handle_event(event) == "back":
                        return GameState.MAIN_MENU
                    
                    for btn in room_buttons:
                        action = btn.handle_event(event)
                        if action and action.startswith("join_"):
                            room_id = int(action.split("_")[1])
                            self.net.send({"action": "join_room", "room_id": room_id})

            # --- Drawing ---
            self.screen.fill(constants.BLACK)
            title_font = pygame.font.SysFont("Trebuchet MS", 70)
            room_font = pygame.font.SysFont("Trebuchet MS", 30)
            
            title_surf = title_font.render("Server Rooms", True, constants.WHITE)
            self.screen.blit(title_surf, (constants.WINDOW_WIDTH / 2 - title_surf.get_width() / 2, 30))
            
            create_button.draw(self.screen, mouse_pos)
            back_button.draw(self.screen, mouse_pos)

            # Draw the room list
            for i, room in enumerate(self.room_list):
                y_pos = 150 + i * 70
                name_surf = room_font.render(room['name'], True, constants.WHITE)
                status_surf = room_font.render(f"Status: {room['player_count']} / {room['max_players']}", True, constants.WHITE)
                self.screen.blit(name_surf, (100, y_pos + 10))
                self.screen.blit(status_surf, (400, y_pos + 10))
                if i < len(room_buttons):
                    room_buttons[i].draw(self.screen, mouse_pos)

            # Draw "Create Room" Popup
            if self.create_room_popup_active:
                s = pygame.Surface((constants.WINDOW_WIDTH, constants.WINDOW_HEIGHT))
                s.set_alpha(200)
                s.fill(constants.BLACK)
                self.screen.blit(s, (0,0))
                
                # Draw popup box
                popup_rect = pygame.Rect(400, 200, 480, 300)
                pygame.draw.rect(self.screen, constants.BOARD_BACKGROUND, popup_rect, border_radius=12)
                pygame.draw.rect(self.screen, constants.WHITE, popup_rect, 2, border_radius=12)
                
                popup_title = room_font.render("Create Room", True, constants.WHITE)
                self.screen.blit(popup_title, (popup_rect.x + 20, popup_rect.y + 20))
                name_label = room_font.render("Name:", True, constants.WHITE)
                self.screen.blit(name_label, (popup_rect.x + 20, popup_rect.y + 80))
                
                self.popup_text_box.rect.topleft = (popup_rect.x + 20, popup_rect.y + 130)
                self.popup_create_button.rect.center = (popup_rect.centerx, popup_rect.y + 230)
                self.popup_close_button.rect.topright = (popup_rect.right - 10, popup_rect.top + 10)
                
                self.popup_text_box.draw(self.screen)
                self.popup_create_button.draw(self.screen, mouse_pos)
                self.popup_close_button.draw(self.screen, mouse_pos)
            
            pygame.display.update()
            self.clock.tick(30)

    def room_lobby_loop(self):
        """ Replaces online_lobby_loop. Shows players in a room. """
        
        my_ready_status = False
        ready_button = Button(440, 600, 400, 60, "Ready", constants.ORANGE, constants.ACCENT, "ready")
        start_button = Button(800, 600, 400, 60, "Start Game", constants.BOARD_GRID, constants.BOARD_GRID, "start_game") 
        
        is_host = self.current_room_info['players'][self.local_client_id]['is_host']
        
        while True:
            mouse_pos = pygame.mouse.get_pos()
            
            # --- Non-blocking receive for updates ---
            server_data = self.net.receive_data(blocking=False)
            if server_data:
                if server_data.get("action") == "room_update":
                    self.current_room_info = server_data.get("room_info")
                    is_host = self.current_room_info['players'][self.local_client_id]['is_host']
                elif server_data.get("action") == "game_start":
                    self.init_game_session(server_data.get("game_state"))
                    return GameState.GAMEPLAY
                elif server_data.get("action") == "room_disbanded":
                    return GameState.ROOM_LIST
            
            # --- Event Handling ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT: return GameState.QUIT
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return GameState.ROOM_LIST # TODO: Send "leave_room"
                
                action = ready_button.handle_event(event)
                if action == "ready":
                    my_ready_status = not my_ready_status
                    self.net.send({"action": "set_ready", "is_ready": my_ready_status})
                    ready_button.text = "Unready" if my_ready_status else "Ready"
                    ready_button.color = constants.GREEN if my_ready_status else constants.ORANGE

                if is_host:
                    action = start_button.handle_event(event)
                    if action == "start_game":
                        self.net.send({"action": "start_game"})

            # --- Drawing ---
            self.screen.fill(constants.BLACK)
            title_font = pygame.font.SysFont("Trebuchet MS", 70)
            player_font = pygame.font.SysFont("Trebuchet MS", 40)
            
            room_name = self.current_room_info['name']
            title_surf = title_font.render(f"Room: {room_name}", True, constants.WHITE)
            self.screen.blit(title_surf, (constants.WINDOW_WIDTH / 2 - title_surf.get_width() / 2, 30))
            
            # Draw player list
            player_ids = list(self.current_room_info['players'].keys())
            for i, p_id in enumerate(player_ids):
                player = self.current_room_info['players'][p_id]
                y_pos = 150 + i * 80
                
                player_name = player['name']
                if p_id == self.local_client_id:
                    player_name += " (You)"
                
                name_surf = player_font.render(player_name, True, constants.WHITE)
                self.screen.blit(name_surf, (200, y_pos))
                
                status_text = "Ready" if player['is_ready'] else "Waiting..."
                status_color = constants.GREEN if player['is_ready'] else constants.RED
                status_surf = player_font.render(status_text, True, status_color)
                self.screen.blit(status_surf, (800, y_pos))

            ready_button.draw(self.screen, mouse_pos)
            
            # Enable/Disable Start button
            all_ready = all(p["is_ready"] for p in self.current_room_info['players'].values())
            if is_host and all_ready and len(self.current_room_info['players']) == 4:
                start_button.color = constants.GREEN
                start_button.hover_color = constants.ACCENT
            else:
                start_button.color = constants.BOARD_GRID
                start_button.hover_color = constants.BOARD_GRID

            if is_host:
                start_button.draw(self.screen, mouse_pos)

            pygame.display.update()
            self.clock.tick(30)
    
    def init_game_session(self, initial_game_state):
        """ Creates the game session once the server gives the start signal. """
        
        p1 = {"is_ai": False, "color": constants.PURPLE, "name_if_ai": None, "ai_class": None}
        p2 = {"is_ai": False, "color": constants.ORANGE, "name_if_ai": None, "ai_class": None}
        p3 = {"is_ai": False, "color": constants.RED, "name_if_ai": None, "ai_class": None}
        p4 = {"is_ai": False, "color": constants.GREEN, "name_if_ai": None, "ai_class": None}
        params = {"p1": p1, "p2": p2, "p3": p3, "p4": p4}
        
        self.game_session = GameSession(params, self.screen, self.background, self.clock, 
                                        rows=constants.ROW_COUNT_4P, cols=constants.COLUMN_COUNT_4P, 
                                        online_net=self.net, local_pid=self.local_client_id)
        
        self.game_session.gameboard.turn_number = initial_game_state.get("turn", 1)

    def difficulty_menu_loop(self):
        buttons = [
            Button(440, 320, 400, 60, "Easy", constants.GREEN, constants.ACCENT, "easy"),
            Button(440, 400, 400, 60, "Hard", constants.RED, constants.ACCENT, "hard"),
            Button(440, 520, 400, 60, "Back", (100, 100, 100), constants.ACCENT, "back")
        ]
        while True:
            mouse_pos = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT: return GameState.QUIT
                for button in buttons:
                    action = button.handle_event(event)
                    if action == "easy":
                        ai_param = constants.AI_PARAMS["mcts_easy_p2"]
                        params = {"p1": constants.HUMAN_PARAMS["default_p1"], "p2": ai_param}
                        self.game_session = GameSession(params, self.screen, self.background, self.clock,
                                                        rows=constants.ROW_COUNT_2P, cols=constants.COLUMN_COUNT_2P)
                        return GameState.GAMEPLAY
                    if action == "hard":
                        ai_param = constants.AI_PARAMS["mcts_hard_p2"]
                        params = {"p1": constants.HUMAN_PARAMS["default_p1"], "p2": ai_param}
                        self.game_session = GameSession(params, self.screen, self.background, self.clock,
                                                        rows=constants.ROW_COUNT_2P, cols=constants.COLUMN_COUNT_2P)
                        return GameState.GAMEPLAY
                    if action == "back": return GameState.MAIN_MENU
            drawElements.draw_menu(self.screen, "Select Difficulty", buttons, mouse_pos)
            pygame.display.update()
            self.clock.tick(60)

    def load_game_state(self):
        """Loads the game state from the save file."""
        if not os.path.exists(SAVE_FILE):
            print("No save file found.")
            return False
        with open(SAVE_FILE, 'r') as f:
            try:
                saved_state = json.load(f)
            except json.JSONDecodeError:
                print("Save file is corrupted.")
                return False
        
        player_init_params = {}
        for i, p_state in enumerate(saved_state["players"]):
            pid = i + 1
            if p_state["is_ai"]:
                if p_state["ai_name"] == "MinimaxAI":
                     params = constants.AI_PARAMS["alphabeta_hard_p2"]
                else:
                     params = constants.AI_PARAMS["randombot_p2"] 
            else:
                params = constants.HUMAN_PARAMS["default_p1"]             
            player_init_params[f"p{pid}"] = params
            
        self.game_session = GameSession(player_init_params, self.screen, self.background, self.clock, rows=saved_state["rows"], cols=saved_state["cols"], saved_state=saved_state)
        return True

if __name__ == "__main__":
    manager = GameManager()
    manager.main_loop()