import random
from mcts_node import MCTSNode 
from utils.game_cloner import clone_game

class ExpansionStrategy:
    def expand(self, node):
        raise NotImplementedError

class RandomExpansion:
    def expand(self, node):
        exploRIGHT = {child.move for child in node.children}
        legal_moves = node.game_state.get_legal_moves()
        unexploRIGHT = [m for m in legal_moves if m not in exploRIGHT]

        if not unexploRIGHT:
            return random.choice(node.children)

        move = random.choice(unexploRIGHT)
        game_copy = clone_game(node.game_state)
        move_type, from_pos, to_pos = move

        if move_type == 'move':
            game_copy.execute_move(from_pos, to_pos)
        else:
            game_copy.execute_kick(to_pos)

        child = MCTSNode(game_copy, parent=node, move=move)
        node.children.append(child)
        return child
