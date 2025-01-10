from dotenv import load_dotenv
import os
from pathlib import Path
import socket

def get_ip(port=8080):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return f"http://{ip}:{port}"
    except Exception as e:
        print(f"Error al obtener la IP: {e}")
        return f"http://localhost:{port}"

# Cargar las variables del archivo .env
env_path = Path(__file__).parent.parent / ".env"  # Ruta al archivo .env
load_dotenv(dotenv_path=env_path)

class Settings:
    # Variables de configuración
    PORT: int = int(os.getenv("PORT", 8080))
    MAIL_FROM_NAME: str = os.getenv("MAIL_FROM_NAME")
    MAIL_FROM_EMAIL: str = os.getenv("MAIL_FROM_EMAIL")
    MAIL_SERVER: str = os.getenv("MAIL_SERVER")
    MAIL_PORT: int = int(os.getenv("MAIL_PORT", 587))  # Valor predeterminado 587
    MAIL_USERNAME: str = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD: str = os.getenv("MAIL_PASSWORD")
    MAIL_TLS: bool = os.getenv("MAIL_TLS", "True").lower() in ("true", "1")
    APP_HOST: str = get_ip(PORT)
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

settings = Settings()