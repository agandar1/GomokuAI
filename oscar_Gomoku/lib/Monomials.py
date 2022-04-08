class Monomials:
    """Class to generate all possible monomials based on board size and winning chain size"""
    def __init__(self, board_size, chain_size):
        self.board_size, self.chain_size = board_size, chain_size
        self.board_points, self.monomial_list, self.type_list, self.count, self.index_list, self.count_split_list = [], [], [], [], [], None
        self.close_update_left = [[] for _ in range(self.board_size * self.board_size)]
        self.close_update_right = [[] for _ in range(self.board_size * self.board_size)]
        self.create_points()
        self.create_monomials()
        self.create_count()
        self.create_monomials_index()
        self.points_index = [x for x in range(self.board_size * self.board_size)]

    def create_points(self):
        """Generate all points based on bogpard size"""
        for x in range(0, self.board_size):
            for y in range(0, self.board_size):
                self.board_points.append([y, x])

    def c_function(self, row, col, m_type, x, y):
        self.monomial_list.append(self.stack_lists(row, col))
        self.type_list.append(m_type)
        self.adjacent_finder(x, y, m_type)

    def adjacent_finder(self, x,  y, m_type):
        if m_type == 0:
            mod_point_a = [x - 1, y]
            mod_point_b = [x + self.chain_size, y]
        elif m_type == 1:
            mod_point_a = [x, y - 1]
            mod_point_b = [x, y + self.chain_size]
        elif m_type == 2:
            mod_point_a = [x - 1, y - 1]
            mod_point_b = [x + self.chain_size, y + self.chain_size]
        elif m_type == 3:
            mod_point_a = [x + 1, y - 1]
            mod_point_b = [x - self.chain_size, y + self.chain_size]
        else:
            print("Error, Monomial Typing")
            return

        if mod_point_a in self.board_points:
            self.close_update_left[self.get_coord(mod_point_a)].append(len(self.monomial_list)-1)
        if mod_point_b in self.board_points:
            self.close_update_right[self.get_coord(mod_point_b)].append(len(self.monomial_list)-1)

    def create_monomials(self):
        for x in range(self.board_size):
            for y in range(self.board_size):
                h_row = [z for z in range(x, x + self.chain_size)]
                v_row = [z for z in range(y, y + self.chain_size)]
                n_row = [z for z in range(x-self.chain_size + 1, x + 1)]
                h_fill = [x] * self.chain_size
                v_fill = [y] * self.chain_size

                """Checks If Points Are On Board Then If Open/Close"""
                if [x + self.chain_size - 1, y] in self.board_points:
                    self.c_function(h_row, v_fill, 0, x, y)
                if [x, y + self.chain_size - 1] in self.board_points:
                    self.c_function(h_fill, v_row, 1, x, y)
                if [x + self.chain_size - 1, y + self.chain_size - 1] in self.board_points:
                    self.c_function(h_row, v_row, 2, x, y)
                if [x - self.chain_size + 1, y + self.chain_size - 1] in self.board_points:
                    self.c_function(n_row[::-1], v_row, 3, x, y)


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
        mono_index_list = [[] for _ in range(len(self.monomial_list))]
        for monomial_index in range(len(self.monomial_list)):
            for point in self.monomial_list[monomial_index]:
                mono_index_list[monomial_index].append((point[0] * self.board_size) + point[1])
        return mono_index_list

    def get_close_update(self):
        return [self.close_update_left, self.close_update_right]

    def get_coord(self, point):
        """Get Point Index From Point Format, Board Flipped In Monomial Creation!"""
        return point[1] + (point[0] * self.board_size)
