from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.openapi.utils import get_openapi
from db import SessionDep, create_all_tables
from sqlmodel import select
from models import Item
from routers import (
    object_router, process_router, stage_router, test_jobs, 
    ocr_routes, validate_csv, list_jobs, details, job_status, 
    object_current_stage, item_router, user_router, auth_router
)
from generate_qr import generate_qr, generate_pdf

# Generar QR y PDF
qr_path = generate_qr()
generate_pdf(qr_path)

# Configuración de la aplicación
app = FastAPI(
    title="Tu API",
    description="Descripción de tu API",
    version="1.0.0",
    lifespan=create_all_tables
)

# Configuración de seguridad para Swagger UI
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Tu API",
        version="1.0.0",
        description="Descripción de tu API",
        routes=app.routes,
    )
    
    # Añadir componente de seguridad
    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2PasswordBearer": {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": "token",
                    "scopes": {}
                }
            }
        }
    }
    
    # Aplicar seguridad globalmente
    openapi_schema["security"] = [
        {
            "OAuth2PasswordBearer": []
        }
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Incluir routers
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
app.include_router(auth_router.router)

# Archivos estáticos
app.mount("/static", StaticFiles(directory="./static"), name="static")
app.mount("/apk", StaticFiles(directory="./apk"), name="apk")

# Configuración de templates
templates = Jinja2Templates(directory="templates")

# Rutas HTML
@app.get("/new_job", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse, name="login")
async def admin(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/QR", response_class=HTMLResponse)
async def qr_page(request: Request):
    return templates.TemplateResponse("qr.html", {"request": request})

@app.get("/home", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/info", response_class=HTMLResponse)
async def get_info(request: Request):
    return templates.TemplateResponse("info.html", {"request": request})

@app.get("/documentacion", response_class=HTMLResponse)
async def get_documentation(request: Request):
    return templates.TemplateResponse("documentation.html", {"request": request})

@app.get("/admin", response_class=HTMLResponse)
async def admin(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})

@app.get("/admin/jobs", response_class=HTMLResponse)
async def admin_jobs(request: Request):
    return templates.TemplateResponse("admin_jobs.html", {"request": request})

@app.get("/admin/items", response_class=HTMLResponse)
async def admin_items(request: Request):
    return templates.TemplateResponse("admin_items.html", {"request": request})

@app.get("/admin/objects", response_class=HTMLResponse)
async def admin_objects(request: Request):
    return templates.TemplateResponse("admin_objects.html", {"request": request})

@app.get("/cis_apk")
async def redirect_to_apk(request: Request):
    base_url = request.base_url
    return RedirectResponse(url=f"{base_url}apk/current_app.apk")

@app.get("/cis_qr_pdf")
async def redirect_to_qr_pdf(request: Request):
    base_url = request.base_url
    return RedirectResponse(url=f"{base_url}static/documents/qr.pdf")

@app.get("/item", response_model=list[Item])
def get_item(session: SessionDep):
    return session.exec(select(Item)).all()