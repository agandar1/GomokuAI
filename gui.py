import pygame
import math
from bot import Bot
from bot_old import Bot as oldBot


class Button:
    def __init__(self, x, y, image):
        self.image = image
        self.x, self.y = x, y
        self.rect = self.image.get_rect(topleft=(x, y))

    def clicked(self, pos):
        if (self.rect.collidepoint(pos)):
            return True

    def draw(self, screen):
        screen.blit(self.image, (self.x, self.y))


class Game:
    def __init__(self, screen, bot_first, human_playing, colors, ltheme, dtheme):
        self.screen = screen
        self.bot = Bot(19)
        self.old_bot = oldBot(19)
        self.running, self.game_over = True, False
        self.human_playing = human_playing
        self.colors = colors
        self.ltheme, self.dtheme = ltheme, dtheme
        self.theme = ltheme
        coords = [[62+(49*x), 122+(49*y), -1] for x in range(19) for y in range(19)]
        self.points = [coords[x:x+19] for x in range(0, len(coords), 19)]
        if bot_first:
            self.place_piece(self.bot.start(), True)
            self.black_turn = False
        else:
            self.black_turn = True

    def nearest(self, pos):
        """find which point is closest to the mouse"""
        pos = list(pos)
        closest = (0, 0)
        dist = math.dist(pos, self.points[0][0][:2])
        for x in range(len(self.points)):
            for y in range(len(self.points[0])):
                p = self.points[x][y]
                new_dist = math.dist(pos, p[:2])
                if (new_dist < dist):
                    dist = new_dist
                    closest = (x, y)
        return closest

    def place_piece(self, pos, bot_move):
        placed = False
        i = [pos[0], pos[1]] if bot_move else self.nearest(pos)
        p = self.points[i[0]][i[1]]
        if (p[2] == -1):
            p[2] = 0 if self.black_turn else 1
            self.black_turn = not self.black_turn        
            placed = True
        self.game_over = self.check_win(i)
        return (i, placed)

    def check_win(self, coords):
        point = self.points[coords[0]][coords[1]]
        color = point[2]
        x, y = coords[0], coords[1]
        directions = [(1, 0), (0, 1), (1, 1), (-1, 1)]
        
        for d in directions:
            counts = [0, 0] 
            for n in ((1, 0), (-1, 1)):
                for i in range (1, 5):
                    newx, newy = x+(n[0]*(i*d[0])), y+(n[0]*(i*d[1]))
                    if (-1 < newx < 19 and -1 < newy < 19):
                        if (self.points[newx][newy][2] == color):
                            counts[n[1]] += 1
                        else: break
            if (counts[0] + counts[1] >= 4): return ((x, y), counts[0], d)

        return False

    def draw_line(self, info):
        x, y = info[0][0], info[0][1]
        count1 = info[1] if info[1] < 5 else 5
        direction = info[2]
        spots = []
        for i in range(count1+1):
            newx, newy = x + (i * direction[0]), y + (i * direction[1])
            spots.append(self.points[newx][newy][:2])
        for i in range(5 - count1):
            newx, newy = x - (i * direction[0]), y - (i * direction[1])
            spots.append(self.points[newx][newy][:2])
        for s in spots:
            pygame.draw.line(self.screen, self.colors["red"], spots[0], s, 5)
            

    def new_game(self, player_first, ai_vs_ai):
        self.running = True
        self.game_over = False
        self.human_playing = not ai_vs_ai
        
        for x in range(len(self.points)):
            for y in range(len(self.points[0])):
                self.points[x][y][2] = -1
        self.bot.new_board()
        self.old_bot.new_board()

        self.black_turn = True
        if (not player_first and not ai_vs_ai):
            self.place_piece(self.bot.start(), True)
        elif (ai_vs_ai):
            self.ai_vs_ai()
            
    def ai_vs_ai(self):
        move = self.old_bot.start()
        self.place_piece(move, True)
        self.draw_screen()
        self.check_input()
        old_turn = False
        while (not self.game_over and not self.human_playing and self.running):
            keys = pygame.key.get_pressed()
            pygame.event.pump()
            if (keys[pygame.K_SPACE]):
                if old_turn:
                    move = self.old_bot.turn(move)
                    old_turn = False
                else:
                    move = self.bot.turn(move)
                    old_turn = True
                self.place_piece(move, True)
                self.draw_screen()
            self.check_input()
            
    def check_input(self):
        """check for user input"""
        pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if (event.type == pygame.QUIT):
                self.running = False

            elif (event.type == pygame.MOUSEBUTTONDOWN):
                if (1028 > pos[1] > 95 and 965 > pos[0] > 35):
                    if (not self.game_over and self.human_playing):
                        move = self.place_piece(pos, False)
                        self.draw_screen()
                        if (not self.game_over and move[1] == True):
                            self.place_piece(self.bot.turn(move[0]), True)

                if (self.theme["play1"].clicked(pos)):
                    self.new_game(player_first=True, ai_vs_ai=False)

                if (self.theme["play2"].clicked(pos)):
                    self.new_game(player_first=False, ai_vs_ai=False)

                if (self.theme["ai_vs_ai"].clicked(pos)):
                    self.new_game(player_first=False, ai_vs_ai=True)

                if (self.theme["theme"].clicked(pos)):
                    if (self.theme == self.ltheme):
                        self.theme = self.dtheme
                    else:
                        self.theme = self.ltheme

                if (self.theme["exit"].clicked(pos)):
                    self.running = False

    def draw_screen(self):
        """draw everything on the SCREEN"""
        # draw board
        self.screen.blit(self.theme["board"], (0, 0))

        #draw buttons
        self.theme["play1"].draw(self.screen)
        self.theme["play2"].draw(self.screen)
        self.theme["ai_vs_ai"].draw(self.screen)
        self.theme["theme"].draw(self.screen)
        self.theme["exit"].draw(self.screen)

        # draw pieces
        for x in range(len(self.points)):
            for y in range(len(self.points[0])):
                p = self.points[x][y]
                if (p[2] != -1):
                    if (p[2] == 0):
                        color = self.colors['black']
                    else:
                        color = self.colors['white']
                    pygame.draw.circle(self.screen, color, (p[0], p[1]), 24)

        # draw winning line
        if (self.game_over):
            self.draw_line(self.game_over)

        # finally flip display
        pygame.display.flip()


