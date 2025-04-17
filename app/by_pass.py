from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from db import SessionDep, create_all_tables
from sqlmodel import select
from models import Item, User
from logs_setup import setup_api_logger
from routers import (
    object_router, process_router, stage_router, test_jobs, 
    ocr_routes, validate_csv, list_jobs, details, job_status, 
    object_current_stage, item_router, user_router, auth_router, 
    rest_password_router, products_router, issue_router, defect_record_router,
    correction_process_router, status_router
)
from generate_qr import generate_qr, generate_pdf

logger = setup_api_logger("main")
qr_path = generate_qr()
generate_pdf(qr_path)

app = FastAPI(lifespan=create_all_tables)
# Se ha eliminado el middleware de autenticación

# Rutas públicas
app.include_router(rest_password_router.router)
app.include_router(auth_router.router)

@app.get("/cis_apk",
        summary="Redirect to the latest APK file",
        response_description="Redirects to the URL of the latest APK file",
        tags=["Resources"], 
    )
async def redirect_to_apk(request: Request):
    """
    ## Endpoint to redirect to the latest APK file

    This endpoint redirects the user to the URL of the latest APK file hosted on the server.

    ### Workflow:
    1. Constructs the full URL of the APK file using the request's base URL.
    2. Redirects the user to the APK file's URL.
    """
    base_url = request.base_url
    return RedirectResponse(url=f"{base_url}apk/current_app.apk")

@app.get("/cis_qr_pdf",
        summary="Redirect to the QR PDF file",
        response_description="Redirects to the URL of the QR PDF file",
        tags=["Resources"],
    )
async def redirect_to_qr_pdf(request: Request):
    """
    ## Endpoint to redirect to the QR PDF file

    This endpoint redirects the user to the URL of the QR PDF file hosted on the server.

    ### Workflow:
    1. Constructs the full URL of the QR PDF file using the request's base URL.
    2. Redirects the user to the QR PDF file's URL.
    """
    base_url = request.base_url
    return RedirectResponse(url=f"{base_url}static/documents/qr.pdf")

@app.get("/login", response_class=HTMLResponse, name="login",
        summary="Display the login page",
        response_description="Renders the login page",
        tags=["Authentication"],
    )
async def login_page(request: Request):
    """
    ## Endpoint to display the login page

    This endpoint renders the login page using an HTML template.
    """
    return templates.TemplateResponse("login.html", {"request": request})

# Rutas protegidas (ahora sin protección)
@app.get("/item", 
        summary="Get a list of items",
        response_description="Returns a list of all items",
        tags=["Items"],
    )
def get_item(session: SessionDep):
    """
    ## Endpoint to get a list of items

    This endpoint returns a list of all items in the system.
    """
    return session.exec(select(Item)).all()

# Incluir routers que ya no necesitan autenticación
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
app.include_router(products_router.router)
app.include_router(issue_router.router)
app.include_router(defect_record_router.router)
app.include_router(correction_process_router.router)
app.include_router(status_router.router)

# Configuración de archivos estáticos
app.mount("/static", StaticFiles(directory="./static"), name="static")
app.mount("/apk", StaticFiles(directory="./apk"), name="apk")

# Configuración de templates
templates = Jinja2Templates(directory="templates")

# Endpoints de templates que ya no requieren autenticación
@app.get("/new_job", response_class=HTMLResponse,
        summary="Display the new job creation page",
        response_description="Renders the new job creation page",
        tags=["Templates"], 
    )
async def read_root(request: Request):
    """
    ## Endpoint to display the new job creation page

    This endpoint renders the `index.html` template, which is used for creating new jobs.
    """
    # Usuario ficticio para mantener la compatibilidad con las plantillas
    fake_user = {"username": "admin", "role": {"role_name": "Admin"}}
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "current_user": fake_user}
    )

@app.get("/QR", response_class=HTMLResponse,
        summary="Display the QR page",
        response_description="Renders the QR page",
        tags=["Templates"],
    )
async def qr_page(request: Request):
    """
    ## Endpoint to display the QR page

    This endpoint renders the `qr.html` template, which is used for displaying QR-related content.
    """
    # Usuario ficticio para mantener la compatibilidad con las plantillas
    fake_user = {"username": "admin", "role": {"role_name": "Admin"}}
    return templates.TemplateResponse(
        "qr.html", 
        {"request": request, "current_user": fake_user}
    )

@app.get("/home", response_class=HTMLResponse,
        summary="Display the home page",
        response_description="Renders the home page",
        tags=["Templates"],
    )
