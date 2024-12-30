from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from datetime import timedelta
from sqlmodel import select
from models import Token, User, Role
from db import SessionDep
import auth
from fastapi.responses import RedirectResponse

router = APIRouter(
    prefix="",
    tags=["auth"]
)

@router.post("/token", response_model=Token)
def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: SessionDep
):
    """
    Endpoint de autenticación que genera un token de acceso JWT.

    Args:
        form_data (OAuth2PasswordRequestForm): Formulario con username y password.
        session (Session): Sesión de base de datos.

    Returns:
        Token: Objeto con el token de acceso y su tipo.

    Raises:
        HTTPException: 
            - 401: Si las credenciales son inválidas.
            
    Examples:
        ```
        POST /token
        Form Data:
            username: usuario
            password: contraseña
        
        Response:
        {
            "access_token": "eyJhbGciOiJIUzI1NiIs...",
            "token_type": "bearer"
        }
        ```
    """
    user = auth.authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth.create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return Token(access_token=access_token, token_type="bearer")

@router.get("/users/me", response_model=User, response_model_exclude={"hashed_password"})
def read_users_me(
    current_user: Annotated[User, Depends(auth.get_current_active_user)]
):
    """
    Obtiene la información del usuario actualmente autenticado.

    Args:
        current_user (User): Usuario actual obtenido del token JWT.

    Returns:
        User: Datos del usuario autenticado (excluye hashed_password).

    Raises:
        HTTPException:
            - 401: Si no hay token válido.
            - 400: Si el usuario está inactivo.

    Examples:
        ```
        GET /users/me
        Headers:
            Authorization: Bearer eyJhbGciOiJIUzI1NiIs...

        Response:
        {
            "user_id": 1,
            "username": "usuario",
            "email": "usuario@example.com",
            "first_name": "Nombre",
            "last_name": "Apellido",
            "role_id": 1
        }
        ```
    """
    return current_user

@router.get("/admin/users", response_model=list[User], response_model_exclude={"hashed_password"})
def admin_users(
    session: SessionDep,
    current_user: Annotated[User, Depends(auth.require_role("admin"))]
):
    """
    Lista todos los usuarios del sistema. Solo accesible por administradores.

    Args:
        session (Session): Sesión de base de datos.
        current_user (User): Usuario actual (debe tener rol admin).

    Returns:
        List[User]: Lista de todos los usuarios (excluye hashed_password).

    Raises:
        HTTPException:
            - 401: Si no hay token válido.
            - 403: Si el usuario no tiene rol de administrador.
            - 400: Si el usuario está inactivo.

    Examples:
        ```
        GET /admin/users
        Headers:
            Authorization: Bearer eyJhbGciOiJIUzI1NiIs...

        Response:
        [
            {
                "user_id": 1,
                "username": "usuario1",
                "email": "usuario1@example.com",
                "first_name": "Nombre1",
                "last_name": "Apellido1",
                "role_id": 1
            },
            ...
        ]
        ```
    """
    return session.exec(select(User)).all()

@router.get("/admin/roles", response_model=list[Role])
def admin_roles(
    session: SessionDep,
    current_user: Annotated[User, Depends(auth.require_role("admin"))]
):
    """
    Lista todos los roles disponibles en el sistema. Solo accesible por administradores.

    Args:
        session (Session): Sesión de base de datos.
        current_user (User): Usuario actual (debe tener rol admin).

    Returns:
        List[Role]: Lista de todos los roles existentes.

    Raises:
        HTTPException:
            - 401: Si no hay token válido.
            - 403: Si el usuario no tiene rol de administrador.
            - 400: Si el usuario está inactivo.

    Examples:
        ```
        GET /admin/roles
        Headers:
            Authorization: Bearer eyJhbGciOiJIUzI1NiIs...

        Response:
        [
            {
                "role_id": 1,
                "role_name": "admin"
            },
            {
                "role_id": 2,
                "role_name": "user"
            },
            ...
        ]
        ```
    """
    return session.exec(select(Role)).all()
from fastapi.responses import JSONResponse

@router.post("/authenticate", name="authenticate")
def authenticate_and_redirect(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: SessionDep
):
    """
    Autentica al usuario, genera un token y redirige a /home.
    Si las credenciales son incorrectas, devuelve un mensaje de error.
    """
    user = auth.authenticate_user(session, form_data.username, form_data.password)
    if not user:
        # Devuelve un JSON con el error en lugar de redirigir
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Usuario o contraseña incorrectos"}
        )
    
    # Generar token JWT
    access_token = auth.create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    # Configurar la redirección y la cookie
    response = RedirectResponse(url="/home", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="Authorization",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=True,  # Asegúrate de usar HTTPS en producción
        samesite="Lax",
    )
    return response
