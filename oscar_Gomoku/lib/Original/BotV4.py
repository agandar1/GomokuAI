from lib import Mono_Temp as Mono
import numpy as np
import json
import random
import copy
import math
import threading
import time

POINT_MAX = 65535
MULTIPLIER = 2
CHAIN_FOUR = math.pow(MULTIPLIER, 4)
TYPE_CHECK = [[1, 0], [0, 1], [1, 1], [1, -1]]
RANDOM = False
DEPTH = 5
DIVE = False


class ComputerPlayer:
    def __init__(self, board, chain, points):
        self.boardMonomials = Mono.Monomials(board, chain)
        self.chain, self.board, self.points = chain, board, points

        self.amount_monomials = int((((self.board - (self.chain - 1)) * self.board) + math.pow((self.board - (self.chain - 1)), 2)) * 2)
        self.amount_points = self.board * self.board

        self.my_mono = self.create_mono_structure()
        self.my_mono_index = self.boardMonomials.get_index_list()
        self.monomials = self.boardMonomials.get_monomials()
        self.my_point = self.create_point_structure()
        self.point_active = np.ones((len(self.my_point), 1), dtype=bool)
        self.my_combo = self.create_combo_structure()
        self.winning_mono = None
        self.Monomials = None
        self.Points = None
        self.Combos = None
        self.turn_count = None
        self.thread_count = None

        self.close_update = self.boardMonomials.get_close_update()
        self.updated_monomials = self.boardMonomials.get_monomials_index_version()
        self.reset_variables()
        self.thread_outcome = None
        self.thread_count = 0
        self.all_threads = []
        self.winning_path = []

        self.dive_storage = {}
        self.moves_to_take = []
        np.seterr(all='raise')

        self.w_path, self.l_path, self.b_path = [], [], []
        self.last_move = None
        #print(self.Points[0])

    def reset_variables(self):
        """Set All Structures To Default Value"""
        self.Monomials = [copy.deepcopy(self.my_mono), copy.deepcopy(self.my_mono)]
        self.Points = [copy.deepcopy(self.my_point), copy.deepcopy(self.my_point)]
        self.Combos = [copy.deepcopy(self.my_combo), copy.deepcopy(self.my_combo)]
        self.point_active = np.ones((len(self.my_point), 1), dtype=bool)
        self.turn_count = 0
        self.thread_count = 0

    def load_game(self, moves, player):
        self.reset_variables()
        for x in moves:
            if player == 0:
                self.op_move(x)
            else:
                self.my_move(x)
            player = (player + 1) % 2

    def create_mono_structure(self):
        """Monomial Structure:
        Column 1: Bool Value, Indicates If Monomial Is Active On The Board. If Set To False Atleast 1 Point Needed Was Taken By Opponent
        Column 2: Array, All Points Found In Monomial Ex: Monomial 0 = [[0, 0], [0, 1], [0, 2], [0, 3], [0, 4]]
        Column 3: Int, Value Of Monomial Based On Points Taken. Base Value 1 Once Point Taken Value = 2^(# Points Taken)
        Column 4: Int, Type Of Monomial. Will Either Be 0, 1, 2, or 3. More Information In Monomials.py
        Column 5: Array, Indicates Which Points Are Taken. Ex: [True, True, False, False, False] Indicates First 2 Points In Monomial Are Taken
        Column 6: Int, Distance Between Points. Ex: O__O_ Would Be Distance of 4
        Column 7: Bool, Indicates If Both Sides Of Monomial Are Open. Ex _[O_O_O]_ True| X[O_O_O]_ False
        """
        my_mono = self.boardMonomials.get_monomials()
        my_types = self.boardMonomials.get_types()
        structured_array = np.zeros(self.amount_monomials, dtype=[('Active', 'bool'), ('Mono', 'uint16', (self.chain, 2)), ('Value', 'uint16'), ('Type', 'uint8'), ('Taken', 'bool', self.chain),
                                                                  ('Distance', 'uint8'), ('Open', 'bool')])
        structured_array['Value'] = 1
        structured_array['Active'] = True
        structured_array['Mono'] = my_mono
        structured_array['Type'] = my_types

        for x in range(len(structured_array)):
            structured_array[x]['Open'] = self.check_open(structured_array[x]['Type'], structured_array[x]['Mono'])
        return structured_array

    def create_point_structure(self):
        """Point Structure:
        Column 1: Array, Point Coordinates. Ex: [0, 0], [0, 4]
        Column 2: Int, Value Of Point Based On All Monomials That Are Still Active
        Column 3: Array, Array Containing All Values From Each Monomial Type. Ex: [5, 5, 5, 2]
        Column 4: Array, Array Listing Monomials Remaining That Influence Point. Ex:[5, 5, 5, 5] Indicates All Original Monomials Remain
        Column 5: Array, Array Listing All Monomials That Point Is Located In That Are Still Active Based On Monomial Type
                 Ex:
                 Point [x, y]
                 [[0, 2, 4, 65535, 65535], [5, 6, 7, 65535, 65535], [65535, 65535, 65535, 65535, 65535], [65535, 65535, 65535, 65535, 65535]]
                 Array 0: Indicates 3 Monomials Of Type 0 Exist
                 Array 1: Indicates 3 Monomials Of Type 1 Exist
                 Array 2: Indicates All Monomials Of Type 2 Are Dead
                 Array 3: Indicates All Monomials Of Type 3 Are Dead
                 65535 Used To Indicate End Of List Due To Numpy Structures Required to Stay In Constant Size
        Column 6: Array, Same As Column 5 Except Values Stored Are Scores Provided By Monomial
        Column 7: . . .
        """
        structured_array = np.zeros(self.amount_points, dtype=[('Point', 'uint8', 2), ('Value', 'uint16'), ('Value_Split', 'uint16', 4), ('Mono_Left', 'uint16', 4),
                                                               ('Mono_ID', 'uint16', (4, self.chain)), ('Point_Value_Double_Split', 'uint16', (4, self.chain)), ('Force_Move', 'bool')])
        structured_array['Value'] = self.boardMonomials.get_count()
        structured_array['Point'] = self.points
        structured_array['Value_Split'] = self.boardMonomials.get_count_split()
        structured_array['Mono_Left'] = self.boardMonomials.get_count_split()
        structured_array['Mono_ID'] = POINT_MAX
        for monomial in range(len(self.monomials)):
            for point in self.monomials[monomial]:
                mono_type = self.my_mono[monomial]['Type']
                replace_index = np.where(structured_array[self.get_coord(point)]['Mono_ID'][mono_type] == POINT_MAX)[0][0]
                structured_array[self.get_coord(point)]['Mono_ID'][mono_type][replace_index] = monomial
                structured_array[self.get_coord(point)]['Point_Value_Double_Split'][mono_type][replace_index] += 1
        return structured_array

    def create_combo_structure(self):
        """Combo Structure
        Column 1: Int, Index Of Point In Point Structure
        Column 2: Int, Index Of First Monomial
        Column 3: Int, Index Of Second Monomial
        Column 4: Int, Combo Score For Mono 1 (Score To Indicate # Of Moves Left To Form A Combo)
        Column 5: Int, Combo Score For Mono 2
        Column 6: Int, Total Combo Score
        """
        points, types, total = self.generate_combos()
        structured_array = np.zeros(total, dtype=[('Point_Index', 'uint16'), ('Mono_1_Index', 'uint16'), ('Mono_2_Index', 'uint16'),
                                                  ('Mono_1_Combo_Score', 'uint16'), ('Mono_2_Combo_Score', 'uint16'), ('Combo_Score', 'uint16')])
        structured_array_counter = 0
        for point_index in range(len(self.points)):
            mono_types = [[] for _ in range(4)]
            for type_index in range(4):
                mono_types[type_index] = (types[point_index] == np.uint(type_index))
            for x in range(4):
                for y in range(x + 1, 4):
                    for first_index in np.asarray(points[point_index])[mono_types[x]]:
                        for second_index in np.asarray(points[point_index])[mono_types[y]]:
                            structured_array[structured_array_counter]['Point_Index'] = point_index
                            structured_array[structured_array_counter]['Mono_1_Index'] = first_index
                            structured_array[structured_array_counter]['Mono_2_Index'] = second_index
                            structured_array_counter += 1
        return structured_array

    def generate_combos(self):
        """Get A List Of Every Possible Combo By Forming Every Possible Combination From Monomials Within Reach Of Each Other
        Total Combos: 30194 For Board Of Size 19x19 And Chain Of Size 5
        """
        pre_point_list = [[] for _ in range(self.board * self.board)]
        pre_point_type = [[] for _ in range(self.board * self.board)]
        total_combos = 0

        for monomial_index in range(len(self.monomials)):
            for point in self.monomials[monomial_index]:
                pre_point_list[self.get_coord(point)].append(monomial_index)
                pre_point_type[self.get_coord(point)].append(self.my_mono[monomial_index]['Type'])

        for point in range(len(pre_point_list)):
            type = [[] for _ in range(4)]
            for x in range(4):
                type[x] = pre_point_type[point].count(x)
            for x in range(4):
                for y in range(x+1, 4):
                    total_combos += type[x] * type[y]

        return pre_point_list, pre_point_type, total_combos

    def my_move(self, point):
        """Move Performed By Bot"""
        self.update_structure(0, 1, point, self.Monomials, self.Points, self.Combos, self.point_active)
        return self.check_won()

    def op_move(self, point):
        """Move Performed By Opponent"""
        self.update_structure(1, 0, point, self.Monomials, self.Points, self.Combos, self.point_active)
        self.last_move = self.get_coord(point)
        return self.check_won()

    """Update Functions ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"""
    def update_structure(self, initiator, follower, point, mono_structure, point_structure, combo_structure, point_active_list):
        """Update All Structures (Monomial, Point, Combo) Based On Move Taken, Initiator = Who Made The Move, """
        point_index = self.get_coord(point)
        point_active_list[point_index] = False
        self.update_combo_structure_remove_point(point_index, combo_structure)
        self.update_open(follower, point_index, mono_structure, combo_structure)

        """For Each Monomial Update Value Of Monomial"""
        for monomial_index in self.my_mono_index[point_index]:
            o_score = mono_structure[initiator][monomial_index]['Value']
            mono_structure[initiator][monomial_index]['Value'] *= 2
            i_monomial, v_monomial = mono_structure[initiator][monomial_index], mono_structure[follower][monomial_index]
            i_active, f_active = i_monomial['Active'], v_monomial['Active']
            i_score, f_score = i_monomial['Value'], v_monomial['Value']
            m_type = i_monomial['Type']

            """If Monomial Active For Follower, Update Values Of Points Found Inside"""
            if i_active:
                for z in self.monomials[monomial_index]:
                    t_index = self.get_coord(z)
                    sub_mono_index = np.where(point_structure[initiator][t_index]['Mono_ID'][m_type] == monomial_index)[0]
                    point_structure[initiator][t_index]['Value'] += i_score - o_score
                    point_structure[initiator][t_index]['Value_Split'][m_type] += i_score - o_score
                    point_structure[initiator][t_index]['Point_Value_Double_Split'][m_type][sub_mono_index] = i_score

            """Update Monomial Values"""
            self.update_taken(initiator, monomial_index, point_index, mono_structure)
            self.update_distance(initiator, monomial_index, mono_structure)

            """If Monomial Active For Follower, Set Monomial Active To False, And Update Points To Indicate Changes"""
            if f_active:
                mono_structure[follower][monomial_index]['Active'] = False
                for y in self.monomials[monomial_index]:
                    t_index = self.get_coord(y)
                    sub_mono_index = np.where(point_structure[follower][t_index]['Mono_ID'][m_type] == monomial_index)[0]
                    point_structure[follower][t_index]['Value'] -= f_score
                    point_structure[follower][t_index]['Value_Split'][m_type] -= f_score
                    point_structure[follower][t_index]['Point_Value_Double_Split'][m_type][sub_mono_index] = self.double_split_loss(point_structure[follower][t_index]['Point_Value_Double_Split'][m_type][sub_mono_index])
                    self.reposition_index(follower, t_index, m_type, monomial_index, point_structure)
                    point_structure[follower][t_index]['Mono_Left'][m_type] -= 1
                self.update_combo_structure_remove_mono(follower, monomial_index, combo_structure)
            self.update_combo_structure_values(0, monomial_index, combo_structure, mono_structure)
            self.update_combo_structure_values(1, monomial_index, combo_structure, mono_structure)
        self.turn_count += 1

    def update_open(self, initiator, point_index, mono_structure, combo_structure):
        """Update Monomials To Closed If Adjacent Point's Are Taken"""
        for x in range(len(self.close_update[point_index])):
            for y in self.close_update[point_index][x]:
                if mono_structure[initiator][y]['Type'] == x:
                    mono_structure[initiator][y]['Open'] = False
                    self.update_combo_structure_values(initiator, y, combo_structure, mono_structure)

    @staticmethod
    def update_combo_structure_remove_mono(initiator, monomial_index, combo_structure):
        """Remove Monomials From Combo Structure If Monomial Is Dead"""
        for index in ['Mono_1_Index', 'Mono_2_Index']:
            remove_indexes_player = np.where(combo_structure[initiator][index] == monomial_index)[0]
            combo_structure[initiator] = np.delete(combo_structure[initiator], remove_indexes_player, 0)

    @staticmethod
    def update_combo_structure_remove_point(point_index, combo_structure):
        """Remove Rows From Combo Structure If Point Taken"""
        for player in [0, 1]:
            remove_indexes_player = np.where(combo_structure[player]['Point_Index'] == point_index)[0]
            combo_structure[player] = np.delete(combo_structure[player], remove_indexes_player, 0)

    def update_combo_structure_values(self, initiator, monomial_index, combo_structure, mono_structure):
        """Update Values In Combo Structure"""
        mono_1_indexes = np.where(combo_structure[initiator]['Mono_1_Index'] == monomial_index)[0]
        mono_2_indexes = np.where(combo_structure[initiator]['Mono_2_Index'] == monomial_index)[0]
        for index in mono_1_indexes:
            mono_1_open = mono_structure[initiator][combo_structure[initiator][index]['Mono_1_Index']]["Open"]
            combo_structure[initiator][index]['Mono_1_Combo_Score'] = self.combo_ranker(initiator, combo_structure[initiator][index]['Mono_1_Index'], combo_structure[initiator][index]['Point_Index'], mono_structure)
            combo_structure[initiator][index]['Combo_Score'] = combo_structure[initiator][index]['Mono_1_Combo_Score'] + combo_structure[initiator][index]['Mono_2_Combo_Score']

        for index in mono_2_indexes:
            mono_2_open = mono_structure[initiator][combo_structure[initiator][index]['Mono_2_Index']]["Open"]
            combo_structure[initiator][index]['Mono_2_Combo_Score'] = self.combo_ranker(initiator, combo_structure[initiator][index]['Mono_2_Index'], combo_structure[initiator][index]['Point_Index'], mono_structure)
            combo_structure[initiator][index]['Combo_Score'] = combo_structure[initiator][index]['Mono_1_Combo_Score'] + combo_structure[initiator][index]['Mono_2_Combo_Score']

    @staticmethod
    def double_split_loss(value):
        return 0 if value == 1 else value / 2

    @staticmethod
    def update_distance(initiator, monomial_index, mono_structure):
        """Update Distance In Monomial Table"""
        if mono_structure[initiator][monomial_index]['Value'] == MULTIPLIER:
            mono_structure[initiator][monomial_index]['Distance'] = 1
        else:
            index = np.where(mono_structure[initiator][monomial_index]['Taken'])[0]
            mono_structure[initiator][monomial_index]['Distance'] = index[len(index) - 1] - index[0] + 1

    def update_taken(self, initiator, monomial_index, point_index, mono_structure):
        """Update Point Taken From False To True In Array"""
        index = self.updated_monomials[monomial_index].index(point_index)
        mono_structure[initiator][monomial_index]['Taken'][index] = True

    @staticmethod
    def reposition_index(influence, point_index, monomial_type, monomial_index, point_structure):
        """Re-Position Indexes To Have Active Indexes First And Dead Ones Last"""
        replace_index = np.where(point_structure[influence][point_index]['Mono_ID'][monomial_type] == monomial_index)[0]
        point_structure[influence][point_index]['Mono_ID'][monomial_type][replace_index] = point_structure[influence][point_index]['Mono_ID'][monomial_type][point_structure[influence][point_index]['Mono_Left'][monomial_type] - 1]
        point_structure[influence][point_index]['Mono_ID'][monomial_type][point_structure[influence][point_index]['Mono_Left'][monomial_type] - 1] = POINT_MAX
        point_structure[influence][point_index]['Point_Value_Double_Split'][monomial_type][replace_index] = point_structure[influence][point_index]['Point_Value_Double_Split'][monomial_type][point_structure[influence][point_index]['Mono_Left'][monomial_type] - 1]
        point_structure[influence][point_index]['Point_Value_Double_Split'][monomial_type][point_structure[influence][point_index]['Mono_Left'][monomial_type] - 1] = 0

    """Decision Making Functions ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"""

    def calc_move(self):
        move, category = self.calc_move_v2(self.Monomials, self.Points, self.Combos, self.point_active)
        #temp_fix = self.turn_count
        #print(move)
        # False When Testing
        look = True
        if look and len(self.w_path) != 0:
            print("Taking Path")
            for x in list(self.w_path):
                if self.last_move == x:
                    self.w_path = self.w_path[x]
                    move = list(self.w_path)[0]
                    self.w_path = self.w_path[move]
                    return self.get_point(move)
            print("Path Error?")
            self.w_path = []
        if look and category:
            win_paths, _ = self.look_ahead_tree(0)
            lose_paths, break_paths = self.look_ahead_tree(1)
            # self.l_path, self.w_path, self.b_path
            # self.last_move
            if len(win_paths) != 0:
                depth, index = 99, 0
                for x in range(len(win_paths)):
                    td = self.worst_case_dive(win_paths[x])
                    if td < depth:
                        depth = td
                        index = x
                moves = list(win_paths[index])
                self.w_path = win_paths[index][moves[0]]
                print("Path Found")
                self.view_tree(win_paths[index], 0)
                return self.get_point(moves[0])
            elif len(lose_paths) != 0:
                m = lose_paths[0]
                temp_fix = self.get_leading_moves(0, self.Monomials, self.point_active)
                if len(list(temp_fix)) != 0:
                    print("Avoiding Path, Leading Move")
                    move = list(temp_fix)
                else:
                    print("Path Closed")
                    for a in lose_paths:
                        self.view_tree(a, 1)
                    return self.get_point(list(m)[0])
            #elif len(break_paths) != 0:
            #    self.b_path = break_paths

        temp_fix = self.get_leading_moves(0, self.Monomials, self.point_active)
        pm = list(set(move) & set(list(temp_fix)))
        if len(pm) != 0:
            move = pm

        if len(move) != 1:
            final_move = self.get_highest_score(move, self.Points)
        else:
            final_move = self.get_point(move[0])
        return final_move

    def read_print_paths(self, player_id, paths):
        player_string = "Losing" if player_id else "Winning"

        print("Found", player_string, "Path!", "Turn:", self.turn_count)
        for x in range(len(paths)):
            print("Path", (x + 1), ":", end=" ")
            for y in paths[x]:
                print(self.get_point(y), end=" ")
            print("\n")

    def leading_move_purge(self, influence, point_index, mono_type, mono_structure, point_structure):
        search_list = [0, 1, 2, 3]
        for ignore_type in mono_type:
            search_list.remove(ignore_type)
        total = 0
        possible_monos = []
        point = point_structure[influence][point_index]

        for x in search_list:
            if point['Value_Split'][x] - point['Mono_Left'][x] > 1:
                for y in range(point['Mono_Left'][x]):
                    possible_monos.append(point['Mono_ID'][x][y])

        if len(possible_monos) != 0:
            for x in range(4):
                monos = np.where(mono_structure[influence][possible_monos]['Type'] == x)[0]
                if len(monos) != 0:
                    for x in monos:
                        if (mono_structure[influence][x]['Open'] and mono_structure[influence][x]['Value'] >= math.pow(MULTIPLIER, 3)) or mono_structure[influence][x]['Value'] == CHAIN_FOUR:
                            total += 1
                            break

            return True, total, possible_monos
        return False, total, possible_monos

    def find_block_monos(self, influence, point_type, point, mono_structure):
        purge = np.where(self.updated_monomials == point)[0]
        possible_monos = np.where((mono_structure[influence][purge]['Value'] >= math.pow(MULTIPLIER, 3)) & (mono_structure[influence][purge]['Type'] == point_type))[0]
        return purge[possible_monos]

    @staticmethod
    def minimize_structure(structure, condition):
        """Return Structure With Only Rows That Meet Condition"""
        structure[0] = structure[0][np.ix_(condition)]
        structure[1] = structure[1][np.ix_(condition)]
        return structure

    def handle_block(self, influence, mono_structure, active_structure):
        block_moves = self.get_three(influence, mono_structure, active_structure)
        if isinstance(block_moves, bool):
            block_moves = self.get_four(influence, mono_structure)

        return block_moves


    def dive_node(self, influence, move, point_type, mono_structure, point_structure, combo_structure, active_structure, depth, node):
        op = self.get_opponent(influence)
        result, total, monos = self.leading_move_purge(influence, move, point_type, mono_structure, point_structure)
        if result:
            self.update_structure(influence, op, self.get_point(move), mono_structure, point_structure, combo_structure, active_structure)
            updated_monos = self.minimize_structure(copy.deepcopy(mono_structure), self.find_block_monos(influence, point_type, move, mono_structure))
            block_three = self.handle_block(influence, updated_monos, active_structure)

            if isinstance(block_three, bool):
                for zzz in updated_monos[influence]:
                    print(zzz)
                input("....")
                print("\n\nError!?")
                return False
            else:
                block_storage = {value:[] for value in block_three}
                node[move] = {value:{} for value in block_three}
                for block_move in block_three:
                    block_storage[block_move].append(copy.deepcopy(mono_structure))
                    block_storage[block_move].append(copy.deepcopy(point_structure))
                    block_storage[block_move].append(copy.deepcopy(combo_structure))
                    block_storage[block_move].append(copy.deepcopy(active_structure))
                    self.update_structure(op, influence, self.get_point(block_move), block_storage[block_move][0], block_storage[block_move][1], block_storage[block_move][2], block_storage[block_move][3])
                    future_leading_moves = self.get_leading_moves(influence, self.minimize_structure(copy.deepcopy(block_storage[block_move][0]), monos), block_storage[block_move][3])
                    all_leading_moves = self.get_leading_moves(influence, mono_structure, active_structure)
                    temp = []
                    for p_move in list(future_leading_moves):
                        if p_move not in list(all_leading_moves):
                            temp.append(p_move)
                    for x in temp:
                        del future_leading_moves[x]

                    block_storage[block_move].append(future_leading_moves)
                    node[move][block_move] = {value:{} for value in list(future_leading_moves)}

                    if len(list(node[move][block_move])) == 0:
                        return False

                overall_result = False
                combo_moves = []
                for block_move in block_three:
                    am = []
                    combo_result, moves_result = self.search_winning_combos(influence, block_storage[block_move])
                    if combo_result:
                        for s_coord in np.unique([self.get_coord(point_type) for point_type in moves_result]):
                            leading_after_math = True
                            # Fix. . .
                            op_three = self.get_four(op, block_storage[block_move][0])
                            if isinstance(op_three, bool):
                                op_three = self.get_three(op, block_storage[block_move][0], block_storage[block_move][3])
                            else:
                                op_three = [op_three]
                            if not isinstance(op_three, bool):
                                if s_coord not in op_three:
                                    leading_after_math = False
                                    am.append(False)
                                else:
                                    am.append(True)
                            if leading_after_math:
                                if s_coord in list(node[move][block_move]):
                                    node[move][block_move][s_coord] = ["*"]
                                else:
                                    node[move][block_move][s_coord] = ["&"]
                        overall_result = True
                        combo_moves.append(block_move)
                    if len(am) != 0 and True not in am:
                        return False
                # If Winning Path Found Remove Point From Search, Only Continue True For Points With No Guaranteed path Found
                if overall_result:
                    for cm in combo_moves:
                        block_three = np.delete(block_three, np.where(block_three == cm)[0][0])

                # Search For Paths, In Order For Path To Exist They Must
                # 1. Eventually Lead To A Winning Combo Being Formed
                #    Such As A Combo Move Being Taken Along With A Open 3 Being Formed
                # 2. For Each Move Opponent Can Block With A Combo Can Still Be Formed
                #    Otherwise Opponent Can Break Free
                for block_move in block_three:
                    total_r = [self.dive_node(influence, option_move, block_storage[block_move][4][option_move],
                                              copy.deepcopy(block_storage[block_move][0]),
                                              copy.deepcopy(block_storage[block_move][1]),
                                              copy.deepcopy(block_storage[block_move][2]),
                                              copy.deepcopy(block_storage[block_move][3]),
                                              depth+1, node[move][block_move]) for option_move in node[move][block_move]]
                    if True not in total_r:
                        return False
                return True
        return False

    def search_winning_combos(self, influence, all_struct):
        """Search For Points That Form A Leading Move Such As Open 3 Or Closed 4 & Form A Combo Thus Guaranteeing Win"""
        mono_structure = all_struct[0]
        point_structure = all_struct[1]
        combo_structure = all_struct[2]
        active_structure = all_struct[3]
        leading_moves = self.get_leading_moves(influence, mono_structure, active_structure)
        combos = np.where(combo_structure[influence]['Combo_Score'] == 3)[0]
        moves_total = []
        # 1. Look For Combos That Require 1 Point
        # 2. Check If That 1 Point Is A Leading Move
        # 3. Check If Combo Point Is A Leading Move
        # 4. If So The First Point Can Be Taken For A Win
        # combo point: End Goal
        # move: Leading Move

        for combo in combos:
            for move in leading_moves:
                if move not in [self.get_coord(x) for x in moves_total] and move in self.get_combo_points(influence, combo_structure[influence][combo], mono_structure):
                    if combo_structure[influence][combo]['Point_Index'] in leading_moves:
                        # Combo Point Is A Leading Move, Add
                        if self.combo_safety_case(influence, move, combo_structure[influence][combo], leading_moves[move][0], mono_structure) and self.assure_combo_win(influence, combo_structure[influence][combo], mono_structure, active_structure):
                            moves_total.append(self.get_point(move))
                            #print("^^", self.get_point(move), self.get_point(combo_structure[influence][combo]['Point_Index']))
                            #print(self.print_combo_info(influence, combo_structure[influence][combo], mono_structure))
                    else:
                        # Combo Point Is Not A Leading Move, Check For Unique Case To Make Sure
                        mono_structure_2 = copy.deepcopy(mono_structure)
                        point_structure_2= copy.deepcopy(point_structure)
                        combo_structure_2 = copy.deepcopy(combo_structure)
                        active_structure_2 = copy.deepcopy(active_structure)
                        # Make A Temp Copy Of Structures To See What If Move Taken
                        self.update_structure(influence, self.get_opponent(influence), self.get_point(move), mono_structure_2, point_structure_2, combo_structure_2, active_structure_2)
                        # Check Combo To See If Taking Point Results In Leading Move Being Greater Or Equal To Opponents
                        for potential_combo in np.where(combo_structure_2[influence]['Combo_Score'] == 4)[0]:
                            if move not in [self.get_coord(m) for m in moves_total] and self.combo_leading_check(influence, combo_structure_2[influence][potential_combo], mono_structure_2, point_structure_2):
                                if self.combo_safety_case(influence, move, combo_structure_2[influence][potential_combo], leading_moves[move][0], mono_structure) and self.assure_combo_win(influence, combo_structure_2[influence][potential_combo], mono_structure_2, active_structure_2):
                                    moves_total.append(self.get_point(move))
                                    #print("^^^", self.get_point(move), self.get_point(combo_structure_2[influence][combo]['Point_Index']))
        if len(moves_total) != 0:
            #print(moves_total)
            return True, moves_total
        return False, False

    def get_combo_block_points(self, influence, combo, mono_structure, debug=False):
        coord_list = [[self.get_coord(point) for point in mono_structure[influence][combo[1]]['Mono']],
                      [self.get_coord(point) for point in mono_structure[influence][combo[2]]['Mono']]]
        active_list = [copy.deepcopy(mono_structure[influence][combo['Mono_1_Index']]['Taken']),
                       copy.deepcopy(mono_structure[influence][combo['Mono_2_Index']]['Taken'])]
        watch_list = []
        for x in range(2):
            for y in np.where(active_list[x] == False)[0]:
                watch_list.append(coord_list[x][y])

        if debug:
            print([self.get_point(x) for x in coord_list[0]])
            print([self.get_point(x) for x in coord_list[1]])
        return watch_list


    def print_combo_info(self, influence, combo, mono_structure):
        mono_1 = combo[1]
        mono_2 = combo[2]
        print("Point: ", self.get_point(combo[0]))
        print("Combo 1 Score:", combo[3])
        print("Combo 3 Score:", combo[4])
        print("Mono 1:", mono_structure[influence][mono_1], mono_1)
        print("Mono 2:", mono_structure[influence][mono_2], mono_2)

    def assure_combo_win(self, influence, combo, mono_structure, active_structure):
        # Make Sure Combo Doesn't Have Leading Move Blockable Point, More Common That Thought
        # influence, mono_structure, active_structure, second_pass=True):
        return True #Bugged Out ???
        points = self.get_combo_block_points(influence, combo, mono_structure)
        op_leading = list(self.get_leading_moves(self.get_opponent(influence), mono_structure, active_structure))
        for x in points:
            if x in op_leading:
                return False
        return True

    def combo_safety_case(self, influence, move_taken, combo, mono_type, mono_structure):
        point_a = self.get_point(move_taken)
        # ToDo: Stop Infinite?

        for watch_point in self.get_combo_block_points(influence, combo, mono_structure):
            if watch_point != move_taken:
                point_b = self.get_point(watch_point)
                if point_b[0] != point_b[0]:
                    if point_b[0] > point_a[0]:
                        point_d = [point_b[0] - point_a[0], point_b[1] - point_a[1]]
                    else:
                        point_d = [point_a[0] - point_b[0], point_a[1] - point_b[1]]
                else:
                    if point_b[1] > point_a[1]:
                        point_d = [point_b[0] - point_a[0], point_b[1] - point_a[1]]
                    else:
                        point_d = [point_a[0] - point_b[0], point_a[1] - point_b[1]]

                abs_value = abs(point_d[0]) if point_d[0] != 0 else abs(point_d[1])
                point_d = [int(x / abs_value) for x in point_d]

                if TYPE_CHECK[mono_type][0] == point_d[0] and TYPE_CHECK[mono_type][1] == point_d[1]:
                    return False
        return True


    def combo_leading_check(self, influence, combo, mono_structure, point_structure):
        """Search For Special Cases In Combos"""
        # Special Case: Leading Moves Being Ignored Due To Allowing Opponent To
        # Form A Leading Move Of Their Own. Ignored Due To Not Considering Player
        # Generating 2 Leading Moves Leading To A Guaranteed Win
        # Ex:
        #       O       X
        #         A O O B
        #           O
        #               X
        # Point A Forms A Combo But Ignored Due To B Also Forming A Open 3
        # Flaw Due To Point A Forming Two Separate Open 3's, Rare Case
        # ToDo: Add To All Cases, Move To Leading Function
        coord_list = [[self.get_coord(point) for point in mono_structure[influence][combo[1]]['Mono']],
                      [self.get_coord(point) for point in mono_structure[influence][combo[2]]['Mono']]]
        active_list = [copy.deepcopy(mono_structure[influence][combo['Mono_1_Index']]['Taken']),
                       copy.deepcopy(mono_structure[influence][combo['Mono_2_Index']]['Taken'])]
        watch_list = [[], []]
        mono_scores = [mono_structure[influence][combo['Mono_1_Index']]['Value'],
                       mono_structure[influence][combo['Mono_2_Index']]['Value']]
        for x in range(2):
            active_list[x][np.where(coord_list[x] == combo[0])[0]] = True
            # 3 Possible Scenarios:
            # 1. First 2 Points Not Taken, Take Second Point
            # 2. Last 2 Points Not Taken Take Fourth Point
            # 3. Not Taken Points Separated, Take All Of Them
            if not active_list[x][0] and not active_list[x][1]:
                watch_list[x].append(coord_list[x][1])
            elif not active_list[x][3] and not active_list[x][4]:
                watch_list[x].append(coord_list[x][3])
            else:
                for y in np.where(active_list[x] == False)[0]:
                    watch_list[x].append(coord_list[x][y])
        result = []
        # Check If Opponent Scores Are Higher, If They Are It Means Opponent Can Block And Break Free
        # Otherwise Point Can Be Taken Despite Opponent Forming Open 3/4 Due To Being 1 Move Ahead
        for point in watch_list:
            for actual_point in point:
                op_scores = np.max([np.max(blah) for blah in point_structure[self.get_opponent(influence)][actual_point]['Point_Value_Double_Split']])
            try:
                if len(point) != 0 and op_scores > mono_scores[len(result)]:
                    result.append(False)
                else:
                    result.append(True)
            except:
                print("...")
                print(point, watch_list)
                print(active_list[0])
                print(active_list[1])
                print([self.get_point(x) for x in coord_list[0]])
                print([self.get_point(x) for x in coord_list[1]])
                print(combo)
                print(mono_structure[influence][combo[1]])
                print(mono_structure[influence][combo[2]])
                print(point_structure[influence][combo[0]])
        return result[0] and result[1]

    def get_combo_points(self, influence, combo_row, mono_structure):
        """Return Points That When Taken Form A Combo"""
        # Choose The Less Complete Mono, Only Mono's Of Score 3
        # Considered. One Guaranteed To Have A Value Of 1
        mono_search = 1 if combo_row['Mono_1_Combo_Score'] == 1 else 2
        original_point = combo_row['Point_Index']
        points_coord = [self.get_coord(point) for point in mono_structure[influence][combo_row[mono_search]]['Mono']]
        active_list = mono_structure[influence][combo_row[mono_search]]['Taken']
        index = np.where(points_coord == original_point)[0][0]

        # If Point Found In Edge Of Monomial Get Rid Of
        # Unimportant Point Due To It Providing No Benefit
        if index == 0 or index == 4 or active_list[0] or active_list[4]:
            points_coord = points_coord[1:4]

        # Combo Point Should Not Be Considered
        if original_point in points_coord:
            points_coord.remove(original_point)
        return points_coord

    def look_ahead_tree(self, influence):
        starting_nodes = self.get_leading_moves(influence, self.Monomials, self.point_active)
        w_path, b_path = [], []
        for possible_move in list(starting_nodes):
            root = {possible_move:[]}
            r = self.dive_node(influence, possible_move, starting_nodes[possible_move], copy.deepcopy(self.Monomials), copy.deepcopy(self.Points), copy.deepcopy(self.Combos), copy.deepcopy(self.point_active), 0, root)
            if r:
                self.clean_tree(root)
                w_path.append(copy.deepcopy(root))
            else:
                if influence == 1:
                    self.view_tree(root, influence)
                self.break_tree(root)
                b_path.append(copy.deepcopy(root))
        return w_path, b_path

    def best_case(self, tree, depth=0):
        cases = []
        for node in list(tree):
            if depth % 2 == 0:
                if len(tree[node] ) == 0:
                    cases.append(1)
                else:
                    cases.append(self.best_case(tree[node], depth+1) + 1)
            else:
                r = self.best_case(tree[node], depth+1)
                cases = max(r)
        return cases

    def worst_case_dive(self, tree):
        worst = 0
        for node in list(tree):
            if len(tree[node]) == 0:
                return 0
            if not isinstance(tree[node], dict):
                return 1
            temp = self.worst_case_dive(tree[node]) + 1
            if temp > worst:
                worst = temp
        return worst

    def clean_tree(self, tree, depth=1):
        nodes = list(tree)
        n = list(range(len(nodes)))
        reversed(n)
        r = []
        for x in n:
            if isinstance(tree[nodes[x]], dict):
                if len(tree[nodes[x]]) == 0:
                    del tree[nodes[x]]
                else:
                    if self.clean_tree(tree[nodes[x]], depth+1):
                        r.append(True)
                    else:
                        del tree[nodes[x]]
            else:
                r.append(True)
        if len(r) != 0:
            return True in r

    def break_tree(self, tree, depth=1):
        nodes = list(tree)
        n = list(range(len(nodes)))
        reversed(n)
        for x in n:
            if isinstance(tree[nodes[x]], dict):
                if depth % 2 == 0:
                    values = tree[nodes[x]].values()
                    if ['*'] in values or ['&'] in values:
                        del tree[nodes[x]]
                    else:
                        self.break_tree(tree[nodes[x]], depth + 1)
                else:
                    self.break_tree(tree[nodes[x]], depth+1)

    def view_tree(self, root, influence, space=0, depth=1):
        for node in root:
            for _ in range(space):
                print(" ", end="")
            if isinstance(node, str):
                print(node)
            else:
                c_num = 96-influence if depth % 2 == 0 else 88
                print('\033[' + str(c_num) + "mDepth:", depth, "|", self.get_point(node), "(" + str(node) + ")\033[0m:")
                self.view_tree(root[node], influence, space+4, depth+1)

    def options_block_four(self):
        pass

    def options_block_three(self, mono, active):
        points = []
        x1, x2 = 0, 2

        if mono['Distance'] == 5:
            return []
        elif mono['Taken'][0]:
            if mono['Distance'] != 4:
                x2 = 1
            adjacent_point = self.get_adjacent(mono['Type'], mono['Mono'][0], False)
            if active[adjacent_point]:
                points.append(adjacent_point)
        elif mono['Taken'][4]:
            if mono['Distance'] != 4:
                x1 = 1
            adjacent_point = self.get_adjacent(mono['Type'], mono['Mono'][4], True)
            if active[adjacent_point]:
                points.append(adjacent_point)

        for point in mono['Mono'][np.invert(mono['Taken'])][x1:x2, :]:
            points.append(self.get_coord(point))

        return points

    def get_adjacent(self, mono_type, point, positive):
        #x = point + TYPE_CHECK[mono_type] if positive else point - TYPE_CHECK[mono_type]
        #print(x)
        move = point + TYPE_CHECK[mono_type] if positive else point - TYPE_CHECK[mono_type]
        for x in move:
            if 0 > x  or x > self.board - 1:
                return -1
        return self.get_coord(move)

    def options_block_two(self):
        pass

    def check_status(self):
        pass

    def options_block_three_v2(self, mono, distance, taken, mono_type, active_structure):
        total_points = []
        x1, x2 = 0, 2
        tf = [False, True] if mono_type != 3 else [True, False]
        if distance == 5:
            return []
        elif taken[0]:
            if distance != 4:
                x2 = 1
            adjacent_point = self.get_adjacent(mono_type, mono[0], tf[0])
            if adjacent_point > 0:
                if active_structure[adjacent_point]:
                    total_points.append(adjacent_point)
        elif taken[4]:
            if distance != 4:
                x1 = 1
            adjacent_point = self.get_adjacent(mono_type, mono[4], tf[1])
            if adjacent_point > 0:
                if active_structure[adjacent_point]:
                    total_points.append(adjacent_point)

        for point in mono[np.invert(taken)][x1:x2, :]:
            total_points.append(self.get_coord(point))

        return total_points

    def get_leading_moves(self, influence, mono_structure, active_structure, second_pass=True):
        """Find All Points That Cause Action To Be Needed, Only Consider Points That Will Keep Bot In Lead
        Ex:
            A
            B
            O X
          O O X X
            C
            D

        Bot: O, Opponent: X
        A, B, C, D Each Form A Monomial Of Size 3 And Lead To The Following Options To Be Taken By Opponent
        A: B
        B: A, C
        C: B, D
        D: C

        By Taking One Of Those Moves Opponent Will Be Forced To Follow, Since Point B Allows Opponent To Form
        A Monomial Of Size 3 This Will Force Bot To Follow. Due To This Move Taken Should Be One Which Doesn't
        Allow B To Be An Option For Opponent, Such As B, Or D Due To These Two Forcing Opponent To Take Moves
        Which Leave Him Following.
        """

        active_monos = [[], []]
        leading_monos = [[], []]
        leading_points = [[], []]
        op = (influence+1) % 2
        for player_index in range(2):
            active_monos[player_index] = mono_structure[player_index][mono_structure[player_index]['Active']]
            leading_monos[player_index] = np.where(((active_monos[player_index]['Value'] == math.pow(MULTIPLIER, 2)) & (active_monos[player_index]['Open']) & (active_monos[player_index]['Distance'] != 5)) | (active_monos[player_index]['Value'] == math.pow(MULTIPLIER, 3)))[0]

        point_association = {}
        type_association = {}

        temp_fix = {}
        for player_index in range(2):
            for mono_index in range(len(leading_monos[player_index])):
                current_mono = active_monos[player_index][leading_monos[player_index][mono_index]]

                if current_mono['Value'] == math.pow(MULTIPLIER, 3):
                    temp_list = []
                    for point in current_mono['Mono'][np.invert(current_mono['Taken'])]:
                        temp_list.append(self.get_coord(point))
                    if player_index == influence:
                        self.dictionary_append_v2(point_association, temp_list[0], [temp_list[1]])
                        self.dictionary_append_v2(point_association, temp_list[1], [temp_list[0]])
                        for point in temp_list:
                            self.dictionary_append_v2(type_association, point, [current_mono['Type']])

                    for point in temp_list:
                        if player_index == 1:
                            self.temp_fix_function(temp_fix, self.get_point(point), temp_fix, 1)
                        leading_points[player_index].append(point)
                else:
                    current_taken = current_mono['Taken']
                    my_range = range(0, 5)
                    if current_mono['Taken'][4]:
                        my_range = range(1, 5)
                    elif current_mono['Taken'][0]:
                        my_range = range(0, 4)
                    for x in my_range:
                        if not current_taken[x]:
                            c_taken_2 = copy.deepcopy(current_mono['Taken'])
                            c_taken_2[x] = True
                            index = np.where(c_taken_2)[0]
                            l_moves = self.options_block_three_v2(current_mono['Mono'], index[len(index) - 1] - index[0] + 1, c_taken_2, current_mono['Type'], active_structure)
                            for point in current_mono['Mono'][np.invert(current_mono['Taken'])][list(my_range)[0]:list(my_range)[len(list(my_range))-1]-1, :]:
                                leading_points[player_index].append(self.get_coord(point))
                                if player_index == 1:
                                    self.temp_fix_function(temp_fix, point, temp_fix)
                            if player_index == influence:
                                self.dictionary_append_v2(point_association, self.get_coord(current_mono['Mono'][x]), l_moves)
                                self.dictionary_append_v2(type_association, self.get_coord(current_mono['Mono'][x]), [current_mono['Type']])

        #Need Monomial Information Here Know How Much You Risk By Blocking. . . Make Function Just For Combos Instead? Sounds Like A Better Solution
        point_and_type = {}
        re_check = []
        if second_pass:
            tl = self.get_leading_moves(influence, mono_structure, active_structure, False)
        for point_keys in list(point_association):
            for point in np.unique(leading_points[op]):
                if point in point_association[point_keys]:
                    tb = True
                    #ToDo: . . .
                    if second_pass and point in temp_fix:
                        for x in temp_fix[point]:
                            if x in tl and x != point_keys:
                                tb = False
                                re_check.append(point_keys)
                    if tb:
                        del point_association[point_keys]
                        break


        for point_keys in list(point_association):
            point_and_type[point_keys] = np.unique(type_association[point_keys])
        return point_and_type

    def temp_fix_function(self, dict, point, other_points, debug=0):
        point = self.get_coord(point)
        if point not in dict:
            dict[point] = []
        for x in other_points:
            if x not in dict[point] and x != point:
                dict[point].append(x)

    def dictionary_append_v2(self, dict, point_index, points):
        if point_index in dict:
            for point in points:
                dict[point_index].append(point)
        else:
            dict[point_index] = points

    def minimize_moves(self, point_list, point_structure):
        if len(point_list) <= 2:
            return point_list
        else:
            possible_point = []
            score_list = [[], []]
            for point in point_list:
                score_list[0].append(self.get_score_harsh(0, point, point_structure))
                score_list[1].append(self.get_score_harsh(1, point, point_structure))

            max_moves = [np.where(score_list[0] == np.max(score_list[0]))[0], np.where(score_list[1] == np.max(score_list[1]))[0]]
            cc = 0
            if len(max_moves[0]) == 1 and len(max_moves[1]) == 1 and max_moves[0] == max_moves[1]:
                return max_moves[0]
            else:
                while len(possible_point) != 2:
                    possible_point.append(random.choice(max_moves[cc]))
                    cc = (cc + 1) % 2
            return possible_point

    def calc_move_v2(self, mono_structure, point_structure, combo_structure, point_active_list, initiator=0, follower=1):
        """Decision Making
        Priority:
        Chain Of 4
        Unblockable Chain Of 3
        Combo
        Leading Moves
        Combo Setup Move
        """

        my_max_m = max(mono_structure[initiator][mono_structure[initiator]['Active']]['Value'])
        op_max_m = max(mono_structure[follower][mono_structure[follower]['Active']]['Value'])

        if my_max_m == 1:
            return [self.second_move(point_structure, point_active_list)], False

        if my_max_m == CHAIN_FOUR:
            return [self.get_four(initiator, mono_structure)], False
        if op_max_m == CHAIN_FOUR:
            return [self.get_four(follower, mono_structure)], False

        if my_max_m == math.pow(MULTIPLIER, 3):
            move = self.get_three(initiator, mono_structure, point_active_list)
            if not isinstance(move, bool):
                return move, False
        if op_max_m == math.pow(MULTIPLIER, 3):
            move = self.get_three(follower, mono_structure, point_active_list)
            if not isinstance(move, bool):
                return move, False

        combo_move_bot, score_b = self.combo_move_ranker(initiator, combo_structure, mono_structure)
        combo_move_op, score_o = self.combo_move_ranker(follower, combo_structure, mono_structure)

        #print(score_b, score_o)

        l_moves = self.get_leading_moves(initiator, mono_structure, point_active_list)
        #if len(l_moves) != 0:
        #    #print(l_moves)
        #    return list(l_moves), True
        if score_b <= 4 and score_o <= 4:
            temp_moves = self.get_point_move(initiator, mono_structure, point_structure, my_max_m)
            purge_moves = self.get_leading_moves(follower, mono_structure, point_active_list)
            temp_moves = list(set(temp_moves))
            for x in purge_moves:
                if x in temp_moves:
                    temp_moves.remove(x)
            return temp_moves, True
        #. . .Combos Take Into Account

        if len(l_moves) != 0 and score_b < 3:
           #print(l_moves)
           return list(l_moves), True
        if not isinstance(combo_move_bot, bool):
            if score_b >= score_o:
                return combo_move_bot, False
        if not isinstance(combo_move_op, bool):
            return combo_move_op, False


    def get_point_move(self, influence, mono_structure, point_structure, point_goal):
        search_monos = np.where(mono_structure[influence]['Value'] == point_goal)
        points = []
        for mono in mono_structure[influence][search_monos]:
            for x in range(5):
                if not mono['Taken'][x]:
                    points.append(self.get_coord(mono['Mono'][x]))
        #print("Returning, ", points)
        return points
    def get_highest_score(self, point_list, point_structure, influence=False):
        """Obtain Scores Of All Moves, Return Move With Highest Score. If Influence Sent Make Sure To Only Use Score From Specific Player"""
        score_list_bot = []
        score_list_op = []
        point_list = np.unique(point_list)
        point_list = point_list.tolist()
        avoid_moves = self.get_leading_moves(1, self.Monomials, self.point_active)
        leading_moves = self.get_leading_moves(0, self.Monomials, self.point_active)

        pre_selection = point_list
        for x in point_list:
            if x in avoid_moves:
                point_list.remove(x)
        if len(point_list) == 0:
            point_list = pre_selection

        for point in point_list:
            score_list_bot.append(self.get_score_harsh(0, point, point_structure))
            score_list_op.append(self.get_score_harsh(1, point, point_structure))
        if isinstance(influence, bool):
            try:
                if max(score_list_bot) >= max(score_list_op):
                    index = random.choice(range(0, len(score_list_bot))) if RANDOM else random.choice(np.where(score_list_bot == np.max(score_list_bot))[0])
                else:
                    index = random.choice(range(0, len(score_list_op))) if RANDOM else random.choice(np.where(score_list_bot == np.max(score_list_bot))[0])
            except:
                print(score_list_bot,score_list_op, point_list)
                print("Hmm")
        else:
            if influence == 0:
                index = random.choice(range(0, len(score_list_bot))) if RANDOM else random.choice(np.where(score_list_bot == np.max(score_list_bot))[0])
            else:
                index = random.choice(range(0, len(score_list_op))) if RANDOM else random.choice(np.where(score_list_bot == np.max(score_list_bot))[0])
        return self.get_point(point_list[index])

    def get_score_harsh(self, influence, point_index, point_structure):
        """Return Values After Subtracting # Of Monomials For Each Type, Leads To Score Of Monomials With No Points Taken Being Cancelled Out"""
        value = 0
        for x in range(4):
            value += point_structure[influence][point_index]['Value_Split'][x] - point_structure[influence][point_index]['Mono_Left'][x]
        return value

    def combo_point_getter(self, influence, potential_moves, mono_structure):
        """Get Points Based On Provided Points. Returns Either possible_double_combo Which Indicates Point Which Benefits Two
        Combos, Or Will Return very_point Which Indicates That No Point Was Found To Benefit Multiple Combos"""
        check_points = []
        point_tracker = []
        helper_tracker = []
        every_point = []
        possible_double_combo = []

        for combo in potential_moves:
            index = np.where(point_tracker == combo['Point_Index'])[0]
            """If No Point Found Then Point Hasn't Appeared, If So Append New List To Variables To Store Information For New Point, Else Index Already Exists"""
            if len(index) == 0:
                index = len(point_tracker)
                point_tracker.append([])
                point_tracker[index] = combo['Point_Index']
                check_points.append(combo['Point_Index'])
                helper_tracker.append([])
            else:
                index = index[0]
            """If Monomial 1 Closer To Forming A Combo Improve Monomial 2 Instead"""
            check = 'Mono_2_Index' if combo['Mono_1_Combo_Score'] > combo['Mono_2_Combo_Score'] else 'Mono_1_Index'
            for point in self.get_possible_points_combo(influence, combo['Point_Index'], combo[check], mono_structure):
                    if point not in helper_tracker[index]:
                        helper_tracker[index].append(point)
                        every_point.append(point)

        """Check If Point Appears Multiple Times If So Benefits Multiple, Prioritize"""
        for x in range(len(point_tracker)):
            for point_x in helper_tracker[x]:
                for point_lists in range(x + 1, len(point_tracker)):
                    if point_x in helper_tracker[point_lists]:
                        possible_double_combo.append(point_x)
                if point_x in check_points:
                    possible_double_combo.append(point_x)

        """Prioritize Points Which Benefit Multiple"""
        if len(possible_double_combo) != 0:
            return possible_double_combo, True
        else:
            return every_point, False

    def combo_move_ranker(self, influence, combo_structure, mono_structure):
        """Return Moves Which Have Best Chance To Help Win
        Moves Given A Score To Help Determine Which Choice To Make Between Self And Opponent
        5: Double Combo
        4: Form 2 Combos
        3: From Single Combo or Combo + Help Form Another Combo
        2: Help Form Combo (2, 1)
        1: Help Form Combo (1, 1)
        """
        bug_check = False
        potential_moves = [[] for _ in range(4)]
        return_list = []
        combo_score = []

        combo_search_list = np.argsort(combo_structure[influence]['Combo_Score'])[::-1]
        organized_combos = combo_structure[influence][combo_search_list]
        current_index = 0

        for x in range(5):
            """Get All Combos For Current Goal, Search For Score Of 4-x, If None Found Will Loop Back And Search Again"""

            while 4 - organized_combos[current_index]['Combo_Score'] == x:
                potential_moves[4 - organized_combos[current_index]['Combo_Score']].append(organized_combos[current_index])
                current_index += 1

            """Check For Combos, Else Check For Moves To Help Form Combo"""
            if x == 0 and len(potential_moves[0]) != 0:
                for combo in potential_moves[0]:
                    """Don't Bother With Alternate Moves Unless Opponent"""
                    score = self.Monomials[influence][combo['Mono_1_Index']]['Value'] + self.Monomials[influence][combo['Mono_2_Index']]['Value']
                    if bug_check:
                        print("Check:", influence, combo)
                        print(self.Monomials[influence][combo['Mono_1_Index']])
                        print(self.Monomials[influence][combo['Mono_2_Index']])
                        print(score, "\n")

                    if influence == 1:
                        for y in self.find_extra_double_move(influence, combo, mono_structure):
                            return_list.append(y)
                    return_list.append(combo['Point_Index'])
                    combo_score.append(score)

                return return_list, max(combo_score)
            else:
                if len(potential_moves[x]) != 0:
                    moves, category = self.combo_point_getter(influence, potential_moves[x], mono_structure)
                    if len(moves) != 0:
                        """Moves Which Benefit Multiple Combos, Else Moves Which Don't"""
                        if category:
                            return moves, 5 - x
                        else:
                            return moves, 4 - x

    def find_extra_double_move(self, influence, combo, mono_structure):
        """Return Other Options To Stopping A Combo"""
        check_index = ['Mono_1_Index', 'Mono_2_Index']
        moves = []

        for value_index in range(2):
            location = np.where(self.updated_monomials[combo[check_index[value_index]]] == combo['Point_Index'])[0][0]
            taken = mono_structure[influence][combo[check_index[value_index]]]['Taken']
            taken_index = np.where(taken == False)[0]
            taken_index = taken_index.tolist()

            for x in range(0, 2):
                if 0 < abs(location - taken_index[x]) < 4:
                    moves.append(self.updated_monomials[combo[check_index[value_index]]][taken_index[x]])
        return moves

    def get_possible_points_combo(self, influence, point_index, mono_index, mono_structure):
        """Get All Points Which Will Benefit Based On Monomial Size, Range Starts With 2 And Increases As The Monomial Score Grows.
        Ex: Monomial _ _ _ _ O Will Only Consider _ _ _ X O 1 Point
            Monomial _ _ _ O O Will Only Consider _ X X O O 2 Points
            Monomial _ O _ O _ Will Only Consider X O X O X 3 Points
        """
        search_range = (mono_structure[influence][mono_index]['Value'] // 2) + 1
        relative_index = np.where(self.updated_monomials[mono_index] == point_index)[0][0]
        start_index = relative_index - search_range if (relative_index - search_range) >= 0 else 0
        end_index = relative_index + search_range if (relative_index + search_range <= self.chain) else self.chain
        helper = []

        for x in range(start_index, end_index):
            if not mono_structure[influence][mono_index]['Taken'][x] and x != relative_index:
                helper.append(self.updated_monomials[mono_index][x])
        return helper

    def combo_ranker(self, influence, mono_index, point_index, mono_structure):
        """Ranks Monomial
        2: This Monomial Can Form A Combo
        1: Monomial Needs 1 More Point To Be Capable Of Forming A Combo
        0: Monomial Needs 2 Or More Points To Be Capable Of Forming A Comb"""
        mono = mono_structure[influence][mono_index]
        if mono['Value'] >= 8 or (mono['Value'] == 4 and mono['Open'] and (mono['Taken'][0] == False and mono['Taken'][4] == False) and self.valid_point_range(influence, mono_index, point_index)):
            return 2
        elif (mono['Value'] == 4 and (mono['Taken'][0] == False and mono['Taken'][4] == False)) or (mono['Value'] == 2 and mono['Open'] and self.valid_point_range(influence, mono_index, point_index)):
            return 1
        else:
            return 0

    def valid_point_range(self, influence, monomial_index, point_index):
        """Checks To See If Monomial Is Valid To Form A Combo By Making Sure Distance Isn't Too High Or That Edges Are Clear"""
        point_index_location = self.updated_monomials[monomial_index].index(point_index)
        taken_list = self.Monomials[influence][monomial_index]['Taken']
        distance = self.Monomials[influence][monomial_index]['Distance']
        if 0 < point_index_location < 4:
            if distance <= 4:
                return True
        else:
            if not taken_list[0] and not taken_list[4]:
                return True
        return False

    def get_four(self, influence, mono_structure):
        """Get Fifth Point For Win/Win-Prevention"""
        four_value = math.pow(MULTIPLIER, 4)
        possible_mono = np.where((mono_structure[influence]['Value'] == four_value) & mono_structure[influence]['Active'])[0]
        for x in mono_structure[influence][possible_mono]:
            location = np.where(x['Taken'] == False)[0][0]
            return self.get_coord(x['Mono'][location])
        return False
    def get_three(self, influence, mono_structure, active_structure):
        """Return Points To Block If Monomial Is Forced To Be Block, Ex: _ _ O O O _ _"""
        possible_mono_new = np.where((mono_structure[influence]['Active']) & (mono_structure[influence]['Open']) & (mono_structure[influence]['Value'] == 8))[0]
        points_speed = []
        for mono in mono_structure[influence][possible_mono_new]:
            moves = self.options_block_three(mono, active_structure)
            for move in moves:
                points_speed.append(move)
        if len(points_speed) != 0:
            return np.unique(points_speed)
        else:
            return False

    @staticmethod
    def second_move(point_structure, point_active_list):
        """Move To Perform Is Second, Random Point Around Opponents Point"""
        op_max_value = max(point_structure[1][np.reshape(point_active_list, (len(point_active_list)))]['Value'])
        op_max_points = np.where(point_structure[1]['Value'] == op_max_value)[0]
        choice = random.choice(op_max_points)
        return choice

    def opening_move(self):
        """Move To Perform If First, Point In Center Of Board"""
        x = int(self.board / 2)
        possible_range = range(x - self.chain + 2, x + self.chain - 2)
        return [random.choice(possible_range), random.choice(possible_range)]

    """######################################################################################################"""
    """######################################################################################################"""
    """######################################################################################################"""
    """######################################################################################################"""
    """######################################################################################################"""

    def check_open(self, monomial_type, mono):
        """Check If Points On Either Edge Of Monomial Or Open, Will Only Return False For Monomials Located On Edge Of Board"""
        first_point = mono[0] - TYPE_CHECK[monomial_type]
        second_point = mono[4] + TYPE_CHECK[monomial_type]
        if first_point[0] in range(self.board) and first_point[1] in range(self.board) and second_point[0] in range(self.board) and second_point[1] in range(self.board):
            return True
        else:
            return False

    def check_won(self):
        result = [self.check_math(0), self.check_math(1)]
        return any(result)

    def check_math(self, player):
        my_max = np.amax(self.Monomials[player]['Value'])
        if my_max == math.pow(MULTIPLIER, self.chain):
            self.winning_mono = self.Monomials[player][(self.Monomials[player]['Value'] == math.pow(MULTIPLIER, self.chain))]
            return True
        return False

    def return_win(self):
        return self.winning_mono['Mono'][0]

    def get_coord(self, point):
        return (point[0] * self.board) + point[1]

    def get_point(self, coord):
        return [int(coord / self.board), coord % self.board]

    def dump_info(self):
        return self.Monomials, self.Points

    def my_point_value(self):
        return self.Points[0]['Point'].tolist(), self.Points[0]['Value'].tolist()

    def op_point_value(self):
        return self.Points[1]['Point'].tolist(), self.Points[1]['Value'].tolist()

    @staticmethod
    def get_opponent(influence):
        return (influence + 1) % 2

    @staticmethod
    def get_count(point_list):
        points, counts = np.unique(point_list, return_counts=True, axis=0)
        counts = np.reshape(counts, (counts.size, 1))
        return np.append(points, counts, 1)
