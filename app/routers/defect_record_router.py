from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from datetime import datetime

# Importa tus modelos y dependencias
from models import DefectRecord, DefectRecordCreate, DefectRecordRead, DefectRecordUpdate
from db import SessionDep

router = APIRouter(prefix="/defect-records", tags=["Defect Records"])

@router.post("/", response_model=DefectRecordRead)
def create_defect_record(
    defect_record: DefectRecordCreate, 
    session: Session = Depends(SessionDep)
):
    # Crea una instancia del modelo de base de datos
    db_defect_record = DefectRecord.from_orm(defect_record)
    
    # Guarda en la base de datos
    session.add(db_defect_record)
    session.commit()
    session.refresh(db_defect_record)
    
    return db_defect_record

@router.get("/", response_model=List[DefectRecordRead])
def get_all_defect_records(
    session: Session = Depends(SessionDep),
    skip: int = 0,
    limit: int = 100
):
    # Obtiene todos los registros con paginación
    defect_records = session.exec(
        select(DefectRecord)
        .offset(skip)
        .limit(limit)
    ).all()
    return defect_records

@router.get("/{defect_record_id}", response_model=DefectRecordRead)
def get_defect_record(
    defect_record_id: int, 
    session: Session = Depends(SessionDep)
):
    # Busca por ID
    defect_record = session.get(DefectRecord, defect_record_id)
    if not defect_record:
        raise HTTPException(status_code=404, detail="Defect record not found")
    return defect_record

@router.put("/{defect_record_id}", response_model=DefectRecordRead)
def update_defect_record(
    defect_record_id: int,
    defect_record_data: DefectRecordUpdate,
    session: Session = Depends(SessionDep)
):
    # Obtiene el registro existente
    db_defect_record = session.get(DefectRecord, defect_record_id)
    if not db_defect_record:
        raise HTTPException(status_code=404, detail="Defect record not found")
    
    # Actualiza los campos proporcionados
    update_data = defect_record_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_defect_record, key, value)
    
    # Actualiza la fecha de modificación
    db_defect_record.updated_at = datetime.utcnow()
    
    session.add(db_defect_record)
    session.commit()
    session.refresh(db_defect_record)
    
    return db_defect_record

@router.delete("/{defect_record_id}")
def delete_defect_record(
    defect_record_id: int,
    session: Session = Depends(SessionDep)
):
    # Busca y elimina el registro
    defect_record = session.get(DefectRecord, defect_record_id)
    if not defect_record:
        raise HTTPException(status_code=404, detail="Defect record not found")
    
    session.delete(defect_record)
    session.commit()
    
    return {"message": "Defect record deleted successfully"}