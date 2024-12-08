import sqlite3

# Conectar a la base de datos (modifica el nombre según tu archivo)
db_name = 'app/db.sqlite3'  # Cambia esto según tu base de datos
conn = sqlite3.connect(db_name)

# Crear un cursor para ejecutar comandos SQL
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tablas = cursor.fetchall()


print(f"tables: {tablas}")



# Obtener todas las tablas
cursor.execute("SELECT * FROM job limit(3);")
job = cursor.fetchall()
print(f"Jobs: {job}")


cursor = conn.cursor()

# Obtener todas las tablas
cursor.execute("PRAGMA table_info(item);")
items_columns = cursor.fetchall()
print(f"items_columns: {items_columns}")

cursor = conn.cursor()

# Obtener todas las tablas
cursor.execute("SELECT * FROM item limit(1);")
items = cursor.fetchall()
print(f"items: {items}")

cursor = conn.cursor()

# Obtener todas las tablas
cursor.execute("SELECT * FROM object;")
object = cursor.fetchall()
print(f"objects: {object}")

# Obtener todas las tablas
cursor.execute("SELECT * FROM stage;")
stage = cursor.fetchall()
print(f"stage: {stage}")
