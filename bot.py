import numpy as np
import functools as f
import random

class Bot:
    def __init__(self, board_size):
        self.board_size = board_size
        self.board = np.full((board_size, board_size), 1, dtype=int)
        self.monomials = self.gen_monomials()

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

    def spot_value(self, spot):
        vals = []
        for m in self.find_monomials(spot):
            vals.append(list(map(lambda x: self.board[x[0]][x[1]], m)))
        for i in range(len(vals)):
            vals[i] = f.reduce(lambda x, y: x*y, vals[i])
        return f.reduce(lambda x, y: x+y, vals)

    def find_greatest_mono(self, board):
        greatest = 0
        greatest_monos = []
        for m in self.monomials:
            vals = list(map(lambda x: board[x[0]][x[1]], m))
            m_val = f.reduce(lambda x, y: x*y, vals)
            if (m_val > greatest):
                greatest = m_val
                greatest_monos = [m]
            if (m_val == greatest):
                greatest_monos.append(m)
        return random.choice(greatest_monos)

    def find_greatest_spot(self, board):
        greatest = 1
        greatest_coords = []
        for x in range(board.shape[0]):
            for y in range(board.shape[1]):
                if board[x][y] == 1:
                    value = self.spot_value([x, y])
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
    
    def start(self):
        """run when the bot will start the game"""
        move = self.find_greatest_spot(self.board)
        self.board[move[0]][move[1]] = 2
        return move

    def turn(self, opponent_move):
        """takes opponent's last move (x, y) and returns bot's move (x, y)"""
        self.board[opponent_move[0]][opponent_move[1]] = 0
        best_mono = self.find_greatest_mono(self.board)
        mono_scores = list(map(lambda x: self.spot_value(x), best_mono))
        best_move = best_mono[0]
        best_score = 0
        for i in range(len(mono_scores)):
            spot = self.board[best_mono[i][0]][best_mono[i][1]]
            if (mono_scores[i] > best_score and spot == 1):
                best_score = mono_scores[i]
                best_move = best_mono[i]
        self.board[best_move[0]][best_move[1]] = 2
        return best_move
        
        
bot = Bot(19)
