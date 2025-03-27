# Instrucciones de uso

Ejecutar "make docker-compose-up".

# Solución al ejercicio 6

Se edita el protocolo anteriormente definido para permitir interpretar un mensaje "batch".

Consiste de la cantidad de entradas en el batch, y luego las entradas separadas por //.
Cada argumento en una entrada se separa por |.
Se marca el fin del mensaje con un newline.

```
batch := ""
	batch += strconv.Itoa(len(*data))
	for _, row := range *data {
		nombre := row[0]
		apellido := row[1]
		documento := row[2]
		nacimiento := row[3]
		numero := row[4]
		line := fmt.Sprintf("//%v|%v|%v|%v|%v", nombre, apellido, documento, nacimiento, numero)
		batch += line
	}
	batch += "\n"
```

Hay un socket por cada cliente.

Se cargan los datos de entrada usando volúmenes de Docker y se leen usando un Scanner de Go.