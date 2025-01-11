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

@router.post("/request")
async def request_password_reset(
    request: Request,
    password_request: ForgetPasswordRequest,
    background_tasks: BackgroundTasks,
    session: SessionDep
):
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

@router.post("/reset")
async def reset_password(
    request: ResetPasswordRequest,
    session: SessionDep
):
    """
    Resetea la contraseña de un usuario si el token es válido.
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

@router.get("/reset-password")
async def show_reset_password_form(
    request: Request,
    token: str,
    session: SessionDep
):
    """
    Muestra el formulario para resetear la contraseña
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

@router.post("/admin-reset/{email}")
async def admin_reset_password(
    email: str,
    current_user: Annotated[User, Depends(require_role("admin"))],
    session: SessionDep
):
    """
    Resetea la contraseña de un usuario a un valor predeterminado (Arga2025).
    Solo puede ser ejecutado por usuarios con rol de admin.
    
    Args:
        email: El email del usuario cuya contraseña se reseteará
        current_user: Usuario administrador (inyectado por el decorador require_role)
        session: Sesión de base de datos
        
    Returns:
        dict: Mensaje de confirmación y detalles del usuario actualizado
        
    Raises:
        HTTPException: Si el usuario no existe o hay un error en la operación
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