import numpy as np, pygame, os, json
from enum import Enum
import board, pieces, constants, player, drawElements
from board import Board
from AI import AIManager
from drawElements import Button

os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (30, 30)
SAVE_FILE = "savegame.json"

class GameState(Enum):
    MAIN_MENU = 1
    DIFFICULTY_MENU = 2
    GAMEPLAY = 3
    QUIT = 4

class GameSession:
    def __init__(self, player_init_params, screen, background, clock, saved_state=None):
        self.screen = screen
        self.background = background
        self.clock = clock
        self.offset_list = []
        self.game_over = False
        self.selected = None
        self.board_rects = drawElements.init_gameboard(Board().board)
        self.infobox_msg_time_start = None
        self.infobox_msg_timeout = 4000  # milliseconds
        self.infobox_msg = ""

        if saved_state:
            self.load_from_state(saved_state, player_init_params)
        else:
            self.gameboard = Board()
            self.player1, self.player2 = self.init_players(player_init_params)
            self.active_player, self.opponent = self.player1, self.player2
        
        drawElements.init_piece_rects(self.player1.remaining_pieces, self.player2.remaining_pieces)

    def init_players(self, player_init_params):
        player1 = player.Player(constants.PLAYER1_VALUE, player_init_params["p1"]["color"],
                                player_init_params["p1"]["is_ai"], player_init_params["p1"]["name_if_ai"],
                                player_init_params["p1"]["ai_class"])
        player2 = player.Player(constants.PLAYER2_VALUE, player_init_params["p2"]["color"],
                                player_init_params["p2"]["is_ai"], player_init_params["p2"]["name_if_ai"],
                                player_init_params["p2"]["ai_class"])
        return player1, player2

    def event_handler(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return GameState.QUIT
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.selected is not None:
                    if drawElements.are_squares_within_board(self.active_player.current_piece, self.board_rects):
                        rect_coords = [self.active_player.current_piece["rects"][0].centerx,
                                       self.active_player.current_piece["rects"][0].centery]
                        board_arr_coords = drawElements.grid_to_array_coords(rect_coords)
                        j = 0
                        while not self.active_player.current_piece["arr"][0][j] == 1:
                            j += 1
                        board_arr_coords[1] -= j
                        self.active_player.current_piece["place_on_board_at"] = board_arr_coords
                        if self.gameboard.fit_piece(self.active_player.current_piece, self.active_player, self.opponent):
                            self.selected = None
                            self.active_player, self.opponent = player.switch_active_player(self.active_player, self.opponent)
                            self.save_game_state()
                        else:
                            self.display_infobox_msg_start("not_valid_move")
                    else:
                        self.selected = None
                else:
                    self.offset_list, self.selected = drawElements.generate_element_offsets(self.active_player.remaining_pieces, event)
                    if self.selected is not None:
                        self.active_player.current_piece["piece"] = self.selected
                        self.active_player.current_piece["arr"] = self.active_player.remaining_pieces[self.selected]["arr"]
                        self.active_player.current_piece["rects"] = self.active_player.remaining_pieces[self.selected]["rects"]
            elif event.type == pygame.MOUSEBUTTONUP:
                drawElements.init_piece_rects(self.player1.remaining_pieces, self.player2.remaining_pieces)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return GameState.MAIN_MENU
                if self.selected is not None:
                    self.key_controls(event)
        return None

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

    def run(self):
        if self.active_player.is_ai:
            self.display_infobox_msg_start("ai_turn")
            self.draw()
            pygame.time.wait(100)
            AIManager.main(self.gameboard, self.active_player, self.opponent)
            self.active_player, self.opponent = player.switch_active_player(self.active_player, self.opponent)
            self.save_game_state()
            self.display_infobox_msg_end(True)
        else:
            new_state = self.event_handler()
            if new_state:
                return new_state

        self.draw()
        if board.is_game_over(self.gameboard, self.active_player, self.opponent):
            self.display_infobox_msg_start("game_over")
        return GameState.GAMEPLAY

    def draw(self):
        self.background.fill(constants.BLACK)
        drawElements.draw_infobox(self.background, self.player1, self.player2, self.active_player)
        if self.infobox_msg_time_start is not None:
            drawElements.draw_infobox_msg(self.background, self.player1, self.player2, self.infobox_msg)
            self.display_infobox_msg_end()
        drawElements.draw_gameboard(self.background, self.board_rects, self.gameboard, self.active_player.current_piece, self.active_player)
        drawElements.draw_pieces(self.background, self.player1, self.player2, self.active_player, self.selected)
        if self.selected is not None:
            drawElements.draw_selected_piece(self.background, self.offset_list, pygame.mouse.get_pos(), self.active_player.current_piece, self.active_player.color)
        self.screen.blit(self.background, (0, 0))
        pygame.display.update()

    def get_state_to_save(self):
        return {
            "board": self.gameboard.board.tolist(),
            "turn_number": self.gameboard.turn_number,
            "active_player_num": self.active_player.number,
            "player1": self.player1.get_state(),
            "player2": self.player2.get_state(),
        }

    def save_game_state(self):
        state = self.get_state_to_save()
        with open(SAVE_FILE, 'w') as f:
            json.dump(state, f, indent=4)

    def load_from_state(self, saved_state, player_init_params):
        self.gameboard = Board()
        self.gameboard.board = np.array(saved_state["board"])
        self.gameboard.turn_number = saved_state["turn_number"]
        
        self.player1, self.player2 = self.init_players(player_init_params)
        self.player1.load_state(saved_state["player1"])
        self.player2.load_state(saved_state["player2"])

        if saved_state["active_player_num"] == 1:
            self.active_player, self.opponent = self.player1, self.player2
        else:
            self.active_player, self.opponent = self.player2, self.player1
        
        self.gameboard.update_board_corners(self.player1, self.player2)


class GameManager:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(constants.WINDOW_SIZE)
        self.background = pygame.Surface(constants.WINDOW_SIZE)
        pygame.display.set_caption("Blokus")
        self.clock = pygame.time.Clock()
        self.game_state = GameState.MAIN_MENU
        self.game_session = None

    def main_loop(self):
        while self.game_state != GameState.QUIT:
            if self.game_state == GameState.MAIN_MENU:
                self.game_state = self.main_menu_loop()
            elif self.game_state == GameState.DIFFICULTY_MENU:
                self.game_state = self.difficulty_menu_loop()
            elif self.game_state == GameState.GAMEPLAY:
                if not self.game_session:
                    self.game_state = GameState.MAIN_MENU
                    continue
                self.game_state = self.game_session.run()
            self.clock.tick(60)
        pygame.quit()

    def main_menu_loop(self):
        buttons = [
            Button(440, 280, 400, 60, "Player vs AI", constants.PURPLE, constants.ACCENT, "vs_ai"),
            Button(440, 360, 400, 60, "Player vs Player", constants.ORANGE, constants.ACCENT, "vs_player"),
            Button(440, 440, 400, 60, "Continue", constants.GREEN, constants.ACCENT, "continue"),
            Button(440, 520, 400, 60, "Quit", constants.RED, constants.ACCENT, "quit")
        ]
        while True:
            mouse_pos = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return GameState.QUIT
                for button in buttons:
                    action = button.handle_event(event)
                    if action == "vs_ai": return GameState.DIFFICULTY_MENU
                    if action == "vs_player":
                        params = {"p1": constants.HUMAN_PARAMS["default_p1"], "p2": constants.HUMAN_PARAMS["default_p2"]}
                        self.game_session = GameSession(params, self.screen, self.background, self.clock)
                        return GameState.GAMEPLAY
                    if action == "continue":
                        if self.load_game_state():
                            return GameState.GAMEPLAY
                    if action == "quit": return GameState.QUIT
            drawElements.draw_menu(self.screen, "Blokus", buttons, mouse_pos)
            pygame.display.update()
            self.clock.tick(60)

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
                        ai_param = constants.AI_PARAMS["alphabeta_easy_p2"]
                        params = {"p1": constants.HUMAN_PARAMS["default_p1"], "p2": ai_param}
                        self.game_session = GameSession(params, self.screen, self.background, self.clock)
                        return GameState.GAMEPLAY
                    if action == "hard":
                        ai_param = constants.AI_PARAMS["alphabeta_hard_p2"]
                        params = {"p1": constants.HUMAN_PARAMS["default_p1"], "p2": ai_param}
                        self.game_session = GameSession(params, self.screen, self.background, self.clock)
                        return GameState.GAMEPLAY
                    if action == "back": return GameState.MAIN_MENU
            drawElements.draw_menu(self.screen, "Select Difficulty", buttons, mouse_pos)
            pygame.display.update()
            self.clock.tick(60)

    def load_game_state(self):
        if not os.path.exists(SAVE_FILE):
            print("No save file found.")
            return False
        with open(SAVE_FILE, 'r') as f:
            try:
                saved_state = json.load(f)
            except json.JSONDecodeError:
                print("Save file is corrupted.")
                return False
        
        p1_params = constants.HUMAN_PARAMS["default_p1"]
        p2_is_ai = saved_state["player2"]["is_ai"]
        if p2_is_ai:
            p2_params = constants.AI_PARAMS["alphabeta_hard_p2"]
        else:
            p2_params = constants.HUMAN_PARAMS["default_p2"]
            
        params = {"p1": p1_params, "p2": p2_params}

        self.game_session = GameSession(params, self.screen, self.background, self.clock, saved_state=saved_state)
        return True

if __name__ == "__main__":
    manager = GameManager()
    manager.main_loop()