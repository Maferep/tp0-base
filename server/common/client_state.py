from common.utils import load_bets, has_won
from common.protocol import parse_message, MessageStream, send_message
from common.utils import store_bets
import logging
import multiprocessing
import queue

class Client:
    def __init__(self, id):
        assert(isinstance(id, int))
        self.id = id
        self.state = "batch"
        self.results_ready = None # used sif clients request arrives after poll
        self.socket = None
        self.queue = None

    def receive_done_message(self):
        self.state = "done"
        self.queue.put(("Done",self.id))
        print("received a done message from {}".format(self.id))

    def request_results(self):
        print(f"Got result request for {self.id}")
        self.state = "requested"
        if self.results_ready:
            send_message(self.results_ready, self.socket)
        else:
            self.queue.put(("Request", self.id))
    def handle_connection(self):
        while self.state == "batch":
            # read from net socket
            try:
                self.receive_message()
            except OSError as e:
                logging.error(f"action: receive_message | result: fail | error: {e}")
                self.state = "error"
                break
            except Exception as e:
                logging.error(f"action: receive_message | result: fail | error: {e}")
                self.state = "error"
                break
        while self.state == "done":
            print("were done")
            self.receive_request_message()
        assert(self.state == "requested")
        # name, results_message = self.queue.get(timeout = 0.1) #BUG
        send_message("12345", self.socket)

    def receive_request_message(self):
        print("getting message...")
        message = self.stream.get_message()
        description, content = parse_message(message)
        if description == "RequestWinners":
            self.request_results()


    def receive_message(self):
        print("getting message...")
        message = self.stream.get_message()
        description, content = parse_message(message)
        if description == "Done":
            _client_id = int(content)
            self.receive_done_message()
        else:
            bets = content[0]
            _client_id = content[1]
            store_bets(bets)
            logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(bets)}')
        
            addr = self.socket.getpeername()
            logging.info(f'action: receive_message | result: success | ip: {addr[0]} | msg: {message}')
        
            response = "OK"
            send_message(response, self.socket)
        return

class Clients:
    def __init__(self, quantity):
        self.done_counter = 0
        self.client_state : dict = {}
        self.active_processes = {}
        for i in range(1,quantity+1):
            self.client_state[i] = Client(i)
    
    def do_raffle(self):
        bets = load_bets()
        winners = []
        for bet in bets:
            if has_won(bet):
                winners.append(bet)
        return winners

    def handle_connection(self, client_id, stream, sock):
        '''
        creates new process for us to communicate with the client
        and a queue to share a client object
        process stops once it receives 'done' message or error
        '''
        self.client_state[client_id].socket = sock
        self.client_state[client_id].stream = stream
        
        queue = multiprocessing.Queue()
        client = self.client_state[client_id]
        child = multiprocessing.Process(target=client_handle_connection, args=(client, queue,))
        child.start()
        self.active_processes[client_id] = (child, queue) # this will allow us to communicate w process later


        if len(self.active_processes) == 5 :
            print("waiting for subprocesses")
            while self.done_counter < 5:
                self.pop_message_queues()
            print("leave loop")

            


    def announce_winners(self, winners):
        for _id in range(1, 5+1):
            agency_winners_dnis = [(bet.document) for bet in winners if bet.agency == _id]
            results = "|".join(agency_winners_dnis)
            results_message = "Results|{}".format(results) # TODO move to protocol
            print(results_message)
            
            handle, q = self.active_processes[_id]
            q.put(("Results", results_message))

    def notify_done(self, id):
        print(f"Got done message from {id}")
        self.done_counter += 1
        if self.done_counter == len(self.client_state.keys()):
            winners = self.do_raffle()
            print("action: sorteo | result: success")
            self.announce_winners(winners)

    def pop_message_queues(self):
        val = self.active_processes.values()
        queues = [q for handle, q in val]
        print("check queues {}, counter {}", len(queues), self.done_counter)
        for q in queues:
            try:
                name, content = q.get(timeout=0.1)
                print("popped {} {}".format(name, content))
                if name == "Done":
                    id = content
                    self.notify_done(id)
                else:
                    pass
            except queue.Empty:
                print("empty")
                pass


def client_handle_connection(client : Client, queue: multiprocessing.Queue) -> Client:
    client.queue = queue
    client.handle_connection()
    # socket descriptor closed implicitly
    return