# Globals
screen = pygame.display.set_mode((1000, 1060))
clock = pygame.time.Clock()
fps = 60
colors = {
    "black": (0, 0, 0),
    "white": (255, 255, 255),
    "red": (179, 46, 46)
}
ltheme = {
    "board": pygame.image.load("img/board.png"),
    "play1": Button(10, 5, pygame.image.load("img/play1.png").convert_alpha()),
    "play2": Button(207, 5, pygame.image.load("img/play2.png").convert_alpha()),
    "ai_vs_ai": Button(405, 5, pygame.image.load("img/ai.png").convert_alpha()),
    "theme": Button(600, 5, pygame.image.load("img/theme.png").convert_alpha()),
    "exit": Button(807, 5, pygame.image.load("img/exit.png").convert_alpha())
}
dtheme = {
    "board": pygame.image.load("img/board_dark.png"),
    "play1": Button(10, 5, pygame.image.load("img/play1_dark.png").convert_alpha()),
    "play2": Button(207, 5, pygame.image.load("img/play2_dark.png").convert_alpha()),
    "ai_vs_ai": Button(405, 5, pygame.image.load("img/ai_dark.png").convert_alpha()),
    "theme": Button(600, 5, pygame.image.load("img/theme_dark.png").convert_alpha()),
    "exit": Button(807, 5, pygame.image.load("img/exit_dark.png").convert_alpha()),
}


# Run main game loop
game = Game(screen, False, True, colors, ltheme, dtheme)
while game.running:
    clock.tick(fps)
    game.check_input()
    game.draw_screen()

pygame.quit()
