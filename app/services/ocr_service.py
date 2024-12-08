import os
import time
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials
from dotenv import load_dotenv
import logging

load_dotenv()

# Configuración de logs
logging.basicConfig(level=logging.INFO)

class OCRService:
    def __init__(self, subscription_key: str, endpoint: str):
        """
        Inicializa el cliente de Azure Computer Vision.
        """
        if not subscription_key or not endpoint:
            raise ValueError("Azure Subscription Key y Endpoint deben estar configurados correctamente.")
        self.client = ComputerVisionClient(endpoint, CognitiveServicesCredentials(subscription_key))

    def azure_ocr(self, image) -> str | None:
        """
        Procesa una imagen para obtener texto reconocido mediante Azure OCR.
        """
        try:
            logging.info("Enviando imagen a Azure OCR...")
            ocr_result = self.client.read_in_stream(image, raw=True)

            # Obtener el ID de la operación
            operation_location = ocr_result.headers["Operation-Location"]
            operation_id = operation_location.split("/")[-1]

            # Esperar a que la operación termine
            while True:
                get_result = self.client.get_read_result(operation_id)
                if get_result.status in ['succeeded', 'failed']:
                    break
                time.sleep(1)

            # Procesar resultados
            if get_result.status == 'succeeded':
                logging.info("Reconocimiento de texto completado con éxito.")
                recognized_texts = "\n".join(
                    line.text
                    for result in get_result.analyze_result.read_results
                    for line in result.lines
                )
                return recognized_texts
            else:
                logging.error("El reconocimiento de texto falló.")
                return None
        except Exception as e:
            logging.error(f"Error al procesar la imagen: {e}")
            return None

# Inicializar el servicio con credenciales desde variables de entorno
ocr_service = OCRService(
    subscription_key=os.getenv("AZURE_SUBSCRIPTION_KEY"),
    endpoint=os.getenv("AZURE_ENDPOINT")
)
