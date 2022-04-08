from lib import Monomials as Mono
import numpy as np
import random
import copy
import math

POINT_MAX = 65535


class ComputerPlayer:
    def __init__(self, board, chain, points):
        """
        Args:
            board (int):  Board length
            chain (int): Winning chain length
            points (int): List of points found on board
        """
        self.boardMonomials = Mono.Monomials(board, chain)
        self.chain, self.board, self.points = chain, board, points
        """Monomial and Point Tables"""
        self.my_mono = self.create_mono_structure()
        self.my_point = self.create_point_structure()
        self.my_combo = self.create_combo_structure()
        self.my_mono_index = self.boardMonomials.get_index_list()
        self.winning_mono = None    #Winning monomial
        self.point_active = None    #List of all points, True or False to indicate taken. Used by both tables
        self.Monomials = None       #List of monomial table
        self.Points = None          #List of point table
        self.Combos = None
        self.reset_variables()
        np.seterr(all='raise')
        self.create_combo_structure()

    def reset_variables(self):
        """Assign variables default values"""
        self.Monomials = [copy.deepcopy(self.my_mono), copy.deepcopy(self.my_mono)]
        self.Points = [copy.deepcopy(self.my_point), copy.deepcopy(self.my_point)]
        self.Combos = [copy.deepcopy(self.my_combo), copy.deepcopy(self.my_combo)]
        self.point_active = np.ones((len(self.my_point)), dtype=bool)

    def load_game(self, moves, player):
        """Load game by replaying moves until correct sate is reached
        Args:
            moves (list): List of points
            player (int): 0: Bot, 1: Opponent

        Points are played by designated player until all moves are played
        """
        self.reset_variables()
        for x in moves:
            if player == 0:
                self.op_move(x)
            else:
                self.my_move(x)
            player = (player + 1) % 2

    def create_mono_structure(self):
        """Monomial Structure
        Column1: Bool value, True: can still be formed. False: can't be formed, at least one point taken by opponent
        Column2: Monomial values list of five points, Ex: [[0, 0], [0, 1], [0, 2], [0, 3], [0, 4]]
        Column3: Value, # of points taken. Ex: 0: no points taken, 3: 3 points taken
        Column4: Type, Type of monomial. More info below.
        Column5: List of bool values, indicate which monomials are taken. Ex. [True, True, True, True, False] would indicate first 4 points of the monomial are taken

        Monomials assigned type based on direction
        Ex:
        X X X X X   X           X                     X
                    X             X                 X
                    X               X             X
                    X                 X         X
                    X                   X     X
        Type 1      Type 2      Type 3        Type 4

        """
        """Column of monomials and there types retrieved from Monomial class"""
        my_mono = self.boardMonomials.get_monomials()
        my_types = self.boardMonomials.get_types()
        structured_array = np.zeros(len(my_mono), dtype=[('Active', 'bool'), ('Mono', 'uint16', (self.chain, 2)), ('Value', 'uint16'), ('Type', 'uint8'), ('Taken', 'bool', self.chain)])
        """All columns assigned variables, columns not assigned remain with default value of 0 or False"""
        structured_array['Value'] = 1
        structured_array['Active'] = True
        structured_array['Mono'] = my_mono
        structured_array['Type'] = my_types
        return structured_array

    def create_point_structure(self):
        """Point Structure
        Column1: Point, stored as list. Ex. [0, 0], [9, 9]
        Column2: Value, stored as int. Based on all monomials which it relies on.

        """
        structured_array = np.zeros(len(self.points), dtype=[('Point', 'uint8', 2), ('Value', 'uint16')])
        structured_array['Value'] = self.boardMonomials.get_count()
        structured_array['Point'] = self.points

        return structured_array

    def create_combo_structure(self):
        """
        Column1: Point, Scored as list. Ex. [0, 0], [9, 9]
        Column2: Value, stored as int. Based on all the monomials which can for a combo
        Column3: Monomial combo tracker. Keeps track of # of monomials which can form a combo
        [0, 0, 0, 0]
        Each index keeps track of a specific type of monomial. Type1, Type2, Type3, or Type4.

        No combo can exist until at least 2 of the values are at least 2.
        Ex: [0, 2, 2, 1]
        """
        structured_array = np.zeros(len(self.points), dtype=[('Point', 'uint8', 2), ('Value', 'uint8'), ("Mono_Amount", 'uint16'), ('Combo_Tracker', 'uint16', 4),  ('MonoID', 'uint16', self.chain * 4)])
        structured_array['Point'] = self.points
        structured_array['MonoID'] = POINT_MAX
        return structured_array

    def my_move(self, point):
        """Updates ables with own move and return if game has been won
        Args:
            point (list): point on board
        Returns:
            bool
        """
        self.update_structure(0, 1, point)
        return self.check_won()

    def op_move(self, point):
        """Update tables with opponents move and return if game has been won
        Args:
            point (list): point on board
        Returns:
            bool
        """
        self.update_structure(1, 0, point)
        return self.check_won()

    def update_structure(self, initiator, follower, point):
        point_index = self.get_coord(point)
        self.point_active[point_index] = False

        for monomial_index in self.my_mono_index[point_index]:
            i_monomial, v_monomial = self.Monomials[initiator][monomial_index], self.Monomials[follower][monomial_index]
            i_active, f_active = i_monomial['Active'], v_monomial['Active']
            self.Monomials[initiator][monomial_index]['Value'] *= 2
            i_score, f_score = i_monomial['Value'], v_monomial['Value']

            if i_active:
                for z in self.Monomials[initiator][monomial_index]['Mono']:
                    t_index = self.get_coord(z)
                    self.Points[initiator][t_index]['Value'] += int(self.Monomials[initiator][monomial_index]['Value'])

            for y in range(self.chain):
                if self.get_coord(self.Monomials[initiator][monomial_index]['Mono'][y]) == point_index:
                    self.Monomials[initiator][monomial_index]['Taken'][y] = True

            if f_active:
                self.Monomials[follower][monomial_index]['Active'] = False
                for y in self.Monomials[follower][monomial_index]['Mono']:
                    t_index = self.get_coord(y)
                    self.Points[follower][t_index]['Value'] -= (self.Monomials[follower][monomial_index]['Value'] * 2) - 1
            self.update_combo_structure(initiator, follower, i_active, f_active, monomial_index, i_score, f_score)

    def update_combo_structure(self, culprit, victim, culprit_bool, victim_bool, monomial_index, culprit_score, victim_score):
        partial_score = math.pow(2, 2)
        full_score = math.pow(2, 3)

        if culprit_bool:
            culprit_monomial = self.Monomials[culprit][monomial_index]
            if culprit_score == partial_score:
                position = np.nonzero(culprit_monomial['Taken'])[0]
                c = False
                if position[1] - position[0] == 2:
                    a, b = get_range(position[0], position[1])
                    c = True
                elif position[1] - position[0] == 1:
                    a, b = get_range(position[0], position[1])
                    c = True
                elif position[1] - position[0] == 3:
                    a, b = 0, 5
                    c = True

                #print(position[1] - position[0])
                #print(culprit_monomial["Mono"][a:b])
                if c:
                    for point in culprit_monomial["Mono"][a:b]:
                        point_index = self.get_coord(point)
                        self.Combos[culprit][point_index]['Combo_Tracker'][self.Monomials[culprit][monomial_index]['Type'] - 1] += 1
                        self.Combos[culprit][point_index]["MonoID"][self.Combos[culprit][point_index]["Mono_Amount"]] = monomial_index
                        self.Combos[culprit][point_index]["Mono_Amount"] += 1
            elif culprit_score == full_score:
                for point in self.Monomials[culprit][monomial_index]["Mono"]:
                    point_index = self.get_coord(point)
                    if monomial_index not in self.Combos[culprit][point_index]['MonoID']:
                        self.Combos[culprit][point_index]['Combo_Tracker'][self.Monomials[culprit][monomial_index]['Type'] - 1] += 1
                        self.Combos[culprit][point_index]["MonoID"][self.Combos[culprit][point_index]["Mono_Amount"]] = monomial_index
                        self.Combos[culprit][point_index]["Mono_Amount"] += 1
        if victim_bool:
            for point in self.Monomials[victim][monomial_index]["Mono"]:
                point_index = self.get_coord(point)
                if monomial_index in self.Combos[victim][point_index]['MonoID']:
                    self.Combos[victim][point_index]['Combo_Tracker'][self.Monomials[victim][monomial_index]['Type'] - 1] -= 1
                    replace_index = np.where(self.Combos[victim][point_index]["MonoID"] == monomial_index)
                    self.Combos[victim][point_index]["MonoID"][replace_index] = self.Combos[victim][point_index]["MonoID"][self.Combos[victim][point_index]["Mono_Amount"]]
                    self.Combos[victim][point_index]["MonoID"][self.Combos[victim][point_index]["Mono_Amount"]] = POINT_MAX
                    self.Combos[victim][point_index]["Mono_Amount"] -= 1
        """
        Use The Monomial, If Score = 2 Check If It Is Dependent
        If IT Is Add
        Else Don't
        If 3
        Check If IT Is Already In THe List
        If It Is Do NOthing
        Else Subtract

        """
        pass


    def get_move(self, player, value):
        """Most common option to get move
        Args:
            player (int): 0: Bot, 1: Opponent
            value (int): Minimum score required from monomial to be included
        Returns:
            point
        1. All possible points obtained from monomials
        2. Points rated by appearance, points which appear multiple times get more importance.
        3. Point chosen based on appearance and score.
        """
        move = self.get_points(player, value)
        move = get_count(move)
        return self.final_choice(move)

    def get_move_three(self, player, value, combos):
        """Altered form of get_move made for monomials of value 3.
        Only return point if monomial guarantees a win, otherwise
        can be blocked and may be ignored

        Args:
            player (int): 0: Bot, 1: Opponent
            value (int): Minimum score required from monomial to be included
            combos (list): List of points which are possible combos
        Returns:
            Move if criteria met, otherwise False
        """
        p_move = self.get_points_harsh(player, value)
        if len(p_move) != 0:
            if not isinstance(combos, bool) and combos in p_move:
                return combos
            return self.final_choice(get_count(p_move))
        else:
            return False

    def calc_move(self):
        """Decide which move to take"""
        """Get max value of monomials"""
        my_max_m = max(self.Monomials[0][self.Monomials[0]['Active']]['Value'])
        op_max_m = max(self.Monomials[1][self.Monomials[1]['Active']]['Value'])

        #print(op_max_m, math.pow(2, self.chain - 1))
        zzz = np.where(self.Combos[0]["Mono_Amount"] >= 4)[0]
        #for x in zzz:
        #    print(convert_point(self.Combos[0][x]["Point"]))
        #    blah = np.where(self.Combos[0][x]["Combo_Tracker"] >= 2)[0]
        #    print(blah)
        #print(zzz)
        """Get Combo Move if there exists one else set to False"""
        combo_move_bot = self.case_combo_v2(0)
        combo_move_op = self.case_combo_v2(1)

        """If my_max_m == 4 can win, take winning move. If my_max_m == 0 first turn, take move near opponent. If_max_op == 4 opponent has monomial of size 4, block"""
        if my_max_m == math.pow(2, self.chain - 1):
            return self.get_move(0, my_max_m)
        if my_max_m == 1 or op_max_m == math.pow(2, self.chain - 1):
            return self.get_move(1, op_max_m)

        """If no winning move check if monomials of size 3 that can not be blocked exist"""
        if my_max_m == math.pow(2, self.chain - 2):
            move = self.get_move_three(0, my_max_m, combo_move_bot)
            if not isinstance(move, bool):
                return move
        if op_max_m == math.pow(2, self.chain - 2):
            move = self.get_move_three(1, op_max_m, combo_move_op)
            if not isinstance(move, bool):
                return move

        """Check if guaranteed combos exist"""
        if not isinstance(combo_move_bot, bool):
            return combo_move_bot
        if not isinstance(combo_move_op, bool):
            return combo_move_op

        """Check if monomial of size 3 exists, if exists is blockable but safe move"""
        #if my_max_m == 3:
        #    return self.get_move(0, my_max_m)

        """Last Resort Move, try to choose a good point."""
        p_move = self.get_best(0)
        if not isinstance(p_move, bool):
            return p_move
        p_move = self.get_points(0, my_max_m)
        p_move = get_count(p_move)
        return self.final_choice(p_move)

    def get_points(self, influence, goal):
        """
        Args:
            influence (int): 0 or 1. Index to determine which table to look int
            goal (int): Point goal, minimum value of monomial in order to be included

        Returns:
            List of all possible points which meet conditions, can include duplicates
        """
        my_list = []
        """For each monomial which meets the criteria check the points found to see if active, if active append"""
        for x in self.Monomials[influence][(self.Monomials[influence]['Value'] == goal) & (self.Monomials[influence]['Active'])]:
            for y in x['Mono'].tolist():
                if self.point_active[self.get_coord(y)]:
                    my_list.append(y)
        return my_list

    def get_points_harsh(self, influence, goal):
        """
        Altered version of get_points, points must appear a minimum of 2 times
        Used to detect chains of 3 which are blockable in order to ignore them
        and focus on better options.
        """

        """!!!REWORK!!!"""
        my_list = []
        my_types = []
        final_list = []
        for x in self.Monomials[influence][(self.Monomials[influence]['Value'] == goal) & (self.Monomials[influence]['Active'])]:
            for y in x['Mono'].tolist():
                if self.point_active[self.get_coord(y)]:
                    my_list.append(self.get_coord(y))
                    my_types.append(x['Type'])

        for x in np.asarray(np.unique(my_list)):
            index = np.asarray(np.where(my_list == x))[0]
            points, counts = np.unique(np.asarray(my_types)[index], return_counts=True, axis=0)
            for y in counts:
                if y >= 2:
                    for z in range(y):
                        final_list.append(self.get_point(x))

        return final_list

    def final_choice(self, my_list):
        """Get best point by finding best option
        Args:
            my_list (np array): List of points and their appearances
            Column 1: x coordinate
            Column 2: y coordinate
            Column 3: # appearances
        """
        """Get only the points which appear the most amount of times"""
        most_common = np.amax(my_list[:, 2])
        most_common = my_list[:, 2] == most_common
        most_common = my_list[most_common]
        most_common = most_common[:, [0, 1]].tolist()
        decision = []

        """For each point get the value they hold"""
        for x in most_common:
            decision.append(self.Points[0][self.get_coord(x)]['Value'])

        """If Value is equal to max set to true in order to minimize options again"""
        for x in range(0, len(decision)):
            if decision[x] == max(decision):
                decision[x] = True
            else:
                decision[x] = False
        most_common = np.array(most_common)

        """Return most common point with highest value, if multiple points share appearance and point choose randomly"""
        return random.choice(most_common[decision])

    def get_best(self, player):
        """Function to get points of high value
        Args:
            player (int): 0: Self (bot), 1: Opponent
        """
        possible_points = self.Points[player][(self.point_active & (self.Points[player]['Value'] >= 24))]
        if len(possible_points) >= 1:
            possible_points = np.flip(np.sort(possible_points, order='Value'), 0)
            return possible_points[0]['Point']
        else:
            return False

    def case_combo_v2(self, player):
        """Search board for combos, if found return
        Args:
            player (int): 0: Self (bot), 1: Opponent
        Combos = Combination of 2 chains that form a guaranteed win for player who forms them

        Note: Only one combo returned, if more than 1 combo is found win/lose is already guaranteed
        """
        point_list, type_list, result_list = [], [], []

        for x in self.Monomials[player][((self.Monomials[player]['Active']) & (self.Monomials[player]['Value'] >= 4))]:
            if x['Value'] == 2:
                """If only 2 points taken only get the points which can take combo, more info in get_range"""
                position = np.nonzero(x['Taken'])[0]
                if position[1] - position[0] == 2:
                    a, b = get_range(position[0], position[1])
                elif position[1] - position[0] == 1:
                    a, b = get_range(position[0], position[1])
                elif position[1] - position[0] == 3:
                    a, b = 0, 5
                else:
                    break
            else:
                """If 3 points taken all points can be used to form combo, use all points"""
                a, b = 0, 5

            possible_points = x['Taken'][a:b]
            for y in range(0, len(possible_points)):
                if not possible_points[y]:
                    """For each point, if not taken append list and type to list"""
                    point_list.append(self.get_coord(x['Mono'][y + a].tolist()))
                    type_list.append(x['Type'])

        for x in np.asarray(np.unique(point_list)):
            index = np.asarray(np.where(point_list == x))[0]
            if len(np.unique(np.asarray(type_list)[index])) >= 2:
                """If point more than one monomial of unique type (1, 2, 3, 4)"""
                points, counts = np.unique(np.asarray(type_list)[index], return_counts=True, axis=0)
                co = np.asarray(np.where(counts > 1))[0]
                if len(co) >= 2:
                    """If 2 monomials of 2 unique types are present combo found, append"""
                    result_list.append(x)

        if len(result_list) > 0:
            return self.get_point(result_list[0])
        return False

    def opening_move(self):
        """Return opening move which consists of center most point"""
        x = int(self.board / 2)
        return [x, x]

    def check_won(self):
        """Return if any player has won"""
        result = [self.check_math(0), self.check_math(1)]
        return any(result)

    def check_math(self, player):
        """Return if player has winning move, if so save winning monomial
        Args:
            player (int): 0: Self (bot), 1: Opponent
        """
        my_max = np.amax(self.Monomials[player]['Value'])
        if my_max == math.pow(2, self.chain):
            self.winning_mono = self.Monomials[player][(self.Monomials[player]['Value'] == math.pow(2, self.chain))]
            return True
        return False

    def return_win(self):
        """Return monomial containing winning chain"""
        return self.winning_mono['Mono'][0]

    def get_coord(self, point):
        """Return coord, Ex: [0, 0]: 0, [0, 1]: 1, [1, 0]: 18
        Args:
            point ([x, x]): Point on board
        """
        return (point[0] * self.board) + point[1]

    def get_point(self, coord):
        """Return point, Ex: 0: [0, 0], 1: [0, 1], 18: [1, 0]
        Args:
            coord (int): Index used to identify point, 0 - (self.board)^2 - 1
        """
        return [int(coord / self.board), coord % self.board]

    def dump_info(self):
        """Return Monomial and Point tables"""
        return self.Monomials, self.Points

    def my_point_value(self):
        """Return score values of self"""
        return self.Points[0]['Point'].tolist(), self.Points[0]['Value'].tolist()

    def op_point_value(self):
        """Return score values of opponent"""
        return self.Points[1]['Point'].tolist(), self.Points[1]['Value'].tolist()

    def print_taken_points(self):
        """Print All Taken Points"""
        my_list = copy.deepcopy(self.Points[1][np.invert(self.point_active)]['Point'])
        for x in range(len(my_list)):
            print(convert_point(my_list[x]))

    def print_combo_structure(self, index):
        print(self.Combos[index][self.point_active])


