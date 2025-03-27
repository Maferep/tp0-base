# Instrucciones de uso

Ejecutar "make docker-compose-up"

# Solución al ejercicio 5
Desde el cliente se leen las variables de entorno usando getenv.

Se usa la clase MessageStream para encapsular el parsing del mensaje apuesta.

Los mensajes que se reciben se leen de newline a newline. Existe por ahora
sólo el tipo de mensaje "apuesta" que se deserializa de la misma manera.