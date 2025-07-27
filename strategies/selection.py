from collections import defaultdict
import math

class SelectionStrategy:
    def select(self, node):
        raise NotImplementedError
    
    
# ------------------------------
# UCT SELECTION (por defecto)
# ------------------------------

class UCTSelection(SelectionStrategy):
    def __init__(self, exploration_constant=1.414):
        self.c = exploration_constant

    def select(self, node):
        return max(node.children, key=lambda n: self.uct_score(n))

    def uct_score(self, node):
        if node.visits == 0:
            return float('inf')
        exploit = node.total_reward / node.visits
        explore = self.c * math.sqrt(math.log(node.parent.visits + 1e-9) / node.visits)
        return exploit + explore

# ------------------------------
# PROGRESSIVE HISTORY SELECTION

#  Nijssen and Winands propose the Progressive History
# enhancement, which combines Progressive Bias
# with the history heuristic by replacing the heuristic
# value Hi in the progressive bias calculation for each
# node i with that node’s history score, during node
# selection.
# ------------------------------
class ProgressiveHistorySelection(SelectionStrategy):
    def __init__(self, exploration_constant=1.414):
        self.c = exploration_constant
        # Tabla global por jugador: (team, move) -> [total_reward, visit_count]
        self.history_table = defaultdict(lambda: [0.0, 0])

    def select(self, node):
        children = node.children
        if not children:
            return None
        return max(children, key=lambda child: self.ph_score(child))

    def ph_score(self, node):
        if node.visits == 0:
            return float('inf')

        avg_reward = node.total_reward / node.visits
        bias = self.get_history_bias(node)
        exploration = self.c * math.sqrt(math.log(node.parent.visits + 1e-9) / node.visits)
        return avg_reward + bias + exploration

    def get_history_bias(self, node):
        team = node.game_state.current_team
        key = (team, node.move)
        total_reward, count = self.history_table[key]
        if count == 0:
            return 0
        return total_reward / count

    def update_history(self, node, reward):
        if node.move is None:
            return  # nodo raíz
        team = node.game_state.current_team
        key = (team, node.move)
        self.history_table[key][0] += reward
        self.history_table[key][1] += 1

    def reset(self):
        self.history_table.clear()

# ------------------------------
# PROGRESSIVE BIAS (PB) SELECTION
# ------------------------------

class ProgressiveBiasSelection(UCTSelection):
    def __init__(self, exploration_constant=1.414):
        super().__init__(exploration_constant)

    def uct_score(self, node):
        if node.visits == 0:
            return float('inf')

        base_score = super().uct_score(node)
        bias = self.heuristic(node) / (node.visits + 1)
        return base_score + bias

    def heuristic(self, node):
        """
        Devuelve un sesgo heurístico si algún jugador del equipo actual está adyacente a la pelota y tiene posibilidad de patear.
        """
        ball_pos = node.game_state.ball.position
        if not node.game_state.is_ball_in_neutral_state():
            for p in node.game_state.players:
                if p.team == node.game_state.current_team:
                    if p.position.is_adjacent(ball_pos):
                        return 5.0  # alto sesgo: excelente posición
        return 0.0

