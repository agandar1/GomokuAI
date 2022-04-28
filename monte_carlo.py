from random import choice
from time import time
from math import log, sqrt
from simulation_bot import SimBot

class MonteCarlo:
    def __init__(self):
        # Parameters
        self.board = self.new_board()
        self.turn = 2
        self.time_limit = 30
        self.max_moves = 50
        self.explore = 2
        self.wins = {}
        self.moves = {}
        self.simulator = SimBot(self.board)

    def search_tree(self):
        """main mcts function, builds game tree and updates values for each state"""
        moves, wins = self.moves, self.wins
        visited = set()
        board = self.board

        expand = True
        for i in range(self.max_moves):
            # Selection Step & Simulation Step
            available = self.possible_moves(board)
            next_states = [(move, self.next_state(board, move)) for move in available]
            self.simulator.set_board(board)
            if self.turn == 0:
                self.simulator.toggle_turn()

            # Pick a move to simulate using UCB1 if we have info on all the next states
            if all(moves.get((self.turn, board)) for move, board in next_states):
                log_sum = log(sum(moves[(self.turn, board)] for move, board in next_states))
                value, move, board = max(
                    ((wins[(self.turn, board)] / moves[(self.turn, board)])
                     + self.explore * sqrt(log_sum / moves[(self.turn, board)]),
                     move,
                     board) for move, board in next_states)
                print("ucb1 move:", move)
            # or Pick a move using the simulator
            else: 
                move = self.simulator.turn()
                board = self.next_state(board, move)
                #print("simulator move:", move)

            visited.add((self.turn, board))

            # Expansion Step
            # if we find a new state, add it and set values to 0
            if expand and (self.turn, board) not in moves: 
                expand = False
                moves[(self.turn, board)] = 0
                wins[(self.turn, board)] = 0            
                
            winner = self.winner(board)
            if winner != 1:
                print("winner:", winner)
                break

            # flip the turn
            self.turn = 0 if self.turn == 2 else 2

        # Backpropagation Step
        # update values for the nodes we visited
        for player, board in visited:
            if (player, board) not in moves:
                continue
            moves[(player, board)] += 1
            if player == winner:
                print("incrementing win for player:", player)
                wins[(player, board)] += 1
        
    def choose_best_move(self):
        """run the search and pick the best move for current player"""
        board = self.board
        self.turn = 2
        available = self.possible_moves(board)
        start = time()
        while time() < start + self.time_limit:
            self.search_tree()

        next_states = [(move, self.next_state(board, move)) for move in available]
        # win_percent, move = max((self.wins.get((self.turn, board), 0) /
        #                          self.moves.get((self.turn, board), 1),
        #                          move)
        #                         for move, board in next_states)

        options = []
        found_nonzero = False
        print("wins dict:",self.wins)
        print("moves dict:",self.moves)
        for move, board in next_states:
            win = self.wins.get((2, board), "did not find in wins")
            mov = self.moves.get((2, board), "did not find in visits")
            #win_percent = win/mov
            win_percent = 0.0
            fond_nonzero = True if win_percent != 0.0 else False
            print(move, "-", win, "-", mov, "-", win_percent)
            options.append((win_percent, mov, move))
        if fond_nonzero:
            move = max(options, key=lambda x: x[0])
            print("using wins:", move[0])
        else:
            move = max(options, key=lambda x: x[1])
            print("using visits:", move[1])
            

        print("sending move:", move[2])
        return move[2]

    def apply_move(self, move, player):
        self.turn = player
        self.board = self.next_state(self.board, move)
        self.turn = 0 if self.turn == 2 else 2
        
    def new_board(self):
        """return a clean board"""
        return ((1,) * 19,) * 19

    def next_state(self, board, move):
        """update board with move and toggle the turn"""
        board = list(map(list, board))
        board[move[0]][move[1]] = self.turn
        return tuple(map(tuple, board))

    def possible_moves(self, board):
        """return all legal moves on the current board"""
        return [(x, y) for x in range(19) for y in range(19)
                if board[x][y] == 1]

    def reset_tree(self):
        self.board = self.new_board()
        self.turn = 2
        self.wins = {}
        self.moves = {}
        self.simulator.new_board()

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
    
