import socket
import logging
import signal
from common.protocol import parse_message, MessageStream, send_message
from common.utils import store_bets
from common.client_state import Clients

class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._exit_signal = False

        # business logic
        self.client_state = Clients(5)

    def _exit_gracefully(self, signum, frame):
        self._exit_signal = True
        self._server_socket.shutdown(socket.SHUT_RDWR)

    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """

        # TODO: Modify this program to handle signal to graceful shutdown
        # the server
        signal.signal(signal.SIGTERM, self._exit_gracefully)
        while not self._exit_signal:
            try:
                client_sock = self.__accept_new_connection()
                self.__handle_client_connection(client_sock)
            except OSError:
                break
        print("Shutting down...")

  
    def receive_first_message(self, stream, client_sock) -> int: # TODO handle receive done message with no content
        message = stream.get_message()
        description, content = parse_message(message)
        client_id = None
    
        bets = content[0]
        client_id = content[1]
        store_bets(bets)
        logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(bets)}')
    
        addr = client_sock.getpeername()
        logging.info(f'action: receive_message | result: success | ip: {addr[0]} | msg: {message}')
    
        response = "OK"
        send_message(response, client_sock)
        return int(client_id)  

    def __handle_client_connection(self, client_sock):
        """
        Spawn process to handle client connection
        """
        done = False
        client_id = None
        stream = MessageStream(client_sock) # buffers messages from the client socket
        client_id = self.receive_first_message(stream, client_sock) # use first batch to get client id
        self.client_state.handle_connection(client_id, stream, client_sock)

        

    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """

        # Connection arrived
        logging.info('action: accept_connections | result: in_progress')
        c, addr = self._server_socket.accept()
        logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
        return c
