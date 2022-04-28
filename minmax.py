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
        self.score_board = self.network(np.copy(self.board))

    def spot_value(self, board, spot):
        """calculate the value of a single spot on the board"""
        return sum([self.mono_prod(board, m, False) for m in self.find_monomials(spot)])

    def network(self, board):
        """calculate values of all spots to create a score board"""
        stacks = 1
        scores = np.copy(board)
        for x in range(stacks):
            for i in range(self.size):
                for j in range(self.size):
                    scores[i][j] = self.spot_value(board, [i, j])
        return scores

    def mono_prod(self, board, mono, for_self):
        """get the value for a single monomial"""
        # calculate value of the monomial, closed monomials are worth 0
        val = np.prod([board[x[0]][x[1]] for x in mono])
        return val

    def lonely_spot(self, board, spot):
        """check if this spot is too far away from other pieces"""
        x, y = spot[0], spot[1]
        directions = [(1, 0), (0, 1), (1, 1), (-1, 1)]
        for d in directions:
            counts = [0, 0] 
            for n in ((1, 0), (-1, 1)):
                for i in range (1, 2):
                    newx, newy = x+(n[0]*(i*d[0])), y+(n[0]*(i*d[1]))
                    if (0 <= newx <= 18 and 0 <= newy < 18):
                        if (board[newx][newy] != 1):
                            return False
        return True

    def winner(self, board):
        """check if someone won"""
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
        l = [p1[0]-change_x, p1[1]-change_y]
        r = [p5[0]+change_x, p5[1]+change_y]
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
        #left = board[l[0]][l[1]] if (0 <= l[0] < 19 and 0 <= l[1] < 19) else 0
        #right = board[r[0]][r[1]] if (0 <= r[0] < 19 and 0 <= r[1] < 19) else 0
        #return left, right

    def mono_pattern(self, board, monomial):
        """get the pattern of a single monomial on a board"""
        ai_mono = [board[p[0]][p[1]] for p in monomial]
        op_mono = self.flip_mono(ai_mono)
        ai_val, op_val = np.prod(ai_mono), np.prod(op_mono)
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
            val = 4800 if open_outer >= 2 else 500
        elif pieces == 3:
            val = 600 if open_outer >= 2 else 200
        elif pieces == 2:
            val = 50 if open_outer >= 2 else 10

        return val
        
    def board_eval(self, board):
        mono_patterns = [self.mono_pattern(board, m) for m in self.monomials]
        mono_values = [self.mono_value(ai) - self.mono_value(op) for ai, op in mono_patterns]
        return sum(mono_values)

    def open_spots(self, board):
        for mono in self.monomials:
            ai_mono = [board[p[0]][p[1]] for p in mono]
            op_mono = self.flip_mono(ai_mono)
            ai_val, op_val = np.prod(ai_mono), np.prod(op_mono)
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
            if ai_val == 16 or op_val == 16:
                open = [p for p in mono if board[p[0]][p[1]] == 1]
                if ai_mono[0] != 1 and ai_l == 1:
                    open.append(outer[0])
                if ai_mono[-1] != 1 and ai_r == 1:
                    open.append(outer[1])
                print("found 4", open)
                return open
        for mono in self.monomials:
            print(len(self.monomials))
            #print(mono)
            ai_mono = [board[p[0]][p[1]] for p in mono]
            op_mono = self.flip_mono(ai_mono)
            ai_val, op_val = np.prod(ai_mono), np.prod(op_mono)
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
            #print(ai_mono, "-", ai_val, "/", op_mono, "-", op_val)
            if (op_val == 8 or ai_val == 8) and (ai_mono[0] == 1 or ai_l == 1) and (ai_mono[-1] == 1 or ai_r == 1):
                open = [p for p in mono if board[p[0]][p[1]] == 1]
                if op_mono[0] != 1 and ai_l == 1:
                    open.append(outer[0])
                if op_mono[-1] != 1 and ai_r == 1:
                    open.append(outer[1])
                print("found open 3", open)
                return open
            
        open = [[x, y] for x in range(19) for y in range(19)
                if board[x][y] == 1 and not self.lonely_spot(board, [x, y])]
        print("just all")
        return open

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
                #print("max:",best,"value:", value)
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
                #print("min:",best,"value:", value)
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
        scores = self.network(board)
        available = [[x, y] for x in range(19) for y in range(19) if scores[x][y] == 16]
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
        print(best_move)
        return best_move
