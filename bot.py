import numpy as np
from sklearn import preprocessing
import random

class Bot:
    def __init__(self, board_size):
        self.board_size = board_size
        self.board = np.full((board_size, board_size), 1, dtype=int)
        self.monomials = self.gen_monomials()
        self.score_board = np.copy(self.board)
        self.score_board = self.network(self.score_board)

    def new_board(self):
        self.board = np.full((self.board_size, self.board_size), 1, dtype=int)
        
    def gen_monomials(self):
        size = self.board.shape[0]
        monomials = []
        for i in range(size):
            for j in range(size):
                if (i < size - 4):
                    monomials.append([[x, j] for x in range(i, i+5)])
                if (j < size - 4):
                    monomials.append([[i, y] for y in range(j, j+5)])
                if (i < size - 4 and j < size - 4):
                    monomials.append([[i+x, j+x] for x in range(5)])
                if (i > 3 and j < size - 4):
                    monomials.append([[i-x, j+x] for x in range(5)])
        return monomials

    def find_monomials(self, spot):
        monomials = []
        for m in self.monomials:
            if ([spot[0], spot[1]] in m):
                monomials.append(m)
        return monomials

    def spot_value(self, board, spot):
        vals = []
        for m in self.find_monomials(spot):
            vals.append(list(map(lambda x: board[x[0]][x[1]], m)))
        for i in range(len(vals)):
            vals[i] = np.prod(vals[i]) 
        return np.sum(vals)

    def two_layers(self, board):
        scores = np.copy(board)
        for x in range(len(board)):
            for y in range(len(board)):
                scores[x][y] = self.spot_value(board, [x, y])
        return np.array(scores)

    def network(self, board):
        for x in range(1):
            board = self.two_layers(board)
        return board

    def find_greatest_spot(self, board, scores):
        greatest = 0
        greatest_coords = []
        for x in range(board.shape[0]):
            for y in range(board.shape[1]):
                if board[x][y] == 1:
                    value = scores[x][y]
                    if (value > greatest):
                        greatest = value
                        greatest_coords = [[x, y]]
                    elif (value == greatest):
                        greatest_coords.append([x, y])
        return random.choice(greatest_coords)

    def gen_opponent_board(self):
        temp = np.where(self.board != 2, self.board, 3)
        temp = np.where(temp != 0, temp, 2)
        return np.where(temp != 3, temp, 0)

    def block_open_three(self):
        enemy = self.gen_opponent_board()
   #     for m in self.monomials:
            
    def start(self):
        """run when the bot will start the game"""
        move = self.find_greatest_spot(self.board, self.score_board)
        self.board[move[0]][move[1]] = 2
        return move

    def turn(self, opponent_move):
        """takes opponent's last move (x, y) and returns bot's move (x, y)"""
        self.board[opponent_move[0]][opponent_move[1]] = 0
        self.score_board = self.network(self.board)
        best_move = self.find_greatest_spot(self.board, self.score_board)
        self.board[best_move[0]][best_move[1]] = 2
        return best_move
        
        
bot = Bot(19)
