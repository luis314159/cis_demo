from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
from auth import verify_token, get_token
import jwt
from auth import SECRET_KEY, ALGORITHM

async def check_admin_access(request: Request, allowed_roles):
    token = get_token(request)
    if not token:
        return False
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_role = payload.get("role")
        return user_role in allowed_roles
    except jwt.JWTError:
        return False

# async def auth_middleware(request: Request, call_next):
#     # Rutas que no requieren autenticación
#     public_paths = {"/login", "/token", "/authenticate", "/static", "/apk", 
#                    "/cis_apk", "/cis_qr_pdf", "/rest-password"}
    
#     allowed_roles = ["admin", "ingeniero", "supervisor"]

#     path = request.url.path
    
#     # Verifica si la ruta actual es pública
#     if any(path.startswith(public_path) for public_path in public_paths):
#         return await call_next(request)
    
#     # Obtiene y verifica el token
#     token = get_token(request)
#     if not token or not verify_token(token):
#         return RedirectResponse(url="/login", status_code=303)
    
#     # Verifica los permisos de admin si la ruta comienza con /admin
#     if path.startswith("/admin"):
#         is_allowed = await check_admin_access(request, allowed_roles)
#         if not is_allowed:
#             if "html" in request.headers.get("accept", ""):
#                 return RedirectResponse(url="/home", status_code=303)
#             raise HTTPException(status_code=403, detail="No tienes permisos suficientes")
    
#     return await call_next(request)

allowed_roles = ["admin", "ingeniero", "supervisor"]

async def auth_middleware(request: Request, call_next):
    #return await call_next(request)
    # Rutas que no requieren autenticación
    public_paths = {"/login", "/token", "/authenticate", "/static", "/apk", 
                   "/cis_apk", "/cis_qr_pdf", "/rest-password"}
    
    path = request.url.path
    
    # Verifica si la ruta actual es pública
    if any(path.startswith(public_path) for public_path in public_paths):
        return await call_next(request)
    
    # Obtiene el token
    token = get_token(request)
    if not token:
        return RedirectResponse(url="/login", status_code=303)
    
    # Verifica el token y obtiene el payload
    payload = verify_token(token)
    if not payload:
        return RedirectResponse(url="/login", status_code=303)
    
    # Verifica los permisos de admin si la ruta comienza con /admin
    if path.startswith("/admin"):
        user_role = payload.get("role")
        if not user_role or user_role not in allowed_roles:
            if "html" in request.headers.get("accept", ""):
                return RedirectResponse(url="/home", status_code=303)
            raise HTTPException(
                status_code=403, 
                detail="No tienes permisos suficientes para acceder a esta sección"
            )
    
    return await call_next(request)