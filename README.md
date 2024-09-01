# Protocol
Client-server text protocol made up of variable length messages separated by newlines, on top of TCP.
## Server 
_central de Lotería Nacional_
## Client 
_agencia de quiniela_
Client sends exactly one message with a terminating newline and closes the connection (ej5).


Message: [nombre]|[apellido]|[documento]|[nacimiento]|[número]\n

_nacimiento_: YYYY-MM-DD
Every other field is alphanumeric plus periods, spaces.
A malformed message results in undefined behavior.