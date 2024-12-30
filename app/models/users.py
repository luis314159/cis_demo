from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime, timezone
from pydantic import EmailStr, field_validator
from sqlmodel import Field, Relationship, Session, SQLModel, select
from db import engine

class BaseRole(SQLModel):
    role_name: str = Field(unique=True)

class CreateRole(BaseRole):
    pass

class Role(BaseRole, table=True):
    role_id: Optional[int] = Field(default=None, primary_key=True)
    users: list["User"] = Relationship(back_populates="role")


class Token(SQLModel):
    access_token: str
    token_type: str


class TokenData(SQLModel):
    username: Optional[str] = None

class BaseUser(SQLModel):
    username: str = Field(nullable=False)
    email: EmailStr = Field(nullable=False)
    first_name: str = Field(nullable=False)
    last_name: str = Field(nullable=False)

class CreateUser(BaseUser):
    role_name: str = Field(nullable=False)
    password: str = Field(nullable=False)

class User(BaseUser, table=True):
    __tablename__ = "user"
    user_id: Optional[int] = Field(default=None, primary_key=True)
    is_active: bool = Field(default=True)
    hashed_password: str = Field(nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    role_id: int = Field(foreign_key="role.role_id", nullable=False)
    role: "Role" = Relationship(back_populates="users")

    def update_timestamps(self):
        """Actualiza el campo updated_at al momento de modificar el registro."""
        self.updated_at = datetime.now(timezone.utc)