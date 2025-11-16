import pygame, math
import constants
MARGIN = 2
BORDER_RADIUS = 4

# --- Global board dimensions ---
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

def adjust_grid_scaling(rows):
    """
    Adjusts the board drawing dimensions based on grid size (14 or 20).
    """
    global board_width, board_height, board_box_width, board_box_height, piece_box_width, board_origin
    
    max_dim = 620 
    
    board_width = max_dim
    board_height = max_dim
    
    board_box_width = (board_width - (MARGIN * (rows + 1))) / rows
    board_box_height = (board_height - (MARGIN * (rows + 1))) / rows
    
    piece_box_width = (constants.WINDOW_WIDTH - board_width) / 2
    
    board_origin[0] = piece_box_width 
    board_origin[1] = info_box_height


def grid_to_array_coords(pos):
    col = int((pos[0] - (board_origin[0] + MARGIN)) // (MARGIN + board_box_width))
    row = int((pos[1] - (board_origin[1] + MARGIN)) // (MARGIN + board_box_height))
    return [row, col]


def init_gameboard(board_arr, rows, cols):
    """Initializes the main game board rectangles."""
    adjust_grid_scaling(rows) 
    rects = []
    
    for row in range(rows):
        for column in range(cols):
            box_width = board_origin[0] + MARGIN + ((MARGIN + board_box_width) * column)
            box_height = board_origin[1] + MARGIN + ((MARGIN + board_box_height) * row)
            dims = [box_width, box_height, board_box_width, board_box_height]
            rects.append(pygame.Rect(dims))
    return rects


def draw_gameboard(canvas, board_rects, gameboard, current_piece, player):
    counter = 0
    board_arr = gameboard.board
    rows, cols = board_arr.shape
    is_valid_move = False
    
    start_points = constants.get_start_points(rows, cols)

    if len(current_piece["rects"]) > 0:
        if are_squares_within_board(current_piece, board_rects):
            rect_coords = [current_piece["rects"][0].centerx, current_piece["rects"][0].centery]
            board_arr_coords = grid_to_array_coords(rect_coords)
            
            # Align piece logic
            j = 0
            while not current_piece["arr"][0][j] == 1:
                j += 1
            board_arr_coords[1] -= j

            if player.is_1st_move:
                target_pos = start_points[player.number]
                is_within_starting_pos = False
                for i in range(current_piece["arr"].shape[0]):
                    for k in range(current_piece["arr"].shape[1]):
                        if [board_arr_coords[0]+i, board_arr_coords[1]+k] == target_pos and current_piece["arr"][i][k] == 1:
                            is_within_starting_pos = True
                if is_within_starting_pos:
                    is_valid_move = True
            else:
                if gameboard.check_is_move_valid(current_piece["arr"], player, board_arr_coords):
                    is_valid_move = True

    for row in range(rows):
        for column in range(cols):
            rect = board_rects[counter]
            
            val = board_arr[row][column]
            if val == constants.BOARD_FILL_VALUE:
                fill_color = constants.BOARD_BACKGROUND
            elif val == constants.PLAYER1_VALUE:
                fill_color = constants.PURPLE
            elif val == constants.PLAYER2_VALUE:
                fill_color = constants.ORANGE
            elif val == constants.PLAYER3_VALUE:
                fill_color = constants.RED
            elif val == constants.PLAYER4_VALUE:
                fill_color = constants.GREEN
            
            pygame.draw.rect(canvas, fill_color, rect, border_radius=BORDER_RADIUS)
            pygame.draw.rect(canvas, constants.BOARD_GRID, rect, 1, border_radius=BORDER_RADIUS)

            if is_valid_move:
                for piece_rect in current_piece["rects"]:
                    if piece_rect.colliderect(rect) and board_arr[row][column] == constants.BOARD_FILL_VALUE:
                        pygame.draw.rect(canvas, constants.GREEN, rect, 2, border_radius=BORDER_RADIUS)

            # Draw dynamic start points
            for p_num, coords in start_points.items():
                if [row, column] == coords:
                    text = pygame.font.SysFont(None, 15).render(f"P{p_num}", True, constants.WHITE)
                    canvas.blit(text, text.get_rect(center=rect.center))
            
            counter += 1


def init_piece_rects(players_list):
    """Initializes piece rects for a list of players (2 or 4) in a 6-col grid."""
    
    # Define a 6x4 grid layout
    num_columns = 6
    num_rows = 4 
    
    available_width = piece_box_width 
    available_height = 300 
    
    col_width = available_width / num_columns
    row_height = available_height / num_rows
    
    # --- Player 1 (Top-Left) ---
    if len(players_list) > 0:
        p1 = players_list[0]
        row, column = 0, 0
        for piece in p1.remaining_pieces.keys():
            piece_rects = []
            for i in range(p1.remaining_pieces[piece]["arr"].shape[0]):
                for j in range(p1.remaining_pieces[piece]["arr"].shape[1]):
                    if p1.remaining_pieces[piece]["arr"][i][j] == 1:
                        x = (col_width * column) + ((MARGIN + single_piece_width) * j) + MARGIN
                        y = info_box_height + 60 + (row_height * row) + ((MARGIN + single_piece_height) * i) # +60px offset
                        piece_rects.append(pygame.Rect([x, y, single_piece_width, single_piece_height]))
            p1.remaining_pieces[piece]["rects"] = piece_rects
            column += 1
            if column == num_columns:
                row += 1
                column = 0

    # --- Player 2 (Top-Right) ---
    if len(players_list) > 1:
        p2 = players_list[1]
        row, column = 0, 0
        for piece in p2.remaining_pieces.keys():
            piece_rects = []
            for i in range(p2.remaining_pieces[piece]["arr"].shape[0]):
                for j in range(p2.remaining_pieces[piece]["arr"].shape[1]):
                    if p2.remaining_pieces[piece]["arr"][i][j] == 1:
                        x = board_origin[0] + board_width + (col_width * column) + (
                                    (MARGIN + single_piece_width) * j) + MARGIN
                        y = info_box_height + 60 + (row_height * row) + ((MARGIN + single_piece_height) * i) # +60px offset
                        piece_rects.append(pygame.Rect([x, y, single_piece_width, single_piece_height]))
            p2.remaining_pieces[piece]["rects"] = piece_rects
            column += 1
            if column == num_columns:
                row += 1
                column = 0
                
    # --- Player 3 (Bottom-Right) ---
    if len(players_list) > 2:
        p3 = players_list[2]
        row, column = 0, 0
        for piece in p3.remaining_pieces.keys():
            piece_rects = []
            for i in range(p3.remaining_pieces[piece]["arr"].shape[0]):
                for j in range(p3.remaining_pieces[piece]["arr"].shape[1]):
                    if p3.remaining_pieces[piece]["arr"][i][j] == 1:
                        x = board_origin[0] + board_width + (col_width * column) + (
                                    (MARGIN + single_piece_width) * j) + MARGIN
                        y = info_box_height + 360 + (row_height * row) + ((MARGIN + single_piece_height) * i) # +360px offset
                        piece_rects.append(pygame.Rect([x, y, single_piece_width, single_piece_height]))
            p3.remaining_pieces[piece]["rects"] = piece_rects
            column += 1
            if column == num_columns:
                row += 1
                column = 0
                
    # --- Player 4 (Bottom-Left) ---
    if len(players_list) > 3:
        p4 = players_list[3]
        row, column = 0, 0
        for piece in p4.remaining_pieces.keys():
            piece_rects = []
            for i in range(p4.remaining_pieces[piece]["arr"].shape[0]):
                for j in range(p4.remaining_pieces[piece]["arr"].shape[1]):
                    if p4.remaining_pieces[piece]["arr"][i][j] == 1:
                        x = (col_width * column) + ((MARGIN + single_piece_width) * j) + MARGIN
                        y = info_box_height + 360 + (row_height * row) + ((MARGIN + single_piece_height) * i) # +360px offset
                        piece_rects.append(pygame.Rect([x, y, single_piece_width, single_piece_height]))
            p4.remaining_pieces[piece]["rects"] = piece_rects
            column += 1
            if column == num_columns:
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


def draw_pieces(canvas, players_list, active_player, selected):
    """Draws all pieces for all players in the list."""
    for p in players_list:
        if not (p.number == active_player.number):
            for key, val in p.remaining_pieces.items():
                for unit_sq in val["rects"]:
                    pygame.draw.rect(canvas, p.color, unit_sq, border_radius=2)
                    pygame.draw.rect(canvas, constants.BOARD_GRID, unit_sq, 1, border_radius=2)
        else:
            # This is the active player
            for key, val in p.remaining_pieces.items():
                if not (key == selected):
                    for unit_sq in val["rects"]:
                        pygame.draw.rect(canvas, p.color, unit_sq, border_radius=2)
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


def draw_infobox(canvas, players_list, active_player):
    """Draws info box for 2 or 4 players."""
    font = pygame.font.SysFont("Trebuchet MS", 30)
    
    title_surf = font.render("Blokus", True, constants.WHITE)
    title_rect = title_surf.get_rect(center=(constants.WINDOW_WIDTH / 2, info_box_height / 3))
    canvas.blit(title_surf, title_rect)

    active_rect = None
    
    if len(players_list) == 2:
        # P1 (Left)
        p1 = players_list[0]
        p1_score_surf = font.render(f"Player 1: {p1.score}", True, p1.color)
        p1_score_rect = p1_score_surf.get_rect(center=(piece_box_width / 2, info_box_height / 2))
        canvas.blit(p1_score_surf, p1_score_rect)
        if p1.number == active_player.number:
            active_rect = p1_score_rect
        
        # P2 (Right)
        p2 = players_list[1]
        p2_score_surf = font.render(f"Player 2: {p2.score}", True, p2.color)
        p2_score_rect = p2_score_surf.get_rect(center=(constants.WINDOW_WIDTH - piece_box_width / 2, info_box_height / 2))
        canvas.blit(p2_score_surf, p2_score_rect)
        if p2.number == active_player.number:
            active_rect = p2_score_rect
            
    elif len(players_list) == 4:
        font_player = pygame.font.SysFont("Trebuchet MS", 28)
        
        # --- P1 (Top-Left) ---
        p1 = players_list[0]
        p1_score_surf = font_player.render(f"Player 1: {p1.score}", True, p1.color)
        p1_score_rect = p1_score_surf.get_rect(topleft=(20, info_box_height + 20))
        canvas.blit(p1_score_surf, p1_score_rect)
        if p1.number == active_player.number: active_rect = p1_score_rect

        # --- P2 (Top-Right) ---
        p2 = players_list[1]
        p2_score_surf = font_player.render(f"Player 2: {p2.score}", True, p2.color)
        p2_score_rect = p2_score_surf.get_rect(topright=(constants.WINDOW_WIDTH - 20, info_box_height + 20))
        canvas.blit(p2_score_surf, p2_score_rect)
        if p2.number == active_player.number: active_rect = p2_score_rect

        # --- P3 (Bottom-Right) ---
        p3 = players_list[2]
        p3_score_surf = font_player.render(f"Player 3: {p3.score}", True, p3.color)
        p3_score_rect = p3_score_surf.get_rect(topright=(constants.WINDOW_WIDTH - 20, info_box_height + 320))
        canvas.blit(p3_score_surf, p3_score_rect)
        if p3.number == active_player.number: active_rect = p3_score_rect
        
        # --- P4 (Bottom-Left) ---
        p4 = players_list[3]
        p4_score_surf = font_player.render(f"Player 4: {p4.score}", True, p4.color)
        p4_score_rect = p4_score_surf.get_rect(topleft=(20, info_box_height + 320))
        canvas.blit(p4_score_surf, p4_score_rect)
        if p4.number == active_player.number: active_rect = p4_score_rect

    if active_rect:
        underline_rect = pygame.Rect(active_rect.left, active_rect.bottom + 5, active_rect.width, 4)
        pygame.draw.rect(canvas, constants.ACCENT, underline_rect, border_radius=2)


def draw_infobox_msg(canvas, msg_key):
    """ This function is now simple and just draws pre-made text """
    
    text_dict = {
        "not_valid_move": ("Invalid move. This piece cannot be placed there.", constants.RED),
        "ai_turn": ("AI's turn. Evaluating next move...", constants.GREEN),
        "auto_skip": (f"No available moves. Skipping turn.", constants.ACCENT)
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
        
def draw_game_over_panel(canvas, text, button, mouse_pos):
    """Draws a game over overlay with winner text and a back button."""
    
    overlay = pygame.Surface((constants.WINDOW_WIDTH, constants.WINDOW_HEIGHT))
    overlay.set_alpha(200) # Make it dark (0-255)
    overlay.fill((0, 0, 0))
    canvas.blit(overlay, (0, 0))

    cx, cy = constants.WINDOW_WIDTH // 2, constants.WINDOW_HEIGHT // 2
    panel_w, panel_h = 600, 350
    panel_rect = pygame.Rect(cx - panel_w//2, cy - panel_h//2, panel_w, panel_h)
    
    pygame.draw.rect(canvas, constants.BOARD_BACKGROUND, panel_rect, border_radius=15)
    pygame.draw.rect(canvas, constants.WHITE, panel_rect, 2, border_radius=15)

    font_title = pygame.font.SysFont("Trebuchet MS", 60)
    font_sub = pygame.font.SysFont("Trebuchet MS", 40)
    
    parts = text.split('!')
    
    title_surf = font_title.render(parts[0] + "!", True, constants.RED)
    title_rect = title_surf.get_rect(center=(cx, cy - 80))
    canvas.blit(title_surf, title_rect)
    
    if len(parts) > 1:
        sub_surf = font_sub.render(parts[1].strip(), True, constants.GREEN)
        sub_rect = sub_surf.get_rect(center=(cx, cy - 10))
        canvas.blit(sub_surf, sub_rect)

    button.draw(canvas, mouse_pos)
    
def draw_pause_panel(canvas, buttons, mouse_pos):
    """Draws a pause menu overlay with a title and buttons."""
    
    # Darken the background
    overlay = pygame.Surface((constants.WINDOW_WIDTH, constants.WINDOW_HEIGHT))
    overlay.set_alpha(200) # 0-255 transparency
    overlay.fill((0, 0, 0))
    canvas.blit(overlay, (0, 0))

    # Panel dimensions
    cx, cy = constants.WINDOW_WIDTH // 2, constants.WINDOW_HEIGHT // 2
    panel_w, panel_h = 400, 300
    panel_rect = pygame.Rect(cx - panel_w//2, cy - panel_h//2, panel_w, panel_h)
    
    # Draw the panel
    pygame.draw.rect(canvas, constants.BOARD_BACKGROUND, panel_rect, border_radius=15)
    pygame.draw.rect(canvas, constants.WHITE, panel_rect, 2, border_radius=15)

    # Title
    font_title = pygame.font.SysFont("Trebuchet MS", 60)
    title_surf = font_title.render("Paused", True, constants.WHITE)
    title_rect = title_surf.get_rect(center=(cx, cy - 80))
    canvas.blit(title_surf, title_rect)
    
    # Draw all buttons passed to the function
    for button in buttons:
        button.draw(canvas, mouse_pos)