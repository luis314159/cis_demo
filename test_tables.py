import sqlite3

# Conectar a la base de datos (modifica el nombre según tu archivo)
db_name = 'app/db.sqlite3'  # Cambia esto según tu base de datos
conn = sqlite3.connect(db_name)

# Crear un cursor para ejecutar comandos SQL
cursor = conn.cursor()

# Obtener todas las tablas
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tablas = cursor.fetchall()

if tablas:
    print("Tablas y columnas en la base de datos:")
    for tabla in tablas:
        nombre_tabla = tabla[0]
        print(f"\nTabla: {nombre_tabla}")

        # Obtener información de las columnas de la tabla
        cursor.execute(f"PRAGMA table_info({nombre_tabla});")
        columnas = cursor.fetchall()

        if columnas:
            print("Columnas:")
            for columna in columnas:
                print(f"- {columna[1]} (Tipo: {columna[2]})")  # columna[1]: nombre, columna[2]: tipo
        else:
            print("No se encontraron columnas en esta tabla.")
else:
    print("No se encontraron tablas en la base de datos.")

# Cerrar la conexión
conn.close()
