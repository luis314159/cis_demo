from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from models import (
    ProcessOrder,
    ProcessOrderCreate,
    ProcessOrderRead,
    ProcessOrderUpdate,
)
from db import SessionDep
from logs_setup import setup_api_logger

router = APIRouter(
    prefix="/process_order",
    tags=["Process Order"],
)

logger = setup_api_logger("process_order")

@router.get("/", response_model=list[ProcessOrderRead])
def get_process_orders(session: SessionDep) -> list[ProcessOrderRead]:
    """Retrieve all existing process orders."""
    return session.exec(select(ProcessOrder)).all()


@router.get("/{process_order_id}", response_model=ProcessOrderRead)
def get_process_order(
    process_order_id: int, session: SessionDep
) -> ProcessOrderRead:
    """Retrieve a single process order by its ID."""
    order = session.get(ProcessOrder, process_order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Process order not found",
        )
    return order


@router.post("/", response_model=ProcessOrderRead, status_code=status.HTTP_201_CREATED)
def create_process_order(
    process_order_data: ProcessOrderCreate, session: SessionDep
) -> ProcessOrderRead:
    """Create a new process order. The process_order_id field is ignored if the table uses auto-increment."""
    new_order = ProcessOrder.model_validate(process_order_data)
    session.add(new_order)
    session.commit()
    session.refresh(new_order)
    return new_order

@router.delete("/{process_order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_process_order(
    process_order_id: int, session: SessionDep
) -> None:
    """Delete a process order. Returns 409 Conflict if there are dependent records."""
    order = session.get(ProcessOrder, process_order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Process order not found",
        )

    try:
        session.delete(order)
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete process order because it is referenced by other records",
        )