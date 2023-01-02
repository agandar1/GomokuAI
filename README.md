# GomokuAI
**Gomoku AI Senior Project**\
This project uses Minimax Algorithm and Monomials to play gomoku.
As part of the project, we created a gomoku GUI in racket to play the ai's against each other.

**To Just Play**\
You should have the following installed for the included AIs to work:
1. Python 3
2. Numpy
3. Racket from https://download.racket-lang.org/ \

Run the gomoku.rkt racket file first, then the bot client python files with the following commands:
1. racket gomoku.rkt
2. python3 minimax\_client.py
2. python3 oscar\_client.py
You might need to use separate terminals for this.
You can also run the file "gomoku_old_engine.py" with python3 to see our initial gui

**To Connect Custom AI**\
The GUI also supports connecting other ai's written in any language, as long as they follow the compatibility criteria.
To use your own ai with our engine, follow the same steps as above, but start your own bot client instead of the included ones. 

**Included AIs**\
We have included two ai's: our minimax ai ("minimax\_client.py"), and a previous year's gomoku project ("oscar\_client.py")

**AI Client Compatibility**\
You may use any ai you make as long as it meets these criteria:
1. It must connect to the server at host "127.0.0.1" port 8085 via TCP socket
2. Immediately upon connection, it should send it's name to the server (e.g. "Minimax")
3. Then it should just wait for commands from the server and reply accordingly
4. Commands will be delivered as a string in this format: "command/row, col" where command is the command to be run, row and col are row and column coordinates on the board.
5. Your AI should support the following commands:
   * "close/0, 0": terminate connection, no return
   * "start/0, 0": return your AI's opening move in format "(row col)"
   * "new_game/0, 0": clear the board and prepare for the next game, no return
   * "turn/row, col": opponent just played in (row, col), return your AI's response in format "(row col)"
