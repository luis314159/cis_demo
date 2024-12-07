from sqlmodel import Field, SQLModel
from typing import Optional


# Modelos para la tabla Users
class RoleBase(SQLModel):
    role: str = Field(max_length=20, nullable=False)


class Role(RoleBase, table=True):
    role_id: Optional[int] = Field(default=None, primary_key=True)

