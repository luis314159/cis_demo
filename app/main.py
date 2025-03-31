from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Annotated
from db import SessionDep, create_all_tables
from sqlmodel import select
from models import Item, User
from auth import get_current_active_user
from logs_setup import setup_api_logger
from routers import (
    object_router, process_router, stage_router, test_jobs, 
    ocr_routes, validate_csv, list_jobs, details, job_status, 
    object_current_stage, item_router, user_router, auth_router, 
    rest_password_router, products_router
)
from generate_qr import generate_qr, generate_pdf
from middleware import auth_middleware

logger = setup_api_logger("main")
qr_path = generate_qr()
generate_pdf(qr_path)

app = FastAPI(lifespan=create_all_tables)
app.middleware("http")(auth_middleware)

# Rutas públicas (no necesitan token)
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

    ### Example Usage:
    ```http
    GET /cis_apk

    Response:
    - Redirects to `{base_url}/apk/current_app.apk`
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

    ### Example Usage:
    ```http
    GET /cis_qr_pdf

    Response:
    - Redirects to `{base_url}/static/documents/qr.pdf`
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

    ### Workflow:
    1. Renders the `login.html` template.
    2. Returns the rendered HTML as the response.

    ### Example Usage:
    ```http
    GET /login

    Response:
    - Renders the `login.html` template.
    """
    return templates.TemplateResponse("login.html", {"request": request})

# Rutas protegidas (necesitan token)
@app.get("/item", response_model=list[Item],
        summary="Get a list of items",
        response_description="Returns a list of all items",
        tags=["Items"],  # Agrupa este endpoint en la sección "Items"
        responses={
            200: {"description": "Successfully returned the list of items"},
            401: {"description": "Invalid or missing token"},
            403: {"description": "User does not have the required permissions"},
        },
    )
def get_item(
    session: SessionDep,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    ## Endpoint to get a list of items (Protected)

    This endpoint returns a list of all items in the system. It requires a valid JWT token for authentication.

    ### Arguments:
    - **session** (Session): Database session to query item information.
    - **current_user** (User): The authenticated user (obtained from the JWT token).

    ### Returns:
    - **List[Item]**: A list of all items in the system.

    ### Raises:
    - `HTTPException`:
        - `401`: If no valid token is provided.
        - `403`: If the user does not have the required permissions.

    ### Example Usage:
    ```http
    GET /item
    Headers:
        Authorization: Bearer eyJhbGciOiJIUzI1NiIs...

    Response:
    [
        {
            "item_id": 1,
            "name": "Item 1",
            "description": "Description of Item 1"
        },
        {
            "item_id": 2,
            "name": "Item 2",
            "description": "Description of Item 2"
        },
        ...
    ]
    """
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
app.include_router(products_router.router)

# Configuración de archivos estáticos
app.mount("/static", StaticFiles(directory="./static"), name="static")
app.mount("/apk", StaticFiles(directory="./apk"), name="apk")

# Configuración de templates
templates = Jinja2Templates(directory="templates")

# Endpoints de templates que requieren autenticación
@app.get("/new_job", response_class=HTMLResponse,
        summary="Display the new job creation page",
        response_description="Renders the new job creation page",
        tags=["Templates"], 
    )
async def read_root(
    request: Request,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    ## Endpoint to display the new job creation page

    This endpoint renders the `index.html` template, which is used for creating new jobs.
    It requires authentication.

    ### Workflow:
    1. Verifies the user's authentication token.
    2. Renders the `index.html` template with the current user's data.
    3. Returns the rendered HTML as the response.

    ### Example Usage:
    ```http
    GET /new_job
    Headers:
        Authorization: Bearer eyJhbGciOiJIUzI1NiIs...

    Response:
    - Renders the `index.html` template.
    """
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "current_user": current_user}
    )

@app.get("/QR", response_class=HTMLResponse,
        summary="Display the QR page",
        response_description="Renders the QR page",
        tags=["Templates"],
    )
