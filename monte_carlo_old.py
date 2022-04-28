import numpy as np
import random
import time
from simulation_bot import SimBot

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
    def __init__(self, board):
        self.root_state = np.copy(board)
        self.root = Node()
        self.turn = 2
        self.simulator = SimBot(board)

    def search_tree(self):
        start = time.time()
        max_time = 15
        rollouts_cnt = 0
        available = 361

        while time.time() < start + max_time and rollouts_cnt < available:
            node, board, tmp_available = self.select_node()
            available = tmp_available if tmp_available > -1 else available
            print("selected:", node.move)
            result = self.roll_out(board)
            print("outcome:", result)
            self.backpropagate(node, self.turn, result)
            rollouts_cnt += 1
        
    def select_node(self):
        node = self.root
        board = np.copy(self.root_state)
        posibilities = -1

        while len(node.children) > 0:
            children = node.children.values()
            max_val = max(children, key=lambda c: c.value()).value()
            tied_nodes = [c for c in children if c.value() == max_val]
            node = random.choice(tied_nodes)
            board = self.update_board(board, node.move)

            if node.visits == 0:
                return (node, board, posibilities)

        if self.expand_node(node, board):
            posibilities = len(node.children)
            node = random.choice(list(node.children.values()))
            board = self.update_board(board, node.move)
        return (node, board, posibilities)

    def expand_node(self, parent, board):
        children = []
        if self.game_over(board) != 1:
            print("GAME OVER")
            return False
        
        for move in self.possible_moves(board):
            children.append(Node(move, parent))
            
        parent.add_children(children)
        return True

    def roll_out(self, board):
        self.simulator.set_board(board)
        while self.game_over(board) == 1:
            self.simulator.toggle_turn()
            move = self.simulator.turn()
            board = self.update_board(board, move)
        return self.game_over(board)

    def backpropagate(self, node, turn, result):
        reward = 0 if result == turn else 1
        while node is not None:
            node.visits += 1
            node.reward += reward
            node = node.parent
            reward = 0 if reward == 1 else 1

    def choose_best_move(self):
        max_reward = max(self.root.children.values(), key=lambda c: c.reward+c.visits)
        max_reward = max_reward.reward + max_reward.visits
        max_children = [c for c in self.root.children.values() if c.reward+c.visits == max_reward]
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
        self.root_state = np.copy(new_board)
        self.root = Node()
        
    def set_turn(self, to_play):
        self.turn = to_play
        
    def update_board(self, board, move):
        x, y = move
        new_board = np.copy(board)
        new_board[x][y] = self.turn
        self.turn = 0 if self.turn == 2 else 2
        return new_board

    def possible_moves(self, board):
        scores = self.simulator.network(board)
        enemy_board = self.simulator.gen_opponent_board(board)
        best_monos = self.simulator.find_best_monos(board, enemy_board)
        
        if (best_monos[1][1] > best_monos[0][1]):
            available = self.simulator.block(board, scores, best_monos)
        else:
            available = self.simulator.build(board, scores, best_monos[0]) 

        print("available:", available)
        return [tuple(move) for move in available]

    def game_over(self, board):
        #print(board)
        for x in range(19):
            for y in range(19):
                player = board[x][y]
                if player == 1:
                    continue
                directions = [(1, 0), (0, 1), (1, 1), (-1, 1)]
                for d in directions:
                    counts = [0, 0] 
                    for n in ((1, 0), (-1, 1)):
                        for i in range (1, 5):
                            newx, newy = x+(n[0]*(i*d[0])), y+(n[0]*(i*d[1]))
                            if (0 <= newx <= 18 and 0 <= newy < 18):
                                if (board[newx][newy] == player):
                                    counts[n[1]] += 1
                                else: break
                    if (counts[0] + counts[1] >= 4):
                        return player
        return 1
