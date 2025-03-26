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
        - employee_number: Optional employee number (for all users)
        - supervisor_number: Optional supervisor number (only for supervisors)

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
        "role_name": "operator",
        "employee_number": "EMP-001"
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
        "is_active": true,
        "employee_number": "EMP-001",
        "supervisor_number": null
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
    
    # Verificar si es un supervisor
    is_supervisor = role.role_name.lower() == 'supervisor'
    
    # Verificar número de supervisor (solo si es supervisor y se proporciona un número)
    if user_data.supervisor_number:
        if not is_supervisor:
            raise HTTPException(
                status_code=400, 
                detail="Solo los usuarios con rol de supervisor pueden tener número de supervisor"
            )
            
        # Verificar si el número de supervisor ya está en uso
        existing_supervisor = session.exec(
            select(User).where(User.supervisor_number == user_data.supervisor_number)
        ).first()
        if existing_supervisor:
            raise HTTPException(
                status_code=400, 
                detail="El número de supervisor ya está en uso"
            )
    
    # Verificar que un supervisor tenga número de supervisor
    if is_supervisor and not user_data.supervisor_number:
        raise HTTPException(
            status_code=400,
            detail="Los usuarios con rol de supervisor deben tener un número de supervisor"
        )

    # Crear una instancia de User con la contraseña hasheada
    hashed_password = get_password_hash(user_data.password)
    user = User(
        username=user_data.username,
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        hashed_password=hashed_password,
        role_id=role.role_id,
        employee_number=user_data.employee_number,  # Añadido el campo de número de empleado
        supervisor_number=user_data.supervisor_number if is_supervisor else None  # Añadido el campo de número de supervisor
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
            response_description="Returns list of all users"
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
        - employee_number: Employee identification number
        - supervisor_number: Supervisor identification number (only for supervisor role)

    ### Example Request:
    ```json
    {
        "email": "new.email@example.com",
        "role_name": "supervisor",
        "supervisor_number": "SUP-1234"
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
        "is_active": true,
        "employee_number": "EMP-001",
        "supervisor_number": "SUP-1234"
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
    
    # Variable para rastrear si el rol ha cambiado y qué rol es
    new_role = None
    is_supervisor = False
    
    # Verificar si se está cambiando el rol
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
        # Determinar si el nuevo rol es de supervisor
        is_supervisor = new_role.role_name.lower() == 'supervisor'
    else:
        # Obtener el rol actual
        current_role = session.exec(
            select(Role).where(Role.role_id == db_user.role_id)
        ).first()
        is_supervisor = current_role.role_name.lower() == 'supervisor'

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

    # Actualizar el rol si se ha proporcionado y es diferente
    if new_role and new_role.role_id != db_user.role_id:
        db_user.role_id = new_role.role_id
        changes_made = True
        
        # Si cambia de supervisor a otro rol, eliminar el número de supervisor
        if not is_supervisor and db_user.supervisor_number:
            db_user.supervisor_number = None
            changes_made = True

    if user_update.is_active is not None and user_update.is_active != db_user.is_active:
        db_user.is_active = user_update.is_active
        changes_made = True
    
    # Manejar el número de empleado
    if user_update.employee_number is not None and user_update.employee_number != db_user.employee_number:
        db_user.employee_number = user_update.employee_number
        changes_made = True
    
    # Manejar el número de supervisor
    if user_update.supervisor_number is not None:
        # Verificar si el rol es de supervisor
        if not is_supervisor:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Solo los usuarios con rol de supervisor pueden tener número de supervisor"
            )
        
        # Verificar si el número de supervisor ya está en uso por otro usuario
        if user_update.supervisor_number != db_user.supervisor_number:
            existing_supervisor = session.exec(
                select(User)
                .where(User.supervisor_number == user_update.supervisor_number)
                .where(User.username != username)
            ).first()
            
            if existing_supervisor:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El número de supervisor ya está en uso"
                )
                
            db_user.supervisor_number = user_update.supervisor_number
            changes_made = True
    
    # Verificar que un usuario con rol de supervisor tenga número de supervisor
    if is_supervisor and not (db_user.supervisor_number or user_update.supervisor_number):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Los usuarios con rol de supervisor deben tener un número de supervisor"
        )

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
            detail=f"Error al actualizar el usuario: {str(e)}"
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