def get_count(point_list):
    """Return unique points and there count
    Args:
        point_list (list points): List of points, can have repeating values

    Ex
    [[0, 0], [2, 2], [0, 0], [0, 1]]
    Would Return
    [[0, 0, 2]
     [2, 2, 1]
     [0, 0, 1]]
    Column1: X Variable, Column2: Y Variable, Column3: Appearance of point
    """

    points, counts = np.unique(point_list, return_counts=True, axis=0)
    counts = np.reshape(counts, (counts.size, 1))
    return np.append(points, counts, 1)


def convert_point(point):
    """Convert point from [#, #] format to display format
    Args:
        point ([x, x]): Point on board

        Ex
        [0, 0] -> A19
        [0, 18] -> A1
    """
    return chr(ord("A") + point[0]) + str(19-point[1])


def convert_monomials(point_list):
    """Convert all points inside the monomials into display format
    Args:
        point_list (Monomial): A monomial containing 5 points
    """

    points = ""
    for x in point_list:
        points += convert_point(x)
        points += "  "
    return points


def get_range(x1, x2):
    """Return range of points monomial should use, used to determine which points used for combo detection.
    Args:
        x1 (int): Index of first point
        x2 (int): Index of second point

    Ex:
    X: Taken
    O: Free
    [X, O, X, O, O] x1 = 0, x2 = 2, return 0, 4     fifth point can't be used to form a combo
    [O, O, X, X, O] x1 = 2, x2 = 3, return 0, 5     all points can be used to form a combo
    [O, O, O, X, X] x1 = 3, x2 = 4, return 1, 5     first point can't be used to form a combo
    """

    s1 = 1 if x2 == 4 else 0
    s2 = 4 if x1 == 0 else 5
    return s1, s2
