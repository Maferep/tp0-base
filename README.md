# Instrucciones de uso

Ejecutar "make docker-compose-up".

# Solución al ejercicio 8

Usa la librería multiprocessing de Python, incluyendo su cola de mensajes y Lock.

El código de cliente no cambia.

Desde el servidor, la entidad "clientes" crea un proceso por cada cliente ejecutando 
la función "client_handle_connection", dentro de la cual "receive bets" realiza todo
el protocolo, y la sincronización de los mensajes a la hora del sorteo ocurre con dos colas por
proceso cliente.

la cola principal para mensajes "Done" y "request" de resultados, y la cola "result"
para que el proceso central mande los resultados a cada cliente.

Se usa nu único processing.Lock para sincronizar acceso a archivos en todos los procesos.
Véase este snippet en server.py:

```python
stream = MessageStream(client_sock) # buffers messages from the client socket
file_lock = multiprocessing.Lock()

client_id = self.receive_first_message(stream, client_sock, file_lock) # use first batch to get client id
self.client_state.handle_connection(client_id, stream, client_sock, file_lock)
```

En el archivo thread_safe_bets hay funciones 'wrapper' que aceptan el lock como parámetro y hacen lectura y escritura segura.