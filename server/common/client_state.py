from common.utils import load_bets, has_won
from common.protocol import parse_message, MessageStream, send_message
class Client:
    def __init__(self, id):
        assert(isinstance(id, int))
        self.id = id
        self.done = False
        self.wants_results = False
        self.socket = None
        # self.requested_results = False

    def receive_done_message(self):
        self.done = True
    def request_results(self):
        self.wants_results = True
    def requested_results(self):
        return self.wants_results

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

    def request_results(self, id):
        print(f"Got result request from {id}")
        self.client_state[id].request_results()
    
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
        for id in range(1, 5+1):
            agency_winners_dnis = [(bet.document) for bet in winners if bet.agency == id]
            if self.client_state[id].requested_results(): # this should be true for every successful client
                # send using socket associated with this id (it should still be open!)
                results = "|".join(agency_winners_dnis)
                results_message = "Results|{}".format(results) # TODO move to protocol
                print(results_message)
                send_message(results_message, self.client_state[id].socket)