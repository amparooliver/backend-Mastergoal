from mastergoalGame import MastergoalGame
from ball import Ball
from position import Position
from player import Player

def clone_game(game):
    new_game = MastergoalGame(game.level)
    new_game.left_goals = game.left_goals
    new_game.right_goals = game.right_goals
    new_game.current_team = game.current_team
    new_game.last_possession_team = game.last_possession_team
    new_game.passes_count = game.passes_count
    new_game.turn_count = game.turn_count
    new_game.skip_next_turn = game.skip_next_turn
    new_game.ball = Ball(Position(game.ball.position.row, game.ball.position.col))
    new_game.players = [
        Player(Position(p.position.row, p.position.col), p.team, p.player_id, p.is_goalkeeper)
        for p in game.players
    ]
    return new_game
