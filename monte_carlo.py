import numpy as np
import random
import time
from copy import deepcopy

class Node:
    def __init__(self, move: tuple = None, parent: object = None):
        self.move = move
        self.parent = parent
        self.visits = 0  # number of visits
        self.reward = 0  # reward
        self.children = {}
        self.outcome = 0

    def add_children(self, children):
        for c in children:
            self.children[c.move] = c

    def value(self):
        explore = 0.5
        if self.visits == 0:
            return np.inf
        else:
            return self.reward / self.visits + explore * np.sqrt(2 * np.log(self.parent.visits) / self.visits)


class MonteCarlo:
    def __init__(self, board, turn):
        self.root_state = deepcopy(board)
        self.root = Node()
        self.node_count = 0
        self.num_rollouts = 0
        self.turn = turn

    def search_tree(self):
        start = time.time()
        max_time = 10
        rollouts_cnt = 0

        while time.time() < start + max_time:
            node, board = self.select_node()
            result = self.roll_out(board)
            self.backpropagate(node, self.turn, result)
        
    def select_node(self):
        node = self.root
        board = deepcopy(self.root_state)

        while len(node.children) > 0:
            children = node.children.values()
            max_val = max(children, key=lambda c: c.value()).value()
            tied_nodes = [c for c in children if c.value() == max_val]
            node = random.choice(tied_nodes)
            board = self.update_board(board, node.move)

            if node.visits == 0:
                return (node, board)
            
        if self.expand_node(node, board):
            node = random.choice(list(node.children.values()))
            board = self.update_board(board, node.move)
        return (node, board)

    def expand_node(self, parent, board):
        children = []
        if self.game_over(board) != 1:
            return False
        
        for move in self.possible_moves(board):
            children.append(Node(move, parent))
            
        parent.add_children(children)
        return True

    def roll_out(self, board):
        moves = self.possible_moves(board)
        while self.game_over(board) == 1:
            move = random.choice(moves)
            board = self.update_board(board, move)
            moves.remove(move)
        return self.game_over(board)

    def backpropagate(self, node, turn, result):
        reward = 0 if result == turn else 1
        while node is not None:
            node.visits += 1
            node.reward += reward
            node = node.parent
            reward = 0 if reward == 1 else 1

    def choose_best_move(self):
        if self.game_over(self.root_state) != 1:
            return "Game has already ended"
        max_visits = max(self.root.children.values(), key=lambda c: c.visits).visits
        max_children = [c for c in self.root.children.values() if c.visits == max_visits]
        best_move = random.choice(max_children)
        return best_move.move

    def apply_move(self, move):
        if move in self.root.children:
            child = self.root.children[move]
            child.parent = None
            self.root = child
            self.root_state = self.update_board(self.root_state, child.move)
            return
        self.root_state = self.update_board(self.root_state, move)
        self.root = Node()

    def reset_tree(self, new_board):
        self.root_state = deepcopy(new_board)
        self.root = Node()
        
    def set_turn(self, to_play):
        self.turn = to_play
        
    def update_board(self, board, move):
        x, y = move
        new_board = deepcopy(board)
        new_board[x][y] = self.turn
        self.turn = 0 if self.turn == 2 else 2
        return new_board

    def game_over(self, board):
        for x in range(19):
            for y in range(19):
                player, count = board[x][y], 0
                if player == 1:
                    continue
                if y + 5 <= 18:
                    for i in range(5):
                        if player == board[x][y+i]:
                            count += 1
                    if count >= 5: return player
                if x + 5 <= 18:
                    count = 0
                    for i in range(5):
                        if player == board[x+i][y]:
                            count += 1
                    if count >= 5: return player
                    count = 0
                    if y + 5 <= 18:
                        for i in range(5):
                            if player == board[x+i][y+i]:
                                count += 1
                        if count >= 5: return player
                    count = 0
                    if y - 5 >= 0:
                        for i in range(5):
                            if player == board[x+i][y-i]:
                                count += 1
                        if count >= 5: return player
        return 1

    def possible_moves(self, board):
        return [(x, y) for x in range(19) for y in range(19)
                if board[x][y] == 1]

    
                    
                    

            
            
        
