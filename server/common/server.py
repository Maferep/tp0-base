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

    

    def __handle_client_connection(self, client_sock):
        """
        Reads as many messages as it can until it encounters "done" message or error.
        """
        done = False
        client_id = None
        stream = MessageStream(client_sock) # buffers messages from the client socket
        while not done:
            try:
                message = stream.get_message()
                description, content = parse_message(message)
                if description == "Done":
                    print("received a done message from {}".format(content))
                    client_id = int(content)
                    self.client_state.receive_done_message(client_id)
                elif description == "RequestWinners":
                    self.client_state.request_results(client_id)
                    done = True
                else:
                    bets = content[0]
                    client_id = content[1]
                    # TODO bad way of doing it: update client id corresponding to the socket every bet received
                    self.client_state.set_socket(client_id, client_sock)
                    store_bets(bets)
                    logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(bets)}')

                    addr = client_sock.getpeername()
                    logging.info(f'action: receive_message | result: success | ip: {addr[0]} | msg: {message}')

                    response = "OK"
                    bytes_sent = send_message(response, client_sock)

            except OSError as e:
                logging.error(f"action: receive_message | result: fail | error: {e}")
                break
            except Exception as e:
                logging.error(f"action: receive_message | result: fail | error: {e}")
                break
        return done

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
