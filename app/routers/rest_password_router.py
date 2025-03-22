from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from pydantic import BaseModel
from datetime import timedelta, timezone
from passlib.context import CryptContext
from sqlmodel import select
from db import SessionDep
from models import User
from auth import create_access_token, require_role, verify_token
from config import settings
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from datetime import timedelta
from fastapi import HTTPException, status, BackgroundTasks, Request
from sqlmodel import select
from config import settings
from fastapi.templating import Jinja2Templates
from email.mime.image import MIMEImage
import os
from models import ForgetPasswordRequest, ResetPasswordRequest
from datetime import datetime
 
# Configuración
RESET_TOKEN_EXPIRE_MINUTES = 10
PWD_CONTEXT = CryptContext(schemes=["bcrypt"], deprecated="auto")


router = APIRouter(
    prefix="/password-reset",
    tags=["Password-reset"]
)

templates = Jinja2Templates(directory="templates")

@router.post("/request",
             summary= "Request password reset",
             response_description= "Generates a password reset token and sends an email with instructions.",
             responses={
                200: {"description": "Mail sent successfully"},
                404: {"description": "The user is not registered"},
                500: {"description": "Error sending mail"}
            }
             )
async def request_password_reset(
    request: Request,
    password_request: ForgetPasswordRequest,
    background_tasks: BackgroundTasks,
    session: SessionDep
):
    """
    ## Endpoint to request a password reset

    This endpoint allows users to request a password reset link.
    If the email is registered in the system, a reset token is generated
    and an email with a link to change the password is sent.

    ### Arguments:
    - **request** (Request): HTTP request received.
    - **password_request** (ForgetPasswordRequest): Object containing the user's email.
    - **background_tasks** (BackgroundTasks): Allows running background tasks.
    - **session** (Session): Database session to query users.

    ### Responses:
    - `200`: The email with instructions has been sent.
    - `404`: The user is not registered.
    - `422`: Input data validation error.
    - `500`: An error occurred while sending the email.

    ### Usage Example:
    ```json
    POST /request
    {
        "email": "user@example.com"
    }

    Response:
    {
        "message": "An email with instructions to reset the password has been sent"
    }
    ```

    ### Workflow:
    1. Query the database to find the user associated with the provided email.
    2. If the user is not found, return a `404` error.
    3. Generate a password reset token with an expiration time.
    4. Create a password reset link using the generated token.
    5. Prepare an email with both plain text and HTML content, including the reset link and expiration time.
    6. Attach the application logo to the email (if available).
    7. Use a background task to send the email via SMTP.
    8. If the email fails to send, return a `500` error.
    9. Return a success message confirming that the email has been sent.
    """
    # Buscar usuario
    statement = select(User).where(User.email == password_request.email)
    user = session.exec(statement).first()
    user_name = user.first_name 
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Email no registrado"
        )

    # Generar token
    token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)
    )

    # Crear enlace de reseteo
    reset_link = f"{settings.APP_HOST}/password-reset/reset-password?token={token}"

    # Preparar el correo
    msg = MIMEMultipart('related')
    msg["From"] = f"{settings.MAIL_FROM_NAME} <{settings.MAIL_FROM_EMAIL}>"
    msg["To"] = user.email
    msg["Subject"] = "Instrucciones para restablecer contraseña"

    # Crear la parte alternativa para texto plano y HTML
    msgAlternative = MIMEMultipart('alternative')
    msg.attach(msgAlternative)

    # Versión texto plano
    text_content = f"""
    Has solicitado restablecer tu contraseña.
    
    Por favor, visita el siguiente enlace para continuar:
    {reset_link}
    
    Este enlace expirará en {RESET_TOKEN_EXPIRE_MINUTES} minutos.
    """
    msgAlternative.attach(MIMEText(text_content, 'plain'))

    # Renderizar y adjuntar HTML
    context = {
        "reset_link": reset_link,
        "expiration": RESET_TOKEN_EXPIRE_MINUTES,
        "user": user_name
    }
    html_content = templates.get_template("reset_password.html").render(**context)
    msgAlternative.attach(MIMEText(html_content, 'html'))

    # Adjuntar la imagen del logo
    try:
        with open("static/images/gpoargaHDpng.png", "rb") as logo_file:
            logo = MIMEImage(logo_file.read())
            logo.add_header('Content-ID', '<logo>')
            logo.add_header('Content-Disposition', 'inline')
            msg.attach(logo)
    except FileNotFoundError:
        print("Warning: Logo file not found")
        # Continuar sin el logo en lugar de fallar

    # Función para enviar el correo
    async def send_email_background():
        try:
            with smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT) as server:
                if settings.MAIL_TLS:
                    server.starttls()
                server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
                server.sendmail(
                    settings.MAIL_FROM_EMAIL,
                    user.email,
                    msg.as_string()
                )
        except Exception as e:
            print(f"Error al enviar el correo: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al enviar el correo: {str(e)}"
            )

    # Agregar tarea en segundo plano
    background_tasks.add_task(send_email_background)

    return {
        "message": "Se ha enviado un correo con las instrucciones para restablecer la contraseña"
    }

