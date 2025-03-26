from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from datetime import timedelta
from sqlmodel import select
from models import Token, User, Role, ResponseUser
from db import SessionDep
import auth
from fastapi.responses import RedirectResponse, JSONResponse
from logs_setup import setup_api_logger

logger = setup_api_logger(__name__)
logger.propagate = False

router = APIRouter(
    prefix="",
    tags=["Authentication"]
)

@router.post("/logout",
        summary="Log out the current user",
        response_description="Redirects to the login page and deletes the authentication cookie",
        responses={
            303: {"description": "Redirects to the login page after logging out"},
        },
    )
async def logout():
    """
    ## Endpoint to log out the current user

    This endpoint logs out the user by deleting the authentication cookie (`auth_token`)
    and redirecting them to the login page.

    ### Workflow:
    1. Create a `RedirectResponse` to the login page with a status code of `303 SEE OTHER`.
    2. Delete the `auth_token` cookie, ensuring it is `httponly` and `samesite="lax"`.
    3. Return the response to redirect the user.

    ### Example Usage:
    ```http
    POST /logout

    Response:
    - Redirects to `/login`
    - Deletes the `auth_token` cookie
    ```
    """
    response = RedirectResponse(
        url="/login",
        status_code=status.HTTP_303_SEE_OTHER
    )
    # Eliminar la cookie
    response.delete_cookie(
        key="auth_token",
        httponly=True,
        samesite="lax"
    )
    return response

@router.post("/token", 
             response_model=Token,  
            summary="Authenticate and generate a JWT access token",
            response_description="Returns a JWT access token for authenticated users",
            responses={
                200: {"description": "Successfully authenticated, returns a JWT access token"},
                401: {"description": "Invalid credentials"},
            },
        )
