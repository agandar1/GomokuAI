import socket
import sys
from minimax import Bot


class BotClient:
    def __init__(self, host, port, name, bot):
        self.host = host
        self.port = port
        self.name = name
        self.bot = bot

        # create socket
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error:
            print('Failed to create socket')
            sys.exit()
        # Connect to socket
        self.s.connect((host, port))
        # send name to server
        self.send_data(self.name)
        # start communication
        self.send_recieve_loop()

    def coord_to_str(self, coord):
        """convert the bot's coordinates tuple to racket list"""
        return "({x[0]} {x[1]})".format(x=coord)

    def send_data(self, data):
        """send the data through the socket"""
        new_data = str(data)+'\n'
        try:
            self.s.send(str.encode(new_data))
        except socket.error:
            print('Send failed')
            sys.exit()

    def send_recieve_loop(self):
        close = False
        while not close:
            reply = self.s.recv(1024).decode("utf-8").replace('"', '')
            reply_lst = reply.split('/')
            command, point = reply_lst[0], reply_lst[1]
            if command == "close":
                close = True
            elif command == "start":
                response = self.coord_to_str(self.bot.start())
                self.send_data(response)
            elif command == "new_game":
                self.bot.new_board()
            elif command == "turn":
                coords = tuple(map(int, point.split(', ')))
                response = self.coord_to_str(self.bot.turn(coords))
                self.send_data(response)
        print("exiting")
    
BotClient('127.0.0.1', 8085, "Minimax", Bot())
