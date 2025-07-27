import random

from utils.game_cloner import clone_game

class SimulationStrategy:
    def simulate(self, node):
        raise NotImplementedError

class RandomPlayout(SimulationStrategy):
    def __init__(self, AI_team):
        self.AI_team = AI_team

    def simulate(self, node):
        game = clone_game(node.game_state)
        while game.get_winner() is None:
            moves = game.get_legal_moves()
            if not moves:
                break
            move = random.choice(moves)
            move_type, from_pos, to_pos = move
            if move_type == 'move':
                game.execute_move(from_pos, to_pos)
            else:
                game.execute_kick(to_pos)
        return self.calculate_reward(game)

    def calculate_reward(self, game):
        winner = game.get_winner()
        if winner == self.AI_team:
            return 1.0
        elif winner is None:
            return 0.0
        else:
            return -1.0
