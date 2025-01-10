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

class ReponseUser(SQLModel):
    user_id: Optional[int]
    role_id: int
    is_active: bool

class BaseUser(SQLModel):
    username: str = Field(nullable=False)
    email: EmailStr = Field(nullable=False)
    first_name: str = Field(nullable=False)
    last_name: str = Field(nullable=False)


class UpdateUserRequest(SQLModel):
    user_name : Optional[str] = None
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    password: Optional[str] = None
    role_name: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("role_name")
    @classmethod
    def validate_role_name(cls, value, info: FieldValidationInfo):
        if value is None:
            return value
        
        # Get the SQLModel session from the context
        session: Session = info.context.get("session")
        if session is None:
            raise ValueError("No database session provided for validation")
        
        # Query to check if the role exists
        query = select(Role).where(Role.role_name == value)
        role = session.exec(query).first()
        
        if role is None:
            raise ValueError(f"The role '{value}' does not exist.")
        
        return value
    

# Modelos para el flujo
class ForgetPasswordRequest(SQLModel):
    email: str = Field(nullable=False)

class ResetPasswordRequest(SQLModel):
    token: str = Field(nullable=False)
    new_password: str = Field(nullable=False)
    confirm_password: str = Field(nullable=False)
