import numpy as np
import random

class SimBot:
    def __init__(self, board):
        self.size = 19
        self.board = list(map(list, board))
        self.monomials = self.gen_monomials()
        self.score_board = self.network(np.copy(self.board))
        self.turns_cnt = 0

    def new_board(self):
        """make a new empty board size x size filled with 1's"""
        self.board = np.full((self.size, self.size), 1, dtype=int)
        self.score_board = self.network(np.copy(self.board))
        self.turns_cnt = 0

    def set_board(self, board):
        """change the board to the passed in BOARD"""
        self.board = list(map(list, board))
        self.score_board = self.network(np.copy(self.board))

    def toggle_turn(self):
        """swap values on the board to play as the opponent"""
        self.board = self.gen_opponent_board(self.board)
        self.score_board = self.network(np.copy(self.board))
        
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
        if (val == 8 and self.is_closed(board, mono)):
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

    def gen_opponent_board(self, board):
        """generate the enemy's board by flipping bot's board"""
        new_board = np.copy(board)
        for i in range(19):
            for j in range(19):
                if new_board[i][j] == 2:
                    new_board[i][j] = 0
                elif new_board[i][j] == 0:
                    new_board[i][j] = 2
        return new_board
    
    def highest_spots(self, board, scores):
        """find bot's most valuable spot"""
        available = [[x, y] for x in range(19) for y in range(19) if board[x][y] == 1]
        flat_scores = [scores[spot[0]][spot[1]] for spot in available]
        sorted_scores = np.sort(flat_scores)
        highest = list(dict.fromkeys(sorted_scores))
        available = [[a[0], a[1]] for a in available if scores[a[0]][a[1]] >= highest[-2]]
        return available

    def block(self, board, scores, monos):
        """find the best place to block a monomial"""
        coords, val = monos[1][0], monos[1][1]
        # block closed 4, or try to block open 4
        if (val == 16):
            available = [c for c in coords if board[c[0]][c[1]] == 1]
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
        # choose a spot close to the opponent's opening
        elif (val == 2):
            available = [[x, y] for x in range(19) for y in range(19) if scores[x][y] == 16]
        # otherwise just try to build
        else:
            available =  self.build(board, scores, monos[0])
        return available
            
    def build(self, board, scores, best_mono):
        """pick a spot to try to win"""
        coords, val = best_mono
        # immediately win if we have 4 in a row or pick best spot in open 3
        if (val >= 8):
            available = [c for c in coords if board[c[0]][c[1]] == 1]
            if (len(available) > 0):
                return available
        # otherwise just get most valuable spot
        return self.highest_spots(board, scores)
        
    def start(self):
        """run when the bot will start the game"""
        # just picks random spot near the center
        move = [random.randint(7, 11), random.randint(7, 11)]
        self.board[move[0]][move[1]] = 2
        self.turns_cnt += 1
        return move

    def turn(self):
        """return a decent move for the simulation"""
        # calculate bot's and opponent's scores
        self.score_board = self.network(self.board)
        enemy_board = self.gen_opponent_board(self.board)

        # see who is ahead
        best_monos = self.find_best_monos(self.board, enemy_board)
        if (((best_monos[1][1] > best_monos[0][1]) and best_monos[1][1] != 4)or self.turns_cnt < 3):
            # block if enemy is ahead
            best_moves = self.block(self.board, self.score_board, best_monos)
        else:
            # ignore enemy and build if bot is ahead
            best_moves = self.build(self.board, self.score_board, best_monos[0]) 

        random.shuffle(best_moves)
        #best_move = max(best_moves, key=lambda x: self.score_board[x[0]][x[1]]) 
        best_move = random.choice(best_moves)
        
        # place piece and send choice back to gui
        self.board[best_move[0]][best_move[1]] = 2
        self.turns_cnt += 1
        return best_move
