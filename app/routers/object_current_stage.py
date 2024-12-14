from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from db import SessionDep
from models import Object, Item, Stage

router = APIRouter(
    prefix="/object",
    tags=["Object"]
)

@router.put("/update_stage")
def update_object_stage(
    ocr: str,
    new_stage_name: str,
    session: SessionDep
):
    """
    Actualiza el current_stage de un objeto dado el OCR del item asociado
    y el nuevo stage_name al que se quiere actualizar.
    
    :param ocr: OCR del item asociado al objeto (ignorar último carácter).
    :param new_stage_name: Nombre del nuevo stage.
    """
    # Ignorar el último carácter del OCR
    delimitador = "_"
    pieces = ocr.split(delimitador)
    ocr_cleaned, part = pieces[0:-1][0], pieces[-1]


    # Obtener el Item asociado al OCR
    #print(ocr_cleaned)
    item = session.exec(select(Item).where(Item.ocr == ocr_cleaned)).first()
    if not item:
        raise HTTPException(status_code=404, detail=F"Item con el OCR proporcionado no encontrado, OCR {ocr_cleaned}.")

    # Verificar que el nuevo stage exista
    stage = session.exec(select(Stage).where(Stage.stage_name == new_stage_name)).first()
    if not stage:
        raise HTTPException(status_code=404, detail="Stage proporcionado no existe.")
    
    # Obtener el Object asociado al Item
    #print(f"OCR: {ocr_cleaned}, Part: {part}")
    nth_term = int(part) -1
    obj = session.exec(
    select(Object)
    .where(Object.item_id == item.item_id)
    .offset(nth_term)  # Saltar las primeras nth_term piezas.
    .limit(1)          # Obtener solo una pieza.
    ).first()
    #obj = session.exec(select(Object).where(Object.item_id == item.item_id)).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Object asociado al Item no encontrado.")
    
    
    # Actualizar el current_stage del Object
    obj.current_stage = stage.stage_id  # Debes asignar el ID del stage, no el nombre
    session.add(obj)
    session.commit()
    session.refresh(obj)

    return {"message": "Stage actualizado correctamente", "object_id": obj.object_id, "new_stage": new_stage_name}



@router.put("/test_update_stage")
def test_update_object_stage(
    ocr: str,
    new_stage_name: str,
    session: SessionDep
):
    """
    Prueba de actualización del current_stage de un objeto dado el OCR del item asociado
    y el nuevo stage_name al que se quiere actualizar. No realiza cambios en la base de datos.
    
    :param ocr: OCR del item asociado al objeto (ignorar último carácter).
    :param new_stage_name: Nombre del nuevo stage.
    """
    # Ignorar el último carácter del OCR
    delimitador = "_"
    pieces = ocr.split(delimitador)
    ocr_cleaned, part = pieces[0:-1][0], pieces[-1]


    # Obtener el Item asociado al OCR
    #print(ocr_cleaned)
    item = session.exec(select(Item).where(Item.ocr == ocr_cleaned)).first()
    if not item:
        raise HTTPException(status_code=404, detail=F"Item con el OCR proporcionado no encontrado, OCR {ocr_cleaned}.")

    # Verificar que el nuevo stage exista
    stage = session.exec(select(Stage).where(Stage.stage_name == new_stage_name)).first()
    if not stage:
        raise HTTPException(status_code=404, detail="Stage proporcionado no existe.")
    
    # Obtener el Object asociado al Item
    #print(f"OCR: {ocr_cleaned}, Part: {part}")
    nth_term = int(part) -1
    obj = session.exec(
    select(Object)
    .where(Object.item_id == item.item_id)
    .offset(nth_term)  # Saltar las primeras nth_term piezas.
    .limit(1)          # Obtener solo una pieza.
    ).first()
    #obj = session.exec(select(Object).where(Object.item_id == item.item_id)).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Object asociado al Item no encontrado.")
    
    # Simulación de actualización
    return {
        "message": "Prueba exitosa. Estos serían los valores actualizados:",
        "object_id": obj.object_id,
        "Pieza" : part,
        "current_stage": obj.current_stage,
        "new_stage": new_stage_name,
        "associated_item_ocr": ocr_cleaned,
        "associated_item_id": item.item_id,
        "associated_item_name": item.item_name,
    }