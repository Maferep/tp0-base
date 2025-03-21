from common.utils import Bet, store_bets
class MessageStream:
	def __init__(self, socket):
		self.buffer =  b''
		self.socket = socket
		self.messages = []

	def get_message(self):
		while not self.messages:
			recv = self.socket.recv(1024)
			self.buffer += recv
			strings = self.buffer.split(b'\n')
			if len(strings) == 1: continue 
			self.buffer = strings[-1]
			# consume message and ignore leftover
			self.messages += strings[:-1]
		message = self.messages.pop(0)
		message = message.rstrip().decode('utf-8')
		return message

def parse_bet(message):
	args = message.split("|")
	if len(args) != 5:
		print(f"Bad message ${args}")
	return Bet(123, args[0], args[1], args[2], args[3], args[4])