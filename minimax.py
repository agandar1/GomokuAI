import numpy as np
import random

class Bot:
    def __init__(self):
        self.size = 19
        self.board = np.full((19, 19), 1, dtype=int)
        self.monomials = self.gen_monomials()
        self.turn_cnt = 0

    def new_board(self):
        """make a new empty board size x size filled with 1's"""
        self.board = np.full((self.size, self.size), 1, dtype=int)

    def monos_and_vals(self, board, mono):
        ai_mono = [board[p[0]][p[1]] for p in mono]
        op_mono = self.flip_mono(ai_mono)
        return ai_mono, op_mono, np.prod(ai_mono), np.prod(op_mono)

    def lonely_spot(self, board, spot, max_range):
        """check if this spot is too far away from other pieces"""
        x, y = spot[0], spot[1]
        directions = [(1, 0), (0, 1), (1, 1), (-1, 1)]
        for d in directions:
            counts = [0, 0] 
            for n in ((1, 0), (-1, 1)):
                for i in range (1, max_range):
                    newx, newy = x+(n[0]*(i*d[0])), y+(n[0]*(i*d[1]))
                    if (0 <= newx <= 18 and 0 <= newy < 18):
                        if (board[newx][newy] != 1):
                            return False
        return True

    def winner(self, board):
        """check if someone won"""
        for m in self.monomials:
            ai_mono, op_mono, ai_val, op_val = self.monos_and_vals(board, m)
            if ai_val >= 32:
                return 2
            if op_val >= 32:
                return 0
        return 1
        
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

    def flip_mono(self, mono_values):
        """flip 2s and 0s in a monomial to get the opponent's perspective"""
        op_mono = []
        for v in mono_values:
            if v == 2:
                op_mono.append(0)
            elif v == 1:
                op_mono.append(1)
            elif v == 0:
                op_mono.append(2)
        return op_mono

    def get_outer(self, board, monomial):
        """get a monomial's outer values"""
        # get the change to figure out the mono's direction
        p1, p2, p5 = monomial[0], monomial[1], monomial[4]
        change_x, change_y = p2[0] - p1[0], p2[1] - p1[1]
        # calculate the outer points using the change
        l = False
        r = False

        for i in range(len(monomial)):
            p = monomial[i]
            if board[p[0]][p[1]] != 1:
                l = [p[0]-change_x, p[1]-change_y]
                break
        for i in range(len(monomial)-1, -1, -1):
            p = monomial[i]
            if board[p[0]][p[1]] != 1:
                r = [p[0]+change_x, p[1]+change_y]
                break

        if not l:
            l = [p1[0]-change_x, p1[1]-change_y]
        if not r:
            r = [p1[0]+change_x, p1[1]+change_y]
        # only take the coordinates if it's within bounds
        result = []
        if 0 <= l[0] < 19 and 0 <= l[1] < 19:
            result.append(l)
        else:
            result.append(False)
        if 0 <= r[0] < 19 and 0 <= r[1] < 19:
            result.append(r)
        else:
            result.append(False)
        return result

    def mono_pattern(self, board, monomial):
        """get the pattern of a single monomial on a board"""
        ai_mono, op_mono, ai_val, op_val = self.monos_and_vals(board, monomial)
        outer = self.get_outer(board, monomial)
        if outer[0]:
            ai_l = board[outer[0][0]][outer[0][1]]
        else:
            ai_l = 0
        if outer[1]:
            ai_r = board[outer[1][0]][outer[1][1]]
        else:
            ai_r = 0
        op_l, op_r = 2 if ai_l == 0 else 0, 2 if ai_r == 0 else 0
        players = {'ai': {'val': ai_val, 'mono': ai_mono, 'out': [ai_l, ai_r]},
                   'op': {'val': op_val, 'mono': op_mono, 'out': [op_l, op_r]}}
        results = []
        for player, vals in players.items():
            val, mono = vals['val'], vals['mono']
            open_count, split = 0, 0
            out_l, out_r = vals['out'][0], vals['out'][1]
            open_count += 1 if mono[0] == 1 or out_l == 1 else 0 
            open_count += 1 if mono[-1] == 1 or out_r == 1 else 0
            if val == 32:
                result = (5, 2, 0)
            elif val == 16:
                if mono[0] == 2 and mono[-1] == 2:
                    split = 1
                result = (4, open_count, split)
            elif val == 8:
                if mono[0] == 2 and mono[-1] == 2:
                    split = 2
                elif (mono[0] == 2 or mono[-1] == 2) and (mono[1] == 2 and mono[-2] == 2):
                    split = 1
                result = (3, open_count, split)
            elif val == 4:
                if mono[0] == 2 and mono[-1] == 2:
                    split = 3
                else:
                    split = 0
                    found_first, found_second = False, False
                    for x in mono:
                        if not found_first and x == 2:
                            found_first = True
                        elif found_first and not found_second and x != 2:
                            split += 1
                        elif found_first and not found_second and x == 2:
                            break
                result = (2, open_count, split)
            else:
                result = (0, 0, 0)
            results.append(result)
        return results

    def mono_value(self, pattern):
        """give a value to a monomial pattern"""
        pieces = pattern[0]
        spaces = pattern[2]
        open_outer = pattern[1]
        val = 0
        if pieces == 5:
            val = 100000
        elif pieces == 4:
            val = 4800 if open_outer >= 2 else 600
        elif pieces == 3:
            val = 600 if open_outer >= 2 else 200
        elif pieces == 2:
            val = 50 if open_outer >= 2 else 10

        return val
        
    def board_eval(self, board):
        mono_patterns = [self.mono_pattern(board, m) for m in self.monomials]
        mono_values = [self.mono_value(ai) - self.mono_value(op) for ai, op in mono_patterns]
        return sum(mono_values)

    def find_open3_spots(self, mono, board):
        taken = [p for p in mono if board[p[0]][p[1]] != 1]
        x, y, last_x, last_y = taken[0][0], taken[0][1], taken[-1][0], taken[-1][1]
        change_x, change_y = mono[1][0] - mono[0][0], mono[1][1] - mono[0][1]
        split = True if last_x-x >= 3 or last_y - y >= 3 else False
        split = 0
        x_dif , y_dif = last_x - x, last_y - y
        if x_dif == 3 or y_dif == 3:
            split = 1
        elif x_dif == 4 or y_dif == 4:
            split = 2
        
        # get available vertical spots
        if (change_x == 0):
            outer = [[x, y-1], [last_x, last_y+1]]
            available = [[o[0], o[1]] for o in outer if 0 <= o[0] <= 18 and 0 <= o[1] <= 18 and board[o[0]][o[1]] == 1]
            available += [[x, y+i] for i in range(len(taken)) if 0 <= x <= 18 and 0 <= y+i <= 18 and board[x][y+i] == 1]
        # get available horizontal spots
        elif (change_y == 0):
            outer = [[x-1, y], [last_x+1, last_y]]
            available = [[o[0], o[1]] for o in outer if 0 <= o[0] <= 18 and 0 <= o[1] <= 18 and board[o[0]][o[1]] == 1]
            available += [[x+i, y] for i in range(len(taken)) if 0 <= x+i <= 18 and 0 <= y <= 18 and board[x+i][y] == 1]
        # get available negative slope diagonal spots
        elif (change_x > 0 and change_y > 0):
            outer = [[x-1, y-1], [last_x+1, last_y+1]]
            available = [[o[0], o[1]] for o in outer if 0 <= o[0] <= 18 and 0 <= o[1] <= 18 and board[o[0]][o[1]] == 1]
            available += [[x+i, y+i] for i in range(len(taken)) if 0 <= x+i <= 18 and 0 <= y+i <= 18 and board[x+i][y+i] == 1]
        # get available positive slope diagonal spots
        else:
            outer = [[x+1, y-1], [last_x-1, last_y+1]]
            available = [[o[0], o[1]] for o in outer if 0 <= o[0] <= 18 and 0 <= o[1] <= 18 and board[o[0]][o[1]] == 1]
            available += [[x-i, y+i] for i in range(len(taken)) if 0 <= x-i <= 18 and 0 <= y+i <= 18 and board[x-i][y+i] == 1]
        return available, split

    def open_spots(self, board):
        for mono in self.monomials:
            ai_mono, op_mono, ai_val, op_val = self.monos_and_vals(board, mono)
            outer = self.get_outer(board, mono)
            if outer[0]:
                ai_l = board[outer[0][0]][outer[0][1]]
            else:
                ai_l = -1
            if outer[1]:
                ai_r = board[outer[1][0]][outer[1][1]]
            else:
                ai_r = -1

            # return forced/urgent spots immediately
            if ai_val == 16:
                available = [p for p in mono if board[p[0]][p[1]] == 1]
                if ai_mono[0] != 1 and ai_l == 1:
                    available.append(outer[0])
                if ai_mono[-1] != 1 and ai_r == 1:
                    available.append(outer[1])
                print("found own 4", available)
                return available
        for mono in self.monomials:
            ai_mono, op_mono, ai_val, op_val = self.monos_and_vals(board, mono)
            outer = self.get_outer(board, mono)
            if outer[0]:
                ai_l = board[outer[0][0]][outer[0][1]]
            else:
                ai_l = -1
            if outer[1]:
                ai_r = board[outer[1][0]][outer[1][1]]
            else:
                ai_r = -1
            op_l, op_r = 2 if ai_l == 0 else 0, 2 if ai_r == 0 else 0

            # return forced/urgent spots immediately
            if op_val == 16:
                available = [p for p in mono if board[p[0]][p[1]] == 1]
                if ai_mono[0] != 1 and ai_l == 1:
                    available.append(outer[0])
                if ai_mono[-1] != 1 and ai_r == 1:
                    available.append(outer[1])
                print("found enemy 4", available)
                return available
        for mono in self.monomials:
            ai_mono, op_mono, ai_val, op_val = self.monos_and_vals(board, mono)
            if ai_val == 8:
                available, split = self.find_open3_spots(mono, board)
                if len(available) - split == 2 and split != 2:
                    print("found own 3", available)
                    return available
        for mono in self.monomials:
            ai_mono, op_mono, ai_val, op_val = self.monos_and_vals(board, mono)
            if op_val == 8:
                available, split = self.find_open3_spots(mono, board)
                if len(available) - split == 2:
                    print("found enemy 3", available)
                    return available
            
        available = [[x, y] for x in range(19) for y in range(19)
                if board[x][y] == 1 and not self.lonely_spot(board, [x, y], 2)]
        return available

    def minimax(self, board, depth, max_depth, ai_turn, alpha, beta):
        board = np.copy(board)
        if self.winner(board) != 1 or depth >= max_depth:
            return (self.board_eval(board),)
        moves = self.open_spots(board)
        best_move = [-1, -1]
        if ai_turn:
            best = np.NINF
            for move in moves:
                next_board = np.copy(board)
                next_board[move[0]][move[1]] = 2
                value = self.minimax(next_board, depth+1, max_depth, False, alpha, beta)[0]
                next_board[move[0]][move[1]] = 1
                best = max(best, value)
                best_move = move if value == best else best_move
                alpha = max(alpha, best)
                if beta <= alpha:
                    break
            return (best, best_move)
        else:
            best = np.inf
            for move in moves:
                next_board = np.copy(board)
                next_board[move[0]][move[1]] = 0
                value = self.minimax(next_board, depth+1, max_depth, True, alpha, beta)[0]
                next_board[move[0]][move[1]] = 1
                best = min(best, value)
                best_move = move if value == best else best_move
                beta = min(beta, best)
                if beta <= alpha:
                    break
            return (best, best_move)
        
    def start(self):
        """run when the bot will start the game"""
        # just picks the center spot
        self.board[9][9] = 2
        self.turn_cnt += 1
        return (9, 9)

    def early_game(self, board):
        available = [[x, y] for x in range(19) for y in range(19)
                if board[x][y] == 1 and not self.lonely_spot(board, [x, y], 2)]
        print(available)
        return random.choice(available)

    def turn(self, opponent_move):
        """takes opponent's last move (x, y) and returns bot's move (x, y)"""
        # mark opponent's last move
        self.board[opponent_move[0]][opponent_move[1]] = 0
        self.turn_cnt +=1

        if self.turn_cnt < 2:
            best_move = self.early_game(self.board)
        else:
            best_move = self.minimax(self.board, 0, 2, True, np.NINF, np.inf)[1]
        self.board[best_move[0]][best_move[1]] = 2
        self.turn_cnt +=1
        return best_move
