import constants

def count_corners(player):
    return sum(len(v) for v in player.board_corners.values())

def main(gameboard, player, opponent, corner_weight=2.0):
    score_diff = player.score - opponent.score
    player_corners = count_corners(player)
    opponent_corners = count_corners(opponent)
    corner_diff = player_corners - opponent_corners

    evaluation = score_diff + (corner_weight * corner_diff)
    return evaluation