package common

import (
	"bufio"
	"errors"
	"fmt"
	"net"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID            string
	ServerAddress string
	LoopAmount    int
	LoopPeriod    time.Duration
}

// Client Entity that encapsulates how
type Client struct {
	config ClientConfig
	conn   net.Conn
}

// NewClient Initializes a new client receiving the configuration
// as a parameter
func NewClient(config ClientConfig) *Client {
	client := &Client{
		config: config,
	}
	return client
}

// CreateClientSocket Initializes client socket. In case of
// failure, error is printed in stdout/stderr and exit 1
// is returned
func (c *Client) createClientSocket() error {
	conn, err := net.Dial("tcp", c.config.ServerAddress)
	if err != nil {
		log.Criticalf(
			"action: connect | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
		return errors.New("could not connect")
	}
	c.conn = conn
	return nil
}

// StartClientLoop Send messages to the client until some time threshold is met
func (c *Client) StartClientLoop() {
	ticker := time.NewTicker(c.config.LoopPeriod)
	terminated := make(chan os.Signal, 1)
	signal.Notify(terminated, syscall.SIGTERM)
	// There is an autoincremental msgID to identify every message sent
	// Messages if the message amount threshold has not been surpassed
	interrupted := false
	for msgID := 1; msgID <= c.config.LoopAmount && !interrupted; msgID++ {
		select {
		case <-ticker.C:
			// Create the connection the server in every loop iteration. Send an}
			err := c.createClientSocket()
			if err != nil {
				fmt.Println("Got an error creating the socket")
				break
			}
			// TODO: Modify the send to avoid short-write
			interactionError := interactWithServer(c, msgID)
			if interactionError {
				return
			}
		case <-terminated:
			fmt.Println("Graceful shutdown!")
			// Connection is not closed if it hasn't yet been created (createClientSocket)
			if c.conn != nil {
				c.conn.Close()
			}
			interrupted = true
		}
	}
	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
}

// Handle an interaction with the server.
// Formats and sends a client request, receives a server response,
// and logs the interaction.
// Reports whether an error occurred.
func interactWithServer(c *Client, msgID int) bool {

	fmt.Fprintf(
		c.conn,
		"[CLIENT %v] Message N°%v\n",
		c.config.ID,
		msgID,
	)
	msg, err := bufio.NewReader(c.conn).ReadString('\n')
	c.conn.Close()

	if err != nil {
		log.Errorf("action: receive_message | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
		return true
	}

	log.Infof("action: receive_message | result: success | client_id: %v | msg: %v",
		c.config.ID,
		msg,
	)
	return false
}
