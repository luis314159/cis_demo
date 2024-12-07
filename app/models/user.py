from datetime import datetime, timezone
from typing import Optional
from pydantic import EmailStr, field_validator
from sqlmodel import Field, SQLModel, select, Session, Relationship
from db import engine
from .role import Role


class UserBase(SQLModel):
    first_name: str = Field(max_length=20, nullable=False)
    last_name: str = Field(max_length=20, nullable=False)
    email: EmailStr = Field(nullable=False)
    password_hash: str = Field(max_length=255, nullable=False)
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = Field(default=None)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value):
        with Session(engine) as session:  # Asegúrate de que `engine` esté bien configurado
            query = select(User).where(User.email == value)
            result = session.exec(query).first()
            if result:
                raise ValueError("This email is already registered")
        return value


class User(UserBase, table=True):
    user_id: Optional[int] = Field(default=None, primary_key=True)
    role_id: int = Field(foreign_key="role.role_id", nullable=False)
    role: Role = Relationship()


class UserCreate(UserBase):
    role_id: int


class UserUpdate(UserBase):
    pass
