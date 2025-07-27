import math

class MCTSNode:
    def __init__(self, game_state, parent=None, move=None):
        self.game_state = game_state
        self.parent = parent
        self.move = move
        self.children = []
        self.visits = 0
        self.total_reward = 0.0

    def is_fully_expanded(self):
        return len(self.children) == len(self.game_state.get_legal_moves())

    def uct_score(self, exploration_constant=1.414):
        if self.visits == 0:
            return float('inf')
        exploit = self.total_reward / self.visits
        explore = exploration_constant * ((self.parent.visits)**0.5 / self.visits)**0.5 if self.parent else 0
        return exploit + explore