def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: SessionDep
):
    """
    ## Authentication endpoint to generate a JWT access token

    This endpoint authenticates a user by validating their username and password.
    If the credentials are valid, it generates and returns a JWT access token.

    ### Arguments:
    - **form_data** (OAuth2PasswordRequestForm): Form data containing the username and password.
    - **session** (Session): Database session to query user information.

    ### Returns:
    - **Token**: An object containing the access token and its type.

    ### Raises:
    - `HTTPException`:
        - `401`: If the provided credentials are invalid.

    ### Example Usage:
    ```http
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

    ### Workflow:
    1. Authenticate the user by validating the provided username and password.
    2. If the credentials are invalid, return a `401` error.
    3. If the credentials are valid, generate a JWT access token with an expiration time.
    4. Return the access token and its type.
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

@router.get("/users/me",
            response_model=ResponseUser,
            summary="Get information about the currently authenticated user",
            response_description="Returns the details of the authenticated user",
            responses={
                    200: {"description": "Successfully returned the authenticated user's details"},
                    401: {"description": "Invalid or missing token"},
                    400: {"description": "User is inactive"},
                },
)
def read_users_me(
    current_user: Annotated[User, Depends(auth.get_current_active_user)]
):
    """
    ## Endpoint to get information about the currently authenticated user

    This endpoint retrieves the details of the user currently authenticated via a valid JWT token.
    The response excludes sensitive information like `hashed_password`.

    ### Arguments:
    - **current_user** (User): The authenticated user, obtained from the JWT token.

    ### Returns:
    - **ResponseUser**: The details of the authenticated user.

    ### Raises:
    - `HTTPException`:
        - `401`: If no valid token is provided.
        - `400`: If the user is inactive.

    ### Example Usage:
    ```http
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

    ### Workflow:
    1. Extract the authenticated user from the JWT token using the `get_current_active_user` dependency.
    2. If the token is invalid or missing, return a `401` error.
    3. If the user is inactive, return a `400` error.
    4. Return the authenticated user's details (excluding sensitive fields like `hashed_password`).
    """
    return current_user

@router.get("/admin/users", response_model=list[ResponseUser],
            summary="List all users in the system (Admin only)",
            response_description="Returns a list of all users (excluding sensitive fields like hashed_password)",
            responses={
                200: {"description": "Successfully returned the list of users"},
                401: {"description": "Invalid or missing token"},
                403: {"description": "User does not have admin role"},
                400: {"description": "User is inactive"},
            },
        )
def admin_users(
    session: SessionDep,
    current_user: Annotated[User, Depends(auth.require_role("admin"))]
):
    """
    ## Endpoint to list all users in the system (Admin only)

    This endpoint retrieves a list of all users in the system. It is only accessible to users with the "admin" role.
    The response excludes sensitive information like `hashed_password`.

    ### Arguments:
    - **session** (Session): Database session to query user information.
    - **current_user** (User): The authenticated user (must have the "admin" role).

    ### Returns:
    - **List[ResponseUser]**: A list of all users in the system.

    ### Raises:
    - `HTTPException`:
        - `401`: If no valid token is provided.
        - `403`: If the user does not have the "admin" role.
        - `400`: If the user is inactive.

    ### Example Usage:
    ```http
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

    ### Workflow:
    1. Verify that the current user has the "admin" role (enforced by the `require_role` dependency).
    2. Query the database to retrieve all users.
    3. Return the list of users (excluding sensitive fields like `hashed_password`).
    """
    return session.exec(select(User)).all()

@router.get("/admin/roles", response_model=list[Role],
            summary="List all available roles in the system (Admin only)",
            response_description="Returns a list of all roles in the system",
            responses={
                200: {"description": "Successfully returned the list of roles"},
                401: {"description": "Invalid or missing token"},
                403: {"description": "User does not have admin role"},
                400: {"description": "User is inactive"},
            },
        )
def admin_roles(
    session: SessionDep,
    current_user: Annotated[User, Depends(auth.require_role("admin"))]
):
    """
    ## Endpoint to list all available roles in the system (Admin only)

    This endpoint retrieves a list of all roles available in the system. It is only accessible to users with the "admin" role.

    ### Arguments:
    - **session** (Session): Database session to query role information.
    - **current_user** (User): The authenticated user (must have the "admin" role).

    ### Returns:
    - **List[Role]**: A list of all roles in the system.

    ### Raises:
    - `HTTPException`:
        - `401`: If no valid token is provided.
        - `403`: If the user does not have the "admin" role.
        - `400`: If the user is inactive.

    ### Example Usage:
    ```http
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

    ### Workflow:
    1. Verify that the current user has the "admin" role (enforced by the `require_role` dependency).
    2. Query the database to retrieve all roles.
    3. Return the list of roles.
    """
    return session.exec(select(Role)).all()


@router.post("/authenticate",
            summary="User authentication",
            response_description="Returns an access token or redirects to the home page",
            responses={
                200: {"description": "Successfully authenticated, returns a JWT access token"},
                303: {"description": "Redirects to the home page after setting the token in a cookie"},
                401: {"description": "Invalid credentials"},
            },
    )
async def authenticate(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: SessionDep
):
    """
    ## Endpoint to authenticate a user and generate an access token

    This endpoint authenticates a user by validating their username and password.
    If the credentials are valid, it generates a JWT access token containing the user's role.

    ### Arguments:
    - **username** (str): The username provided in the form.
    - **password** (str): The user's password.

    ### Response Flow:
    - If the credentials are valid, a **JWT token** is generated with the user's role.
    - If the request accepts `application/json`, the token is returned in JSON format.
    - Otherwise, the token is set in a cookie, and the user is redirected to `/home`.

    ### Errors:
    - `401`: Invalid credentials.

    ### Example JSON Response:
    ```json
    {
        "access_token": "eyJhbGciOiJIUzI1...",
        "token_type": "bearer"
    }
    ```

    ### Workflow:
    1. Authenticate the user by validating the provided username and password.
    2. If the credentials are invalid, return a `401` error.
    3. Generate a JWT access token containing the user's role.
    4. If the request accepts `application/json`, return the token in JSON format.
    5. Otherwise, set the token in a cookie and redirect the user to `/home`.
    """
    user = auth.authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    
    # Registrar el login exitoso
    logger.info("Login success for user: %s", user.username)

    # Incluimos el rol del usuario en el payload del token
    access_token = auth.create_access_token(
        data={
            "sub": user.username,
            "role": user.role.role_name  # Agregamos el rol al token
        }
    )
    
    if "application/json" in request.headers.get("accept", ""):
        return {"access_token": access_token, "token_type": "bearer"}
    
    response = RedirectResponse("/home", status_code=303)
    response.set_cookie(
        key="auth_token",
        value=access_token,
        secure=False,
        httponly=True,
        samesite="lax",
        max_age=7200
    )
    return response