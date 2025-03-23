from fastapi import APIRouter, UploadFile, File, HTTPException, Response
from services.ocr_service import ocr_service  # Importa el servicio
import logging
from fastapi.responses import PlainTextResponse

router = APIRouter(
    prefix="/ocr",
    tags=["OCR"]
)

#@router.post("",  response_class = PlainTextResponse)
@router.post("",
        summary="Perform OCR on image",
        response_description="Extracted text from image or error message",
        responses={
            200: {
                "description": "OCR results",
                "content": {
                    "application/json": {
                        "example": {"texts": ["TEXT1", "TEXT2"]}
                    },
                    "text/plain": {
                        "example": "TEXT1\nTEXT2"
                    }
                }
            },
            400: {"description": "Invalid file type"},
            500: {"description": "OCR processing error"}
        }
    )
async def extract_text(image: UploadFile = File(...)):
    """
    ## Extract text from image using Azure OCR

    Processes an uploaded image file to perform Optical Character Recognition (OCR)
    using Microsoft Azure's Computer Vision API.

    ### Arguments:
    - **image** (UploadFile): Image file to process (JPEG, PNG, BMP, etc.)
        - Max size: 4MB
        - Supported formats: All common image formats

    ### Returns:
    - **Union[List[str], dict]**:
        - List of recognized text strings (success)
        - JSON object with error message (no text found)
        - Plain text response with recognized text

    ### Raises:
    - `HTTPException`:
        - 400: Invalid file type uploaded
        - 500: Internal server error during processing

    ### Example Usage:
    ```bash
    curl -X POST "http://api/ocr" \
         -H "Content-Type: multipart/form-data" \
         -F "image=@document.jpg"
    ```

    ### Example Responses:
    **Success (text found):**
    ```text
    ["INVOICE-1234", "ACME Corporation", "Total: $1,234.56"]
    ```

    **Success (no text found):**
    ```json
    {"message": "No se reconoció texto en la imagen."}
    ```

    ### Workflow:
    1. Validate file type is image
    2. Send image to Azure OCR service
    3. Process API response
    4. Return formatted results:
        - JSON for structured data
        - Plain text for raw output
    5. Handle errors and edge cases

    ### Dependencies:
    - Azure Computer Vision API credentials
    - Proper error handling for API failures
    - Image size validation (implied by Azure limits)
    """
    
    if not image.content_type.startswith("image/"):
        logging.warning("Archivo recibido no es una imagen.")
        raise HTTPException(status_code=400, detail="El archivo debe ser una imagen.")

    try:
        logging.info(f"Procesando archivo: {image.filename}")
        recognized_texts = ocr_service.azure_ocr(image.file)
        if recognized_texts:
            logging.info("Texto reconocido con éxito.")
            #return Response(recognized_texts, mimetype='text/plain')
            return recognized_texts
        logging.info("No se reconoció texto en la imagen.")
        return {"message": "No se reconoció texto en la imagen."}
    except Exception as e:
        logging.error(f"Error procesando la imagen: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor al procesar la imagen.")
