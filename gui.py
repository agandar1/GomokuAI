#!/usr/bin/env python3
import pygame
import math
from pathlib import Path

screen = pygame.display.set_mode((1000, 1060))

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
# Images
LIGHT_THEME = pygame.image.load(Path("img/board.png"))
DARK_THEME = pygame.image.load(Path("img/board_dark1.png"))
play_first_img_button = pygame.image.load('img/play_first.png').convert_alpha()
play_second_img_button = pygame.image.load('img/play_second.png').convert_alpha()
ai_vs_ai_img_button = pygame.image.load('img/ai_vs_ai.png').convert_alpha()
theme_img_button = pygame.image.load('img/theme.png').convert_alpha()
exit_img_button = pygame.image.load('img/exit.png').convert_alpha()
# Misc
CLOCK = pygame.time.Clock()
FPS = 60


class Button:
    def __init__(self, x_button, y_button, image_button):
        self.image_button = image_button
        self.rect = self.image_button.get_rect()
        self.rect.topleft = (x_button, y_button)
        self.clicked = False

    def draw(self):
        screen.blit(self.image_button, (self.rect.x, self.rect.y))

    def check_click(self):
        action = False

        # get mouse position
        pos = pygame.mouse.get_pos()
        # check mouseover and clicked conditions
        if self.rect.collidepoint(pos):
            if pygame.mouse.get_pressed()[0] == 1:
                action = True

        if pygame.mouse.get_pressed()[0] == 0:
            self.clicked = False

        return action


class Game:
    def __init__(self, bot_first):
        self.running = True
        self.black_turn = True
        self.board = LIGHT_THEME
        self.screen = pygame.display.set_mode((1000, 1060))
        self.points = [[62+(49*x), 122+(49*y), -1]
                       for x in range(19) for y in range(19)]
        self.first_button = Button(0, 10, play_first_img_button)
        self.second_button = Button(200, 10, play_second_img_button)
        self.ai_vs_ai_button = Button(400, 10, ai_vs_ai_img_button)
        self.theme_button = Button(600, 10, theme_img_button)
        self.exit_button = Button(800, 10, exit_img_button)


    def nearest(self, pos):
        """find which point is closest to the mouse"""
        pos = list(pos)
        closest = 0
        dist = math.dist(pos, self.points[0][:2])
        for i in range(len(self.points)):
            p = self.points[i]
            new_dist = math.dist(pos, p[:2])
            if new_dist < dist:
                dist = new_dist
                closest = i
        print(closest)
        return closest

    def place_piece(self, pos):
        index = self.nearest(pos)
        if self.points[index][2] == -1:
            self.points[index][2] = 0 if self.black_turn else 1
            self.black_turn = not self.black_turn        

    def check_input(self):
        """check for user input"""
        pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if 1028 > pos[1] > 95 and 965 > pos[0] > 35:
                    self.place_piece(pos)
            # check for mouse click on buttons can go here maybe
                if self.first_button.check_click():
                    print("START FIRST")
                if self.second_button.check_click():
                    print("START SECOND")
                if self.ai_vs_ai_button.check_click():
                    print("SPECTATING")
                if self.theme_button.check_click():
                    self.board = DARK_THEME if self.board == LIGHT_THEME else LIGHT_THEME
                    print("THEME CHANGED")
                if self.exit_button.check_click():
                    # print("GOODBYE")
                    self.running = False

    def draw_screen(self):
        """draw everything on the screen"""
        # draw board
        self.screen.blit(self.board, (0, 0))
        #draw buttons
        self.screen.blit(self.first_button.image_button, (self.first_button.rect.x, self.first_button.rect.y))
        self.screen.blit(self.second_button.image_button, (self.second_button.rect.x, self.first_button.rect.y))
        self.screen.blit(self.ai_vs_ai_button.image_button, (self.ai_vs_ai_button.rect.x, self.first_button.rect.y))
        self.screen.blit(self.theme_button.image_button, (self.theme_button.rect.x, self.first_button.rect.y))
        self.screen.blit(self.exit_button.image_button, (self.exit_button.rect.x, self.first_button.rect.y))

        # draw pieces
        for p in self.points:
            if p[2] != -1:
                color = BLACK if (p[2] == 0) else WHITE
                pygame.draw.circle(self.screen, color, p[:2], 24)

        # finally flip display
        pygame.display.flip()

# Run main game loop
game = Game(bot_first=False)
while game.running:
    CLOCK.tick(FPS)
    game.check_input()
    game.draw_screen()

pygame.quit()
