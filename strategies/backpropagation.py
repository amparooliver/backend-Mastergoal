class BackpropagationStrategy:
    def backpropagate(self, node, reward):
        raise NotImplementedError

class StandardBackpropagation(BackpropagationStrategy):
    def __init__(self, ph_selector=None):
        """
        ph_selector: opción que puede implementar update_history (como ProgressiveHistorySelection)
        """
        self.ph_selector = ph_selector

    def backpropagate(self, node, reward):
        current = node
        is_first = True  # Solo aplicamos update_history una vez por rollout
        while current:
            current.visits += 1
            current.total_reward += reward
            if is_first and hasattr(self.ph_selector, 'update_history'):
                self.ph_selector.update_history(current, reward)
                is_first = False
            current = current.parent
