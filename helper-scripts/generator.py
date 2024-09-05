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
    image: client:latest
    entrypoint: /client
    networks:
    - testing_net
    depends_on:
    - server
""".format(number, number)
    client_strings.append(client)

client_strings = "".join(client_strings)

full = """name: tp0
services:
  server:
    container_name: server
    image: server:latest
    entrypoint: python3 /main.py
    networks:
      - testing_net
{}
networks:
  testing_net:
    ipam:
      driver: default
      config:
        - subnet: 172.25.125.0/24
""".format(client_strings)

fp = io.open(name, "w")
fp.write(full)
fp.close()