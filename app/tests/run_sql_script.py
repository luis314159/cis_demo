#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3
import os
import sys
from pathlib import Path

def run_sql_script(db_path, sql_script_path):
    """
    Ejecuta un script SQL en una base de datos SQLite3.
    
    Args:
        db_path (str): Ruta a la base de datos SQLite3
        sql_script_path (str): Ruta al archivo SQL que se ejecutará
    
    Returns:
        bool: True si la ejecución fue exitosa, False en caso contrario
    """
    try:
        # Verificar que los archivos existan
        if not Path(db_path).exists():
            print(f"Error: La base de datos no existe en la ruta: {db_path}")
            return False
        
        if not Path(sql_script_path).exists():
            print(f"Error: El script SQL no existe en la ruta: {sql_script_path}")
            return False
        
        # Leer el contenido del script SQL
        with open(sql_script_path, 'r', encoding='utf-8') as sql_file:
            sql_script = sql_file.read()
        
        # Conectar a la base de datos
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Ejecutar el script SQL
        print(f"Ejecutando script SQL desde: {sql_script_path}")
        print(f"En la base de datos: {db_path}")
        
        # Dividir el script en instrucciones individuales si contiene varias
        # (SQLite no puede ejecutar múltiples instrucciones en una sola ejecución)
        sql_statements = sql_script.split(';')
        
        for statement in sql_statements:
            # Ignorar declaraciones vacías (como la última después del último punto y coma)
            if statement.strip():
                try:
                    cursor.execute(statement)
                    print(f"Ejecutado: {statement[:50]}{'...' if len(statement) > 50 else ''}")
                except sqlite3.Error as e:
                    print(f"Error al ejecutar: {statement[:50]}{'...' if len(statement) > 50 else ''}")
                    print(f"Error SQLite: {e}")
        
        # Confirmar los cambios y cerrar la conexión
        conn.commit()
        print("Cambios confirmados en la base de datos.")
        conn.close()
        
        return True
    
    except sqlite3.Error as e:
        print(f"Error de SQLite: {e}")
        return False
    except Exception as e:
        print(f"Error inesperado: {e}")
        return False

def main():
    # Rutas definidas según los requisitos
    base_dir = Path(r"C:\luis\aethersoft\arga\quality_system\cis_demo")
    db_path = base_dir / "app" / "db.sqlite3"
    sql_script_path = base_dir / "insert_data.sql"
    
    # Ejecutar el script SQL
    success = run_sql_script(str(db_path), str(sql_script_path))
    
    if success:
        print("Script SQL ejecutado correctamente.")
    else:
        print("Hubo un error al ejecutar el script SQL.")
        sys.exit(1)

if __name__ == "__main__":
    main()