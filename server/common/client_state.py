from common.utils import load_bets, has_won
from common.protocol import parse_message, MessageStream, send_message
class Client:
    def __init__(self, id):
        assert(isinstance(id, int))
        self.id = id
        self.done = False
        self.wants_results = False
        self.results_ready = None # used if clients request arrives after poll
        self.socket = None
        # self.requested_results = False

    def receive_done_message(self):
        self.done = True

    def request_results(self):
        print(f"Got result request for {self.id}")
        self.wants_results = True
        if self.results_ready:
            send_message(self.results_ready, self.socket)

    def requested_results(self):
        return self.wants_results

    def notify_results(self, results_message):
        self.results_ready
        if self.wants_results:
            send_message(results_message, self.socket)
        else:
            self.results_ready = results_message

    # def receive_request_for_results()

class Clients:
    def __init__(self, quantity):
        self.done_counter = 0
        self.client_state : dict = {}
        for i in range(1,quantity+1):
            self.client_state[i] = Client(i)

    def receive_done_message(self, id):
        print(f"Got done message from {id}")
        self.client_state[id].receive_done_message()
        self.done_counter += 1
        if self.done_counter == len(self.client_state.keys()):
            winners = self.do_poll()
            print("action: sorteo | result: success")
            self.announce_winners(winners)

    def request_results(self, _id):
        self.client_state[_id].request_results()
    
    def do_poll(self):
        bets = load_bets()
        winners = []
        for bet in bets:
            if has_won(bet):
                winners.append(bet)
        return winners

    def set_socket(self, _id, sock):
        self.client_state[int(_id)].socket = sock

    def announce_winners(self, winners):
        for _id in range(1, 5+1):
            agency_winners_dnis = [(bet.document) for bet in winners if bet.agency == _id]
            results = "|".join(agency_winners_dnis)
            results_message = "Results|{}".format(results) # TODO move to protocol
            print(results_message)
            self.client_state[_id].notify_results(results_message)