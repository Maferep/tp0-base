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

func wait(timer chan string, d time.Duration) {
	time.Sleep(d)
	timer <- "done sleeping"
}

// StartClientLoop Send messages to the client until some time threshold is met
func (c *Client) StartClientLoop() {
	// There is an autoincremental msgID to identify every message sent
	// Messages if the message amount threshold has not been surpassed

	timer := make(chan string, 1)

	signals := make(chan os.Signal, 1)
	signal.Notify(signals, syscall.SIGTERM)
	is_done := false
	go func() {
		<-signals
		fmt.Println("we got a signal!")
		is_done = true
		timer <- "Got a signal!"
	}()

	for msgID := 1; msgID <= c.config.LoopAmount; msgID++ {
		// Create the connection the server in every loop iteration. Send an}
		err := c.createClientSocket()

		if err != nil {
			fmt.Println("Got an error creating the socket")
			break
		}

		// TODO: Modify the send to avoid short-write
		shouldReturn := createMessage(c, msgID)
		if shouldReturn {
			return
		}

		go wait(timer, c.config.LoopPeriod)
		<-timer

		if is_done {
			fmt.Println("Graceful shutdown!")
			c.conn.Close()
			break
		}

	}
	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
}

func createMessage(c *Client, msgID int) bool {

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
