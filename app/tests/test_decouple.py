from decouple import config

# Prueba cargar una variable de entorno
print(config("DATABASE_URL", default="NoDatabaseURL"))