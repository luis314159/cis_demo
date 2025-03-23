from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime, timezone
from pydantic import EmailStr, FieldValidationInfo, field_validator
from sqlmodel import Field, Relationship, SQLModel, Session, select


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
    employee_number: Optional[str] = Field(default=None)


class CreateUser(BaseUser):
    role_name: str = Field(nullable=False)
    password: str = Field(nullable=False)
    supervisor_number: Optional[str] = Field(default=None)


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
    
    # Nuevo campo para todos los usuarios
    employee_number: Optional[str] = Field(default=None)
    
    # Campo específico para supervisores
    supervisor_number: Optional[str] = Field(default=None)

    @field_validator('supervisor_number')
    @classmethod
    def validate_supervisor_number(cls, v, info: FieldValidationInfo):
        # Este validador solo se ejecuta cuando se proporciona un valor
        if v is not None:
            # Obtenemos el role_id o role_name si está disponible
            values = info.data
            role = values.get('role')
            role_name = getattr(role, 'role_name', None) if role else None
            
            # Si tenemos acceso directo al nombre del rol
            if role_name and role_name.lower() != 'supervisor':
                raise ValueError("El número de administrador solo es válido para usuarios con rol de supervisor")
        return v

    def update_timestamps(self):
        """Actualiza el campo updated_at al momento de modificar el registro."""
        self.updated_at = datetime.now(timezone.utc)

class ResponseUser(SQLModel):
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    user_id: int
    role_id: int
    role: Role
    is_active: bool
    employee_number: Optional[str] = None
    supervisor_number: Optional[str] = None

class UpdateUserRequest(SQLModel):
    # No heredamos de BaseUser porque queremos todos los campos opcionales
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    password: Optional[str] = None
    role_name: Optional[str] = None
    is_active: Optional[bool] = None
    employee_number: Optional[str] = None
    supervisor_number: Optional[str] = None
    

# Modelos para el flujo
class ForgetPasswordRequest(SQLModel):
    email: str = Field(nullable=False)

class ResetPasswordRequest(SQLModel):
    token: str = Field(nullable=False)
    new_password: str = Field(nullable=False)
    confirm_password: str = Field(nullable=False)