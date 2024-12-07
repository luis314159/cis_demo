from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel
from job import Job


# Modelos para la tabla Clients
class ClientBase(SQLModel):
    client_name: str = Field(max_length=50, nullable=False)
    phone: Optional[str] = Field(max_length=15)
    rfc: Optional[str] = Field(max_length=13)
    CP: Optional[str] = Field(max_length=5)
    address: Optional[str] = Field(max_length=50)


class Client(ClientBase, table=True):
    client_id: Optional[int] = Field(default=None, primary_key=True)
    jobs: List["Job"] = Relationship(back_populates="client")


class ClientCreate(ClientBase):
    pass


class ClientUpdate(ClientBase):
    pass