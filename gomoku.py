#!/usr/bin/env python3
from gui import *
from bot import Bot
from bot_2 import Bot as oldBot

# The engine may work with any gomoku bot, as long as it has the following methods:
#---------------- start(): ----------------#
# takes no arguments and returns the bot's opening move coordinates in form [x, y]
# [0, 0] is the top left corner, x increases horizontally and y increases vertically

#-------------- new_board(): --------------#
# takes no arguments and returns nothing
# just completely resets the bot internally to prepare for the next game

#---------- turn(opponent_move): ----------#
# takes the opponent's last move as an argument, in form [x, y]
# returns the bot's response move, also in form [x, y]


# Initialize bots that will be used
first = Bot(19)
second = oldBot(19)

# Run main game loop
game = Game(screen, False, True, colors, ltheme, dtheme, first, second)
while game.running:
    clock.tick(fps)
    game.check_input()
    game.draw_screen()

pygame.quit()
