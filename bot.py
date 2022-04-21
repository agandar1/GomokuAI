import numpy as np
import random
from monte_carlo import *

class Bot:
    def __init__(self, size):
        self.size = size
        self.board = np.full((size, size), 1, dtype=int)
        self.monomials = self.gen_monomials()
        self.score_board = self.network(np.copy(self.board))
        self.tree = MonteCarlo(self.board, 2)

    def new_board(self):
        """make a new empty board size x size filled with 1's"""
        self.board = np.full((self.size, self.size), 1, dtype=int)
        self.score_board = self.network(np.copy(self.board))
        self.tree.reset_tree(self.board)
        
    def gen_monomials(self):
        """make a list of all monomial coordinates"""
        monomials = []
        for i in range(self.size):
            for j in range(self.size):
                if (i < self.size - 4):
                    monomials.append([[x, j] for x in range(i, i+5)])
                if (j < self.size - 4):
                    monomials.append([[i, y] for y in range(j, j+5)])
                if (i < self.size - 4 and j < self.size - 4):
                    monomials.append([[i+x, j+x] for x in range(5)])
                if (i > 3 and j < self.size - 4):
                    monomials.append([[i-x, j+x] for x in range(5)])
        return monomials

    def find_monomials(self, spot):
        """find all monomials that correspond to a certain spot"""
        return [m for m in self.monomials if spot in m]

    def spot_value(self, board, spot):
        """calculate the value of a single spot on the board"""
        return sum([self.mono_value(board, m, False) for m in self.find_monomials(spot)])

    def network(self, board):
        """calculate values of all spots to create a score board"""
        stacks = 1
        scores = np.copy(board)
        for x in range(stacks):
            for i in range(self.size):
                for j in range(self.size):
                    scores[i][j] = self.spot_value(board, [i, j])
        return scores

    def get_outer(self, monomial):
        """get a monomial's outer coordinates"""
        # get the change to figure out the mono's direction
        p1, p2, p5 = monomial[0], monomial[1], monomial[4]
        change_x, change_y = p2[0] - p1[0], p2[1] - p1[1]
        # calculate the outer points using the change
        left = [p1[0]-change_x, p1[1]-change_y]
        right = [p5[0]+change_x, p5[1]+change_y]
        outer = []
        # only take the coordinates if it's within bounds
        if (0 <= left[0] < 19 and 0 <= left[1] < 19):
            outer.append(left)
        if (0 <= right[0] < 19 and 0 <= right[1] < 19):
            outer.append(right)
        return outer

    def is_closed(self, board, monomial):
        """check if a monomial is open on both sides"""
        # if there is only one outer point, or one of them is taken, it is closed
        outer = self.get_outer(monomial)
        return (len(outer) != 2 or not all([board[s[0]][s[1]] == 1 for s in outer]))
    
    def mono_value(self, board, mono, for_self):
        """get the value for a single monomial"""
        # calculate value of the monomial, closed monomials are worth 0
        val = np.prod([board[x[0]][x[1]] for x in mono])
        if ((val == 8 or (for_self and 4 <= val <= 8 )) and self.is_closed(board, mono)):
            val = 0
        return val
        
    def find_best_monos(self, board, e_board):
        """find greatest monomial for both players"""
        # make a list of all monomials and their values
        bot_scores = [[m, self.mono_value(board, m, True)] for m in self.monomials]
        enemy_scores = [[m, self.mono_value(e_board, m, False)] for m in self.monomials]
        # return the highest one for each player
        random.shuffle(bot_scores)
        random.shuffle(enemy_scores)
        return [max(bot_scores, key=lambda x: x[1]), max(enemy_scores, key=lambda x: x[1])]

    def gen_opponent_board(self, bot_board):
        """generate the enemy's board by flipping bot's board"""
        temp = np.where(bot_board != 2, bot_board, 3)
        temp = np.where(temp != 0, temp, 2)
        return np.where(temp != 3, temp, 0)
    
    def highest_spot(self, board, scores, enemy_scores):
        """find bot's most valuable spot"""
        coords = [[x, y] for x in range(19) for y in range(19) if board[x][y] == 1]
        random.shuffle(coords)
        return max(coords, key=lambda x: scores[x[0]][x[1]])

    def block(self, board, scores, enemy_scores, monos):
        """find the best place to block a monomial"""
        coords, val = monos[1][0], monos[1][1]
        # block closed 4, or try to block open 4
        if (val == 16):
            available = [c for c in coords if board[c[0]][c[1]] == 1]
            random.shuffle(available)
            return max(available, key=lambda x: scores[x[0]][x[1]])
        # pick most beneficial spot to block open 3 or starting move
        elif (val == 8):
            taken = [c for c in coords if board[c[0]][c[1]] != 1]
            x, y, last_x, last_y = taken[0][0], taken[0][1], taken[-1][0], taken[-1][1]
            change_x, change_y = coords[1][0] - coords[0][0], coords[1][1] - coords[0][1]
            # get available vertical spots
            if (change_x == 0):
                available = [[x, y-1], [last_x, last_y+1]]
                available += [[x, y+i] for i in range(len(taken)) if board[x][y+i] == 1]
            # get available horizontal spots
            elif (change_y == 0):
                available = [[x-1, y], [last_x+1, last_y]]
                available += [[x+i, y] for i in range(len(taken)) if board[x+i][y] == 1]
            # get available negative slope diagonal spots
            elif (change_x > 0 and change_y > 0):
                available = [[x-1, y-1], [last_x+1, last_y+1]]
                available += [[x+i, y+i] for i in range(len(taken)) if board[x+i][y+i] == 1]
            # get available positive slope diagonal spots
            else:
                available = [[x+1, y-1], [last_x-1, last_y+1]]
                available += [[x-i, y+i] for i in range(len(taken)) if board[x-i][y+i] == 1]
            # choose the one best for the bot
            random.shuffle(available)
            move = max(available, key=lambda x: scores[x[0]][x[1]])
            return move
        # choose a spot close to the opponent's opening
        elif (val == 2):
            available = [[x, y] for x in range(19) for y in range(19) if board[x][y] == 1]
            random.shuffle(available)
            return max(available, key=lambda x: enemy_scores[x[0]][x[1]])
        # otherwise just try to build
        else:
            return self.build(board, scores, enemy_scores, monos[0])
            
    def build(self, board, scores, enemy_scores, best_mono):
        """pick a spot to try to win"""
        coords, val = best_mono
        # immediately win if we have 4 in a row or pick best spot in open 3
        if (val >= 8):
            available = [c for c in coords if board[c[0]][c[1]] == 1]
            random.shuffle(available)
            best = max(available, key=lambda x: scores[x[0]][x[1]])
            return best
        # otherwise just get most valuable spot
        else:
            return self.highest_spot(board, scores, enemy_scores)
        
    def start(self):
        """run when the bot will start the game"""
        # just picks random spot near the center
        self.tree.set_turn(2)
        move = [random.randint(7, 11), random.randint(7, 11)]
        self.board[move[0]][move[1]] = 2
        self.tree.apply_move(move)
        return move

    def turn(self, opponent_move):
        """takes opponent's last move (x, y) and returns bot's move (x, y)"""
        # mark opponent's last move
        self.tree.set_turn(0)
        self.board[opponent_move[0]][opponent_move[1]] = 0
        self.tree.apply_move(opponent_move)
        self.tree.set_turn(2)

        # calculate bot's and opponent's scores
        self.score_board = self.network(self.board)
        enemy_board = self.gen_opponent_board(self.board)
        enemy_scores = self.network(enemy_board)

        # see who is ahead
        best_monos = self.find_best_monos(self.board, enemy_board)
        if (best_monos[1][1] > best_monos[0][1] and best_monos[1][1] != 4):
            # block if enemy is ahead
            best_move = self.block(self.board, self.score_board, enemy_scores, best_monos)
        else:
            # ignore enemy and build if bot is ahead
            best_move = self.build(self.board, self.score_board, enemy_scores, best_monos[0]) 

        # place piece and send choice back to gui
        self.tree.search_tree()
        best_move = self.tree.choose_best_move()
        self.board[best_move[0]][best_move[1]] = 2
        self.tree.apply_move(best_move)
        return best_move
        
bot = Bot(19)
