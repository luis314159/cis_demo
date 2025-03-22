from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import select
from db import SessionDep
from models import Object, Item, Stage

router = APIRouter(
    prefix="/object",
    tags=["Object"]
)

@router.put("/update_stage",
            summary="Update the current stage of an object",
            response_description="Confirmation message after updating the object's stage",
            tags=["Object"],
            responses={
                200: {"description": "Stage updated successfully"},
                404: {"description": "Item, stage, or object not found"},
            },
    )
def update_object_stage(
    ocr: str,
    new_stage_name: str,
    session: SessionDep
):
    """
    ## Endpoint to update the current stage of an object

    This endpoint updates the `current_stage` of an object based on the OCR of the associated item
    and the name of the new stage.

    ### Arguments:
    - **ocr** (str): OCR of the item associated with the object (ignore the last character).
    - **new_stage_name** (str): Name of the new stage.

    ### Returns:
    - **dict**: A confirmation message with the updated object ID and new stage name.

    ### Raises:
    - `HTTPException`:
        - `404`: If the item, stage, or object is not found.

    ### Example Usage:
    ```http
    PUT /object/update_stage
    Body:
    {
        "ocr": "ITEM123_1",
        "new_stage_name": "CUTTING"
    }

    Response:
    {
        "message": "Stage actualizado correctamente",
        "object_id": 1,
        "new_stage": "CUTTING"
    }
    ```

    ### Workflow:
    1. Clean the OCR by ignoring the last character.
    2. Retrieve the item associated with the cleaned OCR.
    3. Verify that the new stage exists.
    4. Retrieve the object associated with the item and the specified part number.
    5. Update the `current_stage` of the object.
    6. Commit the changes to the database.
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



@router.put("/test_update_stage",
            summary="Test updating the current stage of an object",
            response_description="Simulation of updating the object's stage without making changes to the database",
            tags=["Object"], 
            responses={
                200: {"description": "Test successful, returns the values that would be updated"},
                404: {"description": "Item, stage, or object not found"},
            },
    )
def test_update_object_stage(
    ocr: str,
    new_stage_name: str,
    session: SessionDep
):
    """
    ## Endpoint to test updating the current stage of an object

    This endpoint simulates updating the `current_stage` of an object based on the OCR of the associated item
    and the name of the new stage. No changes are made to the database.

    ### Arguments:
    - **ocr** (str): OCR of the item associated with the object (ignore the last character).
    - **new_stage_name** (str): Name of the new stage.

    ### Returns:
    - **dict**: A confirmation message with the values that would be updated.

    ### Raises:
    - `HTTPException`:
        - `404`: If the item, stage, or object is not found.

    ### Example Usage:
    ```http
    PUT /object/test_update_stage
    Body:
    {
        "ocr": "ITEM123_1",
        "new_stage_name": "CUTTING"
    }

    Response:
    {
        "message": "Prueba exitosa. Estos serían los valores actualizados:",
        "object_id": 1,
        "Pieza": "1",
        "current_stage": 1,
        "new_stage": "CUTTING",
        "associated_item_ocr": "ITEM123",
        "associated_item_id": 1,
        "associated_item_name": "Item 1"
    }
    ```

    ### Workflow:
    1. Clean the OCR by ignoring the last character.
    2. Retrieve the item associated with the cleaned OCR.
    3. Verify that the new stage exists.
    4. Retrieve the object associated with the item and the specified part number.
    5. Return the values that would be updated.
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


@router.delete("/{item_ocr}/{piece_number}",
            summary="Delete an object by item OCR and piece number",
            response_description="Confirmation message after deleting the object",
            tags=["Object"],
            responses={
                200: {"description": "Object deleted successfully"},
                404: {"description": "Item or object not found"},
                400: {"description": "Piece number out of range"},
            },
    )
def delete_object(item_ocr: str, piece_number: int, session: SessionDep):
    """
    ## Endpoint to delete an object by item OCR and piece number

    This endpoint deletes an object associated with an item identified by its OCR and a specific piece number.

    ### Arguments:
    - **item_ocr** (str): OCR of the item associated with the object.
    - **piece_number** (int): Piece number (1-indexed) of the object to delete.

    ### Returns:
    - **dict**: A confirmation message.

    ### Raises:
    - `HTTPException`:
        - `404`: If the item or object is not found.
        - `400`: If the piece number is out of range.

    ### Example Usage:
    ```http
    DELETE /object/ITEM123/1

    Response:
    {
        "message": "Object con ID '1' eliminado exitosamente del Item 'ITEM123'."
    }
    ```

    ### Workflow:
    1. Retrieve the item associated with the OCR.
    2. Retrieve all objects associated with the item.
    3. Validate that the piece number is within range.
    4. Delete the specified object.
    5. If the item has no more objects, delete the item as well.
    6. Commit the changes to the database.
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


@router.get("/{item_ocr}",
            summary="List all objects associated with an item by OCR",
            response_description="Returns a list of objects associated with the item",
            tags=["Object"],
            responses={
                200: {"description": "Successfully returned the list of objects"},
                404: {"description": "Item or objects not found"},
            },
        )
def list_objects(item_ocr: str, session: SessionDep):
    """
    ## Endpoint to list all objects associated with an item by OCR

    This endpoint retrieves a list of all objects associated with an item identified by its OCR.

    ### Arguments:
    - **item_ocr** (str): OCR of the item whose objects are to be listed.

    ### Returns:
    - **dict**: A list of objects associated with the item, including the current stage name.

    ### Raises:
    - `HTTPException`:
        - `404`: If the item or objects are not found.

    ### Example Usage:
    ```http
    GET /object/ITEM123

    Response:
    {
        "item_ocr": "ITEM123",
        "objects": [
            {
                "object_id": 1,
                "item_id": 1,
                "rework": false,
                "scrap": false,
                "current_stage": "CUTTING"
            },
            {
                "object_id": 2,
                "item_id": 1,
                "rework": false,
                "scrap": false,
                "current_stage": "MACHINING"
            }
        ]
    }
    ```

    ### Workflow:
    1. Retrieve the item associated with the OCR.
    2. Retrieve all objects associated with the item.
    3. Replace the `current_stage` ID with the stage name.
    4. Return the list of objects.
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
