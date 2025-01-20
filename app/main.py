from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Annotated
from db import SessionDep, create_all_tables
from sqlmodel import select
from models import Item, User
from auth import get_current_active_user, SECRET_KEY, ALGORITHM
from logs_setup import setup_api_logger
from routers import (
    object_router, process_router, stage_router, test_jobs, 
    ocr_routes, validate_csv, list_jobs, details, job_status, 
    object_current_stage, item_router, user_router, auth_router, 
    rest_password_router
)
import jwt
from generate_qr import generate_qr, generate_pdf
from jwt.exceptions import InvalidTokenError
from middleware import auth_middleware

logger = setup_api_logger("main")
qr_path = generate_qr()
generate_pdf(qr_path)

app = FastAPI(lifespan=create_all_tables)
app.middleware("http")(auth_middleware)

# Rutas públicas (no necesitan token)
app.include_router(rest_password_router.router)
app.include_router(auth_router.router)

@app.get("/cis_apk")
async def redirect_to_apk(request: Request):
    base_url = request.base_url
    return RedirectResponse(url=f"{base_url}apk/current_app.apk")

@app.get("/cis_qr_pdf")
async def redirect_to_qr_pdf(request: Request):
    base_url = request.base_url
    return RedirectResponse(url=f"{base_url}static/documents/qr.pdf")

@app.get("/login", response_class=HTMLResponse, name="login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# Rutas protegidas (necesitan token)
@app.get("/item", response_model=list[Item])
def get_item(
    session: SessionDep,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    return session.exec(select(Item)).all()

# Incluir routers que necesitan autenticación
app.include_router(test_jobs.router)
app.include_router(ocr_routes.router)
app.include_router(validate_csv.router)
app.include_router(list_jobs.router)
app.include_router(object_router.router)
app.include_router(details.router)
app.include_router(process_router.router)
app.include_router(stage_router.router)
app.include_router(job_status.router)
app.include_router(object_current_stage.router)
app.include_router(item_router.router)
app.include_router(user_router.router)

# Configuración de archivos estáticos
app.mount("/static", StaticFiles(directory="./static"), name="static")
app.mount("/apk", StaticFiles(directory="./apk"), name="apk")

# Configuración de templates
templates = Jinja2Templates(directory="templates")

# Endpoints de templates que requieren autenticación
@app.get("/new_job", response_class=HTMLResponse)
async def read_root(
    request: Request,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "current_user": current_user}
    )

@app.get("/QR", response_class=HTMLResponse)
async def qr_page(
    request: Request,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    return templates.TemplateResponse(
        "qr.html", 
        {"request": request, "current_user": current_user}
    )

@app.get("/home", response_class=HTMLResponse)
async def home(
    request: Request,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    return templates.TemplateResponse(
        "home.html", 
        {"request": request, "current_user": current_user}
    )

@app.get("/info", response_class=HTMLResponse)
async def get_info(
    request: Request,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    return templates.TemplateResponse(
        "info.html", 
        {"request": request, "current_user": current_user}
    )

@app.get("/documentacion", response_class=HTMLResponse)
async def get_documentation(
    request: Request,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    return templates.TemplateResponse(
        "documentation.html", 
        {"request": request, "current_user": current_user}
    )

@app.get("/admin", response_class=HTMLResponse)
async def admin(
    request: Request,
    current_user: Annotated[User, Depends(get_current_active_user)]
):  
    return templates.TemplateResponse(
            "admin.html", 
            {"request": request, "current_user": current_user}
        )

@app.get("/admin/jobs", response_class=HTMLResponse)
async def admin_jobs(
    request: Request,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    return templates.TemplateResponse(
        "admin_jobs.html", 
        {"request": request, "current_user": current_user}
    )

@app.get("/admin/items", response_class=HTMLResponse)
async def admin_items(
    request: Request,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    return templates.TemplateResponse(
        "admin_items.html", 
        {"request": request, "current_user": current_user}
    )

@app.get("/admin/objects", response_class=HTMLResponse)
async def admin_objects(
    request: Request,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    return templates.TemplateResponse(
        "admin_objects.html", 
        {"request": request, "current_user": current_user}
    )

@app.get("/admin/users_panel", response_class=HTMLResponse)
async def admin_objects(
    request: Request,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    return templates.TemplateResponse(
        "admin_users.html", 
        {"request": request, "current_user": current_user}
    )




# # Middleware para redirigir a login si no hay autenticación
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi import HTTPException, status

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
# open_paths = [
#     "/login",
#     "/token",
#     "/static",
#     "/apk",
#     "/cis_apk",
#     "/cis_qr_pdf",
#     "/authenticate",
#     "/docs",
#     "/openapi.json",
#     "/redoc",
#     "/token"
# ]

# @app.middleware("http")
# async def auth_middleware(request: Request, call_next):
#     # Skip auth for open paths
#     if (request.url.path in open_paths or
#         request.url.path.startswith(tuple(open_paths))):
#         return await call_next(request)
    
#     token = None
#     auth_header = request.headers.get("Authorization")
#     auth_cookie = request.cookies.get("auth_token")
    
#     if auth_header and auth_header.startswith("Bearer "):
#         token = auth_header.split(" ")[1]
#     elif auth_cookie:
#         token = auth_cookie
    
#     if not token:
#         return handle_unauthorized(request)
    
#     try:
#         decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         # Si llegamos aquí, el token es válido
#         print("Token válido para usuario:", decoded.get("sub"))
#         # Continuar con la request
#         response = await call_next(request)
#         return response
        
#     except Exception as e:
#         print("Error en token:", str(e))
#         return handle_unauthorized(request)

# def handle_unauthorized(request: Request):
#     # Para peticiones web (HTML)
#     if "html" in request.headers.get("accept", ""):
#         return RedirectResponse("/login", status_code=303)
#     # Para peticiones API
#     raise HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Token inválido o expirado"
#     )