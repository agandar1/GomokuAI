import numpy as np
#from sklearn import preprocessing
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
        return sum(vals)

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

    def get_outer(self, monomial):
        p1, p2, p5 = monomial[0], monomial[1], monomial[4]
        change_x, change_y = p2[0] - p1[0], p2[1] - p1[1]
        outer = []
        if (-1 < p1[0]-change_x < 19 and -1 < p1[1]-change_y < 19):
            outer.append([p1[0]-change_x, p1[1]-change_y])
        if (-1 < p5[0]+change_x < 19 and -1 < p5[1]+change_y < 19):
            outer.append([p5[0]+change_x, p5[1]+change_y])
        return outer

    def can_win(self, board):
        for m in self.monomials:
            vals = list(map(lambda x: board[x[0]][x[1]], m))
            score = np.prod(vals)
            if (score == 16):
                for p in range(len(m)):
                    if (board[m[p][0]][m[p][1]] == 1):
                        return m[p]
        return []
                    
    def block_opponent(self):
        enemy = self.gen_opponent_board()
        enemy_scores = self.network(enemy) 
        for m in self.monomials:
            vals = list(map(lambda x: enemy[x[0]][x[1]], m))
            score = np.prod(vals)
            open_spots = []
            outer = list(map(lambda x: enemy[x[0]][x[1]], self.get_outer(m)))
            if (score >= 8):
                for p in range(len(m)):
                    x, y = m[p][0], m[p][1]
                    if (enemy[x][y] == 1 and not (0 in outer)):
                        if (not ([x, y] in open_spots)):
                            open_spots.append([x, y])
            if (open_spots != []):
                greatest = 0
                greatest_coords = []
                for s in open_spots:
                    val = enemy_scores[s[0]][s[1]]
                    if (val > greatest):
                        greatest = val
                        greatest_coords = [s[0], s[1]]
                return greatest_coords
        return []
            
    def start(self):
        """run when the bot will start the game"""
        move = self.find_greatest_spot(self.board, self.score_board)
        self.board[move[0]][move[1]] = 2
        return move

    def turn(self, opponent_move):
        """takes opponent's last move (x, y) and returns bot's move (x, y)"""
        self.board[opponent_move[0]][opponent_move[1]] = 0
        self.score_board = self.network(self.board)
        enemy_board = self.gen_opponent_board()

        win, enemy_win = self.can_win(self.board), self.can_win(enemy_board)
        if (win != []):
            self.board[win[0]][win[1]] = 2
            return win

        elif (enemy_win != []):
            self.board[enemy_win[0]][enemy_win[1]] = 2
            return enemy_win

        block = self.block_opponent()
        if (block != []):
            self.board[block[0]][block[1]] = 2
            return block

        best_move = self.find_greatest_spot(self.board, self.score_board)
        self.board[best_move[0]][best_move[1]] = 2
        return best_move
        
        
bot = Bot(19)
