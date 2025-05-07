from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime, timezone
from pydantic import EmailStr, FieldValidationInfo, field_validator
from sqlmodel import Field, Relationship, SQLModel, Session, select
from models import DefectRecord

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
    employee_number: int = Field(unique=True, nullable=False)
    username: str = Field(max_length=50, unique=True, nullable=False)
    email: str = Field(max_length=255, nullable=True)
    first_name: str = Field(max_length=50)
    middle_name: Optional[str] = Field(max_length=50, default=None)
    first_surname: str = Field(max_length=50)
    second_surname: Optional[str] = Field(max_length=50, default=None)
    hashed_password: str = Field(max_length=255, nullable=False)
    is_active: bool = Field(default=True)
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = Field(default=None)
    deleted_at: Optional[datetime] = Field(default=None)

class CreateUser(BaseUser):
    role_name: int = Field(foreign_key="role.role_id", nullable=False)
    password: str = Field(nullable=False)
    supervisor_number: Optional[str] = Field(default=None)


class User(BaseUser, table=True):
    __tablename__ = "user"
    user_id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str = Field(nullable=False)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = Field(default=None)
    deleted_at: Optional[datetime] = Field(default=None)
    role_id: int = Field(foreign_key="role.role_id", nullable=False)
    role: Role = Relationship(back_populates="users")
    supervisor_number: Optional[int] = Field(default=None)
    
    # Relaciones con DefectRecord
    inspected_defects: List["DefectRecord"] = Relationship(
        back_populates="inspector",
        sa_relationship_kwargs={"foreign_keys": "DefectRecord.inspector_user_id"}
    )
    family_defects: List["DefectRecord"] = Relationship(
        back_populates="family_user",
        sa_relationship_kwargs={"foreign_keys": "DefectRecord.family_user_id"}
    )

    @field_validator('supervisor_number')
    @classmethod
    def validate_supervisor_number(cls, v, info: FieldValidationInfo):
        if v is not None:
            role = info.data.get('role')
            if role and role.role_name.lower() != 'supervisor':
                raise ValueError("Solo supervisores pueden tener número de supervisor")
        return v

    def update_timestamps(self):
        self.updated_at = datetime.now(timezone.utc)


class ResponseUser(SQLModel):
    user_id: int
    employee_number: int
    username: str
    email: EmailStr | None
    first_name: str
    second_name: str | None
    first_surname: str 
    second_surname: str | None
    role: Role
    is_active: bool
    created_at: datetime
    supervisor_number: Optional[int] = None

class UpdateUserRequest(SQLModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    first_surname: Optional[str] = None
    password: Optional[str] = None
    role_id: Optional[int] = None
    is_active: Optional[bool] = None
    supervisor_number: Optional[int] = None
    

# Modelos para el flujo
class ForgetPasswordRequest(SQLModel):
    email: str = Field(nullable=False)

class ResetPasswordRequest(SQLModel):
    token: str = Field(nullable=False)
    new_password: str = Field(nullable=False)
    confirm_password: str = Field(nullable=False)