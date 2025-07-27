import random
import threading
import concurrent.futures
from collections import defaultdict
from mcts_node import MCTSNode
from utils.game_cloner import clone_game
from strategies.selection import ProgressiveHistorySelection, UCTSelection, ProgressiveBiasSelection
from strategies.expansion import RandomExpansion
from strategies.simulation import RandomPlayout
from strategies.backpropagation import StandardBackpropagation
from strategies.final_move import RobustChildStrategy 
from utils.logger import MCTSLogger
from mastergoalGame import MastergoalGame
from ball import Ball
from position import Position
from player import Player

class RootParallelMCTSAI:
    def __init__(self, game, AI_team, iterations=1000,
                 selection_strategy=None,
                 expansion_strategy=None,
                 simulation_strategy=None,
                 backpropagation_strategy=None,
                 final_move_strategy=None,  # New parameter
                 logger=None, 
                 level=1,
                 use_opening_book=True,
                 num_threads=4):
        self.game = game
        self.AI_team = AI_team
        self.iterations = iterations
        self.level = level
        self.use_opening_book = use_opening_book
        self.num_threads = num_threads
        
        # Strategy factories - we'll create instances per thread
        self.selection_strategy_class = selection_strategy or UCTSelection
        self.expansion_strategy_class = expansion_strategy or RandomExpansion
        self.simulation_strategy_class = simulation_strategy or RandomPlayout
        self.backpropagation_strategy_class = backpropagation_strategy or StandardBackpropagation
        self.final_move_strategy = final_move_strategy or RobustChildStrategy()  # New strategy
        
        # Only create logger if explicitly provided, otherwise disable logging
        self.logger = logger
        
        # Thread-local storage for strategies
        self._thread_local = threading.local()

    def _get_thread_strategies(self):
        """Get or create thread-local strategy instances"""
        if not hasattr(self._thread_local, 'strategies'):
            selection = self.selection_strategy_class()
            expansion = self.expansion_strategy_class()
            simulation = self.simulation_strategy_class(self.AI_team)
            backprop = self.backpropagation_strategy_class(
                selection if hasattr(selection, 'update_history') else None
            )
            
            self._thread_local.strategies = {
                'selection': selection,
                'expansion': expansion,
                'simulation': simulation,
                'backpropagation': backprop
            }
        
        return self._thread_local.strategies

    def get_best_move(self, team):
        if self.game.current_team != team:
            return None

        if self.use_opening_book and self._is_first_turn() and team == self.game.LEFT:
            self.game.turn_count += 1
            return self._opening_book_move()
    
        original_state = self.game.get_game_state()
        
        # Create root nodes for each thread
        root_nodes = []
        iterations_per_thread = self.iterations // self.num_threads
        remaining_iterations = self.iterations % self.num_threads
        
        # Run parallel MCTS
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            futures = []
            
            for thread_id in range(self.num_threads):
                # Give extra iterations to first threads if not evenly divisible
                thread_iterations = iterations_per_thread + (1 if thread_id < remaining_iterations else 0)
                
                future = executor.submit(
                    self._run_mcts_thread, 
                    clone_game(self.game), 
                    thread_iterations,
                    thread_id
                )
                futures.append(future)
            
            # Collect results from all threads
            thread_results = []
            for future in concurrent.futures.as_completed(futures):
                root_node = future.result()
                if root_node:
                    thread_results.append(root_node)
        
        # Merge results from all threads
        merged_root = self._merge_trees(thread_results, clone_game(self.game))
        
        # Select best move using final move strategy
        best_move = None
        if merged_root and merged_root.children:
            best_move = self.final_move_strategy.select_move(merged_root, self.game)
        
        # Restore original game state
        self.restore_game_state(self.game, original_state)
        
        return best_move

    def _run_mcts_thread(self, game_clone, iterations, thread_id):
        """Run MCTS in a single thread"""
        try:
            strategies = self._get_thread_strategies()
            root = MCTSNode(game_clone)
            
            for i in range(iterations):
                node = self._select_node(root, strategies)
                reward = strategies['simulation'].simulate(node)
                strategies['backpropagation'].backpropagate(node, reward)
                
                # Log with thread info only if logger is available
                if self.logger is not None:
                    if hasattr(self.logger, 'log_thread_iteration'):
                        self.logger.log_thread_iteration(thread_id, i, node, reward)
                    else:
                        self.logger.log_iteration(i, node, reward)
            
            # Reset thread-local history if supported
            if hasattr(strategies['selection'], 'reset'):
                strategies['selection'].reset()
                
            return root
            
        except Exception as e:
            print(f"Error in MCTS thread {thread_id}: {e}")
            return None

    def _select_node(self, root, strategies):
        """Node selection logic for a single thread"""
        node = root
        while not self._is_terminal_node(node.game_state):
            if not node.is_fully_expanded():
                return strategies['expansion'].expand(node)
            node = strategies['selection'].select(node)
        return node

    def _merge_trees(self, root_nodes, base_game):
        """Merge statistics from multiple MCTS trees"""
        if not root_nodes:
            return None
            
        # Create merged root
        merged_root = MCTSNode(base_game)
        
        # Dictionary to track merged children by move
        move_to_merged_child = {}
        
        # Process each root node from parallel threads
        for root in root_nodes:
            # Add root statistics
            merged_root.visits += root.visits
            merged_root.total_reward += root.total_reward
            
            # Process children
            for child in root.children:
                move = child.move
                
                if move not in move_to_merged_child:
                    # Create new merged child
                    merged_child = MCTSNode(
                        clone_game(child.game_state), 
                        parent=merged_root, 
                        move=move
                    )
                    move_to_merged_child[move] = merged_child
                    merged_root.children.append(merged_child)
                
                # Merge statistics
                merged_child = move_to_merged_child[move]
                merged_child.visits += child.visits
                merged_child.total_reward += child.total_reward
        
        return merged_root

    def _is_terminal_node(self, game):
        return game.get_winner() is not None

    def restore_game_state(self, game, state):
        game.level = state['level']
        game.left_goals = state['left_goals']
        game.right_goals = state['right_goals']
        game.current_team = state['current_team']
        game.last_possession_team = state.get('last_possession_team', game.LEFT)
        game.passes_count = state['passes_count']
        game.turn_count = state['turn_count']
        game.skip_next_turn = state['skip_next_turn']
        ball_row, ball_col = state['ball_position']
        game.ball = Ball(Position(ball_row, ball_col))
        game.players = [
            Player(Position(row, col), team, pid, gk)
            for team, pid, row, col, gk in state['players']
        ]

    ## OPENING BOOK
    def _is_first_turn(self):
        return self.game.turn_count == 0

    def _opening_book_move(self):
        """
        Returns a pRIGHTefined opening move based on the level.
        """
        if self.level in [1, 2]:
            move = ('move', Position(4, 5), Position(6, 5))
            if move in self.game.get_legal_moves():
                return move
            return None

        if self.level == 3:
            options = [
                ('move', Position(4, 3), Position(6, 5)),
                ('move', Position(4, 7), Position(6, 5))
            ]
            legal = self.game.get_legal_moves()
            valid_moves = [move for move in options if move in legal]
            return random.choice(valid_moves) if valid_moves else None

        return None


