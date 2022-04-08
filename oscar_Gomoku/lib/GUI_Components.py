import tkinter as tk
import time
import threading
import json
import math

BOARD_STYLES = "Files/Styles.json"
GUI_IMAGES = "Images/"
GAME_SAVES = "Games/"
ICON = "Black_Block.ico"


class TimerFrame:
    def __init__(self, timer_name, timer_frame):
        self.timer_variable = tk.StringVar()
        self.timer_frame = tk.Frame(timer_frame, height=50, width=500, bg="#111111")
        self.label_name = tk.Label(self.timer_frame, text=timer_name, bg="#aaaaaa")
        self.label_timer = tk.Label(self.timer_frame, textvariable=self.timer_variable)
        self.timer_frame.pack(side=tk.LEFT)
        self.label_name.pack(side=tk.TOP)
        self.label_timer.pack(side=tk.TOP)

        self.timer_variable.set("00:00.00")
        self.start_time = None
        self.time_num = None
        self.run_timer = False
        self.reset_time()

    def get_time_format(self):
        m, s = divmod(self.time_num, 60)
        s, ms = divmod(s, 1)
        m, s, ms, = int(m), int(s), int(ms*100)
        return "{:02d}:{:02d}.{:02d}".format(m, s, ms)

    def time_loop(self):
        time_difference = time.time() - self.start_time
        self.start_time = time.time()
        self.time_num += time_difference
        self.timer_variable.set(self.get_time_format())

    def stop_timer(self):
        self.time_loop()
        self.run_timer = False

    def resume_timer(self):
        self.start_time = time.time()
        self.run_timer = True
        self.start_timer()

    def start_timer(self):
        while self.run_timer:
            self.time_loop()
            time.sleep(.09)

    def reset_time(self):
        self.start_time = time.time()
        self.time_num = 0
        self.run_timer = False
        self.timer_variable.set(self.get_time_format())

    def start(self):
        if not self.run_timer:
            threading.Thread(target=self.resume_timer).start()


class ToolBox:
    def __init__(self, tool_frame, players, layers, function):
        self.frame = tool_frame
        self.player_setting = tk.IntVar()
        self.layer_setting = tk.IntVar()
        self.display_setting = tk.IntVar()

        self.player_setting.set(0)
        self.layer_setting.set(0)
        self.display_setting.set(0)
        self.set_up_buttons(players, layers)

        self.parent_call = function

    def set_up_buttons(self, players, layers):
        full_layers = ['Mono Size 4', 'Mono Open 3', 'Combos', 'Combo-1 + Leading Move', 'Leading Moves', 'Combo-1', 'Leading-1', 'Combo-1 + Leading Move Creator']
        player_type = ['None', 'Player One', 'Player Two']
        sub_type = ["All", "T1", "T2"]

        for x in range(len(player_type)):
            tk.Radiobutton(self.frame, text=player_type[x], variable=self.player_setting, value=x, command=self.notify_board).pack(anchor=tk.W)

        for display_type in range(3):
            tk.Radiobutton(self.frame, text=sub_type[display_type], variable=self.display_setting, value=display_type, command=self.notify_board).pack(anchor=tk.W)

        counter = 0
        for layer_type in full_layers:
            tk.Radiobutton(self.frame, text=layer_type, variable=self.layer_setting, value=counter, command=self.notify_board).pack(anchor=tk.W)
            counter += 1

    def notify_board(self):
        self.parent_call(self.player_setting.get(), self.layer_setting.get(), self.display_setting.get())


