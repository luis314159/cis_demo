import sqlite3

# Conectar a la base de datos (modifica el nombre según tu archivo)
db_name = 'app/db.sqlite3'  # Cambia esto según tu base de datos
conn = sqlite3.connect(db_name)

# Crear un cursor para ejecutar comandos SQL
cursor = conn.cursor()
cursor.execute("SELECT * FROM item WHERE item_id=1")
item = cursor.fetchall()

print(f"item: {item}")

cursor.execute("SELECT * FROM object WHERE item_id=1")
object = cursor.fetchall()

print(f"object: {object}")

cursor.execute("SELECT * FROM item limit 1;")
items = cursor.fetchall()

print(f"item: {items}")