# Instrucciones de uso

Ejecutar "make docker-compose-up".

# Solución al ejercicio 7

Al haber un sólo proceso, éste bloquea hasta que recibe petición de resultados de todos los clientes.
Luego realiza el sorteo.
Se tomó esta solución a pesar de sus problemas evidentes pensando que se recibe este mensaje de petición
inmediatamente después de que los clientes envían sus apuestas y que el ejercicio 8 permite
una solución concurrente apropiada.