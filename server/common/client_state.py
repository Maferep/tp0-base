from common.utils import load_bets, has_won
class Client:
    def __init__(self, id):
        assert(isinstance(id, int))
        self.id = id
        self.done = False
        # self.requested_results = False

    def receive_done_message(self):
        self.done = True

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
            self.announce_winners(winners)
    
    def do_poll(self):
        print("Do poll")
        bets = load_bets()
        winners = []
        for bet in bets:
            if has_won(bet):
                winners.append(bet)
        return winners

    def announce_winners(self, winners):
        for i in range(1, 5+1):
            agency_winners = [(bet.first_name) for bet in winners if bet.agency == i]
            print(f"winners for {i}: {agency_winners}")