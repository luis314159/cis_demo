from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select, Session
from models import User, Role, UpdateUserRequest
from db import SessionDep
from auth import get_password_hash, get_current_active_user
from models import CreateUser, CreateRole, ResponseUser
from typing import Annotated, Optional


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@router.post("/add_user", response_model=ResponseUser)
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


@router.get("/list_users", response_model=list[ResponseUser], response_model_exclude={"hashed_password"})
def list_users(session: SessionDep):
    users = session.exec(select(User)).all()
    return users


@router.get("/list_roles", response_model=list[Role])
def list_roles(session: SessionDep):
    roles = session.exec(select(Role)).all()
    return roles


@router.patch("/{username}", response_model=ResponseUser)
def update_user(
    username: str,
    user_update: UpdateUserRequest,
    session: SessionDep,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Actualiza los datos de un usuario existente parcialmente.
    Los campos que no se incluyan no serán modificados.
    """
    # Buscar el usuario a actualizar
    db_user = session.exec(
        select(User).where(User.username == username)
    ).first()

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    # Bandera para rastrear si se realizó algún cambio
    changes_made = False

    # Actualizar los campos opcionales
    if user_update.email is not None and user_update.email != db_user.email:
        # Verificar si el nuevo email ya existe para otro usuario
        existing_email = session.exec(
            select(User)
            .where(User.email == user_update.email)
            .where(User.username != username)
        ).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está en uso"
            )
        db_user.email = user_update.email
        changes_made = True

    if user_update.first_name is not None and user_update.first_name != db_user.first_name:
        db_user.first_name = user_update.first_name
        changes_made = True

    if user_update.last_name is not None and user_update.last_name != db_user.last_name:
        db_user.last_name = user_update.last_name
        changes_made = True

    if user_update.password is not None:
        db_user.hashed_password = get_password_hash(user_update.password)
        changes_made = True

    if user_update.role_name is not None:
        # Verificar si el nuevo rol existe
        new_role = session.exec(
            select(Role).where(Role.role_name == user_update.role_name)
        ).first()
        if not new_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El rol especificado no existe"
            )
        if new_role.role_id != db_user.role_id:
            db_user.role_id = new_role.role_id
            changes_made = True

    if user_update.is_active is not None and user_update.is_active != db_user.is_active:
        db_user.is_active = user_update.is_active
        changes_made = True

    # Actualizar timestamp solo si se realizaron cambios
    if changes_made:
        db_user.update_timestamps()

    # Guardar cambios en la base de datos
    try:
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        return db_user
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al actualizar el usuario"
        )
    
@router.delete("/{username}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    username: str,
    session: SessionDep,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    Elimina un usuario existente dado su username.
    Retorna 204 No Content si la eliminación fue exitosa.
    """
    # Buscar el usuario a eliminar
    db_user = session.exec(
        select(User).where(User.username == username)
    ).first()

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    # Prevenir que un usuario se elimine a sí mismo
    if current_user.username == username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes eliminar tu propio usuario"
        )

    try:
        session.delete(db_user)
        session.commit()
        return None
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al eliminar el usuario"
        )