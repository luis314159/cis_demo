from fastapi import APIRouter, UploadFile, HTTPException
import pandas as pd
from fastapi.responses import JSONResponse
from db import SessionDep
from models import Job, Item
from sqlmodel import select
from models import Object, Stage

# Definimos el router
router = APIRouter(
    prefix="/object",
    tags=["Object"]
)

@router.post('/validate-csv')
def validate_csv(file: UploadFile):
    """
    Valida un CSV dado por el usuario

    param CSV: Archivo de CSV cargado por el usuario.
    return: Respuesta de la validación.
    """
    try:
        # Verificar si el archivo fue enviado
        if not file:
            raise HTTPException(status_code=400, detail="No se encontró el archivo en la solicitud.")

        # Intentar leer el archivo CSV con diferentes codificaciones
        df = None
        try:
            df = pd.read_csv(file.file)
        except UnicodeDecodeError:
            file.file.seek(0)  # Resetear el puntero del archivo
            try:
                df = pd.read_csv(file.file, encoding='latin1')
            except Exception as e:
                raise HTTPException(status_code=400, detail={
                    "error": "El archivo no es un CSV válido o no pudo ser leído.",
                    "details": str(e)
                })

        # Verificar que todas las columnas requeridas están presentes
        required_columns = ["Job", "Item", "Material", "Espesor", "Cantidad", "OCR", "Clase", "Longitud", "Ancho", "Alto", "Volumen", "Área Superficial"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(status_code=400, detail={
                "error": "Faltan columnas en el archivo CSV.",
                "missing_columns": missing_columns
            })

        # Validar que todos los valores de "Job" sean iguales
        unique_jobs = df['Job'].unique()
        if len(unique_jobs) > 1:
            raise HTTPException(status_code=400, detail={
                "error": "Los valores de 'Job' no son consistentes.",
                "unique_jobs": unique_jobs.tolist()
            })

        # Validar que "Job" e "Item" sean únicos en conjunto
        duplicates = df.duplicated(subset=["Job", "Item"], keep=False)
        if duplicates.any():
            duplicated_rows = df.loc[duplicates, ["Job", "Item"]].drop_duplicates().to_dict(orient='records')
            raise HTTPException(status_code=400, detail={
                "error": "Existen combinaciones duplicadas de 'Job' e 'Item'.",
                "duplicates": duplicated_rows
            })

        return JSONResponse(content={"message": "El archivo CSV es válido."}, status_code=200)

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "error": "Ocurrió un error inesperado.",
            "details": str(e)
        })



@router.post('/validate-and-insert')
def validate_and_insert(file: UploadFile, session: SessionDep):
    try:
        # Validación del CSV (igual al endpoint anterior)
        if not file:
            raise HTTPException(status_code=400, detail="No se encontró el archivo en la solicitud.")

        df = None
        try:
            df = pd.read_csv(file.file)
        except UnicodeDecodeError:
            file.file.seek(0)
            try:
                df = pd.read_csv(file.file, encoding='latin1')
            except Exception as e:
                raise HTTPException(status_code=400, detail={
                    "error": "El archivo no es un CSV válido o no pudo ser leído.",
                    "details": str(e)
                })

        required_columns = ["Job", "Item", "Material", "Espesor", "Cantidad", "OCR", "Clase", "Longitud", "Ancho", "Alto", "Volumen", "Área Superficial"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(status_code=400, detail={
                "error": "Faltan columnas en el archivo CSV.",
                "missing_columns": missing_columns
            })

        unique_jobs = df['Job'].unique()
        if len(unique_jobs) > 1:
            raise HTTPException(status_code=400, detail={
                "error": "Los valores de 'Job' no son consistentes.",
                "unique_jobs": unique_jobs.tolist()
            })

        duplicates = df.duplicated(subset=["Job", "Item"], keep=False)
        if duplicates.any():
            duplicated_rows = df.loc[duplicates, ["Job", "Item"]].drop_duplicates().to_dict(orient='records')
            raise HTTPException(status_code=400, detail={
                "error": "Existen combinaciones duplicadas de 'Job' e 'Item'.",
                "duplicates": duplicated_rows
            })

        # Llenado de la base de datos
        job_code = unique_jobs[0]
        existing_job = session.exec(select(Job).where(Job.job_code == job_code)).first()

        if existing_job:
            # Si el Job ya existe, validamos y actualizamos los Items si es necesario
            existing_items = session.exec(select(Item).where(Item.job_id == existing_job.job_id)).all()
            existing_item_names = {item.item_name for item in existing_items}

            new_items = []
            for _, row in df.iterrows():
                if row["Item"] not in existing_item_names:
                    item = Item(
                        item_name=row["Item"],
                        espesor=row["Espesor"],
                        longitud=row["Longitud"],
                        ancho=row["Ancho"],
                        alto=row["Alto"],
                        volumen=row["Volumen"],
                        area_superficial=row["Área Superficial"],
                        cantidad=row["Cantidad"],
                        material=row["Material"],
                        ocr=row["OCR"],
                        job_id=existing_job.job_id
                    )
                    session.add(item)
                    session.commit()
                    session.refresh(item)

                    # Crear n objetos basados en la cantidad
                    for _ in range(row["Cantidad"]):
                        obj = Object(
                            current_stage=0,
                            rework=0,
                            scrap=0,
                            item_id=item.item_id
                        )
                        session.add(obj)

            session.commit()
            return JSONResponse(content={"message": "Se agregaron nuevos Items y Objects al Job existente."}, status_code=201)
        else:
            # Si el Job no existe, lo creamos junto con los Items y Objects
            job = Job(job_code=job_code)
            session.add(job)
            session.commit()
            session.refresh(job)

            for _, row in df.iterrows():
                item = Item(
                    item_name=row["Item"],
                    espesor=row["Espesor"],
                    longitud=row["Longitud"],
                    ancho=row["Ancho"],
                    alto=row["Alto"],
                    volumen=row["Volumen"],
                    area_superficial=row["Área Superficial"],
                    cantidad=row["Cantidad"],
                    material=row["Material"],
                    ocr=row["OCR"],
                    job_id=job.job_id
                )
                session.add(item)
                session.commit()
                session.refresh(item)

                # Crear n objetos basados en la cantidad
                for _ in range(row["Cantidad"]):
                    obj = Object(
                        current_stage=0,
                        rework=0,
                        scrap=0,
                        item_id=item.item_id
                    )
                    session.add(obj)

            session.commit()

            # Crear un Stage inicial si no existe
            existing_stage = session.exec(select(Stage).where(Stage.stage_id == 0)).first()
            if not existing_stage:
                stage = Stage(stage_name="Initial")
                session.add(stage)
                session.commit()

            return JSONResponse(content={"message": "Job, Items y Objects creados exitosamente."}, status_code=201)

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "error": "Ocurrió un error inesperado.",
            "details": str(e)
        })
