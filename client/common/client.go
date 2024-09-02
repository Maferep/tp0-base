package common

import (
	"bufio"
	"errors"
	"fmt"
	"net"
	"os"
	"os/signal"
	"strconv"
	"strings"
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
	MaxAmount     int
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
func (c *Client) StartClientLoop() error {
	// There is an autoincremental msgID to identify every message sent
	// Messages if the message amount threshold has not been surpassed
	client_id := os.Getenv("CLI_ID")
	client_id_value, err := strconv.Atoi(client_id)
	if err != nil {
		panic(err)
	}
	name := fmt.Sprintf("/var/lib/client/data/dataset/agency-%v.csv", client_id_value)
	file, err := os.Open(name)
	if err != nil {
		panic(err)
	}
	// remember to close the file at the end of the program
	defer file.Close()

	// set up orderly interrupt function
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

	// read the file line by line
	scanner := bufio.NewScanner(file)
	scanner.Split(bufio.ScanLines)
	rows := new([][]string)
	for scanner.Scan() {
		// parse csv line
		bet_text := scanner.Text()
		datapoints := strings.Split(bet_text, ",")
		if len(datapoints) != 5 {
			panic(datapoints)
		}

		// build batch collection from batch.maxAmount parameter
		*rows = append(*rows, datapoints)

		if len(*rows) == c.config.MaxAmount {
			// create socket and message
			_err := CreateSocketAndSendMessage(c, rows)
			if _err != nil {
				return err
			}

			*rows = nil // TODO reallocates memory - might be suboptimal

			go wait(timer, c.config.LoopPeriod)
			<-timer

		}
		if is_done {
			fmt.Println("Graceful shutdown!")
			c.conn.Close()
			break
		}
	}
	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)

	if err := scanner.Err(); err != nil {
		return err
	}
	return nil
}

/*
Returns a boolean indicating whether a signal interruption occured, and an error value if an error occured
*/
func CreateSocketAndSendMessage(c *Client, data *[][]string) error {
	// build batch message
	batch := ""
	batch += strconv.Itoa(len(*data))
	for _, datapoints := range *data {
		nombre := datapoints[0]
		apellido := datapoints[1]
		documento := datapoints[2]
		nacimiento := datapoints[3]
		numero := datapoints[4]
		line := fmt.Sprintf("//%v|%v|%v|%v|%v", nombre, apellido, documento, nacimiento, numero)
		batch += line
	}
	batch += "\n"

	// create socket
	err := c.createClientSocket()
	if err != nil {
		fmt.Println("Got an error creating the socket")
		return err
	}

	// TODO Fix short write
	_, err = c.conn.Write([]byte(batch))
	if err != nil {
		return err
	}

	// receive server message
	msg, err := bufio.NewReader(c.conn).ReadString('\n')
	c.conn.Close()

	if err != nil {
		log.Errorf("action: receive_message | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
		return err
	} else if msg != "OK\n" {
		log.Errorf("action: receive_message | result: fail | client_id: %v | error: Incorrect Server Response %v",
			c.config.ID, msg)
	} else {
		log.Infof("action: receive_message | result: success | client_id: %v | msg: %v",
			c.config.ID,
			msg,
		)

	}

	return nil
}
