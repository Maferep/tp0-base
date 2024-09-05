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
        self.queue.put((self.id, "Done"))

    def request_results(self):
        '''
        block reading from socket until we get results, then send them back to agencys
        '''
        print(f"Got result request for {self.id}")
        self.state = "requested"
        if self.results_ready:
            send_message(self.results_ready, self.socket)
        else:
            self.queue.put((self.id, "Request"))
            results_message = self.queue.get()[1]
            send_message(results_message, self.socket)

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
            self.receive_message()


    def receive_message(self):
        message = self.stream.get_message()
        description, content = parse_message(message)
        if description == "Done":
            print("received a done message from {}".format(content))
            _client_id = int(content)
            self.receive_done_message()
        elif description == "RequestWinners":
            self.state = "requested"
            self.request_results() # blocks until we get results
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
    
    def do_poll(self):
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


    def announce_winners(self, winners):
        for _id in range(1, 5+1):
            agency_winners_dnis = [(bet.document) for bet in winners if bet.agency == _id]
            results = "|".join(agency_winners_dnis)
            results_message = "Results|{}".format(results) # TODO move to protocol
            print(results_message)
            
            q = self.active_processes[client_id][1]
            q.put(("Results", results_message))

    def notify_done(self, client):
        print(f"Got done message from {client.id}")
        self.done_counter += 1
        if self.done_counter == len(self.client_state.keys()):
            winners = self.do_poll()
            print("action: sorteo | result: success")
            self.announce_winners(winners)


def client_handle_connection(client : Client, queue: multiprocessing.Queue) -> Client:
    client.queue = queue
    client.handle_connection()
    # socket descriptor closed implicitly
    return