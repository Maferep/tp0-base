import sys
import io

try:
    n = int(sys.argv[2])
    name = str(sys.argv[1])
except:
    print("Bad input")
    exit()

client_strings = []
for number in range(1, n+1):
    client = """\
  client{}:
    container_name: client{}
    volumes:
      - dataset:/var/lib/client/data
      - ./client/config.yaml:/config.yaml
    image: client:latest
    entrypoint: /client
    environment:
    - CLI_ID={}
    - CLI_LOG_LEVEL=DEBUG
    networks:
    - testing_net
    depends_on:
    - server
""".format(number, number, number)
    client_strings.append(client)
client_strings = "".join(client_strings)

full = """name: tp0
services:
  server:
    container_name: server
    image: server:latest
    entrypoint: python3 /main.py
    environment:
    - TOTAL_CLIENTS={}
    networks:
      - testing_net
    volumes:
      - ./server/config.ini:/config.ini
{}
networks:
  testing_net:
    ipam:
      driver: default
      config:
        - subnet: 172.25.125.0/24
volumes:
  dataset:
    driver: local
    driver_opts:
      type: none
      o: bind 
      device: ./.data
""".format(n, client_strings)

fp = io.open(name, "w")
fp.write(full)
fp.close()