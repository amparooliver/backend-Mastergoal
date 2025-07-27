import csv
import os
from collections import defaultdict
import threading

class MCTSLogger:
    def __init__(self, log_path='mcts_log.csv'):
        self.log_path = log_path
        self._initialize_file()

    def _initialize_file(self):
        if not os.path.exists(self.log_path):
            with open(self.log_path, mode='w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['iteration', 'event_type', 'node_visits', 'node_total_reward', 'move', 'reward', 'details'])

    def log_iteration(self, iteration, node, reward):
        """Log basic iteration information"""
        with open(self.log_path, mode='a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                iteration,
                'simulation',
                node.visits,
                node.total_reward,
                str(node.move) if node.move else 'None',
                reward,
                ''
            ])

    def log_selection_path(self, iteration, path):
        """Log the selection path taken during tree traversal"""
        path_info = []
        for i, node in enumerate(path):
            path_info.append(f"depth_{i}:visits_{node.visits}")
        
        with open(self.log_path, mode='a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                iteration,
                'selection_path',
                len(path),
                0,  # no specific move for path
                'path',
                0,  # no reward for path
                ' -> '.join(path_info)
            ])

    def log_expansion(self, iteration, node):
        """Log when a new node is expanded"""
        with open(self.log_path, mode='a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                iteration,
                'expansion',
                node.visits,
                node.total_reward,
                str(node.move) if node.move else 'None',
                0,  # no reward for expansion
                f'parent_visits_{node.parent.visits if node.parent else 0}'
            ])

    def log_backpropagation_path(self, iteration, path, reward):
        """Log the backpropagation path"""
        path_info = []
        for i, node in enumerate(path):
            path_info.append(f"depth_{i}:visits_{node.visits}")
        
        with open(self.log_path, mode='a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                iteration,
                'backpropagation',
                len(path),
                reward,
                'backprop_path',
                reward,
                ' -> '.join(path_info)
            ])

    def log_thread_iteration(self, thread_id, iteration, node, reward):
        """Log iteration information with thread ID for parallel MCTS"""
        with open(self.log_path, mode='a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                iteration,
                f'thread_{thread_id}_simulation',
                node.visits,
                node.total_reward,
                str(node.move) if node.move else 'None',
                reward,
                f'thread_{thread_id}'
            ])

    def log_tree_statistics(self, root, iteration=None):
        """Log overall tree statistics"""
        def count_nodes(node):
            count = 1
            for child in node.children:
                count += count_nodes(child)
            return count
        
        total_nodes = count_nodes(root)
        
        with open(self.log_path, mode='a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                iteration or 'final',
                'tree_stats',
                root.visits,
                root.total_reward,
                'tree_summary',
                0,
                f'total_nodes_{total_nodes}_children_{len(root.children)}'
            ])

    def log_best_move_selection(self, iteration, candidates):
        """Log the final move selection process"""
        candidate_info = []
        for move, visits, reward in candidates:
            candidate_info.append(f"{move}:v{visits}:r{reward:.3f}")
        
        with open(self.log_path, mode='a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                iteration,
                'move_selection',
                0,
                0,
                'candidates',
                0,
                ' | '.join(candidate_info)
            ])


class ParallelMCTSLogger(MCTSLogger):
    """Enhanced logger for parallel MCTS execution"""
    
    def __init__(self, log_path='parallel_mcts_log.csv'):
        super().__init__(log_path)
        self.thread_stats = defaultdict(lambda: {'iterations': 0, 'total_reward': 0.0})
        self.lock = threading.Lock()

    def _initialize_file(self):
        """Initialize with additional parallel-specific columns"""
        if not os.path.exists(self.log_path):
            with open(self.log_path, mode='w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['iteration', 'thread_id', 'event_type', 'node_visits', 
                               'node_total_reward', 'move', 'reward', 'details'])

    def log_thread_iteration(self, thread_id, iteration, node, reward):
        """Log iteration with thread tracking"""
        with self.lock:
            self.thread_stats[thread_id]['iterations'] += 1
            self.thread_stats[thread_id]['total_reward'] += reward
            
            with open(self.log_path, mode='a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    iteration,
                    thread_id,
                    'simulation',
                    node.visits,
                    node.total_reward,
                    str(node.move) if node.move else 'None',
                    reward,
                    f'thread_{thread_id}_total_reward_{self.thread_stats[thread_id]["total_reward"]:.3f}'
                ])

    def log_thread_merge(self, merged_stats):
        """Log the results of merging parallel threads"""
        with open(self.log_path, mode='a', newline='') as f:
            writer = csv.writer(f)
            for thread_id, stats in merged_stats.items():
                writer.writerow([
                    'merge',
                    thread_id,
                    'thread_summary',
                    stats.get('total_visits', 0),
                    stats.get('total_reward', 0),
                    'thread_result',
                    stats.get('avg_reward', 0),
                    f'iterations_{stats.get("iterations", 0)}'
                ])

    def get_thread_summary(self):
        """Get summary of all thread statistics"""
        with self.lock:
            return dict(self.thread_stats)

    def log_final_tree_merge(self, root_nodes_count, final_root):
        """Log the final tree merging process"""
        with open(self.log_path, mode='a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'final',
                'all',
                'tree_merge',
                final_root.visits if final_root else 0,
                final_root.total_reward if final_root else 0,
                'merged_tree',
                0,
                f'merged_from_{root_nodes_count}_threads_children_{len(final_root.children) if final_root else 0}'
            ])


class DetailedMCTSLogger(MCTSLogger):
    """Logger with even more detailed information for debugging"""
    
    def __init__(self, log_path='detailed_mcts_log.csv', log_level='normal'):
        super().__init__(log_path)
        self.log_level = log_level  # 'minimal', 'normal', 'detailed', 'verbose'
        self.node_id_counter = 0
        self.node_to_id = {}

    def _get_node_id(self, node):
        """Assign unique IDs to nodes for tracking"""
        if node not in self.node_to_id:
            self.node_to_id[node] = self.node_id_counter
            self.node_id_counter += 1
        return self.node_to_id[node]

    def log_selection_path(self, iteration, path):
        """Enhanced selection path logging with node IDs"""
        if self.log_level in ['detailed', 'verbose']:
            path_info = []
            for node in path:
                node_id = self._get_node_id(node)
                uct_value = getattr(node, 'uct_value', 'N/A')
                path_info.append(f"node_{node_id}:v{node.visits}:uct{uct_value}")
            
            with open(self.log_path, mode='a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    iteration,
                    'detailed_selection',
                    len(path),
                    0,
                    'selection_details',
                    0,
                    ' -> '.join(path_info)
                ])
        else:
            super().log_selection_path(iteration, path)

    def log_node_comparison(self, iteration, parent_node, children_stats):
        """Log detailed comparison of child nodes during selection"""
        if self.log_level == 'verbose':
            for child, stats in children_stats:
                with open(self.log_path, mode='a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        iteration,
                        'node_comparison',
                        child.visits,
                        child.total_reward,
                        str(child.move),
                        stats.get('uct_value', 0),
                        f'parent_{self._get_node_id(parent_node)}_child_{self._get_node_id(child)}_exploration_{stats.get("exploration", 0):.3f}_exploitation_{stats.get("exploitation", 0):.3f}'
                    ])