class Monomials:
    """Class to generate all possible monomials based on board size and winning chain size"""
    def __init__(self, board_size, chain_size):
        self.board_size, self.chain_size = board_size, chain_size
        self.board_points, self.monomial_list, self.type_list, self.count, self.index_list, self.count_split_list = [], [], [], [], [], None
        self.close_update = [[[], [], [], []] for _ in range(self.board_size * self.board_size)]
        self.create_points()
        self.create_monomials()
        self.create_count()
        self.create_monomials_index()
        self.points_index = [x for x in range(self.board_size * self.board_size)]
        self.monomials_index_version = self.create_monomials_index_version()

    def create_points(self):
        """Generate all points based on board size"""
        for x in range(0, self.board_size):
            for y in range(0, self.board_size):
                self.board_points.append([x, y])

    def create_monomials(self):
        """Get all monomials, check each point for 4 type of monomials, if exists append
        Ex:
        For Point [0, 0] for chain of size 5 and board of size 19x19 function will check if points
        [0, 4], [4, 4], [4, 0], and [-4, 4] exist on the board,
        This would lead to monomials:
        [[0, 0], [0, 1], [0, 2], [0, 3], [0, 4]],
        [[0, 0], [1, 1], [2, 2], [3, 3], [4, 4]],
        [[0, 0], [1, 0], [2, 0], [3, 0], [4, 0]]
        being added since each of those point exist in self.board_points unlike point [-4, 4].

        Monomials assigned type based on direction
        Ex:
        X X X X X   X        X                     X
                    X          X                 X
                    X            X             X
                    X              X         X
                    X                X     X
        Type 0      Type 1  Type 2        Type 3

        Once Monomials are found to be valid, points which cause the monomial to be "closed" are found,
        this is done by checking if the points adjacent to either end of the monomial are taken, such as
        for Type 0 _ X X X X X _ the underlined locations will be checked.
        """
        for x in range(self.board_size):
            for y in range(self.board_size):
                h_row = [z for z in range(x, x + self.chain_size)]
                v_row = [z for z in range(y, y + self.chain_size)]
                n_row = [z for z in range(x-self.chain_size + 1, x + 1)]
                h_fill = [x] * self.chain_size
                v_fill = [y] * self.chain_size

                """Checks If Points Are On Board Then If Open/Close"""
                if [x + self.chain_size - 1, y] in self.board_points:
                    self.monomial_list.append(self.stack_lists(h_row, v_fill))
                    self.type_list.append(0)
                    if [x - 1, y] in self.board_points:
                        self.close_update[self.get_coord([x - 1, y])][0].append(len(self.monomial_list) - 1)
                    if [x + self.chain_size, y] in self.board_points:
                        self.close_update[self.get_coord([x + self.chain_size, y])][0].append(len(self.monomial_list) - 1)
                if [x, y + self.chain_size - 1] in self.board_points:
                    self.monomial_list.append(self.stack_lists(h_fill, v_row))
                    self.type_list.append(1)
                    if [x, y - 1] in self.board_points:
                        self.close_update[self.get_coord([x, y - 1])][1].append(len(self.monomial_list) - 1)
                    if [x, y + self.chain_size] in self.board_points:
                        self.close_update[self.get_coord([x, y + self.chain_size])][1].append(len(self.monomial_list) - 1)
                if [x + self.chain_size - 1, y + self.chain_size - 1] in self.board_points:
                    self.monomial_list.append(self.stack_lists(h_row, v_row))
                    self.type_list.append(2)
                    if [x - 1, y - 1] in self.board_points:
                        self.close_update[self.get_coord([x - 1, y - 1])][2].append(len(self.monomial_list) - 1)
                    if [x + self.chain_size, y + self.chain_size] in self.board_points:
                        self.close_update[self.get_coord([x + self.chain_size, y + self.chain_size])][2].append(len(self.monomial_list) - 1)
                if [x - self.chain_size + 1, y + self.chain_size - 1] in self.board_points:
                    self.monomial_list.append(self.stack_lists(n_row[::-1], v_row))
                    self.type_list.append(3)
                    if [x + 1, y - 1] in self.board_points:
                        self.close_update[self.get_coord([x + 1, y - 1])][3].append(len(self.monomial_list) - 1)
                    if [x - self.chain_size, y + self.chain_size] in self.board_points:
                        self.close_update[self.get_coord([x - self.chain_size, y + self.chain_size])][3].append(len(self.monomial_list) - 1)

    def create_monomials_index_version(self):
        """Create Monomial Lists With Point Index Instead Of Point Format
        Ex:
        [[0, 0], [0, 1], [0, 2], [0, 3], [0, 4]] -> [0, 1, 2, 3, 4]
        """
        mono_index_list = [[] for _ in range(len(self.monomial_list))]
        for monomial_index in range(len(self.monomial_list)):
            for point in self.monomial_list[monomial_index]:
                mono_index_list[monomial_index].append((point[0] * self.board_size) + point[1])
        return mono_index_list

    def create_count(self):
        """Get # Of Monomials Each Point Is In Split
        Ex:
        Point [0, 0]: [1, 1, 1, 0]
        Appears Once In Monomials Of Type 0, 1, And 2. Doesn't Appear In Type 3
        """
        count_split_list = [[0 for __ in range(4)] for _ in range(len(self.board_points))]
        self.count = [0] * len(self.board_points)
        for index in range(len(self.monomial_list)):
            for point in self.monomial_list[index]:
                self.count[(point[0] * self.board_size) + point[1]] += 1
                count_split_list[(point[0] * self.board_size) + point[1]][self.type_list[index]] += 1

        self.count_split_list = count_split_list

    def create_monomials_index(self):
        """For Each Point Append The Monomials Index Which They Appear In"""
        index_list = [[] for _ in range(len(self.board_points))]
        for monomial_index in range(len(self.monomial_list)):
            for point in self.monomial_list[monomial_index]:
                index_list[(point[0] * self.board_size) + point[1]].append(monomial_index)
        self.index_list = index_list

    def stack_lists(self, column_one, column_two):
        """Combine two list into a list of points forming a monomial
        Ex:
        [0, 0, 0, 0, 0], [0, 1, 2, 3, 4] -> [[0, 1], [0, 2], [0, 3], [0, 4], [0, 5]]
        """
        return_column = [[]] * self.chain_size
        for x in range(len(column_one)):
            return_column[x] = [column_one[x], column_two[x]]
        return return_column

    def get_monomials(self):
        """Return list of monomials"""
        return self.monomial_list

    def get_types(self):
        """Return list of monomial types, ex: 1, 2, 3, 4"""
        return self.type_list

    def get_count(self):
        """Return # Of Times Points Appear In Monomial"""
        return self.count

    def get_index_list(self):
        """Return List Of Points Length Which Contains Each Monomial They Are In"""
        return self.index_list

    def get_count_split(self):
        """Return # Of Times Points Appear In Monomial Split"""
        return self.count_split_list

    def get_monomials_index_version(self):
        """Return List Of Monomials With Points Saved As Index"""
        return self.monomials_index_version

    def get_close_update(self):
        """Return List Of Whether The Point Is Closed Of Or Not"""
        return self.close_update

    def get_coord(self, point):
        """Get Point Index From Point Format"""
        return (point[0] * self.board_size) + point[1]
