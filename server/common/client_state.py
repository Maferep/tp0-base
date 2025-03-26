from common.utils import load_bets, has_won
from common.protocol import parse_message, MessageStream, send_message
from common.utils import store_bets
import logging
class Client:
    def __init__(self, id):
        assert(isinstance(id, int))
        self.id = id
        self.results_message = None
        self.socket = None
        self.notify_done = None 
        self.wants_results = False
        self.close_connection = False
        self.finish_receiving_bets = False

    def listen_for_done(self, listener):
        self.notify_done = listener

    def receive_done_message(self):
        self.notify_done.notify_done(self)

    def request_results(self):
        if self.results_message:
            send_message(self.results_message, self.socket)
        else:
            self.wants_results = True

    def notify_results(self, results_message):
        if self.wants_results: #send results
            send_message(results_message, self.socket)
        else: # store result for later sending
            self.results_message = results_message

    def receive_bets(self):
        while not self.finish_receiving_bets:
            try:
                self.receive_message()
            except OSError as e:
                logging.error(f"action: receive_message | result: fail | error: {e}")
                break
            except Exception as e:
                logging.error(f"action: receive_message | result: fail | error: {e}")
                break

    def receive_raffle_request(self):
        while not self.wants_results:
            try:
                self.receive_message()
            except OSError as e:
                logging.error(f"action: receive_message | result: fail | error: {e}")
                break
            except Exception as e:
                logging.error(f"action: receive_message | result: fail | error: {e}")
                break
        assert self.wants_results, "could not receive raffle request"

    def receive_message(self) -> bool:
        message = self.stream.get_message()
        description, content = parse_message(message)
        if description == "Done":
            _client_id = int(content)
            self.receive_done_message()
            self.finish_receiving_bets = True
        elif description == "RequestWinners":
            self.request_results()
        else:
            bets = content[0]
            _client_id = content[1]
            store_bets(bets)
            logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(bets)}')
        
            addr = self.socket.getpeername()
            logging.info(f'msg: {message[0:20]}')
        
            response = "OK"
            send_message(response, self.socket)

class Clients:
    def __init__(self, quantity):
        self.done_counter = 0
        self.client_state : dict = {}
        for i in range(1,quantity+1):
            self.client_state[i] = Client(i)
            self.client_state[i].listen_for_done(self)
    
    def do_poll(self):
        bets = load_bets()
        winners = []
        for bet in bets:
            if has_won(bet):
                winners.append(bet)
        return winners

    def set_socket(self, _id, sock):
        self.client_state[int(_id)].socket = sock

    def handle_connection(self, client_id, stream, sock):
        self.client_state[client_id].socket = sock
        self.client_state[client_id].stream = stream
        self.client_state[client_id].receive_bets()
        self.client_state[client_id].receive_raffle_request()

    def announce_winners(self, winners):
        # notify winners
        for _id in range(1, 5+1):
            agency_winners_dnis = [(bet.document) for bet in winners if bet.agency == _id]
            results = "|".join(agency_winners_dnis)
            results_message = "Results|{}".format(results) # TODO move to protocol
            self.client_state[_id].notify_results(results_message)

    def notify_done(self, client):
        self.done_counter += 1
        if self.done_counter == 5:
            winners = self.do_poll()
            print("action: sorteo | result: success")
            self.announce_winners(winners)
