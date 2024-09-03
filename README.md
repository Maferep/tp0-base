# Protocol
Client-server text protocol made up of variable length messages separated by newlines, on top of TCP.
## Server 
_central de Lotería Nacional_
## Client 
_agencia de quiniela_
Envia mensaje batch con cada linea del batch separada por //. Al comienzo indica el nombre de la agencia y la cantidad de lineas.

agencia|tamanio_batch//nombre|apellido|documento|nacimiento|numero//...//nombre|apellido|documento|nacimiento|numero

_nacimiento_: YYYY-MM-DD
Every other field is alphanumeric plus periods, spaces.
A malformed message results in undefined behavior.