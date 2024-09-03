import socket
import logging
import signal
from common.protocol import parse_message, MessageStream
from common.utils import store_bets

class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._exit_signal = False

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

    def send_message(self, message, client_sock):
        sending = "{}\n".format(message).encode('utf-8')
        bytes_sent = 0
        while bytes_sent < len(sending):
            bytes_sent += client_sock.send(sending[bytes_sent:])
        return bytes_sent

    def __handle_client_connection(self, client_sock):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        try:
            message = MessageStream(client_sock).get_message()
            description, content = parse_message(message)
            if description == "Done":
                print("received a done message from {}".format(content))
            else:
                bets = content
                store_bets(bets)
                logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(bets)}')

                addr = client_sock.getpeername()
                logging.info(f'action: receive_message | result: success | ip: {addr[0]} | msg: {message}')

                response = "OK"
                bytes_sent = self.send_message(response, client_sock)

        except OSError as e:
            logging.error(f"action: receive_message | result: fail | error: {e}")
        except Exception as e:
            logging.error(f"action: receive_message | result: fail | error: {e}")
        finally:
            client_sock.close()

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