@router.post("/reset",
             summary= "Resets a user's password",
             response_description= "Confirmation message for password reset",
             responses={
                200: {"description": "Password updated successfully"},
                400: {"description": "Invalid or expired token, or passwords do not match"},
                404: {"description": "User not found"}
                }
            )
async def reset_password(
    request: ResetPasswordRequest,
    session: SessionDep
):
    """
    ## Endpoint to reset a user's password

    This endpoint allows users to reset their password if the provided token is valid.

    ### Arguments:
    - **request** (ResetPasswordRequest): Object containing the reset token, new password, and confirmation password.
    - **session** (SessionDep): Database session to query and update user information.

    ### Responses:
    - `200`: Password has been successfully updated.
    - `400`: Invalid or expired token, or passwords do not match.
    - `404`: User not found.

    ### Example Usage:
    ```json
    POST /reset
    {
        "token": "valid_reset_token",
        "new_password": "new_secure_password",
        "confirm_password": "new_secure_password"
    }

    Response:
    {
        "message": "Password updated successfully"
    }
    ```

    ### Workflow:
    1. Verify the provided token.
    2. If the token is invalid or expired, return a `400` error.
    3. Validate that the new password and confirmation password match.
    4. If passwords do not match, return a `400` error.
    5. Retrieve the user associated with the email in the token payload.
    6. If the user is not found, return a `404` error.
    7. Hash the new password and update the user's password in the database.
    8. Return a success message.
    """
    # Verificar el token
    payload = verify_token(request.token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Token inválido o expirado"
        )
    
    email = payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Token inválido o expirado"
        )

    # Validar contraseñas
    if request.new_password != request.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Las contraseñas no coinciden"
        )

    # Buscar usuario y actualizar contraseña
    statement = select(User).where(User.email == email)
    user = session.exec(statement).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Usuario no encontrado"
        )

    hashed_password = PWD_CONTEXT.hash(request.new_password)
    user.hashed_password = hashed_password
    session.add(user)
    session.commit()

    return {"message": "Contraseña actualizada con éxito"}

