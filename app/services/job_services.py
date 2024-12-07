import pandas as pd
from io import StringIO
from sqlalchemy.ext.asyncio import AsyncSession
from models.object import Item
from fastapi import HTTPException

async def process_csv_and_save_items(file, session: AsyncSession):
    # Leer el archivo CSV
    content = await file.read()
    try:
        df = pd.read_csv(StringIO(content.decode("utf-8")))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al leer el CSV: {str(e)}")

    # Validar las columnas esperadas
    expected_columns = ["object_id", "current_stage", "ocr", "rework", "scrap"]
    if not all(col in df.columns for col in expected_columns):
        raise HTTPException(status_code=400, detail=f"El CSV debe contener las columnas: {expected_columns}")

    # Procesar y guardar los datos
    items = []
    for _, row in df.iterrows():
        # Validar datos específicos
        if not isinstance(row["object_id"], int) or row["object_id"] <= 0:
            raise HTTPException(status_code=400, detail=f"Invalid object_id: {row['object_id']}")
        if not isinstance(row["current_stage"], int) or row["current_stage"] <= 0:
            raise HTTPException(status_code=400, detail=f"Invalid current_stage: {row['current_stage']}")

        # Crear un nuevo objeto Item
        item = Item(
            object_id=row["object_id"],
            current_stage=row["current_stage"],
            ocr=row["ocr"],
            rework=row.get("rework", 0),
            scrap=row.get("scrap", 0)
        )
        items.append(item)

    # Guardar los datos en la base de datos
    session.add_all(items)
    await session.commit()

    return f"Se guardaron {len(items)} items en la base de datos."
