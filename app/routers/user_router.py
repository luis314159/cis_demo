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


@router.post("/add_user", response_model=ResponseUser,
            summary="Create new user",
            response_description="Returns the created user",
            responses={
                201: {"description": "User created successfully"},
                400: {"description": "Username already exists"},
                404: {"description": "Specified role not found"}
            }
    )
def add_user(user_data: CreateUser, session: SessionDep):
    """
    ## Create a new user account

    Registers a new user in the system with the provided credentials and role.

    ### Parameters:
    - **user_data** (CreateUser): User creation data including:
        - username: Unique identifier for the user
        - password: Plain text password (will be hashed)
        - email: User's email address
        - first_name: User's first name
        - last_name: User's last name
        - role_name: Name of the assigned role

    ### Returns:
    - **ResponseUser**: Created user details (excluding password)

    ### Example Request:
    ```json
    {
        "username": "jdoe",
        "password": "securepassword123",
        "email": "jdoe@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "role_name": "operator"
    }
    ```

    ### Example Response:
    ```json
    {
        "user_id": 5,
        "username": "jdoe",
        "email": "jdoe@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "role_id": 2,
        "is_active": true
    }
    ```
    """
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


@router.post("/add_role", response_model=Role,
            summary="Create new role",
            response_description="Returns the created role",
            responses={
                201: {"description": "Role created successfully"},
                400: {"description": "Role already exists"}
            }
        )
def add_role(role_data: CreateRole, session: SessionDep):
    """
    ## Create a new system role

    Adds a new role to the system's role-based access control.

    ### Parameters:
    - **role_data** (CreateRole): Role creation data including:
        - role_name: Unique name for the new role

    ### Example Request:
    ```json
    {
        "role_name": "quality_inspector"
    }
    ```

    ### Example Response:
    ```json
    {
        "role_id": 3,
        "role_name": "quality_inspector"
    }
    ```
    """
    existing_role = session.exec(select(Role).where(Role.role_name == role_data.role_name)).first()
    if existing_role:
        raise HTTPException(status_code=400, detail="El rol ya existe.")

    role = Role(role_name=role_data.role_name)
    session.add(role)
    session.commit()
    session.refresh(role)
    return role


@router.get("/list_users", response_model=list[ResponseUser], response_model_exclude={"hashed_password"},
            summary="List all users",
            response_description="Returns list of all users",
            response_model_exclude={"hashed_password"}
        )
def list_users(session: SessionDep):
    """
    ## Get all system users

    Retrieves a complete list of all registered users.

    ### Returns:
    - **List[ResponseUser]**: List of user objects excluding sensitive data

    ### Example Response:
    ```json
    [
        {
            "user_id": 1,
            "username": "admin",
            "email": "admin@example.com",
            "first_name": "System",
            "last_name": "Admin",
            "role_id": 1,
            "is_active": true
        },
        {
            "user_id": 2,
            "username": "jdoe",
            "email": "jdoe@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "role_id": 2,
            "is_active": true
        }
    ]
    ```
    """
    users = session.exec(select(User)).all()
    return users


@router.get("/list_roles", response_model=list[Role],
            summary="List all roles",
            response_description="Returns list of all roles"
    )
def list_roles(session: SessionDep):
    """
    ## Get all system roles

    Retrieves a complete list of all available roles.

    ### Returns:
    - **List[Role]**: List of role objects

    ### Example Response:
    ```json
    [
        {
            "role_id": 1,
            "role_name": "admin"
        },
        {
            "role_id": 2,
            "role_name": "operator"
        }
    ]
    ```
    """
    roles = session.exec(select(Role)).all()
    return roles


@router.patch("/{username}", response_model=ResponseUser,
            summary="Update user information",
            response_description="Returns updated user details",
            responses={
                200: {"description": "User updated successfully"},
                400: {"description": "Invalid update data"},
                404: {"description": "User not found"}
            }
    )
def update_user(
    username: str,
    user_update: UpdateUserRequest,
    session: SessionDep,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    ## Update user information

    Partially updates user information. Only included fields will be modified.

    ### Parameters:
    - **username** (str): Username of the user to update
    - **user_update** (UpdateUserRequest): Fields to update including:
        - email: New email address
        - first_name: New first name
        - last_name: New last name
        - password: New password
        - role_name: New role name
        - is_active: Account status

    ### Example Request:
    ```json
    {
        "email": "new.email@example.com",
        "role_name": "supervisor"
    }
    ```

    ### Example Response:
    ```json
    {
        "user_id": 2,
        "username": "jdoe",
        "email": "new.email@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "role_id": 3,
        "is_active": true
    }
    ```
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
    
@router.delete("/{username}", status_code=status.HTTP_204_NO_CONTENT,
                responses={
                    204: {"description": "User deleted successfully"},
                    400: {"description": "Cannot delete self"},
                    404: {"description": "User not found"}
                }
    )
def delete_user(
    username: str,
    session: SessionDep,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    ## Delete user account

    Permanently removes a user account from the system.

    ### Parameters:
    - **username** (str): Username of the user to delete

    ### Security:
    - Requires authentication
    - Cannot delete your own account

    ### Returns:
    - 204 No Content on success
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