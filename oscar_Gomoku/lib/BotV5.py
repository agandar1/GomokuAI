from lib import structure_manager as sm
from lib import structure_creator as sc
from lib import tree_manager as tree
import numpy as np
import random
import copy
import math
import time
import operator

POINT_MAX = 65535
MULTIPLIER = 2
CHAIN_FOUR = math.pow(MULTIPLIER, 4)
CHAIN_THREE = math.pow(MULTIPLIER, 3)
CHAIN_TWO = math.pow(MULTIPLIER, 2)
TYPE_CHECK = [[1, 0], [0, 1], [1, 1], [1, -1]]
TYPE_ADJACENT = [19, 1, 20, 18]
MAX_DEPTH = 5
SHOW_FULL = False
RANDOM = False


# ToDo:
# Check Layer 2, False Open 3 Found XO_OO_X
# Go More In Depth Toward Leading Combos, Combos Block Points Leading To Blocked Combo Made By Opponent
# Multiple Move Options Take Into Account Chunks, Such As Example Combo + (Leading, Combo-1)


class ComputerPlayer:
    def __init__(self, board, chain):
        self.chain, self.board, self.points = chain, board, self.generate_points(board)
        self.structure_data = sc.StructureCreator(board, chain, self.points, POINT_MAX)
        self.data_manager = sm.StructureManager(board)
        self.temp_tracker = 0
        self.start_time = time.time()

        self.temp_p_path = []
        self.total_nodes = 0
        self.data_manager.get_all_available_scores()
        self.player_type = 0

    def set_player(self, player):
        self.player_type = player

    def test_changes(self):
        self.calc_move()
        return
        info = self.data_manager.get_moves()
        leading = info[0]["Leading"]
        chosen = 163 #139, 163

        tree_node = tree.TreeManager(0, 0, chosen, leading[chosen], self.data_manager, self.structure_data)
        tree_node.monte()
        path = tree_node.get_path()
        for x in path:
            print(self.get_point(x), [self.get_point(y) for y in path[x]])

    def get_layer_moves(self, influence, layer, display):
        self.data_manager.pull_information()
        if layer == 0:
            moves = self.data_manager.get_layer_one(influence)
            return moves
        elif layer == 1:
            moves = self.data_manager.get_layer_two(influence, display is 1)
            return moves
        else:
            info_dict = self.data_manager.get_moves()[influence]

            if layer == 2:
                return list(info_dict['Combo'])
                if display == 0:
                    return list(set(parse_dict['C']) | set(info_dict['CT1']))
                elif display == 1:
                    return list(info_dict['CT1'])
                else:
                    return parse_dict['C']
                pass
            elif layer == 3:
                return list(info_dict['Leading_Combo'])
            elif layer == 4:
                return list(info_dict['Leading'])
            elif layer == 5:
                return list(info_dict['Combo_Minus'])
            elif layer == 6:
                return list(info_dict['Leading_Minus'])
            elif layer == 7:
                return list(info_dict['??'])
            else:
                input("Invalid Input??")

    def reset_variables(self):
        self.data_manager.reset_variables()
        self.temp_p_path = []

    def return_win(self):
        return [self.get_point(x) for x in self.data_manager.return_winning_mono()]

    def calc_move(self):
        move_options, move_type = self.tier_one_calculator(0, 1, self.data_manager)
        print("!", move_type)
        move_chosen = self.choose_move(move_options)
        print("Move", move_type, move_chosen, [self.get_point(point_index) for point_index in move_options])

        return move_chosen

    # ToDo: Reintroduce Parameters, Base On Points, Original, Harsh, Bot, Op, Mix
    def choose_move(self, choice_list):
        if len(choice_list) == 1:
            print(choice_list)
            return self.get_point(choice_list[0])
        else:
            choice_list = set(choice_list)
            my_info_dict = self.data_manager.get_moves()[0]
            op_info_dict = self.data_manager.get_moves()[1]

            temp_list = choice_list & set(op_info_dict['Leading'])
            if len(temp_list) != 0:
                choice_list = temp_list

            temp_list = choice_list & set(my_info_dict['Leading'])
            if len(temp_list) != 0:
                choice_list = temp_list

            temp_list = choice_list & set(op_info_dict['Leading_Minus'])
            if len(temp_list) != 0:
                choice_list = temp_list

            temp_list = choice_list & set(my_info_dict['Leading_Minus'])
            if len(temp_list) != 0:
                choice_list = temp_list

            if len(choice_list) == 1:
                return self.get_point(list(choice_list)[0])
            else:
                choice_dict = self.data_manager.get_score_normal(choice_list)
            temp = {}
            for k, v in choice_dict.items():
                temp.setdefault(v, []).append(k)
            return self.get_point(random.choice(temp[max(temp.keys())]))

    @staticmethod
    def sort_points(point_struct, point_struct_b, point, harsh=False):
        if harsh:
            return_list_a = [z for _, z in sorted(zip(point_struct[point]['Value']-np.sum(point_struct[point]['Mono_Left']), point))]
            return_list_b = [z for _, z in sorted(zip(point_struct_b[point]['Value'] - np.sum(point_struct_b[point]['Mono_Left']), point))]
        else:
            return_list_a = [z for _, z in sorted(zip(point_struct[point]['Value'], point))]
            return_list_b = [z for _, z in sorted(zip(point_struct_b[point]['Value'], point))]
        return_list_a.reverse()
        return_list_b.reverse()

        if point_struct[return_list_a[0]]['Value'] >= point_struct_b[return_list_b[0]]['Value']:
            return_list = return_list_a
        else:
            return_list = return_list_b
        max_value = point_struct[return_list[0]]['Value']
        mod_value = max_value - np.sum(point_struct[return_list[0]]['Mono_Left'])
        if mod_value == 0:
            return False

        max_points = [point for point in return_list if point_struct[point]['Value'] == max_value]

        return max_points

    @staticmethod
    def check_priority_one(influence, follower, data_structure: sm.StructureManager):
        for player in [influence, follower]:
            player_four = data_structure.get_layer_one(player)
            if len(player_four) != 0:
                return player_four, "Op Chain 4" if player else "Bot Chain 4", True

        return None, None, False

    @staticmethod
    def check_priority_two(influence, follower, move_data, data_structure: sm.StructureManager):
        for player in [influence, follower]:
            closed_threes = data_structure.get_threes(player)
            open_three = data_structure.get_layer_two(player, player == 0)
            closed_combos = list(set(closed_threes) & set(move_data[player]['Combo']))
            if len(open_three) != 0:
                return open_three, "Op Open 3" if player else "Bot Open 3", True
            elif len(closed_combos) != 0:
                if player:
                    temp_list = [point_index for combo_point in closed_combos for point_index in move_data[player]['CC'][combo_point]]
                    temp_list.extend(closed_combos)
                    return list(set(temp_list)), "Op Closed Combo", True
                else:
                    return closed_combos, "Bot Closed Combo", True
        return None, None, False

    def check_priority_three(self, influence, follower, move_data):
        for player in [influence, follower]:
            if len(move_data[player]['Combo']) != 0:
                if player:
                    temp_dict = {}
                    for combo_point in move_data[player]['Combo']:
                        temp_dict[combo_point] = [combo_point]
                        for move in move_data[player]['CC'][combo_point]:
                            temp_dict[combo_point].append(move)
                    if len(temp_dict) == 0:
                        pass
                    elif len(temp_dict) == 1:
                        return temp_dict[move_data[player]['Combo'][0]], "Op Single Combo", True
                    else:

                        temp = {point_index: 0 for point_index in set([item for key in temp_dict for item in temp_dict[key]])}
                        for key in temp_dict:
                            for value in temp:
                                if value in temp_dict[key]:
                                    temp[value] += 1
                        t = {}
                        for k, v in temp.items():
                            t.setdefault(v, []).append(k)
                        return t[max(t.keys())], "Op Multi Combo", True
                else:
                    return list(move_data[player]['Combo']),  "Bot Combo", True
            elif len(move_data[player]['Leading_Combo']) != 0:
                if player == 0:
                    return list(move_data[player]['Leading_Combo']), "Bot Leading Combo", True
                else:
                    leading_combos = move_data[player]['Leading_Combo']

                    temp_dict = {}
                    for leading_combo in leading_combos:
                        temp_dict[leading_combo] = [leading_combo]
                        temp_dict[leading_combo].extend(move_data[player]['Leading'][leading_combo])
                        for m in move_data[player]["LC_Reverse"][leading_combo]:
                            temp_dict[leading_combo].append(m)
                            temp_dict[leading_combo].extend(move_data[player]['CC'][m])
                        # ToDo: Issue Picking Up Moves To Prevent C-1 (L-1) Lead Block Points. Multiple L-1 Options Contained
                    if len(temp_dict) == 0:
                        pass
                    elif len(temp_dict) == 1:
                        return temp_dict[move_data[player]['Leading_Combo'][0]], "Op Leading Combo", True
                    else:
                        temp = {point_index: 0 for point_index in set([item for key in temp_dict for item in temp_dict[key]])}
                        for key in temp_dict:
                            for value in temp:
                                if value in temp_dict[key]:
                                    temp[value] += 1
                        t = {}
                        for k, v in temp.items():
                            t.setdefault(v, []).append(k)
                        print(t)
                        return t[max(t.keys())], "Op Leading Multi Combo", True
                    # return list(move_data[player]['Leading_Combo']), "Op Leading Combo Multi", True
            else:
                if len(self.temp_p_path) != 0:
                    option = random.choice(list(self.temp_p_path))
                    self.temp_p_path = self.temp_p_path[option]
                    return [option], "Following Path", True
                for move in move_data[player]['Leading']:
                    root = tree.TreeManager(player, player, move, move_data[player]['Leading'][move], self.data_manager, self.structure_data)
                    root.monte()
                    if root.get_status():
                        if player == 0:
                            self.temp_p_path = root.get_path()
                        return [move], "Block Tree" if player else "Tree Path", True
        return None, None, False

    def check_priority_four(self, influence, follower, move_data):
        l = [influence, follower] if self.player_type == 0 else [follower, influence]

        if self.player_type == 1:
            for player in l:
                moves = move_data[player]['??']
                if len(moves) != 0:
                    return list(moves), "??-"
        else:
            for player in [0]:
                moves = move_data[player]['??']
                if len(moves) != 0:
                    return list(moves), "??-"
        #for player in l:
        #    moves = move_data[player]['Leading']
        #    if len(moves) != 0:
        #        return list(moves), "??-"
        for player in l:
            moves = move_data[player]['Leading_Minus']
            temp = {move: len(moves[move]) for move in moves}
            #print(temp)
            #print(t)
            #print(move_data[player]['Leading_Minus'])
            if len(moves) != 0:
                t = self.get_max_reverse(temp)
                return t, "-"
        return self.data_manager.get_all_active(), "Corner"

    def tier_one_calculator(self, influence, follower, data_structure: sm.StructureManager):
        info = data_structure.get_moves()

        # Priority One: Fours
        point, message, result = self.check_priority_one(influence, follower, data_structure)
        if result:
            return point, message

        # Priority Two: Threes
        point, message, result = self.check_priority_two(influence, follower, info, data_structure)
        if result:
            return point, message

        # Priority Three: Leading
        point, message, result = self.check_priority_three(influence, follower, info)
        if result:
            return point, message

        # Priority Four: Basic
        point, message = self.check_priority_four(influence, follower, info)
        return point, message

    def opening_move(self):
        x = int(self.board / 2)
        possible_range = range(x - self.chain + 2, x + self.chain - 2)
        return [random.choice(possible_range), random.choice(possible_range)]

    def my_move(self, move):
        self.data_manager.perform_move(0, move)
        return self.check_won()

    def op_move(self, move):
        self.data_manager.perform_move(1, move)

        if len(self.temp_p_path) != 0 and self.get_coord(move) in self.temp_p_path:
            self.temp_p_path = self.temp_p_path[self.get_coord(move)]
        else:
            self.temp_p_path = []
        return self.check_won()

    def get_coord(self, point):
        return point[0] + (point[1] * self.board)

    def get_point(self, coord):
        return [coord % self.board, int(coord / self.board)]

    def get_point_list(self, mono):
        return [self.get_point(point_index) for point_index in mono['Mono']]

    def check_won(self):
        return self.data_manager.check_won()

    @staticmethod
    def generate_points(board_length):
        return [[x, y] for y in range(board_length) for x in range(board_length)]

    @staticmethod
    def get_opposite(influence):
        return (influence+1) % 2

    @staticmethod
    def get_count_dict(item_dict):
        temp = {point_index: 0 for point_index in set([item for key in item_dict for item in item_dict[key]])}

        for key in item_dict:
            for value in temp:
                if value in item_dict[key]:
                    temp[value] += 1
        return temp
    # Insert
    @staticmethod
    def get_max_reverse(item_dict):
        return_dict = {}
        for k, v in item_dict.items():
            return_dict.setdefault(v, []).append(k)
        return return_dict[max(return_dict.keys())]
