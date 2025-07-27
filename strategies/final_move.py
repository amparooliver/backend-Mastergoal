"""
Final Move Selection Strategies for MCTS

This module contains different strategies for selecting the final move
after MCTS tree search is complete.
"""

from abc import ABC, abstractmethod
import math
from mastergoalGame import MastergoalGame

class FinalMoveStrategy(ABC):
    """Abstract base class for final move selection strategies"""
    
    @abstractmethod
    def select_move(self, root_node, game):
        """
        Select the best move from the root node's children
        
        Args:
            root_node: The root MCTS node with expanded children
            game: The current game state
            
        Returns:
            The selected move, or None if no valid move found
        """
        pass

class MaxChildStrategy(FinalMoveStrategy):
    """Select child with highest average reward (exploitation)"""
    
    def select_move(self, root_node, game):
        if not root_node.children:
            return None
            
        best_child = max(root_node.children, 
                        key=lambda child: child.total_reward / child.visits if child.visits > 0 else float('-inf'))
        return best_child.move

class RobustChildStrategy(FinalMoveStrategy):
    """Select child with most visits (most exploRIGHT)"""
    
    def select_move(self, root_node, game):
        if not root_node.children:
            return None
            
        best_child = max(root_node.children, key=lambda child: child.visits)
        return best_child.move

class RobustMaxChildStrategy(FinalMoveStrategy):
    """Hybrid: Select child with most visits among those with highest average reward"""
    
    def __init__(self, top_percentage=0.3):
        """
        Args:
            top_percentage: Consider only children in top X% of average rewards
        """
        self.top_percentage = top_percentage
    
    def select_move(self, root_node, game):
        if not root_node.children:
            return None
            
        # Calculate average rewards for all children
        children_with_rewards = []
        for child in root_node.children:
            if child.visits > 0:
                avg_reward = child.total_reward / child.visits
                children_with_rewards.append((child, avg_reward))
        
        if not children_with_rewards:
            return None
            
        # Sort by average reward (descending)
        children_with_rewards.sort(key=lambda x: x[1], reverse=True)
        
        # Take top percentage
        top_count = max(1, int(len(children_with_rewards) * self.top_percentage))
        top_children = [child for child, _ in children_with_rewards[:top_count]]
        
        # Among top children, select the one with most visits
        best_child = max(top_children, key=lambda child: child.visits)
        return best_child.move

class DecisiveMoveStrategy(FinalMoveStrategy):
    """
    Wrapper strategy that checks for decisive moves (like goal opportunities)
    before falling back to another strategy
    """
    
    def __init__(self, fallback_strategy, enable_decisive=True):
        """
        Args:
            fallback_strategy: Strategy to use when no decisive move found
            enable_decisive: Whether to check for decisive moves
        """
        self.fallback_strategy = fallback_strategy
        self.enable_decisive = enable_decisive
    
    def select_move(self, root_node, game):
        if self.enable_decisive and root_node.children:
            decisive_move = self._find_decisive_move(root_node, game)
            if decisive_move:
                return decisive_move
        
        # Fall back to the wrapped strategy
        return self.fallback_strategy.select_move(root_node, game)
    
    def _find_decisive_move(self, root_node, game):
        """
        Find decisive moves like goal opportunities
        Returns the decisive move or None
        """
        for child in root_node.children:
            move = child.move
            
            # Check if this move leads to a goal opportunity
            if self._is_goal_opportunity(move, game):
                return move

            # TODO: Check if this move prevents opponent from scoring
        return None
    
    def _is_goal_opportunity(self, move, game):
        """
        Check if a move creates a direct goal opportunity
        You can implement your specific goal detection logic here
        """
        # TODO: Implement your goal opportunity detection logic
        # This is where you'll add your specific conditions for detecting
        # moves that lead to goals
        move_type, from_pos, to_pos = move
        
        if move_type == 'kick':
            # Si es un kick valido al arco que termina en gol
            if game.is_goal_LEFT(to_pos) or game.is_goal_RIGHT(to_pos):
                print("GOL DETECTADO!!")
                return True

        return False

