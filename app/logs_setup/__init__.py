import logging
import sys
from pathlib import Path

def setup_api_logger(router_name):
    # Crear directorio logs si no existe
    Path("logs").mkdir(exist_ok=True)
    
    logger = logging.getLogger(f"api.{router_name}")
    logger.setLevel(logging.DEBUG)
    
    # Log file específico para cada router
    file_handler = logging.FileHandler(f"logs/{router_name}.log")
    file_handler.setLevel(logging.DEBUG)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    formato = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(pathname)s:%(lineno)d] - %(message)s')
    file_handler.setFormatter(formato)
    console_handler.setFormatter(formato)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger