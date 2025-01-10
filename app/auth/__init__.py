from datetime import datetime, timedelta, timezone
from typing import Annotated
from sqlmodel import Session, select
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
import jwt
from models import Token, TokenData, User, Role
from db import SessionDep

# Configuración de seguridad
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 720

# Configuración de hashing y OAuth2
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def get_user(session: Session, username: str) -> User | None:
    return session.exec(
        select(User).where(User.username == username)
    ).first()

def authenticate_user(session: Session, username: str, password: str) -> User | None:
    user = get_user(session, username)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta
        else timedelta(minutes=15)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(
    session: SessionDep,
    token: Annotated[str, Depends(oauth2_scheme)]
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    
    user = get_user(session, token_data.username)
    if not user:
        raise credentials_exception
    return user

def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inactivo"
        )
    return current_user

def require_role(required_role: str):
    def role_checker(
        current_user: Annotated[User, Depends(get_current_active_user)]
    ) -> User:
        if current_user.role.role_name != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Se requiere el rol '{required_role}'"
            )
        return current_user
    return role_checker


def verify_token(token: str) -> dict | None:
    """
    Verifica la validez de un token JWT y retorna su payload si es válido.
    
    Args:
        token: El token JWT a verificar
        
    Returns:
        dict: El payload del token si es válido
        None: Si el token es inválido o ha expirado
        
    Raises:
        jwt.InvalidTokenError: Si el token es inválido
        jwt.ExpiredSignatureError: Si el token ha expirado
    """
    try:
        # Decodificar el token usando la clave secreta y el algoritmo configurado
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        
        # Verificar que el token contiene un subject (sub)
        if not payload.get("sub"):
            return None
            
        # Verificar que el token no ha expirado
        exp = payload.get("exp")
        if not exp:
            return None
            
        # Convertir exp a datetime para comparación
        exp_datetime = datetime.fromtimestamp(exp, tz=timezone.utc)
        if datetime.now(timezone.utc) >= exp_datetime:
            return None
            
        return payload
        
    except jwt.InvalidTokenError:
        return None