async def home(request: Request):
    """
    ## Endpoint to display the home page

    This endpoint renders the `home.html` template, which is the main landing page.
    """
    # Usuario ficticio para mantener la compatibilidad con las plantillas
    fake_user = {"username": "admin", "role": {"role_name": "Admin"}}
    return templates.TemplateResponse(
        "home.html", 
        {"request": request, "current_user": fake_user}
    )

@app.get("/info", response_class=HTMLResponse,
        summary="Display the info page",
        response_description="Renders the info page",
        tags=["Templates"],
    )
async def get_info(request: Request):
    """
    ## Endpoint to display the info page

    This endpoint renders the `info.html` template, which provides information.
    """
    # Usuario ficticio para mantener la compatibilidad con las plantillas
    fake_user = {"username": "admin", "role": {"role_name": "Admin"}}
    return templates.TemplateResponse(
        "info.html", 
        {"request": request, "current_user": fake_user}
    )

@app.get("/documentacion", response_class=HTMLResponse,
        summary="Display the documentation page",
        response_description="Renders the documentation page",
        tags=["Templates"],
    )
async def get_documentation(request: Request):
    """
    ## Endpoint to display the documentation page

    This endpoint renders the `documentation.html` template, which provides documentation.
    """
    # Usuario ficticio para mantener la compatibilidad con las plantillas
    fake_user = {"username": "admin", "role": {"role_name": "Admin"}}
    return templates.TemplateResponse(
        "documentation.html", 
        {"request": request, "current_user": fake_user}
    )

@app.get("/admin", response_class=HTMLResponse,
        summary="Display the admin dashboard",
        response_description="Renders the admin dashboard page",
        tags=["Admin"],
    )
async def admin(request: Request):  
    """
    ## Endpoint to display the admin dashboard

    This endpoint renders the `admin.html` template, which is the main dashboard for admin users.
    """
    # Usuario ficticio para mantener la compatibilidad con las plantillas
    fake_user = {"username": "admin", "role": {"role_name": "Admin"}}
    return templates.TemplateResponse(
            "admin.html", 
            {"request": request, "current_user": fake_user}
        )

@app.get("/admin/jobs", response_class=HTMLResponse,
        summary="Display the admin jobs page",
        response_description="Renders the admin jobs page",
        tags=["Admin"],
    )
async def admin_jobs(request: Request):
    """
    ## Endpoint to display the admin jobs page

    This endpoint renders the `admin_jobs.html` template, which is used for managing jobs by admin users.
    """
    # Usuario ficticio para mantener la compatibilidad con las plantillas
    fake_user = {"username": "admin", "role": {"role_name": "Admin"}}
    return templates.TemplateResponse(
        "admin_jobs.html", 
        {"request": request, "current_user": fake_user}
    )

@app.get("/admin/items", response_class=HTMLResponse,
        summary="Display the admin items page",
        response_description="Renders the admin items page",
        tags=["Admin"],
    )
async def admin_items(request: Request):
    """
    ## Endpoint to display the admin items page

    This endpoint renders the `admin_items.html` template, which is used for managing items by admin users.
    """
    # Usuario ficticio para mantener la compatibilidad con las plantillas
    fake_user = {"username": "admin", "role": {"role_name": "Admin"}}
    return templates.TemplateResponse(
        "admin_items.html", 
        {"request": request, "current_user": fake_user}
    )

@app.get("/admin/objects", response_class=HTMLResponse,
        summary="Display the admin objects page",
        response_description="Renders the admin objects page",
        tags=["Admin"],
    )
async def admin_objects(request: Request):
    """
    ## Endpoint to display the admin objects page

    This endpoint renders the `admin_objects.html` template, which is used for managing objects by admin users.
    """
    # Usuario ficticio para mantener la compatibilidad con las plantillas
    fake_user = {"username": "admin", "role": {"role_name": "Admin"}}
    return templates.TemplateResponse(
        "admin_objects.html", 
        {"request": request, "current_user": fake_user}
    )

@app.get("/admin/users_panel", response_class=HTMLResponse,
        summary="Display the admin users panel",
        response_description="Renders the admin users panel page",
        tags=["Admin"],
    )
async def admin_users_panel(request: Request):
    """
    ## Endpoint to display the admin users panel

    This endpoint renders the `admin_users.html` template, which is used for managing users by admin users.
    """
    # Usuario ficticio para mantener la compatibilidad con las plantillas
    fake_user = {"username": "admin", "role": {"role_name": "Admin"}}
    return templates.TemplateResponse(
        "admin_users.html", 
        {"request": request, "current_user": fake_user}
    )