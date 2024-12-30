from fastapi import APIRouter, HTTPException
from sqlmodel import select
from models import User, Role
from db import SessionDep
from auth import get_password_hash
from models import CreateUser, CreateRole

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@router.post("/add_user", response_model=User, response_model_exclude={"hashed_password"})
def add_user(user_data: CreateUser, session: SessionDep):
    # Verificar si el usuario ya existe
    existing_user = session.exec(select(User).where(User.username == user_data.username)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="El usuario ya existe.")

    # Buscar el role_id basado en role_name
    role = session.exec(select(Role).where(Role.role_name == user_data.role_name)).first()
    if not role:
        raise HTTPException(status_code=404, detail="El rol especificado no existe.")

    # Crear una instancia de User con la contraseña hasheada
    hashed_password = get_password_hash(user_data.password)
    user = User(
        username=user_data.username,
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        hashed_password=hashed_password,
        role_id=role.role_id  # Asignar el role_id encontrado
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@router.post("/add_role", response_model=Role)
def add_role(role_data: CreateRole, session: SessionDep):
    existing_role = session.exec(select(Role).where(Role.role_name == role_data.role_name)).first()
    if existing_role:
        raise HTTPException(status_code=400, detail="El rol ya existe.")

    role = Role(role_name=role_data.role_name)
    session.add(role)
    session.commit()
    session.refresh(role)
    return role

@router.get("/list_users", response_model=list[User], response_model_exclude={"hashed_password"})
def list_users(session: SessionDep):
    users = session.exec(select(User)).all()
    return users

@router.get("/list_roles", response_model=list[Role])
def list_roles(session: SessionDep):
    roles = session.exec(select(Role)).all()
    return roles
