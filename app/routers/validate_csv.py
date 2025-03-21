from fastapi import APIRouter, UploadFile, HTTPException
import pandas as pd
from fastapi.responses import JSONResponse
from db import SessionDep
from models import Job, Item, Object, Process
from sqlmodel import select
import logging
import traceback
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Definimos el router
router = APIRouter(
    prefix="/object",
    tags=["Object"]
)

def log_dataframe_info(df: pd.DataFrame) -> Dict[str, Any]:
    """Helper function to create a structured log of DataFrame information"""
    return {
        "shape": df.shape,
        "columns": df.columns.tolist(),
        "unique_jobs": df['Job'].unique().tolist(),
        "total_rows": len(df)
    }

@router.post('/validate-and-insert')
def validate_and_insert(file: UploadFile, session: SessionDep):
    logger.info(f"Starting validate_and_insert for file: {file.filename}")
    
    try:
        if not file:
            logger.error("No file found in request")
            raise HTTPException(status_code=400, detail="No se encontró el archivo en la solicitud.")

        df = None
        try:
            logger.info("Attempting to read CSV with utf-8 encoding")
            df = pd.read_csv(file.file)
            logger.info("Successfully read CSV with utf-8 encoding")
        except UnicodeDecodeError:
            logger.warning("UTF-8 decode failed, attempting with latin1 encoding")
            file.file.seek(0)
            try:
                df = pd.read_csv(file.file, encoding='latin1')
                logger.info("Successfully read CSV with latin1 encoding")
            except Exception as e:
                logger.error(f"Failed to read CSV with latin1 encoding: {str(e)}")
                raise HTTPException(status_code=400, detail={
                    "error": "El archivo no es un CSV válido o no pudo ser leído.",
                    "details": str(e)
                })

        # Log DataFrame information
        logger.info("DataFrame loaded", extra={"df_info": log_dataframe_info(df)})

        required_columns = ["Job", "Item", "Material", "Espesor", "Cantidad", "OCR", "Clase", 
                          "Longitud", "Ancho", "Alto", "Volumen", "Área Superficial"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            logger.error(f"Missing columns in CSV: {missing_columns}")
            raise HTTPException(status_code=400, detail={
                "error": "Faltan columnas en el archivo CSV.",
                "missing_columns": missing_columns
            })

        unique_jobs = df['Job'].unique()
        if len(unique_jobs) > 1:
            logger.error(f"Multiple jobs found in CSV: {unique_jobs.tolist()}")
            raise HTTPException(status_code=400, detail={
                "error": "Los valores de 'Job' no son consistentes.",
                "unique_jobs": unique_jobs.tolist()
            })

        # Check for duplicates
        duplicates = df.duplicated(subset=["Job", "Item"], keep=False)
        if duplicates.any():
            duplicated_rows = df.loc[duplicates, ["Job", "Item"]].drop_duplicates().to_dict(orient='records')
            logger.error(f"Duplicate Job-Item combinations found: {duplicated_rows}")
            raise HTTPException(status_code=400, detail={
                "error": "Existen combinaciones duplicadas de 'Job' e 'Item'.",
                "duplicates": duplicated_rows
            })

        # Database operations
        job_code = str(unique_jobs[0])
        logger.info(f"Processing job_code: {job_code}")
        
        existing_job = session.exec(select(Job).where(Job.job_code == job_code)).first()
        logger.info(f"Existing job found: {existing_job is not None}")

        # Process handling
        process_map = {}
        unique_processes = df["Clase"].unique()
        logger.info(f"Processing {len(unique_processes)} unique processes")
        
        for process_name in unique_processes:
            existing_process = session.exec(select(Process).where(Process.process_name == process_name)).first()
            if not existing_process:
                logger.info(f"Creating new process: {process_name}")
                new_process = Process(process_name=process_name)
                session.add(new_process)
                session.commit()
                session.refresh(new_process)
                process_map[process_name] = new_process
            else:
                logger.info(f"Using existing process: {process_name}")
                process_map[process_name] = existing_process

        if existing_job:
            logger.info(f"Updating existing job: {job_code}")
            existing_items = session.exec(select(Item).where(Item.job_id == existing_job.job_id)).all()
            existing_item_names = {item.item_name for item in existing_items}
            logger.info(f"Found {len(existing_item_names)} existing items")

            items_created = 0
            objects_created = 0
            
            for _, row in df.iterrows():
                if row["Item"] not in existing_item_names:
                    logger.info(f"Creating new item: {row['Item']}")
                    process_name = row["Clase"]
                    
                    # Handle NaN values with default 0
                    volumen = row["Volumen"] if pd.notna(row["Volumen"]) else 0
                    area_superficial = row["Área Superficial"] if pd.notna(row["Área Superficial"]) else 0
                    
                    logger.info(f"Volume for {row['Item']}: {volumen}, Area: {area_superficial}")
                    
                    item = Item(
                        item_name=row["Item"],
                        espesor=row["Espesor"],
                        longitud=row["Longitud"],
                        ancho=row["Ancho"],
                        alto=row["Alto"],
                        volumen=volumen,
                        area_superficial=area_superficial,
                        cantidad=row["Cantidad"],
                        material=row["Material"],
                        ocr=row["OCR"],
                        job_id=existing_job.job_id,
                        process_id=process_map[process_name].process_id
                    )
                    session.add(item)
                    session.commit()
                    session.refresh(item)
                    items_created += 1

                    # Create objects
                    for i in range(row["Cantidad"]):
                        obj = Object(
                            current_stage=1,
                            rework=0,
                            scrap=0,
                            item_id=item.item_id
                        )
                        session.add(obj)
                        objects_created += 1

            session.commit()
            logger.info(f"Updated job {job_code}: Created {items_created} items and {objects_created} objects")
            return JSONResponse(content={"message": "Se agregaron nuevos Items y Objects al Job existente."}, status_code=201)
        
        else:
            logger.info(f"Creating new job: {job_code}")
            job = Job(job_code=job_code)
            session.add(job)
            session.commit()
            session.refresh(job)

            items_created = 0
            objects_created = 0

            for _, row in df.iterrows():
                logger.info(f"Processing item: {row['Item']}")
                process_name = row["Clase"]
                
                # Handle NaN values with default 0
                volumen = row["Volumen"] if pd.notna(row["Volumen"]) else 0
                area_superficial = row["Área Superficial"] if pd.notna(row["Área Superficial"]) else 0
                
                logger.info(f"Volume for {row['Item']}: {volumen}, Area: {area_superficial}")
                
                item = Item(
                    item_name=row["Item"],
                    espesor=row["Espesor"],
                    longitud=row["Longitud"],
                    ancho=row["Ancho"],
                    alto=row["Alto"],
                    volumen=volumen,
                    area_superficial=area_superficial,
                    cantidad=row["Cantidad"],
                    material=row["Material"],
                    ocr=row["OCR"],
                    job_id=job.job_id,
                    process_id=process_map[process_name].process_id
                )
                session.add(item)
                session.commit()
                session.refresh(item)
                items_created += 1

                # Create objects
                for i in range(row["Cantidad"]):
                    obj = Object(
                        current_stage=1,
                        rework=0,
                        scrap=0,
                        item_id=item.item_id
                    )
                    session.add(obj)
                    objects_created += 1

            session.commit()
            logger.info(f"Created new job {job_code}: Created {items_created} items and {objects_created} objects")
            return JSONResponse(content={"message": "Job, Items, Objects y Process creados exitosamente."}, status_code=201)

    except HTTPException as e:
        logger.error(f"HTTP Exception: {str(e.detail)}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}\nTraceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail={
            "error": "Ocurrió un error inesperado.",
            "details": str(e)
        })