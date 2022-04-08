import numpy as np
import math
import copy

POINT_MAX = 65535
MULTIPLIER = 2


class PointsV2:
    def __init__(self):
        pass

    def create_point_structure(self, max_size, chain):
        size = max_size
        sides = chain - 1
        total = 0
        core_size = []
        size_list = []
        formations = []
        while size >= chain:
            temp, core_num, size_num, formation = self.generate_formations(max_size, chain, size, range(size - sides - 1, 1 + sides))
            size = size - 1
            total += temp
            size_list.append(size_num)
            core_size.append(core_num)
            formations.append(formation)

        structured_array = np.zeros(total,
                                    dtype=[('Value', 'uint16'),
                                           ('Position', 'uint16'),
                                           ('Monos', 'uint16', chain),
                                           ('Value_Split', 'uint16', chain),
                                           ('Combo_Score', 'uint16'),
                                           ('Leading_Reaction', dict),
                                           ('Live_Monos', range)])
        array_index = 0
        for cs in range(len(core_size)):
            for num in range(core_size[cs]):
                for x in formations[cs][num]:
                    core_position = num + len(x) - 5
                    f_range = range(4 - core_position, len(x) - core_position)
                    mono_array = []
                    for z in range(0, f_range[0]):
                        mono_array.append(0)

                    for y in range(len(x) - 4):
                        mono_array.append(int("".join(x[y:y+5]), 2) * 4)

                    while len(mono_array) != 5:
                        mono_array.append(0)

                    if cs == 0 or cs == 4:
                        structured_array[array_index]['Position'] = core_position
                        structured_array[array_index]['Live_Monos'] = f_range
                        structured_array[array_index]['Monos'] = mono_array
                        array_index += 1

                    t = copy.deepcopy(mono_array)
                    for y in range(3):
                        if y == 0 or y == 2:
                            t[4 - core_position] += 1
                        elif y == 1 or y == 2:
                            t[len(x) - core_position - 1] += 2

                        structured_array[array_index]['Position'] = core_position
                        structured_array[array_index]['Live_Monos'] = f_range
                        structured_array[array_index]['Monos'] = t
                        array_index += 1
        print(structured_array)

    @staticmethod
    def get_core_range(size, min_size):
        return range(size - min_size - 2, 0 + min_size - 1)

    @staticmethod
    def generate_formations(max_size, min_size, size, core_range):
        core_range = list(core_range)
        list_type = [[] for _ in core_range]

        for combination_num in range(int(math.pow(2, size))):
            binary_format = list("{0:b}".format(combination_num).zfill(size))
            for y in range(len(core_range)):
                if binary_format[core_range[y]] != '1':
                    list_type[y].append(binary_format)

        total_combinations = len(list_type[0]) * len(list_type)
        total_combinations = total_combinations * 4 if max_size == size or min_size == size else total_combinations * 3
        return total_combinations, len(list_type), len(list_type[0]), list_type


class MonomialsV2:
    def __init__(self, chain=5):
        self.create_mono_structure(chain)

    def create_mono_structure(self, chain):
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
                structured_array[index]['LM'] = {index:[] for index in range(5) if not bool_format[index] and potential[index] == 0 and value <= math.pow(MULTIPLIER, 3)}
                for lead in list(structured_array[index]['LM']):
                    updated_distance = self.handle_distance(lead, active_index)
                    relative_index = np.where(inactive_index == lead)[0][0]
                    if updated_distance == 3:
                        points = self.get_all(inactive_index, relative_index)
                    else:
                        points = self.get_adjacent(inactive_index, relative_index)
                    structured_array[index]['LM'][lead] = points

        print(structured_array)

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


x = PointsV2()
x.create_point_structure(9, 5)