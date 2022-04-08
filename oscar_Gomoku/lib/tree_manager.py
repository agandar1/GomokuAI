from lib import structure_manager as sm
import threading
import random
import math
import time

SHOW_FULL = False
NORMAL = '\033[88m'
PINK = '\033[95m'
BLUE = '\033[96m'
RED = '\033[91m'
YELLOW = '\033[93m'
END = '\033[0m'

MAX_DEPTH = 20
DEAD_SCORE = -999

# ToDo:
# First Point no Leading Moves, corner. Add a default choice


class TreeManager:
    def __init__(self, root_player, player, move, block_moves, data_manager: sm.StructureManager, base_data, depth=0):
        self.root_player = root_player
        self.player = player
        self.visit_count = 1
        self.opponent = (player + 1) % 2
        self.base = base_data
        self.depth = depth
        self.data = self.get_copy(data_manager, base_data)
        self.data.perform_move(player, self.get_point(move))
        self.move = move

        self.children_status = {"Available": list(self.set_available_moves(block_moves)), "Failed": [], "Worked": []}
        self.children_nodes = {}

        self.search = False
        self.node_successful = False
        self.node_complete = False
        self.node_amount = 1
        self.node_amount_successful = 0
        self.attempts = 0

        #self.node_score = 0
        if self.end_tree_search():
            self.node_complete = True
            self.node_successful = False
            return
        else:
            self.perform_turn()

    def get_path(self, path={}):
        if self.node_successful:
            if self.node_complete:
                path[self.move] = self.children_nodes
            else:
                for child in self.children_nodes:
                    if self.children_nodes[child].get_status():
                        path[child] = {}
                        self.children_nodes[child].get_path(path[child])
        return path

    def end_tree_search(self):
        if self.depth >= MAX_DEPTH and self.player == self.root_player:
            return True
        elif len(self.children_status['Available']) == 0:
            return True
        else:
            return False

    def set_available_moves(self, block_moves):
        if self.player != self.root_player:
            leading = self.data.get_moves()[self.root_player]['Leading']
            adjacent = self.data.get_all_adjacent(block_moves)
            minus = self.data.get_moves()[self.root_player]['Leading_Minus']
            temp = set(leading) & set(minus) & set(adjacent)
            return list(temp)
        else:
            return block_moves

    def choose_move(self):
        options = list(self.children_status['Available'])
        not_option = [child for child in self.children_nodes if self.children_nodes[child].get_status()]
        options = list(set(options) - set(not_option))

        temp_scores = {}
        if len(options) > 1:
            for option in options:
                if option in self.children_nodes:
                    wins = self.children_nodes[option].get_node_score()
                    tries = self.children_nodes[option].get_attempts()
                    temp_scores[option] = (wins/tries) + (math.sqrt(2) * math.sqrt(math.log(self.attempts)/tries))
                else:
                    temp_scores[option] = 2

            temp = {}
            for k, v in temp_scores.items():
                temp.setdefault(v, []).append(k)
            return temp[max(temp.keys())]
        else:
            return options

    def perform_turn(self):
        if self.player == self.root_player:
            self.handle_turn_self()
        else:
            self.handle_turn_opponent()

    def handle_turn_self(self):
        self.attempts += 1
        chosen_move = self.choose_move()
        if len(chosen_move) == 0:
            return
        chosen_move = random.choice(chosen_move)
        if chosen_move in self.children_nodes:
            self.children_nodes[chosen_move].handle_turn_opponent()
        else:
            self.children_nodes[chosen_move] = TreeManager(self.root_player, self.opponent, chosen_move, self.move, self.data, self.base, self.depth+1)

        self.check_child(chosen_move)
        self.reformed_self_update()
        self.update_count()

    def handle_turn_opponent(self):
        self.attempts += 1
        chosen_move = self.choose_move()
        if len(chosen_move) == 0:
            return
        chosen_move = random.choice(chosen_move)

        move_dictionary = self.data.get_moves()[self.root_player]
        end_move = move_dictionary['Leading_Combo']

        if len(end_move) != 0:
            self.children_nodes = end_move
            self.node_successful = True
            self.node_complete = True
        else:
            if chosen_move in self.children_nodes:
                self.children_nodes[chosen_move].handle_turn_self()
            else:
                self.children_nodes[chosen_move] = TreeManager(self.root_player, self.opponent, chosen_move, move_dictionary['Leading'][chosen_move], self.data, self.base, self.depth+1)

            self.check_child(chosen_move)
            self.reformed_self_update()
            self.update_count()

    def check_child(self, child_index):
        status = self.children_nodes[child_index].get_status()
        complete = self.children_nodes[child_index].get_complete()
        if complete and not status:
            self.children_status['Available'].remove(child_index)
            self.children_status['Failed'].append(child_index)

    def reformed_self_update(self):
        if self.player == self.root_player:
            if len(self.children_status['Available']) == 0:
                self.node_complete = True

            if len(self.children_status['Failed']) != 0:
                self.node_complete = True
                self.node_successful = False
            else:
                if len(self.children_status['Available']) != len(self.children_nodes):
                    pass
                else:
                    status = [self.children_nodes[child].get_status() for child in self.children_nodes]
                    if False not in status:
                        self.node_successful = True
        else:
            if len(self.children_status['Available']) == 0:
                self.node_complete = True
                self.node_successful = False
            else:
                status = [self.children_nodes[child].get_status() for child in self.children_nodes]
                if True in status:
                    self.node_successful = True

    def monte(self):
        self.search = True
        passes = 0
        thread = threading.Timer(5, self.stop_monte_carlo_search)
        thread.start()
        time_start = time.time()
        while self.search:
            self.handle_turn_self()
            passes += 1
            if self.node_successful or self.node_complete:
                thread.cancel()
                break
        print("Status   ", "Passes  ", "Time")
        print(self.node_successful, "     " + str(passes), "     ", time.time() - time_start)
        if self.node_successful:
            self.print_tree()

    def stop_monte_carlo_search(self):
        print("Time Passed")
        self.search = False

    def update_count(self):
        counter = 1
        complete = 0

        for child in self.children_nodes:
            child_count = self.children_nodes[child].get_count()
            if self.children_nodes[child].get_status():
                complete += child_count
            counter += child_count

        self.node_amount_successful = complete
        self.node_amount = counter

    def handle_print(self, print_string, final=False):
        color = (YELLOW if len(print_string) != 0 else RED) if final else (BLUE if self.root_player == self.player else NORMAL)
        space = ' ' * 2 * (self.depth + 1) if final else ' ' * 2 * self.depth
        turn = self.depth + 2 if final else self.depth + 1
        print(color + space + 'Turn:', turn, print_string, "Children:", self.node_amount, "Valid Children:", self.node_amount_successful, END)

    def print_tree(self):
        if self.node_successful or SHOW_FULL:
            self.handle_print(self.get_point(self.move))
            if self.node_complete:
                self.handle_print([self.get_point(move) for move in self.children_nodes], True)
            else:
                for child in self.children_nodes:
                    self.children_nodes[child].print_tree()

    @staticmethod
    def get_point(coord):
        return [coord % 19, int(coord / 19)]

    @staticmethod
    def get_copy(structure, base_data):
        new_struct = sm.StructureManager(19)
        new_struct.set_up_data(structure.extract_data_np())
        return new_struct

    def get_complete(self):
        return self.node_complete

    def get_status(self):
        return self.node_successful

    def get_count(self):
        return self.node_amount

    def get_node_score(self):
        return self.node_amount_successful

    def get_attempts(self):
        return self.attempts
