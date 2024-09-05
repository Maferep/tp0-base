from common.utils import load_bets, has_won
from common.protocol import parse_message, MessageStream, send_message
from common.utils import store_bets
import logging
class Client:
    def __init__(self, id):
        assert(isinstance(id, int))
        self.id = id
        self.done = False
        self.wants_results = False
        self.results_ready = None # used sif clients request arrives after poll
        self.socket = None
        self.observer_of_done = None
        # self.requested_results = False

    def listen_for_done(self, observer):
        self.observer_of_done = observer

    def receive_done_message(self):
        self.done = True
        self.observer_of_done.notify_done(self)

    def request_results(self):
        print(f"Got result request for {self.id}")
        self.wants_results = True
        if self.results_ready:
            send_message(self.results_ready, self.socket)

    def requested_results(self):
        return self.wants_results

    def notify_results(self, results_message):
        if self.wants_results:
            send_message(results_message, self.socket)
        else:
            self.results_ready = results_message

    def handle_connection(self):
        done = False
        while not done:
            try:
                done =  self.receive_message()
            except OSError as e:
                logging.error(f"action: receive_message | result: fail | error: {e}")
                break
            except Exception as e:
                logging.error(f"action: receive_message | result: fail | error: {e}")
                break

    def receive_message(self) -> bool:
        done = False
        message = self.stream.get_message()
        description, content = parse_message(message)
        if description == "Done":
            print("received a done message from {}".format(content))
            _client_id = int(content)
            self.receive_done_message()
        elif description == "RequestWinners":
            self.request_results()
            done = True
        else:
            bets = content[0]
            _client_id = content[1]
            store_bets(bets)
            logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(bets)}')
        
            addr = self.socket.getpeername()
            logging.info(f'action: receive_message | result: success | ip: {addr[0]} | msg: {message}')
        
            response = "OK"
            send_message(response, self.socket)
        return done

class Clients:
    def __init__(self, quantity):
        self.done_counter = 0
        self.client_state : dict = {}
        for i in range(1,quantity+1):
            self.client_state[i] = Client(i)
            self.client_state[i].observer_of_done = self
    
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
        self.client_state[client_id].handle_connection()

    def announce_winners(self, winners):
        for _id in range(1, 5+1):
            agency_winners_dnis = [(bet.document) for bet in winners if bet.agency == _id]
            results = "|".join(agency_winners_dnis)
            results_message = "Results|{}".format(results) # TODO move to protocol
            print(results_message)
            self.client_state[_id].notify_results(results_message)

    def notify_done(self, client):
        print(f"Got done message from {client.id}")
        self.done_counter += 1
        if self.done_counter == len(self.client_state.keys()):
            winners = self.do_poll()
            print("action: sorteo | result: success")
            self.announce_winners(winners)
