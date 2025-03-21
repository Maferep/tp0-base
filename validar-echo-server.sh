#! /bin/sh

MSG='Hello, world!!!'

RESPONSE=$(
    echo "$MSG" \
    | docker run --network tp0_testing_net -i --rm alpine:latest nc server 12345
)

if [ "$MSG" != "$RESPONSE" ]; then
    echo 'action: test_echo_server | result: fail'
else
    echo 'action: test_echo_server | result: success'
fi
