from common.utils import has_won
from common.thread_safe_bets import safe_load_bets
from common.client_state import Client
import logging
import multiprocessing
import queue

class Clients:
    def __init__(self, quantity):
        self.done_counter = 0
        self.client_state : dict = {}
        self.active_processes = {}
        for i in range(1,quantity+1):
            self.client_state[i] = Client(i)
            self.client_state[i].listen_for_done(self)

    def amount(self):
        return len(self.client_state)
    
    def do_raffle(self, lock):
        bets = safe_load_bets(lock)
        winners = []
        for bet in bets:
            if has_won(bet):
                winners.append(bet)
        return winners

    def handle_connection(self, client_id, stream, sock, file_lock):
        '''
        creates new process for us to communicate with the client
        and a queue to share a client object
        process stops once it receives 'done' message or error
        '''
        self.client_state[client_id].socket = sock
        self.client_state[client_id].stream = stream
        
        queue = multiprocessing.Queue()
        results_queue = multiprocessing.Queue()
        client = self.client_state[client_id]
        child = multiprocessing.Process(target=client_handle_connection, args=(client, queue, results_queue, file_lock))
        child.start()
        self.active_processes[client_id] = (child, queue, results_queue) # this will allow us to communicate w process later


        if len(self.active_processes) == self.amount():
            while self.done_counter < self.amount():
                self.pop_message_queues(file_lock)
            
    def announce_winners(self, winners):
        '''
        Announce winners to each active process
        '''
        for _id in range(1, self.amount()+1):
            agency_winners_dnis = [(bet.document) for bet in winners if bet.agency == _id]
            results = "|".join(agency_winners_dnis)
            results_message = "Results|{}".format(results) # TODO move to protocol
            
            
            handle, q, rq = self.active_processes[_id]

            # put raffle results in result queue
            rq.put(("Results", results_message))

    def notify_done(self, id, lock):
        '''
        Allow clients to notify that they are done sending bets
        '''
        self.done_counter += 1
        if self.done_counter == self.amount():
            winners = self.do_raffle(lock)
            logging.info("action: sorteo | result: success")
            self.announce_winners(winners)

    def pop_message_queues(self, lock):
        val = self.active_processes.values()
        queues = [q for handle, q, rq in val]
        
        for q in queues:
            try:
                name, content = q.get(timeout=0.1)
                
                if name == "Done":
                    id = content
                    self.notify_done(id, lock)
                else:
                    pass
            except queue.Empty:
                pass


def client_handle_connection(
        client : Client, 
        queue: multiprocessing.Queue, 
        results_queue: multiprocessing.Queue,
        lock) -> Client:
    client.queue = queue
    client.results_queue = results_queue
    client.receive_bets(lock)
    return