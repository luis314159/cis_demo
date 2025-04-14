from fastapi import APIRouter, UploadFile, HTTPException
import pandas as pd
from fastapi.responses import JSONResponse
from db import SessionDep
from models import Job, Item, Object, Process, Product
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

map_dict: Dict[str, str] = {
    "Almacén": "Warehouse",
    "Corte": "Cutting", 
    "Doblado": "Bending", 
    "Maquinado": "Machining"  # Fixed typo: "Macnining" → "Machining"
}

# Definimos el router
router = APIRouter(
    prefix="/object",
    tags=["Object"]
)

def log_dataframe_info(df: pd.DataFrame) -> Dict[str, Any]:
    """
    ## Generate structured logging information for a DataFrame

    Creates a dictionary containing key metrics and metadata about a pandas DataFrame
    for structured logging purposes.

    ### Parameters:
    - **df** (pd.DataFrame): The DataFrame to analyze

    ### Returns:
    - **Dict[str, Any]**: Structured log information containing:
        - shape: Tuple of (rows, columns)
        - columns: List of column names
        - unique_jobs: List of unique job identifiers
        - total_rows: Total number of rows

    ### Example Usage:
    ```python
    df = pd.DataFrame({
        'Job': ['JOB1', 'JOB1', 'JOB2'],
        'Value': [10, 20, 30]
    })
    
    log_info = log_dataframe_info(df)
    logger.info("DataFrame metrics", extra={"df_info": log_info})
    ```

    ### Example Output:
    ```python
    {
        "shape": (3, 2),
        "columns": ["Job", "Value"],
        "unique_jobs": ["JOB1", "JOB2"],
        "total_rows": 3
    }
    ```

    ### Use Cases:
    - Debugging data processing pipelines
    - Monitoring data quality
    - Tracking data transformations
    - Auditing data inputs

    ### Notes:
    - Assumes the DataFrame contains a 'Job' column
    - Designed for use with structured logging systems
    - Can be extended with additional metrics as needed
    """
    return {
        "shape": df.shape,
        "columns": df.columns.tolist(),
        "unique_jobs": df['Job'].unique().tolist(),
        "total_rows": len(df)
    }


@router.post('/validate-and-insert',
            response_description="Process result message",
            tags=["Object"],
            responses={
                201: {
                    "description": "Data successfully processed",
                    "content": {
                        "application/json": {
                            "examples": {
                                "new_job": {
                                    "summary": "New job created",
                                    "value": {
                                        "message": "Job, Items, Objects y Process creados exitosamente."
                                    }
                                },
                                "existing_job": {
                                    "summary": "Existing job updated",
                                    "value": {
                                        "message": "Se agregaron nuevos Items y Objects al Job existente."
                                    }
                                }
                            }
                        }
                    }
                },
                400: {
                    "description": "Invalid input data",
                    "content": {
                        "application/json": {
                            "examples": {
                                "missing_file": {
                                    "summary": "No file provided",
                                    "value": {
                                        "error": "No se encontró el archivo en la solicitud."
                                    }
                                },
                                "invalid_csv": {
                                    "summary": "Invalid CSV file",
                                    "value": {
                                        "error": "El archivo no es un CSV válido o no pudo ser leído.",
                                        "details": "Specific error details"
                                    }
                                },
                                "missing_columns": {
                                    "summary": "Missing required columns",
                                    "value": {
                                        "error": "Faltan columnas en el archivo CSV.",
                                        "missing_columns": ["Column1", "Column2"]
                                    }
                                },
                                "multiple_jobs": {
                                    "summary": "Multiple jobs in file",
                                    "value": {
                                        "error": "Los valores de 'Job' no son consistentes.",
                                        "unique_jobs": ["JOB1", "JOB2"]
                                    }
                                },
                                "duplicates": {
                                    "summary": "Duplicate entries",
                                    "value": {
                                        "error": "Existen combinaciones duplicadas de 'Job' e 'Item'.",
                                        "duplicates": [
                                            {"Job": "JOB1", "Item": "ITEM1"},
                                            {"Job": "JOB1", "Item": "ITEM2"}
                                        ]
                                    }
                                },
                                "product_not_found": {
                                    "summary": "Product not found",
                                    "value": {
                                        "error": "El producto especificado no existe.",
                                        "product_name": "Nombre del producto"
                                    }
                                }
                            }
                        }
                    }
                },
                500: {
                    "description": "Internal server error",
                    "content": {
                        "application/json": {
                            "example": {
                                "error": "Ocurrió un error inesperado.",
                                "details": "Specific error details"
                            }
                        }
                    }
                }
            }
    )
