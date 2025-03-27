from common.protocol import parse_message, send_message
from common.thread_safe_bets import safe_store_bets
import logging

class Client:
    def __init__(self, id):
        assert(isinstance(id, int))
        self.state = "batch"
        self.queue = None # to notify main process of events
        self.results_queue = None # to get the result of the raffle
        

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
        self.state = "done"
        self.queue.put(("Done",self.id))
        

    def request_results(self):
        
        self.state = "requested"
        if self.results_message:
            send_message(self.results_message, self.socket)
        else:
            self.queue.put(("Request", self.id))

    def notify_results(self, results_message):
        if self.wants_results: #send results
            send_message(results_message, self.socket)
        else: # store result for later sending
            self.results_message = results_message

    def receive_bets(self, lock):
        while self.state == "batch":
            # read from net socket
            try:
                self.receive_message(lock)
            except OSError as e:
                logging.error(f"action: receive_message | result: fail | error: {e}")
                self.state = "error"
                break
            except Exception as e:
                logging.error(f"action: receive_message | result: fail | error: {e}")
                self.state = "error"
                break
        while self.state == "done":
            self.receive_request_message()
        assert(self.state == "requested")
        name, results_message = self.results_queue.get() # wait for ("Results", results_message)
        send_message(results_message, self.socket)

    def receive_request_message(self):
        
        message = self.stream.get_message()
        description, content = parse_message(message)
        if description == "RequestWinners":
            self.request_results()


    def receive_message(self, lock):
        message = self.stream.get_message()
        description, content = parse_message(message)
        if description == "Done":
            _client_id = int(content)
            self.receive_done_message()
        else:
            bets = content[0]
            _client_id = content[1]
            safe_store_bets(bets, lock)
            logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(bets)}')
        
            addr = self.socket.getpeername()
            logging.info(f'action: receive_message | result: success | ip: {addr[0]} | msg: {message}')
        
            response = "OK"
            send_message(response, self.socket)
        return