@router.get("/reset-password",
            summary="Display the password reset form",
            response_description="Renders the password reset form if the token is valid",
            responses={
                200: {"description": "Password reset form rendered successfully"},
                400: {"description": "Invalid or expired token"},
                404: {"description": "User not found"},
            },
)
async def show_reset_password_form(
    request: Request,
    token: str,
    session: SessionDep
):
    """
    ## Endpoint to display the password reset form

    This endpoint renders a password reset form if the provided token is valid.
    It verifies the token, retrieves the associated user, and passes the necessary
    data to the template for rendering.

    ### Arguments:
    - **request** (Request): The HTTP request object.
    - **token** (str): The reset token provided in the URL.
    - **session** (SessionDep): Database session to query user information.

    ### Responses:
    - `200`: The password reset form is rendered successfully.
    - `400`: The token is invalid or expired.
    - `404`: The user associated with the token is not found.

    ### Workflow:
    1. Verify the provided token.
    2. If the token is invalid or expired, return a `400` error.
    3. Retrieve the email from the token payload.
    4. If the email is not found, return a `400` error.
    5. Query the database for the user associated with the email.
    6. If the user is not found, return a `404` error.
    7. Render the password reset form template with user data.
    """
    # Verificar token y obtener datos del usuario
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Token inválido o expirado"
        )
    
    # Obtener el email del payload
    email = payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido"
        )
    
    # Buscar el usuario en la base de datos
    statement = select(User).where(User.email == email)
    user = session.exec(statement).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    return templates.TemplateResponse(
        "reset_password_form.html",
        {
            "request": request, 
            "token": token,
            "user_name": f"{user.first_name} {user.last_name}" if user.last_name else user.first_name,
            "user_email": user.email
        }
    )

@router.post("/admin-reset/{email}",
        summary="Reset a user's password to a default value (Arga2025)",
        response_description="Confirmation message and details of the updated user",
        responses={
            200: {"description": "Password reset successfully"},
            400: {"description": "Cannot reset password for an inactive user"},
            404: {"description": "User not found"},
            403: {"description": "Forbidden - Only admin users can perform this action"},
        },
)
async def admin_reset_password(
    email: str,
    current_user: Annotated[User, Depends(require_role("admin"))],
    session: SessionDep
):
    """
    ## Endpoint to reset a user's password to a default value (Arga2025)

    This endpoint allows admin users to reset another user's password to a default value.
    Only users with the "admin" role can execute this action.

    ### Arguments:
    - **email** (str): The email of the user whose password will be reset.
    - **current_user** (User): The admin user (injected by the `require_role` dependency).
    - **session** (SessionDep): Database session to query and update user information.

    ### Returns:
    - `dict`: A confirmation message and details of the updated user.

    ### Raises:
    - `HTTPException`: If the user does not exist, the user is inactive, or there is an error in the operation.

    ### Example Usage:
    ```json
    POST /admin-reset/user@example.com

    Response:
    {
        "message": "Password reset successfully for the user user@example.com",
        "user": {
            "email": "user@example.com",
            "username": "example_user",
            "first_name": "John",
            "last_name": "Doe",
            "updated_at": "2023-10-05T12:34:56Z"
        }
    }
    ```

    ### Workflow:
    1. Verify that the current user has the "admin" role (enforced by the `require_role` dependency).
    2. Query the database for the target user using the provided email.
    3. If the user is not found, return a `404` error.
    4. If the user is inactive, return a `400` error.
    5. Reset the user's password to the default value (`Arga2025`) and update the `updated_at` timestamp.
    6. Commit the changes to the database.
    7. Return a confirmation message and details of the updated user.
    """
    # Buscar el usuario objetivo
    statement = select(User).where(User.email == email)
    target_user = session.exec(statement).first()
    
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
        
    if not target_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede resetear la contraseña de un usuario inactivo"
        )

    # Resetear la contraseña
    default_password = "Arga2025"
    hashed_password = PWD_CONTEXT.hash(default_password)
    
    # Actualizar la contraseña y timestamp
    target_user.hashed_password = hashed_password
    target_user.updated_at = datetime.now(timezone.utc)
    
    session.add(target_user)
    session.commit()

    return {
        "message": f"Contraseña reseteada exitosamente para el usuario {target_user.email}",
        "user": {
            "email": target_user.email,
            "username": target_user.username,
            "first_name": target_user.first_name,
            "last_name": target_user.last_name,
            "updated_at": target_user.updated_at
        }
    }