class HybridMCTSAI:
    """
    Hybrid version that can switch between sequential and parallel MCTS
    based on available time or complexity
    """
    def __init__(self, game, AI_team, iterations=1000,
                 selection_strategy=None,
                 expansion_strategy=None,
                 simulation_strategy=None,
                 backpropagation_strategy=None,
                 final_move_strategy=None,  # New parameter
                 logger=None, 
                 level=1,
                 use_opening_book=True,
                 num_threads=4,
                 parallel_threshold=500):
        
        # Store parameters
        self.iterations = iterations
        self.parallel_threshold = parallel_threshold
        
        # Pass logger as-is (could be None to disable logging)
        self.logger = logger
        
        # Initialize both sequential and parallel versions with the same logger
        self.sequential_ai = MCTSAI(
            game, AI_team, iterations,
            selection_strategy, expansion_strategy, 
            simulation_strategy, backpropagation_strategy,
            final_move_strategy,  # Pass final move strategy
            logger, level, use_opening_book
        )
        
        self.parallel_ai = RootParallelMCTSAI(
            game, AI_team, iterations,
            selection_strategy, expansion_strategy,
            simulation_strategy, backpropagation_strategy,
            final_move_strategy,  # Pass final move strategy
            logger, level, use_opening_book, num_threads
        )

    def get_best_move(self, team):
        """
        Choose between sequential and parallel MCTS based on iterations
        """
        if self.iterations >= self.parallel_threshold:
            return self.parallel_ai.get_best_move(team)
        else:
            return self.sequential_ai.get_best_move(team)

    def set_iterations(self, iterations):
        """Update iterations for both AI instances"""
        self.iterations = iterations
        self.sequential_ai.iterations = iterations
        self.parallel_ai.iterations = iterations

    def get_current_ai_type(self):
        """Return which AI type will be used"""
        return "parallel" if self.iterations >= self.parallel_threshold else "sequential"
        

