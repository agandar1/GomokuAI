#!/usr/bin/env python3
import pygame
import math
from pathlib import Path

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
# Themes
LIGHT = pygame.image.load(Path("img/board.png"))
DARK = pygame.image.load(Path("img/board_dark.png"))


class Game:
    def __init__(self):
        self.running = True
        self.board = LIGHT
        self.screen = pygame.display.set_mode((1000, 1060))
        self.points = [[62+(49*x), 122+(49*y), 0]
                       for x in range(19) for y in range(19)]
        
    def nearest(self, pos):
        """find which point is closest to the mouse"""
        pos = list(pos)
        closest = self.points[0][:2]
        dist = math.dist(pos, closest)
        for p in self.points:
            new_dist = math.dist(pos, p[:2])
            if new_dist < dist and p[2] == 0:
                dist = new_dist
                closest = tuple(p[:2])
        return closest

    def check_input(self):
        """check for user input"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    def draw_screen(self):
        """draw everything on the screen"""
        self.screen.blit(self.board, (0, 0))

        pos = pygame.mouse.get_pos()
        if 1028 > pos[1] > 95 and 965 > pos[0] > 35:
            pygame.draw.circle(self.screen, BLACK, self.nearest(pos), 25)

        pygame.display.flip()
        

# Run main game loop
game = Game()
while game.running:
    game.check_input()
    game.draw_screen()

pygame.quit()
