from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
import jwt

# Configuración de seguridad (igual que en tu sistema)
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 720

# Usando la misma configuración que en tu sistema de autenticación
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_text(plain_text: str) -> str:
    """
    Hashea un texto usando el mismo método que el sistema de autenticación.
    
    Args:
        plain_text: El texto plano a hashear
        
    Returns:
        str: El texto hasheado
    """
    return pwd_context.hash(plain_text)

def verify_text(plain_text: str, hashed_text: str) -> bool:
    """
    Verifica si un texto plano coincide con un hash.
    
    Args:
        plain_text: El texto plano a verificar
        hashed_text: El hash con el que comparar
        
    Returns:
        bool: True si coinciden, False en caso contrario
    """
    return pwd_context.verify(plain_text, hashed_text)

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Crea un token JWT de acceso.
    
    Args:
        data: Datos a codificar en el token
        expires_delta: Tiempo de expiración opcional
        
    Returns:
        str: El token JWT
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta
        else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> dict | None:
    """
    Verifica la validez de un token JWT y retorna su payload si es válido.
    
    Args:
        token: El token JWT a verificar
        
    Returns:
        dict: El payload del token si es válido
        None: Si el token es inválido o ha expirado
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


# Ejemplo de uso:
if __name__ == "__main__":
    # Ejemplo de hasheo de contraseña
    password = "Arga2025"
    hashed = hash_text(password)
    print(f"Contraseña original: {password}")
    print(f"Contraseña hasheada: {hashed}")
    
    # Verificación de contraseña
    is_verified = verify_text(password, hashed)
    print(f"Resultado de verificación: {is_verified}")
    
    # Ejemplo de creación de token
    user_data = {"sub": "username", "role": "admin"}
    token = create_access_token(user_data)
    print(f"Token JWT: {token}")
    
    # Verificación de token
    payload = verify_token(token)
    print(f"Payload del token: {payload}")