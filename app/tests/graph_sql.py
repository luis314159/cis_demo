import sqlite3
import re
import os

def extract_sqlite_schema(db_path):
    """Extrae el esquema de una base de datos SQLite y genera código DBML."""
    if not os.path.exists(db_path):
        return f"Error: El archivo {db_path} no existe."
    
    conn = None
    try:
        # Conectar a la base de datos
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Obtener la lista de tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = [table[0] for table in cursor.fetchall()]
        
        dbml_code = "// Esquema de la base de datos SQLite extraído automáticamente\n\n"
        
        # Mapeo de tipos SQLite a tipos más genéricos para DBML
        type_mapping = {
            'INTEGER': 'integer',
            'INT': 'integer',
            'TINYINT': 'integer',
            'SMALLINT': 'integer',
            'MEDIUMINT': 'integer',
            'BIGINT': 'integer',
            'UNSIGNED BIG INT': 'integer',
            'TEXT': 'text',
            'CHARACTER': 'varchar',
            'VARCHAR': 'varchar',
            'VARYING CHARACTER': 'varchar',
            'NCHAR': 'varchar',
            'NATIVE CHARACTER': 'varchar',
            'NVARCHAR': 'varchar',
            'CLOB': 'text',
            'REAL': 'float',
            'DOUBLE': 'float',
            'DOUBLE PRECISION': 'float',
            'FLOAT': 'float',
            'NUMERIC': 'decimal',
            'DECIMAL': 'decimal',
            'BOOLEAN': 'boolean',
            'DATE': 'date',
            'DATETIME': 'datetime',
            'TIMESTAMP': 'datetime',
            'BLOB': 'blob'
        }
        
        # Almacenar referencias para agregarlas después
        references = []
        
        # Procesar cada tabla
        for table in tables:
            dbml_code += f'Table {table} {{\n'
            
            # Obtener información de las columnas
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            
            # Obtener información de claves primarias
            pk_columns = [col[1] for col in columns if col[5] > 0]  # col[5] > 0 indica PK
            
            # Procesar cada columna
            for col in columns:
                col_id, col_name, col_type, not_null, default_val, pk = col
                
                # Convertir tipo SQLite a tipo DBML
                col_type_upper = col_type.upper().split('(')[0].strip()
                dbml_type = type_mapping.get(col_type_upper, 'varchar')
                
                # Extraer tamaño si existe
                size_match = re.search(r'\((\d+)\)', col_type)
                size = f"({size_match.group(1)})" if size_match else ""
                
                # Determinar restricciones
                constraints = []
                if pk > 0:
                    constraints.append("pk")
                if not_null:
                    constraints.append("not null")
                if default_val is not None:
                    # Escapar comillas simples en valores predeterminados
                    default_val_str = str(default_val).replace("'", "''")
                    constraints.append(f"default: '{default_val_str}'")
                
                constraints_str = ", ".join(constraints)
                if constraints_str:
                    constraints_str = f" [{constraints_str}]"
                
                dbml_code += f'  {col_name} {dbml_type}{size}{constraints_str}\n'
            
            # Obtener claves foráneas
            cursor.execute(f"PRAGMA foreign_key_list({table})")
            foreign_keys = cursor.fetchall()
            
            # Procesar cada clave foránea
            for fk in foreign_keys:
                id, seq, ref_table, from_col, to_col, on_update, on_delete, match = fk
                references.append(f'Ref: {table}.{from_col} > {ref_table}.{to_col}')
            
            dbml_code += '}\n\n'
        
        # Agregar referencias al final del código DBML
        if references:
            dbml_code += "// Relaciones\n"
            for ref in references:
                dbml_code += f"{ref}\n"
        
        return dbml_code
        
    except sqlite3.Error as e:
        return f"Error de SQLite: {e}"
    finally:
        if conn:
            conn.close()

# Ejemplo de uso
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Uso: python sqlite_to_dbml.py ruta_a_tu_base_de_datos.db")
        sys.exit(1)
    
    db_path = sys.argv[1]
    dbml_code = extract_sqlite_schema(db_path)
    print(dbml_code)
    
    # Opcionalmente guardar a un archivo
    with open("esquema_db.dbml", "w") as f:
        f.write(dbml_code)
    print(f"El código DBML se ha guardado en 'esquema_db.dbml'")