import numpy as np
from lib import structure_creator as sc
import math
import copy
import time
import random

POINT_MAX = 65535
MULTIPLIER = 2
TYPE_ADJACENT = [19, 1, 20, 18]
TYPE_VALUE = {19: 0, 1: 1, 20: 2, 18: 3}
CHAIN_FOUR = math.pow(MULTIPLIER, 4)
CHAIN_THREE = math.pow(MULTIPLIER, 3)

STRUCTURE_DATA = sc.StructureCreator(19, 5, [[x, y] for y in range(0, 19) for x in range(0, 19)], 65535)
STATE_TABLE_MONO = STRUCTURE_DATA.return_state()
STATE_TABLE_POINTS = STRUCTURE_DATA.return_state_point()
STATE_TABLE_POINT_TYPE_LINK = STRUCTURE_DATA.return_type_association()
STATE_TABLE_POW_VALUE = STRUCTURE_DATA.return_pow_association()
POINT_MONO_ASSOCIATION = STRUCTURE_DATA.return_mono_index()
POINT_CLOSE_UPDATE = STRUCTURE_DATA.return_close_updates()

# Next up Tables For Leading/LeadingMinus


class StructureManager:
    def __init__(self, board, tree_node=False):
        self.board_size = board
        self.Monomials = None
        self.Points = None
        self.point_active = None
        self.leading = None
        self.leading_minus = None

        if tree_node:
            pass
        else:
            self.reset_variables()

        self.all_information = None
        self.complete = False
        self.winning_mono = None

    def reset_variables(self):
        # Initialize all variables to default values
        self.Monomials = [STRUCTURE_DATA.return_mono(), STRUCTURE_DATA.return_mono()]
        self.Points = [STRUCTURE_DATA.return_points(), STRUCTURE_DATA.return_points()]
        self.point_active = np.ones((self.board_size * self.board_size, 1), dtype=bool)
        self.leading = [[[] for _ in range(4)] for _ in range(2)]
        self.leading_minus = [[[] for _ in range(4)] for _ in range(2)]
        self.winning_mono = None
        self.complete = False

    def perform_move(self, player, point):
        self.update_structure(player, self.get_opponent(player), point, self.Monomials, self.Points, self.point_active)
        return self.complete

    def remove_leading(self, point_index):
        # Remove all information of point_index from leading containers
        for player_type in range(2):
            for mono_type in range(4):
                if point_index in self.leading[player_type][mono_type]:
                    self.leading[player_type][mono_type].remove(point_index)
                if point_index in self.leading_minus[player_type][mono_type]:
                    self.leading_minus[player_type][mono_type].remove(point_index)

    def update_structure(self, initiator, follower, point, mono_structure, point_structure, point_active_list):
        # Update Structures
        # Set point to false, update all associated monomials, updating all points for player and opponent, remove all information of used point from leading containers
        point_index = self.get_coord(point)
        point_active_list[point_index] = False

        self.update_combo_v2_block(point_index, mono_structure[follower], point_structure[follower], follower)
        points_to_update_bot, points_to_update_op = self.update_monos(initiator, follower, point_index, mono_structure)
        self.update_points(point_index, points_to_update_bot, point_structure[initiator], 'My_Type', initiator)
        self.update_points(point_index, points_to_update_op, point_structure[follower], 'Next_Type', follower)

        self.remove_leading(point_index)

    def update_leading(self, player_type, point_index, mono_type, current_state_index, previous_state_index):
        # Update leading containers, Keep track of which points are leading/leading_minus/non_leading
        # Used in order to minimize time spent finding these points from scratch each turn
        if not self.point_active[point_index]:
            return
        if current_state_index == 65535:
            previous_state = STATE_TABLE_POINTS[previous_state_index]['Combo_Score']
            if previous_state == 0:
                self.leading[player_type][mono_type].remove(point_index)
            elif previous_state == 1:
                self.leading_minus[player_type][mono_type].remove(point_index)
        else:
            current_state, previous_state = STATE_TABLE_POINTS[current_state_index]['Combo_Score'], STATE_TABLE_POINTS[previous_state_index]['Combo_Score']

            if current_state == previous_state:
                pass
            elif current_state == 0:
                self.leading[player_type][mono_type].append(point_index)
                if previous_state == 1:
                    self.leading_minus[player_type][mono_type].remove(point_index)
            elif current_state == 1:
                self.leading_minus[player_type][mono_type].append(point_index)
                if previous_state == 0:
                    self.leading[player_type][mono_type].remove(point_index)
            elif previous_state == 1:
                self.leading_minus[player_type][mono_type].remove(point_index)
            elif previous_state == 0:
                self.leading[player_type][mono_type].remove(point_index)

    def update_points(self, point_index, point_list, point_structure, next_type, player_type):
        # Update the state of all points associated with most recently chosen point
        for sub_point_index in point_list:
            point_row = point_structure[sub_point_index]
            point_type = STATE_TABLE_POINT_TYPE_LINK[point_index][sub_point_index]
            point_pow_type = STATE_TABLE_POW_VALUE[sub_point_index][point_index]
            ps = point_row['State_ID'][point_type]
            point_row['State_ID'][point_type] = STATE_TABLE_POINTS[point_row['State_ID'][point_type]][next_type][point_pow_type]
            cs = point_row['State_ID'][point_type]

            self.update_leading(player_type, sub_point_index, point_type, cs, ps)

    def update_monos(self, influence, follower, point_index, mono_structure):
        # Update the state of all monos
        my_points, op_points = [], []

        for monomial_index in POINT_MONO_ASSOCIATION[point_index]:
            my_mono = mono_structure[influence][monomial_index]
            op_mono = mono_structure[follower][monomial_index]

            if my_mono['Active']:
                my_points.extend(my_mono['Mono'].tolist())
                updated_index = int(my_mono['Index'] + (math.pow(2, 4 - np.where(my_mono['Mono'] == point_index)[0][0]) * 4))
                my_mono['Index'] = updated_index
                # If index is 124, 125, 126 or 127 a player has one
                if updated_index >= 124:
                    self.complete = True
                    self.winning_mono = self.Monomials[influence][monomial_index]['Mono']
            if op_mono['Active']:
                op_points.extend(op_mono['Mono'].tolist())
                op_mono['Active'] = False

        my_points, op_points = set(my_points), set(op_points)
        inactive = set(np.where(self.point_active == False)[0])
        my_points = my_points - inactive
        op_points = op_points - inactive

        return my_points, op_points

    def update_combo_v2_block(self, point_index, mono_structure, point_structure, player_type):
        # Update the state of all points on edge of currently taken point
        # Ex. Point [0, 0] taken leads to [5, 0], [5, 5], and [0, 5] state changing due to their monomials now being closed on 1 or more sides
        for open_side in range(2):
            for mono_index in POINT_CLOSE_UPDATE[open_side][point_index]:
                mono_row = mono_structure[mono_index]
                if mono_row['Active']:
                    mono_row['Index'] += (open_side + 1)
                    point_structure[mono_row['Mono'][4 if open_side == 0 else 0]]['State_ID'][mono_row['Type']] += 1
                    #Point State[Monomial First or last][State][mono_row Type. . .
                    state = point_structure[mono_row['Mono'][4 if open_side == 0 else 0]]['State_ID'][mono_row['Type']]

                    if np.abs(int(mono_row['Mono'][0]) - int(mono_row['Mono'][1])) in TYPE_VALUE:
                        point_type = TYPE_VALUE[np.abs(int(mono_row['Mono'][0]) - int(mono_row['Mono'][1]))]
                        self.update_leading(player_type, mono_row['Mono'][4 if open_side == 0 else 0], point_type, state, state-1)

    def get_coord(self, point) -> int:
        # Convert point format to coordinate Ex. [2, 1] -> 21
        return point[0] + (point[1] * self.board_size)

    def get_point(self, coord) -> [int, int]:
        # Convert board coordinate to point Ex. 100 -> [5, 5]
        return [coord % self.board_size, int(coord / self.board_size)]

    @staticmethod
    def get_opponent(influence) -> int:
        return (influence + 1) % 2

    def check_won(self) -> bool:
        return self.complete

    def return_winning_mono(self) -> [int, int, int, int, int]:
        return self.winning_mono

    def extract_data(self):
        return [copy.deepcopy(self.Monomials), copy.deepcopy(self.Points), copy.deepcopy(self.point_active), copy.deepcopy(self.leading), copy.deepcopy(self.leading_minus)]

    def extract_data_np(self):
        return [np.copy(self.Monomials), np.copy(self.Points), np.copy(self.point_active), copy.deepcopy(self.leading), copy.deepcopy(self.leading_minus)]

    def set_up_data(self, x):
        self.Monomials = x[0]
        self.Points = x[1]
        self.point_active = x[2]
        self.leading = x[3]
        self.leading_minus = x[4]

        self.winning_mono = None

    def get_monos(self):
        return self.Monomials

    def get_point_active(self):
        return self.point_active

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    def get_layer_one(self, influence):
        mono_index = np.where((STATE_TABLE_MONO[self.Monomials[influence]['Index']]['Value'] == CHAIN_FOUR) & self.Monomials[influence]['Active'])[0]
        return [mono['Mono'][np.where(STATE_TABLE_MONO[mono['Index']]['Taken'] == False)[0][0]] for mono in self.Monomials[influence][mono_index]]

    def get_layer_two(self, influence, crucial):
        mono_index = np.where((STATE_TABLE_MONO[self.Monomials[influence]['Index']]['Value'] == CHAIN_THREE) & self.Monomials[influence]['Active'])[0]
        return list(set([point_index for mono in self.Monomials[influence][mono_index] for point_index in self.get_counter_points(mono, STATE_TABLE_MONO[mono['Index']], crucial)]))

    def get_threes(self, influence):
        mono_index = np.where((STATE_TABLE_MONO[self.Monomials[influence]['Index']]['Value'] == CHAIN_THREE) & self.Monomials[influence]['Active'])[0]
        return [point_index for mono in self.Monomials[influence][mono_index] for point_index in self.get_remaining(mono, STATE_TABLE_MONO[mono['Index']]['Taken'])]

    def get_counter_points(self, mono, mono_state, crucial=False):
        return_list = self.get_remaining(mono, mono_state['Taken'])
        if mono_state['Distance'] == 5:
            return []
        elif mono_state['Open'] == 2:
            if not mono_state['Taken'][4]:
                return [return_list[0]] if crucial else return_list[0:1]
        elif mono_state['Open'] == 1:
            if not mono_state['Taken'][0]:
                return [return_list[1]] if crucial else return_list[1:2]
        else:
            if mono_state['Distance'] == 4:
                if mono_state['Taken'][0]:
                    return [return_list[0]] if crucial else return_list
                else:
                    return [return_list[1]] if crucial else return_list
            elif not mono_state['Taken'][0] and not mono_state['Taken'][4]:
                return return_list
        return []

    @staticmethod
    def get_remaining(mono, taken):
        return mono['Mono'][np.invert(taken)]

    def get_leading(self, influence, storage_dict, association_dict, leading_strut):
        for mono_type in range(4):
            for point_index in leading_strut[mono_type]:
                self.dict_add(association_dict, point_index, [mono_type])
                self.dict_add(storage_dict, point_index, [self.adjacent_to_index(point_index, adjacent_value, mono_type) for adjacent_value in STATE_TABLE_POINTS[self.Points[influence][point_index]['State_ID'][mono_type]]['Leading_Reaction']])

    @staticmethod
    def dict_add(dictionary, point_index, information):
        if point_index not in dictionary:
            dictionary[point_index] = []
        dictionary[point_index].extend(information)

    def get_moves(self):
        self.pull_information()
        return self.all_information

    def pull_information(self):
        # ToDo Minor Speed Improvement:
        # Creation of points and follow up calculated each turn
        # Add/Subtract only new information. Will require another copy.deepcopy to transfer when performing tree search
        # Convert leading moves and leading minus data structure to np table. Allows for copy.deepcopy function to be removed

        base_information = [{point_type: {} for point_type in ['Leading', 'Leading_Minus']} for _ in range(2)]
        mono_association = [{point_type: {} for point_type in ['Leading', 'Leading_Minus']} for _ in range(2)]
        for player_type in range(2):
            self.get_leading(player_type, base_information[player_type]['Leading'], mono_association[player_type]['Leading'], self.leading[player_type])
            self.get_leading(player_type, base_information[player_type]['Leading_Minus'], mono_association[player_type]['Leading_Minus'], self.leading_minus[player_type])

        leading_parser = [None, None]
        leading_parser[0] = self.lead_parser(base_information[0]['Leading'], base_information[1]['Leading'])
        leading_parser[1] = self.lead_parser(base_information[1]['Leading'], base_information[0]['Leading'])

        self.all_information = [{point_type: {} for point_type in ['Leading', 'Leading_Minus', "CC", "CM"]} for _ in range(2)]

        for player_type in range(2):
            self.all_information[player_type]["CC"] = base_information[player_type]['Leading']
            self.all_information[player_type]["CM"] = base_information[player_type]['Leading_Minus']
            self.all_information[player_type]['Leading'] = {leading_move: base_information[player_type]['Leading'][leading_move] for leading_move in leading_parser[player_type]}
            self.all_information[player_type]['Leading_Minus'] = base_information[player_type]['Leading_Minus']

            self.all_information[player_type]['??'] = []
            self.all_information[player_type]['Combo'] = []
            self.all_information[player_type]['Combo_Minus'] = []
            self.all_information[player_type]["Leading_Combo"] = []
            self.all_information[player_type]['LC_Reverse'] = {}
            for leading_move in base_information[player_type]['Leading']:
                if len(mono_association[player_type]['Leading'][leading_move]) >= 2:
                    self.all_information[player_type]['Combo'].append(leading_move)
                elif leading_move in self.all_information[player_type]['Leading_Minus']:
                    self.all_information[player_type]['Combo_Minus'].extend(base_information[player_type]['Leading_Minus'][leading_move])
                    for move in base_information[player_type]['Leading_Minus'][leading_move]:
                        # Testing Further
                        for temp in self.all_information[player_type]['Leading_Minus']:
                            if move in self.all_information[player_type]['Leading_Minus'][temp]:
                                if len(set(mono_association[player_type]['Leading_Minus'][leading_move]) - set(mono_association[player_type]['Leading_Minus'][temp])) != 0:
                                #print(temp, mono_association[player_type]['Leading_Minus'][temp])
                                    self.all_information[player_type]["??"].append(temp)
                            #print(temp, self.all_information[player_type]['Leading_Minus'][temp])
                        # Make sure leading_minus move is also a leading move of different mono type
                        if move in self.all_information[player_type]['Leading']:
                            # Make sure leading_minus and leading_move are not of same type
                            if len(set(mono_association[player_type]['Leading'][move]) - set(mono_association[player_type]['Leading_Minus'][leading_move])) != 0:
                                # Make sure block points don't intersect for combo and leading move
                                if len(set(base_information[player_type]['Leading'][leading_move]) & set(base_information[player_type]['Leading'][move])) == 0:
                                    self.all_information[player_type]["Leading_Combo"].append(move)
                                    if move in self.all_information[player_type]['LC_Reverse']:
                                        self.all_information[player_type]['LC_Reverse'][move].append(leading_move)
                                    else:
                                        self.all_information[player_type]['LC_Reverse'][move] = [leading_move]
            self.all_information[player_type]['Combo_Minus'] = set(self.all_information[player_type]['Combo_Minus'])

    @staticmethod
    def lead_parser(my_leading, op_leading):
        remove_set = []
        for lead in my_leading:
            for lead_reaction in my_leading[lead]:
                if lead_reaction in op_leading:
                    remove_set.append(lead)
                    break
        return set(my_leading) - set(remove_set)

    @staticmethod
    def get_all_adjacent(point_index):
        return list(STATE_TABLE_POW_VALUE[point_index])

    @staticmethod
    def adjacent_to_index(point_index, adjacent_value, mono_type):
        return point_index + (TYPE_ADJACENT[mono_type] * adjacent_value)

    @staticmethod
    def dict_add_v2(dictionary, point_index, type_index, information):
        if point_index not in dictionary:
            dictionary[point_index] = {}
        dictionary[point_index][type_index] = information

    def debug_test(self):
        return self.leading_minus[0]

    def get_all_active(self):
        return np.where(self.point_active)[0]

    def print_taken(self):
        return np.where(self.point_active == False)[0]

    def get_highest_score(self, influence, points):
        point_dict = {point: 0 for point in points}

        for point in points:
            score = 0
            for mono_type in range(4):
                id = self.Points[influence][point]['State_ID'][mono_type]
                if id != 65535:
                    score += STATE_TABLE_POINTS[id]['Value']
            point_dict[point] = score

        return random.choice(points)

    def get_all_available_scores(self, player_type=0):
        score_dict = {point_index: 0 for point_index in range(len(self.point_active)) if self.point_active[point_index]}
        for point_index in score_dict:
            score_dict[point_index] = np.sum([STATE_TABLE_POINTS[index]['Value'] for index in self.Points[player_type][point_index]['State_ID'] if index != 65535])
        return score_dict

    def get_score_normal(self, points):
        return {point_index: np.sum([STATE_TABLE_POINTS[state_index]['Value'] - (STATE_TABLE_POINTS[state_index]['Live_Monos'][1] - STATE_TABLE_POINTS[state_index]['Live_Monos'][0]) for state_index in self.Points[0][point_index]['State_ID'] if state_index != POINT_MAX]) + np.sum([STATE_TABLE_POINTS[state_index]['Value'] - (STATE_TABLE_POINTS[state_index]['Live_Monos'][1] - STATE_TABLE_POINTS[state_index]['Live_Monos'][0]) for state_index in self.Points[1][point_index]['State_ID'] if state_index != POINT_MAX])for point_index in points}

    def get_score_characteristics(self, point_list):
        # Make sure to include base score. . .
        values = {"My_Leading": 10, "My_Minus": 5, "Op_Leading": 10, "Op_Minus": 5}
