#!/usr/bin/env python3
import pygame
from pathlib import Path

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

def nearest(c, base=60):
    c0 = base * round(c[0]/base)
    c1 = base * round(c[1]/base)
    return (c0, c1)


screen = pygame.display.set_mode((1000, 1060))
light_background = pygame.image.load(Path("img/board.png"))
dark_background = pygame.image.load(Path("img/board_dark.png"))


running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.blit(light_background, (0, 0))

    pos = pygame.mouse.get_pos()

    if 1003 > pos[1] > 120 and 940 > pos[0] > 60:
        pygame.draw.circle(
            screen, BLACK, nearest(pygame.mouse.get_pos()), 30
        )

    pygame.display.flip()

pygame.quit()