class MovesFrame:
    def __init__(self, move_frame):
        self.text_box = tk.Text(move_frame, bg="#bbbbbb", font=("Times", 12))
        move_frame.update()
        self.text_box.place(x=0, y=0, height=move_frame.winfo_height(), width=move_frame.winfo_width())
        self.text_box.configure(state=tk.DISABLED)

    def insert_text(self, move):
        self.text_box.configure(state=tk.NORMAL)
        self.text_box.insert(tk.INSERT, move + "\n")
        self.text_box.configure(state=tk.DISABLED)

    def insert_move(self, player, turn_count, point):
        text = "(Turn %s) Player %s Move: %s" % (turn_count+1, player+1, chr(ord("A") + point[0]) + str(19-point[1]))
        self.insert_text(text)

    def undo_move(self):
        self.insert_text("Undo Move")

    def delete_game(self):
        self.text_box.configure(state=tk.NORMAL)
        self.text_box.delete("1.0", tk.END)
        self.text_box.configure(state=tk.DISABLED)


class GameBoardFrame:
    def __init__(self, parent_frame, board_size, frame_size, board_rows, chain_size):
        self.frame_size = frame_size
        self.board_canvas = tk.Canvas(parent_frame, width=frame_size, height=frame_size)
        self.start_x = int((frame_size - board_size) / 2)
        self.end_x = frame_size - self.start_x
        self.tile_length = (frame_size - self.start_x * 2) / board_rows
        self.tile_length_o = (frame_size - self.start_x * 2) / board_rows
        self.rows = board_rows

        self.trash_board = None
        self.trash_stones = [None, None]
        self.text_style = None
        self.score_fill = None
        self.move_log = None
        self.map_points = self.generate_points()
        self.style_dictionary = self.load_style()
        self.display_value = 0
        self.r_points = []
        self.grid_notation = False

    def reset_variables(self):
        self.find_and_delete("stone")
        self.find_and_delete("line")
        self.map_points = self.generate_points()
        self.r_points = []

    def set_move_log(self, text_box):
        self.move_log = text_box

    def handle_click(self, x, y, player_type, pixel_point=True):
        if pixel_point:
            board_x = int((x - self.start_x) // self.tile_length)
            board_y = int((y - self.start_x) // self.tile_length)
            clicked_point = [board_x, board_y]
        else:
            clicked_point = [x, y]

        if clicked_point in self.map_points:
            #self.handle_turn(player_type, clicked_point)
            return True, clicked_point
            #self.handle_turn(1, [clicked_point[0] + 1, clicked_point[1] + 1])
        else:
            return False, clicked_point

    def get_remaining_points(self):
        return self.map_points

    def get_remaining_taken(self, num):
        num = len(self.r_points) - num
        a_list = self.r_points[num:]
        b_list = self.r_points[:num]
        self.r_points = b_list

        print("Stay Points", b_list)
        for x in a_list:
            self.map_points.append(x)
        return b_list

    def re_add(self, point):
        self.map_points.append(point)

    def handle_turn(self, stone_type, point):
        turn = (self.rows * self.rows) - len(self.map_points)
        self.move_log.insert_move(stone_type, turn, point)
        self.draw_stone(stone_type, point)
        self.map_points.remove(point)
        self.r_points.append(point)

    def generate_points(self):
        points = []
        for x in range(0, self.rows):
            for y in range(0, self.rows):
                points.append([x, y])
        return points

    def start_up_board(self, style_id):
        self.draw_board_color("#000000")
        self.draw_board_image(GUI_IMAGES + "Spruce.gif")
        self.draw_board_text("#000000", True, "Coord")
        self.draw_board_text("#000000", False, "Formal")
        self.draw_grid("#000000")
        self.apply_style(style_id)
        self.find_and_hide("Formal")

    def find_and_hide(self, board_tag):
        for tag in self.board_canvas.find_withtag(board_tag):
            self.board_canvas.itemconfig(tag, state="hidden")

    def find_and_show(self, board_tag):
        for tag in self.board_canvas.find_withtag(board_tag):
            self.board_canvas.itemconfig(tag, state="normal")

    def get_canvas(self):
        return self.board_canvas

    def apply_style(self, style_id):
        board_image = self.board_canvas.find_withtag("board_image")
        board_color = self.board_canvas.find_withtag("back")
        self.trash_stones[0] = self.prep_image(GUI_IMAGES + self.style_dictionary[style_id]["BlackStone"], self.tile_length - 7)
        self.trash_stones[1] = self.prep_image(GUI_IMAGES + self.style_dictionary[style_id]["WhiteStone"], self.tile_length - 7)

        if self.style_dictionary[style_id]["Type"]:
            self.board_canvas.itemconfig(board_image, state="normal")
            self.board_canvas.itemconfig(board_color, state="hidden")
            self.trash_board = self.prep_image(GUI_IMAGES + self.style_dictionary[style_id]["Board"], self.frame_size - self.start_x * 2)
            self.board_canvas.itemconfig(board_image, image=self.trash_board)
        else:
            self.board_canvas.itemconfig(board_image, state="hidden")
            self.board_canvas.itemconfig(board_color, state="normal")
            self.update_color_tag("back", self.style_dictionary[style_id]["Board"])

        self.update_stones()
        self.score_fill = self.style_dictionary[style_id]["ScoreText"]
        self.text_style = [self.style_dictionary[style_id]["BotOneText"], self.style_dictionary[style_id]["BotTwoText"]]
        self.update_common(style_id)
        self.raise_multiple(["stone_0", "stone_1", "line"])
        self.adjust_score_display(self.display_value)

    def adjust_score_display(self, value):
        self.display_value = value
        if value == 0:
            self.find_and_delete("score_text")
        elif value == 1:
            self.display_score(0)
        elif value == 2:
            self.display_score(1)

    def display_score(self, player):
        pass

    def update_stones(self):
        black_stones = self.board_canvas.find_withtag("black_stone")
        white_stones = self.board_canvas.find_withtag("white_stone")

        for bs in black_stones:
            self.board_canvas.itemconfig(bs, image=self.trash_stones[0])
            self.board_canvas.tag_raise(bs)
        for ws in white_stones:
            self.board_canvas.itemconfig(ws, image=self.trash_stones[1])
            self.board_canvas.tag_raise(ws)

    def draw_score_text(self, value, active):
        self.find_and_delete("score_text")
        for z in range(0, len(active)):
            if active[z]:
                point = [z % self.rows, int(z / self.rows)]
                x = point[0] * self.tile_length + self.start_x
                y = point[1] * self.tile_length + self.start_x
                self.board_canvas.create_text(x + self.tile_length / 2, y + self.tile_length / 2, font="Ariel, 14", fill="#" + self.score_fill, text=value[z], tags=("board", "score_text"))

    def update_common(self, style_index):
        self.update_background_color("#" + self.style_dictionary[style_index]["Background"])
        self.update_color_tag("grid", self.style_dictionary[style_index]["Line"])
        self.update_color_tag("text", self.style_dictionary[style_index]["BoardText"])
        self.update_color_tag("stone_0", self.style_dictionary[style_index]["BotOneText"])
        self.update_color_tag("stone_1", self.style_dictionary[style_index]["BotTwoText"])

    def raise_multiple(self, tag_list):
        for tag in tag_list:
            self.find_and_raise(tag)

    def update_color_tag(self, tag, color):
        item_id = self.board_canvas.find_withtag(tag)
        for item in item_id:
            self.board_canvas.itemconfig(item, fill="#"+color)

    def swap_grid_notation(self):
        self.find_and_hide("Formal" if self.grid_notation else "Coord")
        self.find_and_show("Coord" if self.grid_notation else "Formal")
        self.grid_notation = not self.grid_notation

    @staticmethod
    def load_style():
        with open(BOARD_STYLES) as styles:
            return json.load(styles)

    @staticmethod
    def prep_image(image_location, size):
        image = tk.PhotoImage(file=image_location)
        image_size = int(image.width() / size)
        #image_size -= 1
        return image.subsample(image_size, image_size)

    def pack_board(self, location):
        self.board_canvas.pack(side=location)

    def draw_board_text(self, color, proper, tag):
        #self.find_and_delete("text")
        tile_size = (self.frame_size - (self.start_x * 2)) / self.rows
        for x in range(0, self.rows):
            coord = self.start_x + (tile_size * x) + tile_size / 2
            char_x = x if proper else chr(ord("A") + x)
            char_y = x if proper else self.rows - x
            self.board_canvas.create_text(coord, self.start_x - 30, text=char_x, font="Ariel, 14", fill=color, tags=("board", "text", tag))
            self.board_canvas.create_text(self.start_x - 30, coord, text=char_y, font="Ariel, 14", fill=color, tags=("board", "text", tag))

    def draw_board_image(self, image):
        self.trash_board = self.prep_image(image, self.frame_size - self.start_x * 2)
        self.board_canvas.create_image((self.start_x, self.start_x), image=self.trash_board, anchor=tk.NW, tags=("board", "board_image"))

    def draw_board_color(self, color):
        self.board_canvas.create_rectangle(self.start_x, self.start_x, self.end_x, self.end_x, fill=color, tags=("board", "back"), outline="")

    def draw_grid(self, color):
        board_start = self.start_x + self.tile_length / 2
        board_end = self.frame_size - board_start
        for x in range(0, self.rows):
            coord = self.start_x + (self.tile_length_o * x) + self.tile_length / 2
            self.board_canvas.create_line(board_start, coord, board_end, coord, fill=color, tags=("board", "grid"))
            self.board_canvas.create_line(coord, board_start, coord, board_end, fill=color, tags=("board", "grid"))

    def draw_line(self, points):
        self.get_point_coord(points[0])
        self.get_point_coord(points[4])
        self.board_canvas.create_line(points[0][0], points[0][1], points[4][0], points[4][1], fill="red", width=2, tags=("board", "line"))

    def get_point_coord(self, point):
        point[0] = point[0] * self.tile_length + self.start_x + self.tile_length / 2
        point[1] = point[1] * self.tile_length + self.start_x + self.tile_length / 2

    def draw_stone_text(self, stone_type, point):
        turn = (self.rows * self.rows) - len(self.map_points)

        x = point[0] * self.tile_length + self.start_x + self.tile_length/2
        y = point[1] * self.tile_length + self.start_x + self.tile_length/2
        self.board_canvas.create_text(x, y, text=turn, font="Ariel, 14", fill="#" + self.text_style[stone_type], tags=("board", "stone", "stone_" + str(stone_type)))

    def draw_stone(self, stone_type, coord):
        my_tags = [("board", "black_stone", "stone"), ("board", "white_stone", "stone")]
        coord_x = coord[0] * self.tile_length + self.start_x
        coord_y = coord[1] * self.tile_length + self.start_x
        self.board_canvas.create_image((coord_x, coord_y), image=self.trash_stones[stone_type], anchor=tk.NW, tags=my_tags[stone_type])

    def draw_box(self, coord, color):
        coord_x = coord[0] * self.tile_length + self.start_x
        coord_y = coord[1] * self.tile_length + self.start_x
        self.board_canvas.create_rectangle(coord_x, coord_y, coord_x+self.tile_length, coord_y+self.tile_length, fill=color, tags=("board", "layer"), outline="")

    def update_background_color(self, color):
        self.board_canvas.config(bg=color)

    def update_grid_color(self, color):
        for line in self.board_canvas.find_withtag("grid"):
            self.board_canvas.itemconfig(line, fill=color)

    def find_and_delete_last(self, tag):
        objects = self.board_canvas.find_withtag(tag)
        self.board_canvas.delete(objects[len(objects) - 1])

    def find_and_delete(self, tag):
        objects = self.board_canvas.find_withtag(tag)
        for object_id in objects:
            self.board_canvas.delete(object_id)

    def find_and_raise(self, tag):
        objects = self.board_canvas.find_withtag(tag)
        for object_id in objects:
            self.board_canvas.tag_raise(object_id)