async def qr_page(
    request: Request,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    ## Endpoint to display the QR page

    This endpoint renders the `qr.html` template, which is used for displaying QR-related content.
    It requires authentication.

    ### Workflow:
    1. Verifies the user's authentication token.
    2. Renders the `qr.html` template with the current user's data.
    3. Returns the rendered HTML as the response.

    ### Example Usage:
    ```http
    GET /QR
    Headers:
        Authorization: Bearer eyJhbGciOiJIUzI1NiIs...

    Response:
    - Renders the `qr.html` template.
    """
    return templates.TemplateResponse(
        "qr.html", 
        {"request": request, "current_user": current_user}
    )

@app.get("/home", response_class=HTMLResponse,
        summary="Display the home page",
        response_description="Renders the home page",
        tags=["Templates"],
    )
async def home(
    request: Request,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    ## Endpoint to display the home page

    This endpoint renders the `home.html` template, which is the main landing page for authenticated users.
    It requires authentication.

    ### Workflow:
    1. Verifies the user's authentication token.
    2. Renders the `home.html` template with the current user's data.
    3. Returns the rendered HTML as the response.

    ### Example Usage:
    ```http
    GET /home
    Headers:
        Authorization: Bearer eyJhbGciOiJIUzI1NiIs...

    Response:
    - Renders the `home.html` template.
    """
    return templates.TemplateResponse(
        "home.html", 
        {"request": request, "current_user": current_user}
    )

@app.get("/info", response_class=HTMLResponse,
        summary="Display the info page",
        response_description="Renders the info page",
        tags=["Templates"],
    )
async def get_info(
    request: Request,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    ## Endpoint to display the info page

    This endpoint renders the `info.html` template, which provides information to authenticated users.
    It requires authentication.

    ### Workflow:
    1. Verifies the user's authentication token.
    2. Renders the `info.html` template with the current user's data.
    3. Returns the rendered HTML as the response.

    ### Example Usage:
    ```http
    GET /info
    Headers:
        Authorization: Bearer eyJhbGciOiJIUzI1NiIs...

    Response:
    - Renders the `info.html` template.
    """
    return templates.TemplateResponse(
        "info.html", 
        {"request": request, "current_user": current_user}
    )

@app.get("/documentacion", response_class=HTMLResponse,
        summary="Display the documentation page",
        response_description="Renders the documentation page",
        tags=["Templates"],
    )
async def get_documentation(
    request: Request,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    ## Endpoint to display the documentation page

    This endpoint renders the `documentation.html` template, which provides documentation to authenticated users.
    It requires authentication.

    ### Workflow:
    1. Verifies the user's authentication token.
    2. Renders the `documentation.html` template with the current user's data.
    3. Returns the rendered HTML as the response.

    ### Example Usage:
    ```http
    GET /documentacion
    Headers:
        Authorization: Bearer eyJhbGciOiJIUzI1NiIs...

    Response:
    - Renders the `documentation.html` template.
    """
    return templates.TemplateResponse(
        "documentation.html", 
        {"request": request, "current_user": current_user}
    )

@app.get("/admin", response_class=HTMLResponse,
        summary="Display the admin dashboard",
        response_description="Renders the admin dashboard page",
        tags=["Admin"],
    )
async def admin(
    request: Request,
    current_user: Annotated[User, Depends(get_current_active_user)]
):  
    """
    ## Endpoint to display the admin dashboard

    This endpoint renders the `admin.html` template, which is the main dashboard for admin users.
    It requires authentication and admin privileges.

    ### Workflow:
    1. Verifies the user's authentication token and admin role.
    2. Renders the `admin.html` template with the current user's data.
    3. Returns the rendered HTML as the response.

    ### Example Usage:
    ```http
    GET /admin
    Headers:
        Authorization: Bearer eyJhbGciOiJIUzI1NiIs...

    Response:
    - Renders the `admin.html` template.
    """
    return templates.TemplateResponse(
            "admin.html", 
            {"request": request, "current_user": current_user}
        )

@app.get("/admin/jobs", response_class=HTMLResponse,
        summary="Display the admin jobs page",
        response_description="Renders the admin jobs page",
        tags=["Admin"],
    )
async def admin_jobs(
    request: Request,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    ## Endpoint to display the admin jobs page

    This endpoint renders the `admin_jobs.html` template, which is used for managing jobs by admin users.
    It requires authentication and admin privileges.

    ### Workflow:
    1. Verifies the user's authentication token and admin role.
    2. Renders the `admin_jobs.html` template with the current user's data.
    3. Returns the rendered HTML as the response.

    ### Example Usage:
    ```http
    GET /admin/jobs
    Headers:
        Authorization: Bearer eyJhbGciOiJIUzI1NiIs...

    Response:
    - Renders the `admin_jobs.html` template.
    """
    return templates.TemplateResponse(
        "admin_jobs.html", 
        {"request": request, "current_user": current_user}
    )

@app.get("/admin/items", response_class=HTMLResponse,
        summary="Display the admin items page",
        response_description="Renders the admin items page",
        tags=["Admin"],
    )
async def admin_items(
    request: Request,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    ## Endpoint to display the admin items page

    This endpoint renders the `admin_items.html` template, which is used for managing items by admin users.
    It requires authentication and admin privileges.

    ### Workflow:
    1. Verifies the user's authentication token and admin role.
    2. Renders the `admin_items.html` template with the current user's data.
    3. Returns the rendered HTML as the response.

    ### Example Usage:
    ```http
    GET /admin/items
    Headers:
        Authorization: Bearer eyJhbGciOiJIUzI1NiIs...

    Response:
    - Renders the `admin_items.html` template.
    """
    return templates.TemplateResponse(
        "admin_items.html", 
        {"request": request, "current_user": current_user}
    )

@app.get("/admin/objects", response_class=HTMLResponse,
        summary="Display the admin objects page",
        response_description="Renders the admin objects page",
        tags=["Admin"],
    )
async def admin_objects(
    request: Request,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    ## Endpoint to display the admin objects page

    This endpoint renders the `admin_objects.html` template, which is used for managing objects by admin users.
    It requires authentication and admin privileges.

    ### Workflow:
    1. Verifies the user's authentication token and admin role.
    2. Renders the `admin_objects.html` template with the current user's data.
    3. Returns the rendered HTML as the response.

    ### Example Usage:
    ```http
    GET /admin/objects
    Headers:
        Authorization: Bearer eyJhbGciOiJIUzI1NiIs...

    Response:
    - Renders the `admin_objects.html` template.
    """
    return templates.TemplateResponse(
        "admin_objects.html", 
        {"request": request, "current_user": current_user}
    )

@app.get("/admin/users_panel", response_class=HTMLResponse,
        summary="Display the admin users panel",
        response_description="Renders the admin users panel page",
        tags=["Admin"],
    )
async def admin_objects(
    request: Request,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """
    ## Endpoint to display the admin users panel

    This endpoint renders the `admin_users.html` template, which is used for managing users by admin users.
    It requires authentication and admin privileges.

    ### Workflow:
    1. Verifies the user's authentication token and admin role.
    2. Renders the `admin_users.html` template with the current user's data.
    3. Returns the rendered HTML as the response.

    ### Example Usage:
    ```http
    GET /admin/users_panel
    Headers:
        Authorization: Bearer eyJhbGciOiJIUzI1NiIs...

    Response:
    - Renders the `admin_users.html` template.
    """
    return templates.TemplateResponse(
        "admin_users.html", 
        {"request": request, "current_user": current_user}
    )
