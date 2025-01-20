from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
from auth import get_token
import jwt
from auth import SECRET_KEY, ALGORITHM

allowed_roles = ["admin", "ingeniero", "supervisor"]


async def role_middleware(request: Request, call_next):
    path = request.url.path
    
    # Solo verificar roles para rutas admin
    if not path.startswith("/admin"):
        return await call_next(request)
    
    token = get_token(request)
    if not token:
        return RedirectResponse(url="/login", status_code=303)
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_role = payload.get("role")
        
        if user_role not in allowed_roles:
            if "html" in request.headers.get("accept", ""):
                return RedirectResponse(url="/home", status_code=303)
            raise HTTPException(status_code=403, detail="No tienes permisos suficientes")
            
    except jwt.JWTError:
        return RedirectResponse(url="/login", status_code=303)
    
    return await call_next(request)