import pygame, math
import constants
MARGIN = 2
BORDER_RADIUS = 4

board_width = 620
board_box_width = 42
piece_box_width = (constants.WINDOW_WIDTH - board_width) / 2  # 330
one_piece_box_width = piece_box_width / 2  # 165
single_piece_width = 9
info_box_width = constants.WINDOW_WIDTH  # 1280

board_height = board_width  # 620
board_box_height = board_box_width
piece_box_height = board_height
one_piece_box_height = math.floor(board_height / 11)  # 56
single_piece_height = single_piece_width  # 9
info_box_height = constants.WINDOW_HEIGHT - board_height  # 100

board_origin = [piece_box_width, info_box_height]  # [330, 100]

def grid_to_array_coords(pos):
    col = int((pos[0] - (piece_box_width + MARGIN)) // (MARGIN + board_box_width))
    row = int((pos[1] - (info_box_height + MARGIN)) // (MARGIN + board_box_height))
    return [row, col]


def init_gameboard(board_arr):
    rects = []
    for row in range(board_arr.shape[0]):
        for column in range(board_arr.shape[1]):
            box_width = piece_box_width + MARGIN + ((MARGIN + board_box_width) * column)
            box_height = info_box_height + MARGIN + ((MARGIN + board_box_height) * row)
            dims = [box_width, box_height, board_box_width, board_box_height]
            rects.append(pygame.Rect(dims))
    return rects


def draw_gameboard(canvas, board_rects, gameboard, current_piece, player):
    counter = 0
    board_arr = gameboard.board
    is_valid_move = False

    if len(current_piece["rects"]) > 0:
        if are_squares_within_board(current_piece, board_rects):
            if player.is_1st_move:
                if grid_to_array_coords(current_piece["rects"][0].center) == constants.STARTING_PTS[f"player{player.number}"]:
                    is_valid_move = True
            else:
                if gameboard.check_is_move_valid(current_piece["arr"], player,
                                                 grid_to_array_coords(current_piece["rects"][0].center)):
                    is_valid_move = True

    for row in range(board_arr.shape[0]):
        for column in range(board_arr.shape[1]):
            rect = board_rects[counter]
            
            if board_arr[row][column] == constants.BOARD_FILL_VALUE:
                fill_color = constants.BOARD_BACKGROUND
            elif board_arr[row][column] == constants.PLAYER1_VALUE:
                fill_color = constants.PURPLE
            elif board_arr[row][column] == constants.PLAYER2_VALUE:
                fill_color = constants.ORANGE
            
            pygame.draw.rect(canvas, fill_color, rect, border_radius=BORDER_RADIUS)
            
            pygame.draw.rect(canvas, constants.BOARD_GRID, rect, 1, border_radius=BORDER_RADIUS)

            if is_valid_move:
                for piece_rect in current_piece["rects"]:
                    if piece_rect.colliderect(rect) and board_arr[row][column] == constants.BOARD_FILL_VALUE:
                        pygame.draw.rect(canvas, constants.GREEN, rect, 2, border_radius=BORDER_RADIUS)

            if [row, column] == constants.STARTING_PTS["player1"]:
                text = pygame.font.SysFont(None, 15).render("P1", True, constants.WHITE)
                canvas.blit(text, text.get_rect(center=rect.center))
            elif [row, column] == constants.STARTING_PTS["player2"]:
                text = pygame.font.SysFont(None, 15).render("P2", True, constants.WHITE)
                canvas.blit(text, text.get_rect(center=rect.center))
            
            counter += 1


def init_piece_rects(p1_remaining_pieces, p2_remaining_pieces):
    row, column = 0, 0
    for piece in p1_remaining_pieces.keys():
        piece_rects = []
        for i in range(p1_remaining_pieces[piece]["arr"].shape[0]):
            for j in range(p1_remaining_pieces[piece]["arr"].shape[1]):
                if p1_remaining_pieces[piece]["arr"][i][j] == 1:
                    x = (one_piece_box_width * column) + ((MARGIN + single_piece_width) * j) + MARGIN
                    y = info_box_height + (one_piece_box_height * row) + ((MARGIN + single_piece_height) * i)
                    piece_rects.append(pygame.Rect([x, y, single_piece_width, single_piece_height]))
        p1_remaining_pieces[piece]["rects"] = piece_rects
        column += 1
        if column == 2:
            row += 1
            column = 0

    row, column = 0, 0
    for piece in p2_remaining_pieces.keys():
        piece_rects = []
        for i in range(p2_remaining_pieces[piece]["arr"].shape[0]):
            for j in range(p2_remaining_pieces[piece]["arr"].shape[1]):
                if p2_remaining_pieces[piece]["arr"][i][j] == 1:
                    x = piece_box_width + board_width + (one_piece_box_width * column) + (
                                (MARGIN + single_piece_width) * j) + MARGIN
                    y = info_box_height + (one_piece_box_height * row) + ((MARGIN + single_piece_height) * i)
                    piece_rects.append(pygame.Rect([x, y, single_piece_width, single_piece_height]))
        p2_remaining_pieces[piece]["rects"] = piece_rects
        column += 1
        if column == 2:
            row += 1
            column = 0


def generate_element_offsets(remaining_pieces, event):
    offset_list = []
    selected = None
    for key, val in remaining_pieces.items():
        for r in val["rects"]:
            if r.collidepoint(event.pos):
                selected = key
                break
        if selected is not None:
            break
    if selected is not None:
        for chosen_piece in remaining_pieces[selected]["rects"]:
            selected_offset_x = chosen_piece.x - event.pos[0]
            selected_offset_y = chosen_piece.y - event.pos[1]
            offset_list.append([selected_offset_x, selected_offset_y])
    return offset_list, selected


def draw_pieces(canvas, player1, player2, active_player, selected):
    p1_pieces, p2_pieces = player1.remaining_pieces, player2.remaining_pieces
    p1_color, p2_color = player1.color, player2.color
    for key, val in p1_pieces.items():
        if not (key == selected and player1.number == active_player.number):
            for unit_sq in val["rects"]:
                pygame.draw.rect(canvas, p1_color, unit_sq, border_radius=2)
                pygame.draw.rect(canvas, constants.BOARD_GRID, unit_sq, 1, border_radius=2)

    for key, val in p2_pieces.items():
        if not (key == selected and player2.number == active_player.number):
            for unit_sq in val["rects"]:
                pygame.draw.rect(canvas, p2_color, unit_sq, border_radius=2)
                pygame.draw.rect(canvas, constants.BOARD_GRID, unit_sq, 1, border_radius=2)


def draw_selected_piece(canvas, offset_list, mouse_pos, current_piece, player_color):
    counter = 0
    rects = current_piece["rects"]
    for i in range(current_piece["arr"].shape[0]):
        for j in range(current_piece["arr"].shape[1]):
            if current_piece["arr"][i][j] == 1:
                rects[counter].width = board_box_width
                rects[counter].height = board_box_height
                rects[counter].x = mouse_pos[0] + offset_list[counter][0] + (board_box_width - single_piece_width) * j
                rects[counter].y = mouse_pos[1] + offset_list[counter][1] + (board_box_height - single_piece_height) * i
                
                pygame.draw.rect(canvas, player_color, rects[counter], border_radius=BORDER_RADIUS)
                pygame.draw.rect(canvas, constants.WHITE, rects[counter], 1, border_radius=BORDER_RADIUS)
                counter += 1


def draw_rotated_flipped_selected_piece(current_piece):
    ref_x, ref_y = current_piece["rects"][0].x, current_piece["rects"][0].y
    current_piece["rects"], offset_list = [], []
    mouse_pos = pygame.mouse.get_pos()
    for i in range(current_piece["arr"].shape[0]):
        for j in range(current_piece["arr"].shape[1]):
            if current_piece["arr"][i][j] == 1:
                x = ref_x + ((board_box_width - single_piece_width) * j)
                y = ref_y + ((board_box_height - single_piece_height) * i)
                current_piece["rects"].append(pygame.Rect(x, y, board_box_width, board_box_height))
                
                selected_offset_x = x - mouse_pos[0]
                selected_offset_y = y - mouse_pos[1]
                offset_list.append([selected_offset_x, selected_offset_y])
    return offset_list


def are_squares_within_board(current_piece, board_rects):
    is_within_board = False
    for piece_rect in current_piece["rects"]:
        for board_rect in board_rects:
            if piece_rect.collidepoint(board_rect.centerx, board_rect.centery):
                is_within_board = True
        if not is_within_board:
            return False
        else:
            is_within_board = False
    return True


def draw_infobox(canvas, player1, player2, active_player):
    font = pygame.font.SysFont("Trebuchet MS", 30)
    
    title_surf = font.render("Blokus", True, constants.WHITE)
    title_rect = title_surf.get_rect(center=(constants.WINDOW_WIDTH / 2, info_box_height / 2))
    canvas.blit(title_surf, title_rect)

    p1_score_surf = font.render(f"Player 1: {player1.score}", True, player1.color)
    p1_score_rect = p1_score_surf.get_rect(center=(piece_box_width / 2, info_box_height / 2))
    canvas.blit(p1_score_surf, p1_score_rect)

    p2_score_surf = font.render(f"Player 2: {player2.score}", True, player2.color)
    p2_score_rect = p2_score_surf.get_rect(center=(constants.WINDOW_WIDTH - piece_box_width / 2, info_box_height / 2))
    canvas.blit(p2_score_surf, p2_score_rect)

    if active_player.number == 1:
        underline_rect = pygame.Rect(p1_score_rect.left, p1_score_rect.bottom + 5, p1_score_rect.width, 4)
    else:
        underline_rect = pygame.Rect(p2_score_rect.left, p2_score_rect.bottom + 5, p2_score_rect.width, 4)
    pygame.draw.rect(canvas, constants.ACCENT, underline_rect, border_radius=2)


def draw_infobox_msg(canvas, player1, player2, msg_key):
    game_over_text = ""
    if msg_key == "game_over":
        if player1.score > player2.score:
            game_over_text = f"Game over. Player 1 wins!"
        elif player1.score < player2.score:
            game_over_text = f"Game over. Player 2 wins!"
        else:
            game_over_text = "Game over. It's a tie!"

    text_dict = {
        "not_valid_move": ("Invalid move. This piece cannot be placed there.", constants.RED),
        "game_over": (game_over_text, constants.GREEN),
        "ai_turn": ("AI's turn. Evaluating next move...", constants.GREEN)
    }

    if msg_key in text_dict:
        font = pygame.font.SysFont("Trebuchet MS", 25)
        msg_text, msg_color = text_dict[msg_key]
        msg_surf = font.render(msg_text, True, msg_color)
        msg_rect = msg_surf.get_rect(center=(constants.WINDOW_WIDTH / 2, constants.WINDOW_HEIGHT - 30))
        
        bg_rect = msg_rect.inflate(20, 10)
        bg_surf = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
        bg_surf.fill((40, 40, 40, 180))
        canvas.blit(bg_surf, bg_rect)
        
        canvas.blit(msg_surf, msg_rect)

class Button:
    def __init__(self, x, y, width, height, text, color, hover_color, action):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.action = action
        self.font = pygame.font.SysFont("Trebuchet MS", 40)

    def draw(self, canvas, mouse_pos):
        is_hovered = self.rect.collidepoint(mouse_pos)
        color = self.hover_color if is_hovered else self.color
        
        pygame.draw.rect(canvas, color, self.rect, border_radius=12)
        pygame.draw.rect(canvas, constants.WHITE, self.rect, 2, border_radius=12)

        text_surf = self.font.render(self.text, True, constants.WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        canvas.blit(text_surf, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return self.action
        return None

def draw_menu(canvas, title, buttons, mouse_pos):
    canvas.fill(constants.BLACK)
    
    title_font = pygame.font.SysFont("Trebuchet MS", 90)
    title_surf = title_font.render(title, True, constants.WHITE)
    title_rect = title_surf.get_rect(center=(constants.WINDOW_WIDTH / 2, 150))
    canvas.blit(title_surf, title_rect)

    for button in buttons:
        button.draw(canvas, mouse_pos)
