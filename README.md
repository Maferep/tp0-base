# Instrucciones de uso

Ejecutar "make docker-compose-up"

# Solución al ejercicio 4
Desde el cliente usamos channels para permitir interrupción del programa. Hay un channel para aceptar interrupciones SIGTERM
y otro para aceptar interrupciones por Timer, de esta forma la SIGTERM puede interrumpir al cliente durante esta espera extendida.

Desde el servidor se usan handlers de señales para cerrar el socket, esto causa un error de socket (OsError) dentro de 
un bloque try-catch que hace que el programa salga normalmente.