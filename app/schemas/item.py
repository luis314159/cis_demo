from typing import Optional
from pydantic import BaseModel

class ItemBase(BaseModel):
    object_id: int
    current_stage: int
    ocr: str
    rework: int
    scrap: Optional[int] = 0

class ItemCreate(ItemBase):
    pass

class ItemRead(ItemBase):
    item_id: int

    class Config:
        orm_mode = True
