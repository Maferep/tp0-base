# Instrucciones de uso

Ejecutar "make docker-compose-up"

# Solución al ejercicio 3

Desde el script en la máquina host se levanta un container alpine que contiene una implementación de netcat usando la CLI de docker. El container usa la red por default de los contenedores tal que el servidor no expone puertos al host.

La flag -interactive permite recibir las respuestas por línea de comando en stdout.

```bash
docker run --network tp0_testing_net -i --rm alpine:latest nc server 12345
```