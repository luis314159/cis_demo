import asyncio
from sqlalchemy import text
from db.connection import engine
import logging

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

async def test_connection():
    try:
        async with engine.connect() as conn:
            print("Conexión establecida.")

            # Imprimir detalles de la conexión
            result = await conn.execute(text('SELECT current_database();'))
            current_db = result.scalar()
            print(f"Base de datos actual: {current_db}")

            result = await conn.execute(text('SELECT current_user;'))
            current_user = result.scalar()
            print(f"Usuario actual: {current_user}")

            # Listar todas las tablas disponibles
            result = await conn.execute(text("""
                SELECT table_schema, table_name
                FROM information_schema.tables
                WHERE table_type = 'BASE TABLE'
                ORDER BY table_schema, table_name;
            """))
            tables = result.fetchall()
            print("Tablas disponibles:")
            for schema, table in tables:
                print(f"{schema}.{table}")

            # Intentar ejecutar una consulta SELECT
            result = await conn.execute(text('SELECT * FROM public.Scraps'))
            rows = result.fetchall()
            print(f"Filas obtenidas: {rows}")
    except Exception as e:
        print(f"Error de conexión o consulta: {e}")

asyncio.run(test_connection())

