from lib import Monomials as Mono
import numpy as np
import copy
import math

POINT_MAX = 65535
OFFSETS = [0, 1024, 1536, 1856, 2048]
SUB_OFFSETS = [0, 128, 64, 32, 16]
MULTIPLIER = 2
TYPE_ADJACENT = [19, 1, 20, 18]


class StructureCreator:
    def __init__(self, board, chain, points, point_max):
        self.dead_value = point_max
        self.boardMonomials = Mono.Monomials(board, chain)
        self.chain, self.board, self.points, self.winning_mono = chain, board, points, None
        self.dict_type = {}
        self.close_updates = self.boardMonomials.get_close_update()
        self.my_mono = self.create_mono_structure()
        self.my_mono_index = self.boardMonomials.get_index_list()
        self.my_state = self.create_mono_state_structure(chain)
        self.monomials = self.boardMonomials.get_monomials_index_version()

        self.patch = {}
        self.patcher = []
        self.point_state_struct = self.create_point_state_structure(5)
        self.my_point = self.create_point_structure()
        self.point_active = np.ones((len(self.my_point), 1), dtype=bool)

        self.dict_pow_value = self.point_linker(self.dict_type)

    def point_linker(self, type_association_dict):
        # Assigns an integer value to all adjacent points
        # Values solely unique for points based on monomial type
        # Ex: P[X, Y]: (P[X+4, Y]: 0, [X+3, Y]: 1, [X+2, Y]: 2, [X+1, Y]: 3, [X-1, Y]: 5, [X-2, Y]: 6,[X-3, Y]: 7, [X-4, Y]: 8)
        return {point_index: {sub_point: self.distance_finder(point_index, sub_point, type_association_dict[point_index][sub_point]) for sub_point in type_association_dict[point_index]} for point_index in type_association_dict}

    @staticmethod
    def distance_finder(point_index, adjacent_point_index, mono_type):
        return 4 + (point_index - adjacent_point_index) // TYPE_ADJACENT[mono_type]

    def return_type_association(self):
        return self.dict_type

    def return_pow_association(self):
        return self.dict_pow_value

    def return_basics(self):
        return self.dict_type, self.dict_pow_value

    def create_mono_structure(self):
        # Monomial Structure
        # Active: Monomial still exists in current state of game
        # Mono: Points contained within monomial
        # Type: Monomial direction type
        # Index: Current state monomial resides in
        # ToDo: 'Type' Column Can Potentially Be Removed, Rely On Point Type Assocation Instead
        my_types = self.boardMonomials.get_types()
        structured_array = np.ones(self.get_mono_amount(),
                                   dtype=[('Active', 'bool'),
                                          ('Mono', 'uint16', self.chain),
                                          ('Type', 'uint8'),
                                          ('Index', 'int8')])

        structured_array['Mono'] = self.boardMonomials.get_monomials_index_version()
        structured_array['Type'] = my_types

        for monomial_row in structured_array:
            if monomial_row['Type'] != 3:
                left, right = monomial_row['Mono'][0], monomial_row['Mono'][4]
            else:
                right, left = monomial_row['Mono'][0], monomial_row['Mono'][4]
            monomial_row['Index'] = self.check_open(monomial_row['Type'], left, right)
        return structured_array

    def create_point_structure(self):
        # Point Structure
        # State_ID: The 4 states the point resides in, each point represents one of its monomial types
        structured_array = np.zeros(self.get_point_amount(), dtype=[('State_ID', 'uint16', 4)])
        mono_point_association = self.get_mono_point_association()

        for point_index in range(361):
            self.dict_type[point_index] = {}
            for mono_type in range(4):
                index = np.where(mono_point_association[point_index][mono_type] != POINT_MAX)[0]
                if len(index) != 0:
                    mono_one = self.my_mono[mono_point_association[point_index][mono_type][index[0]]]
                    mono_two = self.my_mono[mono_point_association[point_index][mono_type][index[len(index)-1]]]
                    state = self.re_create_point_state(self.my_state[mono_one['Index']]['Open'], self.my_state[mono_two['Index']]['Open'], 4 + len(index), index[0])
                    structured_array[point_index]['State_ID'][mono_type] = state

                    for sub_point_index in set(mono_one['Mono']) | set(mono_two['Mono']):
                        self.dict_type[point_index][sub_point_index] = mono_type
                else:
                    structured_array[point_index]['State_ID'][mono_type] = POINT_MAX

        return structured_array

    def get_mono_point_association(self):
        # Create a numpy array which contains all associated monomials for each point
        mono_point_association = np.full((self.get_point_amount(), 4, self.chain), POINT_MAX, dtype='uint16')
        for monomial_index in range(len(self.monomials)):
            for point_index in self.monomials[monomial_index]:
                mono_type = self.my_mono[monomial_index]['Type']
                replace_index = [x for x in range(self.chain) if self.monomials[monomial_index][x] == point_index][0]
                replace_index = 4 - replace_index if mono_type == 3 else replace_index
                mono_point_association[point_index][mono_type][4 - replace_index] = monomial_index

        return mono_point_association

    def re_create_point_state(self, state_1, state_2, size, r):
        position = 4 - r
        shape = "0" * size
        offset = state_1 + state_2 if state_2 != state_1 else state_2
        return self.get_point_state_index(size, position, shape, offset)

    def create_mono_state_structure(self, chain):
        mono_size = int(math.pow(MULTIPLIER, chain))
        structured_array = np.zeros(mono_size * 4,
                                    dtype=[('Taken', 'bool', chain),
                                           ('Potential', 'uint16', chain),
                                           ('Distance', 'uint8'),
                                           ('Open', 'uint8'),
                                           ('Value', 'uint8'),
                                           ('Tier', 'uint8'),
                                           ('LM0', 'bool', chain),
                                           ('LM1', 'bool', chain),
                                           ('LM2', 'bool', chain),
                                           ('LM3', 'bool', chain),
                                           ('LM', dict)])

        for mono_state in range(mono_size):
            binary_format = "{0:b}".format(mono_state).zfill(5)
            bool_format = [True if int(bit) else False for bit in binary_format]
            distance = self.find_distance(bool_format)

            for mono_type in range(4):
                index = mono_state * 4 + mono_type
                value = math.pow(2, len(np.where(bool_format)[0]))
                potential = self.potential_ranker(value, bool_format, mono_type, distance)
                structured_array[index]['Taken'] = bool_format
                structured_array[index]['Distance'] = distance
                structured_array[index]['Open'] = mono_type
                structured_array[index]['Value'] = value
                structured_array[index]['Potential'] = potential
                structured_array[index]['Tier'] = np.min(potential)

                for potential_index in range(5):
                    if not bool_format[potential_index]:
                        structured_array[index][6+potential[potential_index]][potential_index] = True

                active_index = np.where(bool_format)[0]
                inactive_index = np.arange(5)[np.where(np.invert(bool_format))[0]]
                structured_array[index]['LM'] = {index: [] for index in range(5) if not bool_format[index] and potential[index] == 0 and value <= math.pow(MULTIPLIER, 3)}

                for lead in list(structured_array[index]['LM']):
                    updated_distance = self.handle_distance(lead, active_index)
                    relative_index = np.where(inactive_index == lead)[0][0]
                    if updated_distance == 3:
                        points = self.get_all(inactive_index, relative_index)
                    else:
                        points = self.get_adjacent(inactive_index, relative_index)
                    structured_array[index]['LM'][lead] = points
        return structured_array

    @staticmethod
    def find_distance(bool_list):
        index = np.where(bool_list)[0]
        return 0 if 2 > len(index) else index[len(index) - 1] - index[0] + 1

    @staticmethod
    def handle_distance(point_location, active_location):
        distance_a = math.fabs(point_location - active_location[0])
        distance_b = math.fabs(point_location - active_location[1])
        return distance_a if distance_a > distance_b else distance_b

    @staticmethod
    def get_adjacent(point_list, index_location):
        return_list = []
        if index_location - 1 >= 0:
            return_list.append(point_list[index_location - 1])
        if index_location + 1 < len(point_list):
            return_list.append(point_list[index_location + 1])
        return return_list

    @staticmethod
    def get_all(point_list, index_location):
        point_list = point_list.tolist()
        return_list = copy.deepcopy(point_list)
        del return_list[index_location]
        return return_list

    @staticmethod
    def potential_ranker(value, bool_format, open_type, distance):
        blocked_score = 3 - len(np.where(bool_format)[0])
        if value >= math.pow(2, 3):
            return [0 for _ in bool_format]
        elif open_type == 3 or distance == 5 or (open_type == 1 and bool_format[0]) or (open_type == 2 and bool_format[4]):
            return [blocked_score for _ in bool_format]
        else:
            base_score = [2 for _ in bool_format]
            for taken_index in np.where(bool_format)[0]:
                update_index = range((0 if taken_index != 4 else 1), (5 if taken_index != 0 else 4))
                for val in update_index:
                    base_score[val] -= 1

            if open_type == 1:
                base_score[0] = blocked_score
            if open_type == 2:
                base_score[4] = blocked_score

            return base_score

    def get_mono_amount(self):
        return int((((self.board - (self.chain - 1)) * self.board) + math.pow((self.board - (self.chain - 1)), 2)) * 2)

    def get_point_amount(self):
        return self.board * self.board

    def check_open(self, monomial_type, start_point, end_point):
        val = 0
        # 0 = Top, 3 = Left, 1 = Right, 2 = Bot
        if monomial_type == 2:
            if self.check_blocked(0, start_point) or self.check_blocked(1, start_point):
                val += 1
            if self.check_blocked(3, end_point) or self.check_blocked(2, end_point):
                val += 2
        elif monomial_type == 3:
            if self.check_blocked(0, start_point) or self.check_blocked(3, start_point):
                val += 2
            if self.check_blocked(1, end_point) or self.check_blocked(2, end_point):
                val += 1
        else:
            if self.check_blocked(0 + monomial_type, start_point):
                val += 1
            if self.check_blocked(2 + monomial_type, end_point):
                val += 2

        return val

    def check_blocked(self, direction_type, point_index):
        if direction_type == 0:
            return self.board > point_index
        elif direction_type == 1:
            return point_index % self.board == 0
        elif direction_type == 2:
            return point_index >= (self.board * (self.board - 1))
        elif direction_type == 3:
            return (point_index + 1) % 19 == 0

    def return_mono_index(self):
        return self.my_mono_index

    def return_close_updates(self):
        return self.close_updates

    def return_mono(self):
        return np.copy(self.my_mono)

    def return_points(self):
        return np.copy(self.my_point)

    def return_state(self):
        return np.copy(self.my_state)

    def return_state_point(self):
        return np.copy(self.point_state_struct)

    def create_point_state_structure(self, chain_size):
        struct_size = self.return_struct_size(chain_size, chain_size)
        structured_array = np.zeros(struct_size,
                                    dtype=[('Value', 'uint16'),
                                           ('Position', 'uint16'),
                                           ('Monos', 'uint16', chain_size),
                                           ('Value_Split', 'uint16', chain_size),
                                           ('Combo_Score', 'uint16'),
                                           ('Leading_Reaction', list),
                                           ('Next_Type', dict),
                                           ('My_Type', dict),
                                           ('Live_Monos', 'uint16', 2)])
        formation_length = (chain_size * 2) - 1

        while formation_length != chain_size-1:
            formations = self.return_mono_formations(formation_length, 5)
            current_index = 4
            for core_type in formations:
                for sub_formation in core_type:
                    monos = self.create_mono_list(current_index, sub_formation)
                    self.handle_insertion(structured_array, len(sub_formation), current_index, sub_formation, monos)
                current_index -= 1
            formation_length -= 1

        for row_index in range(struct_size):
            self.patch[row_index] = []
            row = structured_array[row_index]
            row['Leading_Reaction'] = []
            for index in range(5):
                if row['Monos'][index] != POINT_MAX:
                    row['Value_Split'][index] = self.my_state[row['Monos'][index]]['Value']
            row['Value'] = np.sum(row['Value_Split'])
            row['Combo_Score'] = self.get_min_combo_score(row['Monos'])

        for row_index in range(struct_size):
            row = structured_array[row_index]
            if row['Combo_Score'] == 0:
                row['Leading_Reaction'] = self.leading_finder('LM', row)
            elif row['Combo_Score'] == 1:
                row['Leading_Reaction'] = self.leading_minus('LM1', row)
        return structured_array

    def leading_minus(self, column_index, row):
        rr = []
        offset = 0
        for mono_state in row['Monos'][row['Live_Monos'][0]:row['Live_Monos'][-1]]:
            location = np.where(self.my_state[mono_state][column_index])[0]
            position = 4 - (row['Live_Monos'][0] + offset)
            if position in location:
                potential = self.my_state[mono_state]['Potential']
                temp_range = range(0 if position != 4 else 1, 5 if position != 0 else 4)
                for x in temp_range:
                    if x in location and potential[x] == 1 and x != position:
                        rr.append(x - position)
            offset += 1

        return list(set(rr))

    def leading_finder(self, column_index, row):
        offset = 0
        return_list = []
        for mono_state in row['Monos'][row['Live_Monos'][0]:row['Live_Monos'][-1]]:
            position = row['Live_Monos'][0] + offset
            if 4 - position in self.my_state[mono_state][column_index]:
                for z in self.my_state[mono_state][column_index][4 - position]:
                    return_list.append(z - (4 - position))
            offset += 1
        return list(set(return_list))

    @staticmethod
    def assign_basics(row, position, monos, live_range):
        # Assign simple information
        row['Position'] = position
        row['Monos'] = monos
        row['Live_Monos'][0] = live_range[0]
        row['Live_Monos'][1] = live_range[-1]

    def alt_insert(self, open_type, live_monos, offset, structure, length, position, shape, monos):
        # Calculate the row index for the provided information and fill in information
        if open_type == 1:
            monos[live_monos[0]] += 1
        elif open_type == 2:
            monos[live_monos[-1]] += 2
        elif open_type == 3:
            monos[live_monos[0]] += 1
            monos[live_monos[-1]] += 2

        row_index = self.get_point_state_index(length, position, shape, open_type)
        structure[row_index]['Next_Type'] = self.calc_transition_opponent(shape, position, length, open_type, row_index)
        structure[row_index]['My_Type'] = self.calc_transition_self(length, position, shape, offset, row_index)
        self.assign_basics(structure[row_index], position, monos, range(4 - position, (4 - position) + len(shape) - 3))

    def calc_transition_self(self, length, position, shape, offset, debug):
        # Find the state the current state can convert to if a point is taken by itself
        return_dict = {}
        points = list(range(length))

        relative_index = position + 4
        current_index = 0
        for val in points:
            if val != position and shape[current_index] != "1":
                temp_shape = copy.deepcopy(shape)
                temp_shape = list(temp_shape)
                temp_shape[current_index] = "1"
                temp_shape = "".join(temp_shape)
                return_dict[relative_index] = self.get_point_state_index(length, position, temp_shape, offset)
            current_index += 1
            relative_index -= 1

        return return_dict

    def calc_transition_opponent(self, shape, position, length, open_type, row_index):
        # Find the states the current state can convert to if points are taken by opponent
        nums = list(range(length))
        transition_dict = {}
        index = position + 4
        for val in nums:
            if val != position:
                revised_shape = copy.deepcopy(shape)
                if val < position:
                    revised_shape = revised_shape[val+1:]
                    revised_position = position - (val + 1)
                    side = True
                else:
                    revised_shape = revised_shape[:val]
                    revised_position = position
                    side = False

                if len(revised_shape) >= 5:
                    revised_open_type = self.get_revised_type(open_type, side)
                    transition_dict[index] = self.get_point_state_index(len(revised_shape), revised_position, revised_shape, revised_open_type)
                else:
                    transition_dict[index] = POINT_MAX
            index -= 1

        return transition_dict

    @staticmethod
    def get_revised_type(open_type, side_taken):
        # Get revised open type based on which side got blocked off
        if open_type == 0:
            return 1 if side_taken else 2
        elif open_type == 1:
            return 1 if side_taken else 3
        elif open_type == 2:
            return 3 if side_taken else 2
        else:
            return open_type

    def handle_insertion(self, structure, length, position, shape, monos):
        # Handle insertion into state table, based on position and shape multiple variants exist based on open type
        live_monos = np.where(monos != POINT_MAX)[0]
        if len(live_monos) == 0:
            pass
        elif live_monos[0] != 0 and live_monos[-1] != 4:
            self.alt_insert(3, live_monos, 0, structure, length, position, shape, copy.deepcopy(monos))
        elif live_monos[0] != 0:
            self.alt_insert(1, live_monos, 0, structure, length, position, shape, copy.deepcopy(monos))
            self.alt_insert(3, live_monos, 1, structure, length, position, shape, copy.deepcopy(monos))
        elif live_monos[-1] != 4:
            self.alt_insert(2, live_monos, 0, structure, length, position, shape, copy.deepcopy(monos))
            self.alt_insert(3, live_monos, 1, structure, length, position, shape, copy.deepcopy(monos))
        else:
            self.alt_insert(0, live_monos, 0, structure, length, position, shape, copy.deepcopy(monos))
            self.alt_insert(1, live_monos, 1, structure, length, position, shape, copy.deepcopy(monos))
            self.alt_insert(2, live_monos, 2, structure, length, position, shape, copy.deepcopy(monos))
            self.alt_insert(3, live_monos, 3, structure, length, position, shape, copy.deepcopy(monos))

    @staticmethod
    def create_mono_list(current_index, sub_formation):
        # Create monomial list for point state table based on monomial formation
        monos = []
        for _ in range(4 - current_index):
            monos.append(POINT_MAX)
        for x in range(len(sub_formation) - 4):
            monos.append((int(sub_formation[x:x + 5], 2)) * 4)
        for _ in range(5 - len(monos)):
            monos.append(POINT_MAX)
        return np.asarray(monos)

    @staticmethod
    def get_offset(open_type, length, position):
        return open_type if length == 9 else (0 if position != 4 and position != length - 5 else (1 if open_type == 3 else 0))

    @staticmethod
    def remove_and_get_int_from_binary(shape, position):
        # Return bit from binary string then returns integer value
        del shape[position]
        return int("".join(shape), 2)

    def get_point_state_index(self, length, position, shape, open_type):
        # Return index using OFFSET + (SUB_OFFSET * MULTIPLY VALUE) + OPEN_TYPE_OFFSET
        sub_offset = SUB_OFFSETS[9 - length] * (0 if position == length - 5 else (position - (length - 5)) + 1)
        open_type_offset = self.get_offset(open_type, length, position)
        binary_val = self.remove_and_get_int_from_binary(list(shape), position)
        return OFFSETS[9 - length] + sub_offset + binary_val * (4 if length == 9 else (2 if sub_offset == 0 or position == 4 else 1)) + open_type_offset

    @staticmethod
    def return_mono_formations(monomial_size, chain_size):
        # Return all possible monomial combinations by converting integers to binary strings
        core_range = range(monomial_size - 5, chain_size)
        core_lists = [[] for _ in core_range]

        for mono_state in range(int(math.pow(2, monomial_size-1))):
            for index in core_range:
                list_copy = copy.deepcopy(list("{0:b}".format(mono_state).zfill(monomial_size-1)))
                list_copy.insert(index, "0")
                core_lists[4 - index].append("".join(list_copy))

        return core_lists

    def return_struct_size(self, chain_size, current_size):
        # Recursively return the size of the point state structure based on monomial size
        if current_size == 0:
            return 0
        elif chain_size == current_size:
            return int(math.pow(2, chain_size + 3) * 4 + self.return_struct_size(chain_size, current_size-1))
        else:
            return math.pow(2, chain_size + (3 - (chain_size - current_size))) * (4 + 4 - current_size) + self.return_struct_size(chain_size, current_size-1)

    def get_min_combo_score(self, monos):
        # Get the min combo value from the Monomial state table based on list
        return np.min([self.my_state[monos[mono_index]]['Potential'][4-mono_index] for mono_index in range(5) if monos[mono_index] != POINT_MAX])
