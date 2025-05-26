FROM python:3.12.8

WORKDIR /app

# Instalar poetry
RUN pip install poetry

# Configurar poetry para que no cree un entorno virtual
RUN poetry config virtualenvs.create false

# Copiar los archivos de poetry primero para aprovechar la caché de Docker
COPY pyproject.toml poetry.lock ./

# Instalar dependencias sin instalar el proyecto actual
RUN poetry install --no-interaction --no-ansi --no-root

# Copiar el resto del código
COPY . .

# Cambiar al directorio app y ejecutar desde allí
WORKDIR /app/app

# Ejecutar la aplicación
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]