class MCTSAI:
    def __init__(self, game, AI_team, iterations=1000,
                 selection_strategy=None,
                 expansion_strategy=None,
                 simulation_strategy=None,
                 backpropagation_strategy=None,
                 final_move_strategy=None,  # New parameter
                 logger=None, 
                 level=1,
                 use_opening_book=True):
        self.game = game
        self.AI_team = AI_team
        self.iterations = iterations
        self.level = level
        self.use_opening_book = use_opening_book
        self.ph_selector = selection_strategy or ProgressiveHistorySelection() # IMPORTANT: default constantly changing
        self.selection = selection_strategy or UCTSelection()
        self.expansion = expansion_strategy or RandomExpansion()
        self.simulation = simulation_strategy or RandomPlayout(AI_team)
        self.backpropagation = backpropagation_strategy or StandardBackpropagation(self.selection if hasattr(self.selection, 'update_history') else None)
        self.final_move_strategy = final_move_strategy or RobustChildStrategy()  # New strategy
        # Only assign logger if provided, otherwise disable logging
        self.logger = logger

    def get_best_move(self, team):
        if self.game.current_team != team:
            return None

        if self.use_opening_book and self._is_first_turn() and team == self.game.LEFT:
            self.game.turn_count+=1
            return self._opening_book_move()
    
        original_state = self.game.get_game_state()
        root = MCTSNode(clone_game(self.game))

        for i in range(self.iterations):
            # Track the path during selection
            selection_path = []
            node = self._select_node_with_logging(root, selection_path, i)
            # Log expansion if a new node was created
            if hasattr(node, '_just_expanded') and self.logger is not None:
                self.logger.log_expansion(i, node)
                delattr(node, '_just_expanded')
            # Simulation
            reward = self.simulation.simulate(node)
            # Log simulation result only if logger is available
            if self.logger is not None:
                self.logger.log_iteration(i, node, reward)
            # Backpropagation with path tracking
            backprop_path = self._backpropagate_with_path(node, reward)
            if self.logger is not None:
                self.logger.log_backpropagation_path(i, backprop_path, reward)

        # Use final move strategy instead of simple max selection
        best_move = None
        if root.children:
            best_move = self.final_move_strategy.select_move(root, self.game)
        
        self.restore_game_state(self.game, original_state)

        # Reset PH table ONLY if the selector supports it
        if hasattr(self.selection, 'reset'):
            self.selection.reset()

        return best_move

    def _select_node_with_logging(self, root, path, iteration):
        """Modified selection that tracks the path"""
        node = root
        path.append(node)
        
        while not self._is_terminal_node(node.game_state):
            if not node.is_fully_expanded():
                new_node = self.expansion.expand(node)
                new_node._just_expanded = True  # Mark for logging
                path.append(new_node)
                # Log the selection path up to this point only if logger is available
                if self.logger is not None:
                    self.logger.log_selection_path(iteration, path[:-1])  # Exclude the new node
                return new_node
            
            node = self.selection.select(node)
            path.append(node)
        
        # Log the complete selection path for terminal nodes only if logger is available
        if self.logger is not None:
            self.logger.log_selection_path(iteration, path)
        return node
    
    def _backpropagate_with_path(self, node, reward):
        """Backpropagate and return the path for logging"""
        path = []
        current = node
        
        while current is not None:
            path.append(current)
            current.visits += 1
            current.total_reward += reward
            current = current.parent
            
        return path

    def _is_terminal_node(self, game):
        return game.get_winner() is not None

    def clone_game(self, game):
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

    def restore_game_state(self, game, state):
        game.level = state['level']
        game.left_goals = state['left_goals']
        game.right_goals = state['right_goals']
        game.current_team = state['current_team']
        game.last_possession_team = state.get('last_possession_team', game.LEFT)
        game.passes_count = state['passes_count']
        game.turn_count = state['turn_count']
        game.skip_next_turn = state['skip_next_turn']
        ball_row, ball_col = state['ball_position']
        game.ball = Ball(Position(ball_row, ball_col))
        game.players = [
            Player(Position(row, col), team, pid, gk)
            for team, pid, row, col, gk in state['players']
        ]

    ## OPENING BOOK
    def _is_first_turn(self):
        return self.game.turn_count == 0

    def _opening_book_move(self):
        """
        Returns a pRIGHTefined opening move based on the level.
        """
        if self.level in [1, 2]:
            move = ('move', Position(4, 5), Position(6, 5))
            if move in self.game.get_legal_moves():
                return move
            return None

        if self.level == 3:
            options = [
                ('move', Position(4, 3), Position(6, 5)),
                ('move', Position(4, 7), Position(6, 5))
            ]
            legal = self.game.get_legal_moves()
            valid_moves = [move for move in options if move in legal]
            return random.choice(valid_moves) if valid_moves else None

        return None