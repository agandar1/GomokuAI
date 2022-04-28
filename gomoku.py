#!/usr/bin/env python3
import sys
sys.path.insert(0, 'oscar_Gomoku')
from gui import *
from bot import Bot
#from bot_2 import Bot as oldBot
from bot_nontree import Bot as oldBot
from minmax import Bot as mmBot
from lib import BotV5 as oscar_Bot

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
first_bot = mmBot()
#second_bot = oldBot(19)
second_bot = oscar_Bot.ComputerPlayer(19, 5)

# Game options
bot_first = False # does the bot go first by default?
slow_mode = True # need to press space between moves in ai_vs_ai

# Initialize the game
game = Game(
    screen,
    bot_first,
    colors,
    ltheme,
    dtheme,
    first_bot,
    second_bot,
    slow_mode
)

# Run main game loop
while game.running:
    clock.tick(fps)
    game.check_input()
    game.draw_screen()

pygame.quit()
