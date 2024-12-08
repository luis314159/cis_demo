from fastapi import APIRouter, UploadFile, File, HTTPException
from services.ocr_service import ocr_service  # Importa el servicio
import logging

router = APIRouter(
    prefix="/ocr",
    tags=["OCR"]
)

@router.post("")
async def extract_text(image: UploadFile = File(...)):
    """
    Extrae texto de una imagen usando Azure OCR.

    param image: Archivo de imagen cargado por el usuario.
    return: Lista de textos reconocidos en la imagen.
    """
    if not image.content_type.startswith("image/"):
        logging.warning("Archivo recibido no es una imagen.")
        raise HTTPException(status_code=400, detail="El archivo debe ser una imagen.")

    try:
        logging.info(f"Procesando archivo: {image.filename}")
        recognized_texts = ocr_service.azure_ocr(image.file)
        if recognized_texts:
            logging.info("Texto reconocido con éxito.")
            return {"text": recognized_texts}
        logging.info("No se reconoció texto en la imagen.")
        return {"message": "No se reconoció texto en la imagen."}
    except Exception as e:
        logging.error(f"Error procesando la imagen: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor al procesar la imagen.")
