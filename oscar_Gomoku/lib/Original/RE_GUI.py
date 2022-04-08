import tkinter as tk
from tkinter import ttk
from lib import BotV2 as Bot
from lib import BotV4 as BotV3
from lib import BotV5
import string
import copy
import time
import json

BOARD_STYLES = "Files/Styles.json"
GUI_IMAGES = "Images/"
GAME_SAVES = "Games/"
ICON = "Black_Block.ico"

WINDOW_WIDTH = 1300
WINDOW_HEIGHT = 1000
ORIGINAL_POINTS = True
TESTING = False
STATS = False


class GomokuGUI(tk.Tk):
    def __init__(self, board_rows=19, chain_length=5, title="Gomoku"):
        """
        Args:
            board_rows (int): Number of desired grid locations per row.
            chain_length (int): Number of stones needed to form a winning chain.
            title (str): Title found on GUI.

        By default all variables set for Gomoku match of size 19x19
        """
        super().__init__()
        self.temp_var = ""

        self.rows, self.chain, self.offset = board_rows, chain_length, WINDOW_WIDTH - WINDOW_HEIGHT
        self.start_x = int(WINDOW_HEIGHT / 20)
        self.end_x = WINDOW_HEIGHT - self.start_x
        self.tile_length = int((WINDOW_HEIGHT - self.start_x * 2) / board_rows)
        self.style_dictionary = load_style()

        self.set_window_size(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.set_window_title(title)
        self.timer = [None, None]
        self.log = None
        self.score_fill = None
        self.master_frame = tk.Frame(self, width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
        self.frame_control = tk.Frame(self.master_frame, width=self.offset, height=WINDOW_HEIGHT)
        self.frame_game = tk.Frame(self.master_frame, width=WINDOW_HEIGHT, height=WINDOW_HEIGHT)
        self.frame_time = tk.Frame(self.frame_control, width=self.offset, height=int(WINDOW_HEIGHT/5))
        self.master_frame.pack()
        self.frame_control.pack(side=tk.LEFT)
        self.frame_game.pack(side=tk.RIGHT)
        self.frame_time.pack(side=tk.TOP, expand=tk.YES, fill=tk.BOTH)
        self.set_time_frame()
        self.tab_controller = ttk.Notebook(self.frame_control, width=self.offset, height=WINDOW_HEIGHT)
        self.tab_controller.pack(side=tk.TOP, expand=tk.YES, fill=tk.BOTH)
        self.tabs = []

        self.board_canvas = tk.Canvas(self.frame_game, bg="black", width=WINDOW_HEIGHT, height=WINDOW_HEIGHT, highlightthickness=0, relief='ridge')
        self.board_canvas.pack()

        """Create tabs to insert in frame_control"""
        self.insert_tab("Game")
        self.insert_tab("Buttons")
        self.insert_tab("Customize")
        self.log = tk.Text(self.tabs[0], height=40, width=40, state="disabled")
        self.log.pack()

        """Variables used to store images for board and stones, used to prevent python's garbage collection from deleting images if not stored in self variables"""
        self.trash_board = None
        self.trash_stones = [None, None]

        self.initialize_board()
        self.set_up_customize()
        self.set_up_data()
        self.text_style = [str, str]
        self.display_value = 0
        self.apply_style(3)
        self.config(bg="gray", menu=self.create_menu_bar())

        """Bind functions to mouse buttons"""
        self.board_canvas.bind('<Button-1>', self.clicked_event)
        self.board_canvas.bind('<Button-2>', self.secret_launch)
        self.board_canvas.bind('<Button-3>', self.reverse_move)

        self.game_status = False
        self.player_one = 0
        self.player_two = 1
        self.map_points = self.generate_points()
        self.bots = [Bot.ComputerPlayer(self.rows, self.chain, self.map_points), BotV3.ComputerPlayer(self.rows, self.chain, self.map_points)]
        self.points = []
        self.turn_count = 0
        self.move_tracker = []
        self.current_timer = 0
        self.start_time = None
        self.starting = 0

        self.games_won = 0
        self.game_goal = 50
        self.player_one_wins = 0
        self.game_state_storage = []
        self.set_window_icon(ICON)

        self.adjust_score_display(0)

    def create_menu_bar(self):
        """Function that creates the menu bar for GUI

        Returns:
            tk.Menu: Menu bar containing 4 major functions

        Menu Bar contains 3 cascades and 1 command button.
        Cascade 1: game_menu, contains commands to start the game off
        Cascade 2: display_menu, contains commands to adjust what information is displayed on the board
        Cascade 3: style_menu, contains commands to adjust the display of the board
        Command 4: Exist the program
        """
        menu_bar = tk.Menu(self, bg="black", fg="black")

        game_menu = tk.Menu(menu_bar, tearoff=0)
        game_menu.add_command(label="Play First", command=lambda: self.start_game(0), accelerator="Ctrl + 1")
        game_menu.add_command(label="Play Second", command=lambda: self.start_game(1), accelerator="Ctrl + 2")
        game_menu.add_command(label="Bot Vs Bot", command=lambda: self.start_game(2), accelerator="Ctrl + 3")

        display_menu = tk.Menu(menu_bar, tearoff=0)
        display_menu.add_command(label="No Score", command=lambda: self.adjust_score_display(0), accelerator="Ctrl + 4")
        display_menu.add_command(label="Player One Score", command=lambda: self.adjust_score_display(1), accelerator="Ctrl + 5")
        display_menu.add_command(label="Player Two Score", command=lambda: self.adjust_score_display(2), accelerator="Ctrl + 6")
        #display_menu.add_command(label="Swap Grid ID", command=self.)
        style_menu = tk.Menu(menu_bar, tearoff=0)
        for x in range(0, len(self.style_dictionary)):
            style_menu.add_command(label=self.style_dictionary[x]["Name"], command=lambda y=x: self.apply_style(y))

        menu_bar.add_cascade(label="New Game", menu=game_menu)
        menu_bar.add_cascade(label="View", menu=display_menu)
        menu_bar.add_cascade(label="Appearance", menu=style_menu)
        menu_bar.add_command(label="Exit", command=self.exit_app)

        self.bind('<Control-Key-1>', lambda _: self.start_game(0))
        self.bind('<Control-Key-2>', lambda _: self.start_game(1))
        self.bind('<Control-Key-3>', lambda _: self.start_game(2))
        self.bind('<Control-Key-4>', lambda _: self.adjust_score_display(0))
        self.bind('<Control-Key-5>', lambda _: self.adjust_score_display(1))
        self.bind('<Control-Key-6>', lambda _: self.adjust_score_display(2))
        self.bind('<Control-Key-7>', lambda _: self.scenario(0))

        return menu_bar



    def adjust_score_display(self, value):
        """Function that adjust what information is being displayed on the board

        Args:
            value (int): Indicator of what score to display.

        0: No Display
        1: Display player's 1 score (Black)
        2: Display player's 2 score (White)
        """
        self.display_value = value
        if value == 0:
            self.delete_tag("score_text")
        elif value == 1:
            self.display_score(0)
        elif value == 2:
            self.display_score(1)

    def log_move(self, move_str):
        """Logs move onto textbox located in GUI

        Args:
            move_str (str): String containing information about current turn and the move made.
        """

        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.INSERT, move_str + "\n")
        self.log.configure(state=tk.DISABLED)

    def log_reset(self):
        """Clears text box of all text"""
        self.log.configure(state=tk.NORMAL)
        self.log.delete("1.0", tk.END)
        self.log.configure(state=tk.DISABLED)

    def set_time_frame(self):
        """Creates timer box, timer box has added frame inside to display correctly"""
        mini_frame = tk.Frame(self.frame_time, width=self.offset, height=100)
        self.timer[0] = tk.StringVar()
        self.timer[1] = tk.StringVar()
        tk.Label(mini_frame, text="Player 1 Timer").pack(side=tk.LEFT)
        tk.Label(mini_frame, text="Player 2 Timer").pack(side=tk.RIGHT)
        mini_frame.pack(side=tk.TOP, expand=tk.YES, fill=tk.X)
        tk.Label(self.frame_time, textvariable=self.timer[0]).pack(side=tk.LEFT)
        tk.Label(self.frame_time, textvariable=self.timer[1]).pack(side=tk.RIGHT)

    def insert_tab(self, tab_name):
        """Function which creates new tabs and inserts them into frame

        Args:
            tab_name (str): String which contains text to be displayed on tab
        """
        tab_index = len(self.tabs)
        self.tabs.append(ttk.Frame(self.tab_controller))
        self.tab_controller.add(self.tabs[tab_index], text=tab_name)

    def set_window_size(self, width, height):
        """Adjust window size in pixels

        Args:
            width (int): Desired GUI width
            height (int): Desired GUI height
        """
        self.geometry(str(width) + "x" + str(height))

    def set_window_title(self, name):
        """Adjust name appearing on bar

        Args:
            name (str): Desired text to appear on bar
        """
        self.title(name)

    def set_window_icon(self, file):
        """Adjust icon appearing on bar

       Args:
           file (str): File name of .ico file to replace icon
       """
        self.iconbitmap(GUI_IMAGES + file)

    def apply_style(self, style):
        """Adjust the display style for the board

        Args:
            style (int): Index # to retrieve style information

        Function adjusts the display style by locating all tkinter objects by tag and modifying there fill or image value depending on object
        All objects are then raised in order to appear over the board image/rectangle
        """

        items = self.board_canvas.find_withtag("board_image")
        color = self.board_canvas.find_withtag("back")
        self.trash_stones[0] = prep_image(GUI_IMAGES + self.style_dictionary[style]["BlackStone"], self.tile_length - 7)
        self.trash_stones[1] = prep_image(GUI_IMAGES + self.style_dictionary[style]["WhiteStone"], self.tile_length - 7)

        """Type: Bool value, 0: Background is an image, 1: Background is an rectangle"""
        if self.style_dictionary[style]["Type"]:
            self.board_canvas.itemconfig(items, state="normal")
            self.board_canvas.itemconfig(color, state="hidden")
            self.trash_board = prep_image(GUI_IMAGES + self.style_dictionary[style]["Board"], WINDOW_HEIGHT - self.start_x * 2)
            self.board_canvas.itemconfig(items, image=self.trash_board)
        else:
            self.board_canvas.itemconfig(items, state="hidden")
            self.board_canvas.itemconfig(color, state="normal")
            self.update_color_tag("back", self.style_dictionary[style]["Board"])

        """Update colors of other variables and images of stones"""
        self.update_stones()
        self.update_background_color(self.style_dictionary[style]["Background"])
        self.update_color_tag("grid", self.style_dictionary[style]["Line"])
        self.update_color_tag("text", self.style_dictionary[style]["BoardText"])
        self.update_color_tag("stone_0", self.style_dictionary[style]["BotOneText"])
        self.update_color_tag("stone_1", self.style_dictionary[style]["BotTwoText"])
        self.score_fill = self.style_dictionary[style]["ScoreText"]
        self.text_style = [self.style_dictionary[style]["BotOneText"], self.style_dictionary[style]["BotTwoText"]]

        """Raise layer of stones to prevent appearing behind the board"""
        self.find_and_raise("stone_0")
        self.find_and_raise("stone_1")
        self.find_and_raise("line")
        self.adjust_score_display(self.display_value)

    def find_and_raise(self, tag):
        """Find objects with tag and raise position to display properly on board"""
        objects = self.board_canvas.find_withtag(tag)
        for x in objects:
            self.board_canvas.tag_raise(x)

    def initialize_board(self):
        """Creates the initial board objects"""
        self.draw_board_color("#000000")
        self.draw_board_text("#000000")
        self.draw_board_image("Mahogany.gif")
        self.draw_grid("#000000")

    def set_up_data(self):
        print(self.tab_controller)
        button_frame = tk.Frame(self.tabs[1], width=self.offset, height=WINDOW_HEIGHT)
        input_label = tk.Label(button_frame, text="Point:", width=6).grid(row=0, column=0, sticky=tk.W)
        input_point_x = tk.Entry(button_frame, width=3).grid(row=0, column=1, columnspan=1, sticky=tk.W)
        input_point_y = tk.Entry(button_frame, width=3).grid(row=0, column=2, columnspan=1, sticky=tk.W)
        radio_button_1 = tk.Radiobutton(button_frame, text="P1", variable=self.temp_var, value=0).grid(row=0, column=3, sticky=tk.W)
        radio_button_2 = tk.Radiobutton(button_frame, text="P2", variable=self.temp_var, value=1).grid(row=0, column=4,sticky=tk.W)
        data_frame = tk.Text(button_frame, width=36, height=40, state="normal")#disabled
        data_frame.grid(row=3, columnspan=6)
        print(self.offset, WINDOW_WIDTH)
        button_frame.pack()


    def set_up_customize(self):
        """Sets up customize tab to adjust board"""
        """Labels displayed on tab"""
        labels = ["Board Options:", "Background Color", "Board Color:", "Grid Color:", "Text Color:", "", "GUI Color", "Background Color:", "Text Color", ""]
        for x in range(0, len(labels)):
            tk.Label(self.tabs[2], text=labels[x], anchor=tk.W, width=20).grid(row=x)

        """Create text input boxes"""
        input_board_background_color = tk.Entry(self.tabs[2])
        input_board_color = tk.Entry(self.tabs[2])
        input_board_grid_color = tk.Entry(self.tabs[2])
        input_board_text_color = tk.Entry(self.tabs[2])

        """Place boxes in grid"""
        input_board_background_color.grid(row=1, column=1)
        input_board_color.grid(row=2, column=1)
        input_board_grid_color.grid(row=3, column=1)
        input_board_text_color.grid(row=4, column=1)

        """Assign function to boxes"""
        input_board_background_color.bind('<Return>', lambda _: self.update_background_color(input_board_background_color.get()))
        input_board_color.bind('<Return>', lambda _: self.update_color_tag("back", input_board_color.get()))
        input_board_grid_color.bind('<Return>', lambda _: self.update_color_tag("grid", input_board_grid_color.get()))
        input_board_text_color.bind('<Return>', lambda _: self.update_color_tag("text", input_board_text_color.get()))

    def draw_board_color(self, color):
        """Draw initial board
        Args:
            color (str): Hex color value
        """

        self.board_canvas.create_rectangle(self.start_x, self.start_x, self.end_x, self.end_x, fill=color, tags=("board", "back"), outline="")

    def draw_board_checkered(self, color_one, color_two):
        """Draws checkered pattern for board
        Args:
            color_one (str): Hex color value
            color_two (str): Hex color value
        """

        self.draw_board_color(color_one)
        for x in range(0, self.rows):
            for y in range(0, self.rows):
                if ((x + y) % 2) == 0:
                    x_coord = self.start_x + (x * self.tile_length)
                    y_coord = self.start_x + (y * self.tile_length)
                    self.board_canvas.create_rectangle(x_coord, y_coord, x_coord + self.tile_length, y_coord + self.tile_length, fill=color_two, tags=("board", "back"), outline="")

    def draw_board_outline(self, color):
        """Draw lines which form the outline for the board
        Args:
            color (str): Hex color value
        """

        self.board_canvas.create_line(self.start_x, self.start_x, self.start_x, self.end_x, fill=color, tags=("board", "outline"))
        self.board_canvas.create_line(self.start_x, self.start_x, self.end_x, self.start_x, fill=color, tags=("board", "outline"))
        self.board_canvas.create_line(self.start_x, self.end_x, self.end_x, self.end_x, fill=color, tags=("board", "outline"))
        self.board_canvas.create_line(self.end_x, self.start_x, self.end_x, self.end_x, fill=color, tags=("board", "outline"))

    def draw_board_image(self, image):
        """Draw initial image for board
        Args:
            image (str): File name of image
        """
        self.trash_board = prep_image(GUI_IMAGES + image, WINDOW_HEIGHT - self.start_x * 2)
        self.board_canvas.create_image((self.start_x, self.start_x), image=self.trash_board, anchor=tk.NW, tags=("board", "board_image"))

    def draw_grid(self, color, ):
        """Draw grid on board
        Args:
            color (str): Hex color value
        """
        new_start = self.start_x + self.tile_length / 2

        for x in range(0, self.rows):
            coord = self.start_x + (self.tile_length * x) + self.tile_length / 2
            self.board_canvas.create_line(new_start, coord, WINDOW_HEIGHT - new_start, coord, fill=color, tags=("board", "grid"))
            self.board_canvas.create_line(coord, new_start, coord, WINDOW_HEIGHT - new_start, fill=color, tags=("board", "grid"))

    def draw_stone_image(self, stone_type, point):
        """Draw stone on board
        Args:
            stone_type (int): index, 0: black stone, 1: white stone
            point ([x, x]}: Point on board
        """

        my_tags = [("board", "black_stone", "stone"), ("board", "white_stone", "stone")]
        coord_x = point[0] * self.tile_length + self.start_x
        coord_y = point[1] * self.tile_length + self.start_x
        self.board_canvas.create_image((coord_x, coord_y), image=self.trash_stones[stone_type], anchor=tk.NW, tags=my_tags[stone_type])

    def draw_line(self, points):
        """Draw line on board to mark winning chain
        Args:
            points (monomial list): All points found in monomial
        First and last point in monomial used to draw line
        """
        points[0][0] = points[0][0] * self.tile_length + self.start_x + int(self.tile_length/2)
        points[0][1] = points[0][1] * self.tile_length + self.start_x + int(self.tile_length / 2)
        points[4][0] = points[4][0] * self.tile_length + self.start_x + int(self.tile_length / 2)
        points[4][1] = points[4][1] * self.tile_length + self.start_x + int(self.tile_length / 2)


        #points = [x * self.tile_length + self.start_x + int(self.tile_length/2) for x in points]

        self.board_canvas.create_line(points[0][0], points[0][1], points[4][0], points[4][1], fill="red", width=2, tags=("board", "line"))
        self.update()
    def draw_stone_text(self, point, stone):
        """Draws integer on stone to identify turn stone was placed
        Args:
            point ([x, x]}: Point on board
            stone (int): index, 0: black stone, 1: white stone
        """

        x = point[0] * self.tile_length + self.start_x + self.tile_length/2
        y = point[1] * self.tile_length + self.start_x + self.tile_length/2
        self.board_canvas.create_text(x, y, text=self.turn_count, font="Ariel, 14", fill="#" + self.text_style[stone], tags=("board", "stone", "stone_" + str(stone)))

    def draw_board_text(self, color):
        """Draws text on edge of board to identify tiles location, Ex: A1 B2 E14
        Args:
            color (str): Hex color value
        """

        tile_size = (WINDOW_HEIGHT - (self.start_x * 2)) / self.rows
        for x in range(0, self.rows):
            coord = self.start_x + (tile_size * x) + tile_size / 2
            if ORIGINAL_POINTS:
                text_x, text_y = x, x
            else:
                text_x = self.rows - x
                text_y = chr(ord("A") + x)
            self.board_canvas.create_text(self.start_x - 30, coord, text=text_x, font="Ariel, 14", fill=color, tags=("board", "text"))
            self.board_canvas.create_text(coord, self.start_x - 30, text=text_y, font="Ariel, 14", fill=color, tags=("board", "text"))

    def draw_score_text(self, points, score):
        """Deletes all scores on board then redraws them for each empty intersection
        Args:
            points ([[x, x], [x, x], . . .}: List of all remaining points on board
            score (int list): List of scores for remaining points on board
        """

        self.delete_tag("score_text")
        for z in range(0, len(points)):
            if points[z] in self.map_points:
                x = points[z][0] * self.tile_length + self.start_x
                y = points[z][1] * self.tile_length + self.start_x
                self.board_canvas.create_text(x + self.tile_length / 2, y + self.tile_length / 2, font="Ariel, 14", fill="#" + self.score_fill, text=score[z], tags=("board", "score_text"))

    def update_background_color(self, color):
        """Update fill color of board
        Args:
            color (str): Hex color value
        """
        if check_valid_hex_color(color):
            self.board_canvas.configure(background="#" + color)

    def update_color_tag(self, tag, color):
        """Update color of objects that contain the tag
        Args:
            tag (str): Tag found on tkinter objects
            color (str): Hex color value
        """
        if check_valid_hex_color(color):
            item_id = self.board_canvas.find_withtag(tag)
            self.update_color(item_id, color)
        else:
            print("Invalid Hex Color!")

    def update_color(self, items, color):
        """Update fill color of objects
        Args:
            items (list int): List of id's for tkinter objects
            color (str): Hex color value
        """
        for x in items:
            self.board_canvas.itemconfig(x, fill="#" + color)

    def update_image(self, tag, image):
        """Update tkinter object with new image
        Args:
            tag (list int): List of id's for tkinter objects
            image (tk photo image): Processed image
        """
        items = self.board_canvas.find_withtag(tag)
        for x in items:
            self.board_canvas.itemconfig(x, image=image)

    def update_stones(self):
        """Update all tkinter objects with the tag stone with new images"""
        black_stones = self.board_canvas.find_withtag("black_stone")
        white_stones = self.board_canvas.find_withtag("white_stone")

        for x in black_stones:
            self.board_canvas.itemconfig(x, image=self.trash_stones[0])
            self.board_canvas.tag_raise(x)
        for x in white_stones:
            self.board_canvas.itemconfig(x, image=self.trash_stones[1])
            self.board_canvas.tag_raise(x)

    def display_score(self, player):
        """Obtain all scores from bot then display
        Args:
            player (int): Player identifier, 0: First player, 1: Second player
        """
        if player:
            x, y = self.bots[self.player_two].my_point_value()
        else:
            x, y = self.bots[self.player_two].op_point_value()
        self.draw_score_text(x, y)

    def generate_points(self):
        """Returns all points for board based on board size"""
        points = []
        for x in range(0, self.rows):
            for y in range(0, self.rows):
                points.append([x, y])
        return points

    def delete_tag(self, tag):
        """Delete tkinter object from window based on id provided"""
        self.board_canvas.delete(tag)

    def get_point(self, coord):
        return [int(coord / self.rows), coord % self.rows]

    @staticmethod
    def get_point(point):
        return (point[0] * 19) + point[1]

    def scenario(self, num):

        #self.start_game(0)
        #a = [107, 108, 140, 141, 142, 144, 162, 163, 180, 197, 217]
        #b = [126, 143, 145, 160, 161, 179, 181, 183, 198, 199]

        #aa = [a, b]
        #c = 0;

        #for move in range(len(b)):
        ##    self.perform_turn(self.player_one, self.get_point(aa[0][c]), self.bots[self.player_two].op_move(self.get_point(aa[0][c])))
        #    self.perform_turn(self.player_two, self.get_point(aa[1][c]), self.bots[self.player_two].my_move(self.get_point(aa[1][c])))
        #    c += 1
        #self.perform_turn(self.player_one, self.get_point(a[len(a) - 1]), self.bots[self.player_two].op_move(self.get_point(a[len(a) - 1])))


        #print(". . ")
        #moves = [[10, 5], [10, 3], [11, 5], [10, 4], [11, 6], [10, 6], [11, 7], [10, 7], [12, 7], [11, 8], [10, 8]]
        #moves = [[9, 9], [8, 9], [10, 10], [7, 8], [11, 11], [12, 12], [9, 11], [9, 10]]
        moves = [[7, 13], [8, 12], [8, 13], [9, 14], [10, 12], [10, 10], [12, 9], [12, 11], [12, 12], [13, 7], [14, 8], [13, 10], [15, 8], [14, 9]]
        #moves = [[9, 6], [8, 6], [10, 6], [10, 7], [11, 8], [10, 8], [10, 9], [10, 10], [12, 9], [13, 12], [13, 11], [14, 12]]
        #moves = [[6, 4], [10, 10], [7, 4], [6, 3], [10, 6], [12, 7], [10, 8], [6, 7], [10, 9], [7, 7], [12, 10]]

        t1 = []
        t2 = []
        for x in range(len(moves)):
            if x%2 == 0:
                t1.append(moves[x])
            else:
                t2.append(moves[x])
        print([self.get_point(x) for x in t1])
        print([self.get_point(x) for x in t2])
        self.start_game(0)
        for move in range(len(moves)):
            if move % 2 == 0:
                self.perform_turn(self.player_one, moves[move], self.bots[self.player_two].op_move(moves[move]))
            else:
                self.perform_turn(self.player_two, moves[move], self.bots[self.player_two].my_move(moves[move]))
        self.update()
        feedback = self.bots[self.player_two].calc_move()
        point = list(feedback)
        self.perform_turn(self.player_two, point, self.bots[self.player_two].my_move(point))

    def secret_launch(self, event=None):
        """Function tied to middle click button, currently launches player vs bot"""

        if STATS:
            total_turn = 0
            self.games_won = 0
            self.player_one_wins = 0

            while self.games_won != self.game_goal:
                self.start_game(2)
                self.games_won += 1
                if self.turn_count % 2 == 0:
                    self.player_one_wins += 1
                total_turn += self.turn_count

            print("Player One Won:", self.game_goal - self.player_one_wins)
            print("Player Two Won:", self.player_one_wins)
            print("Player One Won", int(((self.game_goal - self.player_one_wins) / self.game_goal) * 100), "Percent Of Games")
            print("Average Turns", total_turn/self.game_goal)
            self.games_won, self.player_one_wins = 0, 0

        else:
            self.start_game(0)

            #self.perform_turn(self.player_one, [5, 5], self.bots[self.player_two].op_move([5, 5]))
            #self.perform_turn(self.player_one, [5, 6], self.bots[self.player_two].op_move([5, 6]))
            #self.perform_turn(self.player_one, [4, 7], self.bots[self.player_two].op_move([4, 7]))
            #self.perform_turn(self.player_one, [6, 7], self.bots[self.player_two].op_move([6, 7]))

            print("Done")

    def perform_reverse(self, id_list):
        """Delete move recent placed stone from list"""
        self.board_canvas.delete(id_list[-1])

    def reverse_stones(self):
        """Clear latest stones placed, if player has won only remove his stone"""
        bb = ["black_stone", "white_stone"]
        if self.starting == self.turn_count%2:
            self.perform_reverse(self.board_canvas.find_withtag(bb[self.starting]))
        else:
            self.perform_reverse(self.board_canvas.find_withtag(bb[self.turn_count%2]))
        #if player_won:
        #    if self.starting == 1:
        #        self.perform_reverse(self.board_canvas.find_withtag("white_stone"))
        #    else:
        #        self.perform_reverse(self.board_canvas.find_withtag("black_stone"))
        #else:
        #    self.perform_reverse(self.board_canvas.find_withtag("black_stone"))
        #    self.perform_reverse(self.board_canvas.find_withtag("white_stone"))

    def reverse_move(self, event=None):
        #WIP, Faster Version
        #index_to_load = (self.turn_count - self.starting - 1) // 10
        #moves_to_replay = (self.turn_count - self.starting) % 10
        #moves_to_replay = 10 if moves_to_replay == 0 else moves_to_replay
        #moves_to_replay = [] if moves_to_replay == 2 else self.move_tracker[-moves_to_replay:][:-2]
        #if len(moves_to_replay) == 8:
        #    del self.game_state_storage[-1]
        return
        if not self.game_status and len(self.move_tracker) != 0:
            self.delete_tag("line")
            self.game_status = True
        if len(self.move_tracker) > 1:
            self.map_points.append(self.move_tracker[-1])
            del self.move_tracker[-1]
            self.log_move("Undo Move")
            self.turn_count -= 1
            self.bots[self.player_two].load_game(self.move_tracker, self.starting)
            self.reverse_stones()

            self.log_move("Undo Move")
            if self.display_value > 0:
                self.display_score(self.display_value - 1)

    def regular_move(self, x, y):
        pass

    def clicked_event(self, event):
        """Click event manager, converts click location to point on board and performs move"""
        """Obtain position using click position and tile length"""
        board_x = int((event.x - self.start_x) // self.tile_length)
        board_y = int((event.y - self.start_x) // self.tile_length)
        clicked_point = [board_x, board_y]

        if TESTING:
            self.clicked_testing(clicked_point)
        else:
            if self.starting != self.turn_count%2:
                feedback = self.bots[self.player_two].calc_move()
                point = list(feedback)
                self.perform_turn(self.player_two, point, self.bots[self.player_two].my_move(point))
            else:
                if self.game_status and clicked_point in self.map_points:
                    """If game is in progress and tile clicked is empty perform move"""
                    self.perform_turn(self.player_one, clicked_point, self.bots[self.player_two].op_move(clicked_point))
                    self.update()

                    feedback = self.bots[self.player_two].calc_move()
                    point = list(feedback)
                    self.perform_turn(self.player_two, point, self.bots[self.player_two].my_move(point))

    def clicked_testing(self, clicked_point):
        if self.game_status and clicked_point in self.map_points:
            self.bots[self.player_two].show_info()
            if self.turn_count % 2 == self.starting:
                self.perform_turn(self.player_one, clicked_point, self.bots[self.player_two].op_move(clicked_point))
            else:
                self.perform_turn(self.player_two, clicked_point, self.bots[self.player_two].my_move(clicked_point))


    def bot_vs_bot(self):
        """Bot vs Bot manager, perform first move based on opening move followed by performing normal moves until winner found"""
        point = self.bots[self.player_one].opening_move()
        self.perform_turn(self.player_one, point, self.bots[self.player_one].my_move(point), True)
        self.bots[self.player_two].op_move(point)
        while self.game_status:
            self.bot_vs_bot_turn(self.player_two, self.player_one)
            self.update()
            self.bot_vs_bot_turn(self.player_one, self.player_two)
            self.update()

    def bot_vs_bot_turn(self, player, opponent):
        """Obtain move then update tables for both bots using index
        Args:
            player (int): 0: Player 1, 1: Player 2
            opponent (int): 0: Player 1, 1: Player 2
        """

        point = list(self.bots[player].calc_move())
        self.perform_turn(player, point, self.bots[player].my_move(point), True)
        self.bots[opponent].op_move(point)

    def perform_turn(self, player, point, winner, bots=False):
        """Update all variables dealing with turns
        Args:
            player (int): 0: Player 1, 1: Player 2
            point ([x, x]: Point which was taken
            winner (bool): Did the move end the game
            bots (bool): If game is a bot vs bot, if so display turn on stones
        """

        if self.game_status:
            if (self.turn_count + 1) % 10 == self.starting:
                pass
                #temp = copy.deepcopy(self.bots)
                #self.game_state_storage.append(temp)
            """Log turn on GUI, update variables, and draw stones on board"""
            log = "(Turn %s) Player %s Move: %s" % (self.turn_count+1, player+1, convert_point(point))
            self.log_move(log)
            self.turn_count += 1
            self.move_tracker.append(point)
            self.map_points.remove(point)
            self.draw_stone_image((self.turn_count + 1) % 2, point)
            self.switch_timer()
            if bots:
                self.draw_stone_text(point, (self.turn_count + 1) % 2)
            if self.display_value > 0:
                self.display_score(self.display_value - 1)
            if winner:
                if bots:
                    self.draw_line(self.bots[player].return_win())
                else:
                    self.draw_line(self.bots[self.player_two].return_win())
                self.end_game()

    def start_game(self, launch_type):
        """Launch game based on variable
        Args:
            launch_type (int):
                0: First Player: Player, Second Player: Bot
                1: First Player: Bot, Second Player: Player
                2: First Player: Bot, Second Player: Bot
        """

        self.reset_variables()
        if launch_type == 0:
            self.current_timer = 0
            self.starting = 0
        elif launch_type == 1:
            self.current_timer = 1
            self.starting = 1
            point = self.bots[self.player_two].opening_move()
            self.perform_turn(self.player_two, point, self.bots[self.player_two].my_move(point))
        elif launch_type == 2:
            self.current_timer = 0
            self.bot_vs_bot()

        self.game_state_storage.append(copy.deepcopy(self.bots))

    def reset_variables(self):
        """Reset all variables and clear board of text, stones, and lines if present"""
        self.map_points = self.generate_points()
        self.turn_count = 0
        self.move_tracker = []
        self.delete_tag("stone")
        self.delete_tag("line")
        self.delete_tag("score_text")
        self.game_status = True
        self.timer[0].set(0)
        self.timer[1].set(0)
        self.start_time = time.time()
        self.bots[0].reset_variables()
        self.bots[1].reset_variables()
        self.log_reset()
        self.update_timer()
        self.game_state_storage = []
        self.adjust_score_display(self.display_value)

    def end_game(self):
        """Sets game status to False, saves games information"""
        self.game_status = False
        self.save_game()

    def save_game(self):
        """Saves all moves done in game in json file"""
        pass

    def update_time_loop(self):
        """Gets time difference and updates"""
        time_difference = time.time() - self.start_time
        self.start_time = time.time()
        time_difference += float(self.timer[self.current_timer].get())
        self.timer[self.current_timer].set(round(time_difference, 4))

    def update_timer(self):
        """While game in progress continue to update timer every 50ms"""
        if self.game_status:
            self.update_time_loop()
            self.after(50, self.update_timer)

    def switch_timer(self):
        """Update timer variables to keep track of next player"""
        self.update_time_loop()
        self.current_timer = (self.current_timer + 1) % 2
        self.start_time = time.time()

    def exit_app(self):
        """Exits Program"""
        self.quit()

    def start_up(self):
        """Starts Program"""
        self.mainloop()


def prep_image(image_location, size):
    """Adjust size of image to desired size due to limitations of subsample size may be rounded
    Args:
        image_location (str): Location + name of image
        size (int): Desired size of image in px
    Returns:
        tkinter image
    """
    image = tk.PhotoImage(file=image_location)
    x = int(image.width()/size)
    return image.subsample(x, x)


def check_valid_hex_color(color):
    """Return true or false based on if string is valid hex of length 6
    Args:
        color (str): Hex color value
    Returns:
        bool
    """
    return all(len(color) == 6 and x in string.hexdigits for x in color)


def load_style():
    """Returns content of json file as a dictionary"""
    with open(BOARD_STYLES) as styles:
        return json.load(styles)


def convert_point(point):
    """Convert point from [#, #] format to display format
    Args:
        point ([x, x]): point on board
    Returns:
        str
    Ex:
    [0, 0] -> A19
    [0, 18] -> A1
    """
    return chr(ord("A") + point[0]) + str(19-point[1])
