# GomokuAI
**Gomoku AI Senior Project**
This project uses Minimax Algorithm and Monomials to play gomoku.
As part of the project, we created a gomoku GUI in racket to play the ai's against each other.

**To Just Play**
You should have Python3 and Numpy installed for the included AIs to work
We included windows and linux executables that start the default ai's automatically, (files "gomoku-windows.exe"" and "gomoku-linux") just run it and it should be good to go.
You shouldn't need to install racket to run these executables, they should just run.
You can also run the file "gomoku_old_engine.py" with python3 to see our first gui

**To Connect Custom AI**
The GUI also supports connecting other ai's written in any language, as long as they follow the compatibility criteria.

To use your own ai with our engine: 
1. install racket to your computer
3. run the file "gomoku.rkt" manually in one command prompt
4. start running the first ai client in a second command prompt
5. start running the second ai client in a third command prompt
6. enjoy.

**Included AIs**
We have included two ai's: our minimax ai ("minimax\_client.py"), and a previous year's gomoku project ("oscar\_client.py")
They are used as the default options if you just run the executable
You can also connect them manually using the custom ai instructions above

**AI Client Compatibility**
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
