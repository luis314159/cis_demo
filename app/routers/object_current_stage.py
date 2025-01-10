from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import select
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
    
    ocr_cleaned = "_".join(pieces[0:-1])
    print(ocr_cleaned)
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


@router.delete("/{item_ocr}/{piece_number}")
def delete_object(item_ocr: str, piece_number: int, session: SessionDep):
    """
    Endpoint para eliminar un Object relacionado con un Item dado su OCR y el número de pieza.

    Parámetros:
        - item_ocr: OCR del Item al que pertenece el Object.
        - piece_number: Número de pieza (1-indexado) del Object a eliminar.
    """
    # Buscar el Item asociado al OCR
    item = session.exec(select(Item).where(Item.ocr == item_ocr)).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Item con OCR '{item_ocr}' no encontrado.")

    # Obtener los Objects relacionados al Item
    related_objects = session.exec(select(Object).where(Object.item_id == item.item_id)).all()
    
    if not related_objects:
        raise HTTPException(status_code=404, detail=f"No hay Objects relacionados con el Item '{item_ocr}'.")

    # Validar que el número de pieza esté dentro del rango
    if piece_number < 1 or piece_number > len(related_objects):
        raise HTTPException(status_code=400, detail=f"Número de pieza '{piece_number}' fuera de rango. Hay {len(related_objects)} piezas disponibles.")

    # Seleccionar el Object correspondiente al número de pieza (1-indexado)
    object_to_delete = sorted(related_objects, key=lambda obj: obj.object_id)[piece_number - 1]

    # Eliminar el Object
    session.delete(object_to_delete)
    session.commit()

    # Si era el último Object, eliminar el Item
    if len(related_objects) == 1:
        session.delete(item)
        session.commit()
        return {"message": f"Object con ID '{object_to_delete.object_id}' eliminado. El Item '{item_ocr}' también fue eliminado por no tener más objetos."}

    return {"message": f"Object con ID '{object_to_delete.object_id}' eliminado exitosamente del Item '{item_ocr}'."}


@router.get("/{item_ocr}")
def list_objects(item_ocr: str, session: SessionDep):
    """
    Endpoint para listar todos los Objects relacionados con un Item dado su OCR.

    Parámetros:
        - item_ocr: OCR del Item cuyos Objects se desean listar.

    Retorna:
        - Una lista de Objects relacionados con el Item, incluyendo el nombre del stage actual.
    """
    # Buscar el Item asociado al OCR
    item = session.exec(select(Item).where(Item.ocr == item_ocr)).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Item con OCR '{item_ocr}' no encontrado.")

    # Obtener los Objects relacionados al Item
    related_objects = session.exec(select(Object).where(Object.item_id == item.item_id)).all()
    
    if not related_objects:
        raise HTTPException(status_code=404, detail=f"No hay Objects relacionados con el Item '{item_ocr}'.")

    # Reemplazar current_stage con el nombre del stage
    objects_with_stage_names = []
    for obj in related_objects:
        stage = session.exec(select(Stage).where(Stage.stage_id == obj.current_stage)).first()
        if not stage:
            raise HTTPException(status_code=500, detail=f"Stage con ID '{obj.current_stage}' no encontrado.")
        
        objects_with_stage_names.append({
            "object_id": obj.object_id,
            "item_id": obj.item_id,
            "rework": obj.rework,
            "scrap": obj.scrap,
            "current_stage": stage.stage_name
        })

    return {"item_ocr": item_ocr, "objects": objects_with_stage_names}
