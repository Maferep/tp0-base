from common.utils import Bet, store_bets
class MessageStream:
	def __init__(self, socket):
		self.buffer =  b''
		self.socket = socket
		self.messages = []

	def get_message(self):
		'''
		Reads in chunk from the socket until a newline, stores leftover in self.buffer
		'''
		while not self.messages:
			recv = self.socket.recv(1024)
			self.buffer += recv
			strings = self.buffer.split(b'\n')
			if len(strings) == 1: continue 
			self.buffer = strings[-1]
			self.messages += strings[:-1]
		message = self.messages.pop(0)
		message = message.rstrip().decode('utf-8')
		return message

def parse_message(message):
	'''returns a tuple containing the type of mesage and its related values. 
	For example,
	("Bets", ([Bet1, Bet2, Bet3,...], agency_id))
	("Done", agency_number)
	'''
	mesage = str(message)
	if message[:4] == "Done":
		agency_id = message.split("|")[1]
		return ("Done", int(agency_id))
	elif message[:14] == "RequestWinners":
		agency_id = message.split("|")[1]
		return ("RequestWinners", int(agency_id))
	args = message.split('//')
	batch_data = args[0].split("|")
	agency_id = batch_data[0]
	size = batch_data[1]
	bets = args[1:]
	if not size.isnumeric() or not (len(bets) == int(size)):
		raise ValueError("Wrong batch size:{}".format(message))
	parsed_bets = []
	for bet in bets:
		parsed_bets.append(parse_bet(bet, agency_id))
	return ("Bets",(parsed_bets, agency_id))

def parse_bet(message, agency_id):
	args = message.split("|")
	if len(args) != 5:
		print(f"Bad message ${args}")
		return None
	return Bet(agency_id, args[0], args[1], args[2], args[3], args[4])

def send_message(message, client_sock):
	"""
	adds a separator newline and sends over the socket
	"""
	sending = "{}\n".format(message).encode('utf-8')
	bytes_sent = 0
	while bytes_sent < len(sending):
		bytes_sent += client_sock.send(sending[bytes_sent:])
	return bytes_sent