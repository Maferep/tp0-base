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

// StartClientLoop Send messages to the client until some time threshold is met
func (c *Client) StartClientLoop() error {
	ticker := time.NewTicker(c.config.LoopPeriod)
	terminated := make(chan os.Signal, 1)
	signal.Notify(terminated, syscall.SIGTERM)
	// There is an autoincremental msgID to identify every message sent
	// Messages if the message amount threshold has not been surpassed

	// Open file
	client_id := os.Getenv("CLI_ID")
	client_id_value, err := strconv.Atoi(client_id)
	if err != nil {
		client_id_value = 1
	}
	name := fmt.Sprintf("/var/lib/client/data/agency-%v.csv", client_id_value)
	file, err := os.Open(name)
	if err != nil {
		panic(err)
	}
	defer file.Close()

	// read the file line by line
	scanner := bufio.NewScanner(file)
	scanner.Split(bufio.ScanLines)
	rows := new([][]string)

	interrupted := false
	for scanner.Scan() {
		// parse csv line
		bet_text := scanner.Text()
		row := strings.Split(bet_text, ",")
		if len(row) != 5 {
			panic(row)
		}

		// build batch collection from batch.maxAmount parameter
		*rows = append(*rows, row)

		if len(*rows) == c.config.MaxAmount {
			// create socket and message
			err := CreateSocketAndSendMessage(c, rows)
			if err != nil {
				return err
			}

			*rows = nil

			select { // waits for either an interrupt signal or a set time
			case <-ticker.C:
				continue
			case <-terminated:
				fmt.Println("Graceful shutdown!")
				// Connection is not closed if it hasn't yet been created (createClientSocket)
				if c.conn != nil {
					c.conn.Close()
				}
				interrupted = true
			}
			if interrupted {
				break
			}
		}
	}
	if len(*rows) > 0 {
		// create socket and message
		err := CreateSocketAndSendMessage(c, rows)
		if err != nil {
			return err
		}
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
	for _, row := range *data {
		nombre := row[0]
		apellido := row[1]
		documento := row[2]
		nacimiento := row[3]
		numero := row[4]
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
	fmt.Printf("action: apuesta_enviada | result: success")

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
	}

	return nil
}
