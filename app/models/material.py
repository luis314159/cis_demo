from typing import Optional
from sqlmodel import Field, SQLModel, Session


# Modelos para la tabla Materials
class MaterialBase(SQLModel):
    material_name: str = Field(max_length=50, unique=True, nullable=False)


class Material(MaterialBase, table=True):
    material_id: Optional[int] = Field(default=None, primary_key=True)


class MaterialCreate(MaterialBase):
    pass


class MaterialUpdate(MaterialBase):
    pass