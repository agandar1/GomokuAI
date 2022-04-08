import tkinter as tk
from lib import GUI_Components
from tkinter import ttk
from lib import BotV5 as BotV4
import string
import copy
import threading
import time
import json

BOARD_STYLES = "Files/Styles.json"
BOARD_GAMES = "Files/Games.json"
GUI_IMAGES = "Images/"
GAME_SAVES = "Games/"
ICON = "Black_Block.ico"

LAYER_RGB = ["#dcf442", "#41f49d", "#00faff", "#ffc1fc", "#ab1295", "#48ab9a", "#71eeb8"]
WINDOW_WIDTH = 1300
WINDOW_HEIGHT = 1000
ORIGINAL_POINTS = True
TESTING = False
STATS = False
BOT, OP = 0, 1


class GomokuGUI(tk.Tk):
    def __init__(self, board_rows=19, chain_length=5, title="Gomoku"):
        super().__init__()
        self.maximize_window()
        self.set_window_title(title)
        width, height = self.get_window_dimensions()
        offset = width - height

        self.board_rows = board_rows
        # GUI Frames
        self.master_frame = tk.Frame(self, width=width, height=height)
        self.sub_frame = tk.Frame(self.master_frame, width=offset, height=height)
        self.tab_controller = ttk.Notebook(self.sub_frame, width=offset, height=height - 50)

        self.game_frame = tk.Frame(self.master_frame, width=height, height=height)
        self.move_frame = tk.Frame(self.tab_controller, width=offset, height=height-50)
        self.tool_box_frame = tk.Frame(self.tab_controller, width=offset, height=height-50, bg="#333333")
        self.timer_frame = tk.Frame(self.sub_frame, width=offset, height=50, bg="#444444")

        self.tab_controller.add(self.move_frame, text="Moves")
        self.tab_controller.add(self.tool_box_frame, text="Layers")

        self.sub_frame.pack(side=tk.LEFT)
        self.game_frame.pack(side=tk.RIGHT)
        self.timer_frame.pack(side=tk.TOP)
        self.tab_controller.pack(side=tk.TOP)
        self.master_frame.pack()

        # Move Frame
        self.move_box = GUI_Components.MovesFrame(self.move_frame)
        self.tool_box = GUI_Components.ToolBox(self.tool_box_frame, 2, 5, self.tool_box_handle)
        self.timers = [GUI_Components.TimerFrame("Player 1", self.timer_frame), GUI_Components.TimerFrame("Player 2", self.timer_frame)]

        # GameBoard Frame
        self.game_board_manager = GUI_Components.GameBoardFrame(self.game_frame, int(height*.9), height, board_rows, chain_length)
        self.game_board_manager.pack_board(tk.RIGHT)
        self.game_board_manager.start_up_board(3)
        self.style_dictionary = self.load_style(BOARD_STYLES)
        self.saved_games = self.load_style(BOARD_GAMES)
        self.config(bg="gray", menu=self.create_menu_bar())

        self.map_buttons()
        self.protocol('WM_DELETE_WINDOW', self.exit_app)
        # self.set_window_icon(ICON)

        self.map_points = self.generate_points(self.board_rows)
        self.bots = [BotV4.ComputerPlayer(board_rows, chain_length), BotV4.ComputerPlayer(board_rows, chain_length)]

        self.game_active = False
        self.current_timer = 0
        self.player_one = 0
        self.player_two = 1

        self.display_player = 0
        self.display_type = 0
        self.display_layer = 0
        self.display_display = 0
        self.display_score = 0
        self.reverse = False
        self.r_moves = 0

        self.points = [[], []]
        self.free_mode = False

    @staticmethod
    def generate_points(point_range):
        return [[x_coord, y_coord] for x_coord in range(point_range) for y_coord in range(point_range)]

    def map_buttons(self):
        self.game_board_manager.set_move_log(self.move_box)
        canvas = self.game_board_manager.get_canvas()
        canvas.bind('<Button-1>', self.clicked_event)
        canvas.bind('<Button-2>', self.secret_launch)
        canvas.bind('<Button-3>', self.undo_move)
        canvas.bind('Ctrl + a', self.secret_launch)

    def recreate_map(self):
        #map = [[1, [9, 3]], [1, [9, 4]], [0, [8, 3]], [0, [8, 4]], [0, [9, 5]], [0, [8, 2]], [1, [8, 1]], [0, [6, 2]], [1, [5, 1]], [0, [5, 2]], [1, [4, 2]], [0, [7, 2]], [1, [9, 2]], [0, [7, 3]], [1, [10, 6]], [0, [7, 1]], [1, [7, 4]], [0, [8, 5]], [1, [8, 6]], [0, [8, 0]]]
        map = ['I12', 'J12', 'I11', 'I13', 'J11', 'K14', 'K11', 'H11', 'J13', 'N11', 'K12', 'M10', 'L11', 'M11', 'L10', 'M12', 'M9', 'L13', 'O11']
        map = self.point_convert(map)
        print(map)


        for x in range(len(map)):
            if x%2 == 0:
                self.game_board_manager.handle_turn(self.player_one, map[x])
                self.bots[BOT].op_move(map[x])
            else:
                self.game_board_manager.handle_turn(self.player_two, map[x])
                self.bots[BOT].my_move(map[x])
        self.bots[BOT].calc_move()

    @staticmethod
    def point_convert(p_list):
        new_list = []
        for x in p_list:
            a = ord(x[0]) - ord("A")
            b = 19 - int(x[1:])
            new_list.append([a, b])
        return new_list

    def test_layers(self):
        Player1 = [158, 177, 125, 164, 183, 202, 196, 141, 84, 86, 124, 121, 83, 109, 216]
        Player2 = [221, 197, 178, 159, 201, 182, 163, 106, 107, 103, 105, 102, 120, 144, 122, 128, 101, 82, 176, 234]
        Player1 = [125, 144, 164]
        Player2 = [126, 145]

        Player2 = [125, 126, 146, 145]
        Player1 = []

        self.start_game(0)
        for moves in Player1:
            self.game_board_manager.handle_turn(self.player_one, self.get_point(moves))
            self.bots[BOT].my_move(self.get_point(moves))

        for moves in Player2:
            self.game_board_manager.handle_turn(self.player_two, self.get_point(moves))
            self.bots[BOT].op_move(self.get_point(moves))

        self.bots[BOT].test_changes()

    def simulate_moves(self, p1, p2):
        for x in p1:
            self.bots[BOT].my_move(self.get_point(x))
            self.game_board_manager.handle_turn(self.player_two, self.get_point(x))
        for x in p2:
            self.bots[BOT].op_move(self.get_point(x))
            self.game_board_manager.handle_turn(self.player_one, self.get_point(x))

    def tool_box_handle(self, player, layer, display):
        if player == 0:
            self.display_layer, self.display_player, self.display_display = 0, 0, 0
            self.game_board_manager.find_and_delete("layer")
        else:
            self.display_player, self.display_layer, self.display_display = player-1, layer, display
            self.draw_layers(player-1, layer, display)

    def secret_launch(self, event):
        #self.game_board_manager.find_and_delete_last("stone")
       # Player1 = [140, 160, 179, 178, 177, 199]
       # Player2 = [142, 180, 181, 197, 217, 235]
        #self.simulate_moves(Player1, Player2)
        self.test_layers()
        #self.recreate_game()

    def undo_move(self, event):
        self.game_board_manager.find_and_delete_last("stone")
        self.reverse = True
        self.r_moves += 1
        if not self.game_active:
            self.game_active = True
            self.game_board_manager.find_and_delete_last("line")


    def recreate_game(self):
        moves = self.game_board_manager.get_remaining_taken(self.r_moves)

        self.bots[BOT].reset_variables()
        for x in range(len(moves)):
            if x % 2 != self.player_one:
                self.bots[BOT].my_move(moves[x])
            else:
                self.bots[BOT].op_move(moves[x])
        self.r_moves = 0

    def draw_layers(self, influence, layer, display):
        self.game_board_manager.find_and_delete("layer")
        moves = self.bots[BOT].get_layer_moves(influence, layer, display)

        for x in moves:
            self.game_board_manager.draw_box(self.get_point(x), LAYER_RGB[layer-1])

    def perform_turn(self):
        pass

    def display_scores(self, player, score_type):
        self.game_board_manager.adjust_score_display(player)
        self.display_score = player
        self.display_type = score_type
        if player == 0:
            self.game_board_manager.find_and_delete("score_text")
        else:
            active, points = self.bots[BOT].get_score_and_active(self.player_one, score_type) if player == 1 else self.bots[BOT].get_score_and_active(self.player_two, score_type)
            self.game_board_manager.draw_score_text(points, active)

    def maximize_window(self):
        try:
            self.state('zoomed')
        except:
            self.attributes('-zoomed', True)

    def get_window_dimensions(self):
        self.update()
        return self.winfo_width(), self.winfo_height()

    def set_monitor_size(self):
        w, h = self.get_window_dimensions()
        self.resize_window(w, h)

    def resize_window(self, width, height):
        self.set_window_size(width, height)

    @staticmethod
    def load_style(file_name):
        with open(file_name) as styles:
            return json.load(styles)

    def set_window_title(self, name):
        self.title(name)

    def set_window_size(self, width, height):
        self.geometry(str(width) + "x" + str(height))

    def create_menu_bar(self):
        menu_bar = tk.Menu(self, bg="#aaaaaa", fg="black")

        game_menu = tk.Menu(menu_bar, tearoff=0)
        game_menu.add_command(label="Play First", command=lambda: self.start_game(0), accelerator="Ctrl + 1")
        game_menu.add_command(label="Play Second", command=lambda: self.start_game(1), accelerator="Ctrl + 2")
        game_menu.add_command(label="Bot Vs Bot", command=lambda: self.start_game(2), accelerator="Ctrl + 3")

        display_menu = tk.Menu(menu_bar, tearoff=0)
        display_menu.add_command(label="No Score", command=lambda: self.display_scores(0, 0), accelerator="Ctrl + 4")
        display_menu.add_command(label="Swap Grid Notation", command=self.game_board_manager.swap_grid_notation, accelerator="Ctrl + 5")
        display_menu.add_command(label="Player One Score", command=lambda: self.display_scores(1, 0), accelerator="Ctrl + 6")
        display_menu.add_command(label="Player Two Score", command=lambda: self.display_scores(2, 0), accelerator="Ctrl + 7")
        display_menu.add_command(label="Player One Score-Modified", command=lambda: self.display_scores(3, 1), accelerator="Ctrl + 8")
        display_menu.add_command(label="Player Two Score-Modified", command=lambda: self.display_scores(4, 1), accelerator="Ctrl + 9")

        #display_menu.add_command(label="Swap Grid ID", command=self.)
        style_menu = tk.Menu(menu_bar, tearoff=0)
        for x in range(0, len(self.style_dictionary)):
            style_menu.add_command(label=self.style_dictionary[x]["Name"], command=lambda y=x: self.game_board_manager.apply_style(y))

        prototype_menu = tk.Menu(menu_bar, tearoff=0)
        print(self.saved_games[0])
        print(self.saved_games[1])
        for x in range(0, len(self.saved_games)):
            prototype_menu.add_command(label=self.saved_games[x]["Name"], command=lambda y=x: self.scenario(y))

        menu_bar.add_cascade(label="New Game", menu=game_menu)
        menu_bar.add_cascade(label="View", menu=display_menu)
        menu_bar.add_cascade(label="Appearance", menu=style_menu)
        menu_bar.add_cascade(label="Prototype", menu=prototype_menu)
        menu_bar.add_command(label="Exit", command=self.exit_app)

        self.bind('<Control-Key-1>', lambda _: self.start_game(0))
        self.bind('<Control-Key-2>', lambda _: self.start_game(1))
        self.bind('<Control-Key-3>', lambda _: self.start_game(2))
        self.bind('<Control-Key-4>', lambda _: self.display_scores(0, 0))
        self.bind('<Control-Key-5>', lambda _: self.game_board_manager.swap_grid_notation())
        self.bind('<Control-Key-6>', lambda _: self.display_scores(1, 0))
        self.bind('<Control-Key-7>', lambda _: self.display_scores(2, 0))
        self.bind('<Control-Key-8>', lambda _: self.display_scores(1, 1))
        self.bind('<Control-Key-9>', lambda _: self.display_scores(2, 1))

        return menu_bar

    def handle_free_click(self, point_x, point_y):
        point_coord = point_x + point_y * self.board_rows

        if point_coord in self.points[0]:
            self.points[OP].append(point_coord)
            self.points[BOT].remove(point_coord)
        elif point_coord in self.points[1]:
            self.points[OP].remove(point_coord)
        else:
            self.points[BOT].append(point_coord)

        self.reset_variables()

        for player_one_point in self.points[BOT]:
            self.game_board_manager.handle_turn(self.player_one, self.get_point(player_one_point))
        for player_two_point in self.points[OP]:
            self.game_board_manager.handle_turn(self.player_two, self.get_point(player_two_point))

    def set_window_icon(self, file):
        self.iconbitmap(GUI_IMAGES + file)

    def scenario(self, scenario_index):
        print(scenario_index)
        print(self.saved_games[scenario_index]["Name"])
        print(self.saved_games[scenario_index]["Player_1"])
        print(self.saved_games[scenario_index]["Player_2"])

        p1 = self.saved_games[scenario_index]["Player_1"]
        p2 = self.saved_games[scenario_index]["Player_2"]

        p1.reverse()
        p2.reverse()

        self.start_game(0)
        turn = 0
        while True:
            if turn%2 == 0:
                if len(p1) == 0:
                    break
                move = p1.pop()
                self.game_board_manager.handle_turn(self.player_one, self.get_point(move))
                self.bots[BOT].my_move(self.get_point(move))
                self.game_board_manager.draw_stone_text(0, self.get_point(move))
            else:
                if len(p2) == 0:
                    break
                move = p2.pop()
                self.game_board_manager.handle_turn(self.player_two, self.get_point(move))
                self.bots[BOT].op_move(self.get_point(move))
                self.game_board_manager.draw_stone_text(1, self.get_point(move))

            turn += 1


        #self.game_board_manager.play_op_moves()
        #self.game_board_manager.play_my_moves()

        pass

    def timer_work(self):
        other_player = (self.current_timer + 1) % 2
        self.timers[other_player].start()
        self.timers[self.current_timer].stop_timer()
        self.current_timer = other_player

    def clicked_event(self, event):
        # Thread Here Run Calculation Separate, No Timer Frozen
        if self.free_mode:
            valid, move = self.game_board_manager.handle_click(event.x, event.y, self.player_one)
            self.handle_free_click(move[0], move[1])
        else:
            if not self.game_active:
                self.start_game(1)
                return
            if self.reverse:
                self.recreate_game()
                self.reverse = False
                print(len(self.game_board_manager.get_remaining_points()) % 2)
                print(self.player_one, self.player_two)
                if len(self.game_board_manager.get_remaining_points()) % 2 != self.player_one:
                    valid, move = self.game_board_manager.handle_click(event.x, event.y, self.player_one)
                    if valid:
                        self.game_board_manager.handle_turn(self.player_one, move)
                        self.op_full_handle(move)
                else:
                    self.handle_op_move()
            else:
                valid, move = self.game_board_manager.handle_click(event.x, event.y, self.player_one)
                if valid:
                    self.game_board_manager.handle_turn(self.player_one, move)
                    self.op_full_handle(move)
            if self.display_layer != 0:
                self.draw_layers(self.display_player, self.display_layer, self.display_display)

    def full_handle(self):
        pass

    def op_full_handle(self, move):
        self.turn_swap()
        if not self.bots[BOT].op_move(move):
            self.handle_op_move()
        else:
            self.handle_win()
        self.display_scores(self.display_score, self.display_type)

    def handle_win(self):
        self.win_handle(self.bots[BOT].return_win())
        self.stop_timers()

    def handle_op_move(self):
        bot_move = self.bots[BOT].calc_move()
        self.game_board_manager.handle_turn(self.player_two, bot_move)
        self.turn_swap()
        if self.bots[BOT].my_move(bot_move):
            self.handle_win()

    def turn_swap(self):
        self.update()
        self.timer_work()
        if self.display_layer != 0:
            self.draw_layers(self.display_player, self.display_layer, self.display_display)

    def win_handle(self, points):
        self.game_active = False
        self.game_board_manager.draw_line(points)

    def bot_vs_bot(self):
        start_point = self.bots[BOT].opening_move()
        self.game_board_manager.draw_stone_text(self.player_one, start_point)
        self.game_board_manager.handle_turn(self.player_one, start_point)
        self.bots[self.player_one].my_move(start_point)
        self.bots[self.player_two].op_move(start_point)

        current_p, current_o = self.player_one, self.player_two
        while self.game_active:
            self.turn_swap()
            if self.bot_vs_turn(current_o, current_p):
                self.win_handle(self.bots[current_o].return_win())
                break
            current_o, current_p = current_p, current_o
            self.update()
        self.stop_timers()
        self.game_active = False

    def bot_vs_turn(self, player, opponent):
        self.display_scores(self.display_score, self.display_type)
        point = self.bots[player].calc_move()
        self.game_board_manager.draw_stone_text(player, point)
        self.game_board_manager.handle_turn(player, point)
        self.bots[opponent].op_move(point)
        self.game_board_manager.find_and_raise("stone_" + str(player))
        return self.bots[player].my_move(point)

    def start_game(self, launch_option):
        self.reset_variables()

        self.game_active = True
        if launch_option == 0:
            self.player_one, self.player_two, self.current_timer = 0, 1, 0
            self.timers[self.player_one].start()
            self.bots[BOT].set_player(1)
        elif launch_option == 1:
            self.player_one, self.player_two, self.current_timer = 1, 0, 1
            r_move = self.bots[BOT].opening_move()
            self.bots[BOT].my_move(r_move)
            self.game_board_manager.handle_turn(self.player_two, r_move)
            self.timers[self.player_one].start()
            self.bots[BOT].set_player(0)
        else:
            self.bots[BOT].set_player(0)
            self.player_one, self.player_two, self.current_timer = 0, 1, 0
            self.timers[self.player_one].start()
            self.bot_vs_bot()

    def get_point(self, coord):
        return [coord % self.board_rows, int(coord / self.board_rows)]

    def reset_variables(self):
        self.game_board_manager.reset_variables()
        self.timers[0].reset_time()
        self.timers[1].reset_time()
        self.map_points = self.generate_points(self.board_rows)
        self.bots[BOT].reset_variables()
        self.bots[OP].reset_variables()
        self.move_box.delete_game()
        self.reverse = False
        self.r_moves = 0

    def stop_timers(self):
        self.timers[0].stop_timer()
        self.timers[1].stop_timer()

    def exit_app(self):
        self.timers[0].stop_timer()
        self.timers[1].stop_timer()

        self.quit()

    def start_up(self):
        self.mainloop()
