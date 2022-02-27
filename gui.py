#!/usr/bin/env python3
import pygame
import math
from pathlib import Path


# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
# Images
LIGHT_THEME = pygame.image.load(Path("img/board.png"))
DARK_THEME = pygame.image.load(Path("img/board_dark.png"))
# Misc
CLOCK = pygame.time.Clock()
FPS = 60

class Game:
    def __init__(self, bot_first):
        self.running = True
        self.black_turn = True
        self.board = LIGHT_THEME
        self.screen = pygame.display.set_mode((1000, 1060))
        self.points = [[62+(49*x), 122+(49*y), -1]
                       for x in range(19) for y in range(19)]
        
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


    def draw_screen(self):
        """draw everything on the screen"""
        # draw board
        self.screen.blit(self.board, (0, 0))

        # drawing buttons can go here

        # draw pieces
        for p in self.points:
            if p[2] != -1:
                color = BLACK if (p[2] == 0) else WHITE
                pygame.draw.circle(self.screen, color, p[:2], 25)

        # finally flip display
        pygame.display.flip()
        
        

# Run main game loop
game = Game(bot_first=False)
while game.running:
    CLOCK.tick(FPS)
    game.check_input()
    game.draw_screen()

pygame.quit()