def validate_and_insert(
    file: UploadFile, 
    product_name: str, session: SessionDep
):
    """
    ## Validate and insert manufacturing objects from CSV

    Processes a CSV file containing manufacturing object data, validates it,
    and inserts the data into the system. Handles both new jobs and updates
    to existing jobs.

    ### Parameters:
    - **file** (UploadFile): CSV file containing object data with columns:
        - Job: Job identifier (must be consistent across file)
        - Item: Item identifier
        - Material: Material type
        - Espesor: Thickness
        - Cantidad: Quantity
        - OCR: Optical Character Recognition code
        - Clase: Process class
        - Longitud: Length
        - Ancho: Width
        - Alto: Height
        - Volumen: Volume
        - Área Superficial: Surface area
    - **product_name** (str): Name of the product to associate with the job

    ### Returns:
    - **201 Created**:
        - New job: Creates new job, items, objects, and processes
        - Existing job: Adds new items and objects to existing job

    ### Example CSV Format:
    ```csv
    Job,Item,Material,Espesor,Cantidad,OCR,Clase,Longitud,Ancho,Alto,Volumen,Área Superficial
    JOB123,ITEM001,Steel,10,5,OCR001,Cutting,1000,500,20,10000000,3400000
    JOB123,ITEM002,Aluminum,5,3,OCR002,Machining,800,400,15,4800000,1840000
    ```

    ### Workflow:
    1. Validate file existence and format
    2. Check for required columns
    3. Validate job consistency
    4. Check for duplicate entries
    5. Process data:
        - Create new job if needed
        - Create/update items
        - Create objects
        - Handle processes
    6. Commit changes to database
    7. Return appropriate response

    ### Error Handling:
    - Detailed validation errors with specific feedback
    - Comprehensive logging for debugging
    - Graceful handling of encoding issues
    """
    logger.info(f"Starting validate_and_insert for file: {file.filename} with product_name: {product_name}")
    
    try:
        # Verify product exists
        product = session.exec(select(Product).where(Product.product_name == product_name)).first()
        if not product:
            logger.error(f"Product with name '{product_name}' not found")
            raise HTTPException(status_code=400, detail={
                "error": "El producto especificado no existe.",
                "product_name": product_name
            })

        product_id = product.product_id
        logger.info(f"Found product with ID: {product_id}")

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
            # Apply mapping for both new and existing jobs
            process_name_mapped = map_dict[process_name] if process_name in map_dict else process_name
            logger.info(f"Processing process: {process_name} (mapped to: {process_name_mapped})")
            existing_process = session.exec(select(Process).where(Process.process_name == process_name_mapped)).first()
            if not existing_process:
                logger.info(f"Creating new process: {process_name_mapped}")
                new_process = Process(process_name=process_name_mapped)
                session.add(new_process)
                session.commit()
                session.refresh(new_process)
                process_map[process_name] = new_process
            else:
                logger.info(f"Using existing process: {process_name_mapped}")
                process_map[process_name] = existing_process

        if existing_job:
            # Verify that the existing job belongs to the specified product
            if existing_job.product_id != product_id:
                product_name_in_db = session.exec(select(Product.product_name).where(Product.product_id == existing_job.product_id)).first()
                logger.error(f"Job {job_code} exists but belongs to product '{product_name_in_db}', not '{product_name}'")
                raise HTTPException(status_code=400, detail={
                    "error": "El Job ya existe pero está asociado a otro producto.",
                    "current_product": product_name_in_db,
                    "requested_product": product_name
                })
                
            logger.info(f"Updating existing job: {job_code}")
            existing_items = session.exec(select(Item).where(Item.job_id == existing_job.job_id)).all()
            existing_item_names = {item.item_name for item in existing_items}
            logger.info(f"Found {len(existing_item_names)} existing items")

            items_created = 0
            objects_created = 0
            
            for _, row in df.iterrows():
                if row["Item"] not in existing_item_names:
                    logger.info(f"Creating new item: {row['Item']}")
                    # Get process name and apply mapping if needed
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
            logger.info(f"Creating new job: {job_code} for product: {product_name}")
            job = Job(
                job_code=job_code,
                product_id=product_id
            )
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