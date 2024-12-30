from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import select
from db import SessionDep, create_all_tables
from models import Item
from routers import (
    object_router, process_router, stage_router, test_jobs, ocr_routes,
    validate_csv, list_jobs, details, job_status, object_current_stage, item_router
)
from generate_qr import generate_qr, generate_pdf
from .auth import authenticate_user, get_current_active_user, User, TokenData

qr_path = generate_qr()
generate_pdf(qr_path)

app = FastAPI(lifespan=create_all_tables)

# Include routers
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

# Mount static and APK directories
app.mount("/static", StaticFiles(directory="./static"), name="static")
app.mount("/apk", StaticFiles(directory="./apk"), name="apk")

# Template configuration
templates = Jinja2Templates(directory="templates")


# Middleware to enforce login
@app.middleware("http")
async def enforce_login(request: Request, call_next):
    public_routes = ["/login", "/token", "/static", "/apk"]
    if not any(request.url.path.startswith(route) for route in public_routes):
        token = request.cookies.get("access_token")
        if not token:
            return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
        try:
            user = await get_current_active_user(token)
            request.state.user = user
        except HTTPException:
            return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    response = await call_next(request)
    return response


# Role-based access control
def require_role(required_roles: list[str]):
    async def role_checker(request: Request):
        user: User = request.state.user
        if user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource"
            )
    return role_checker


# Routes
@app.get("/new_job", response_class=HTMLResponse, dependencies=[Depends(require_role(["admin", "inge"]))])
async def new_job(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/admin", response_class=HTMLResponse, dependencies=[Depends(require_role(["admin"]))])
async def admin(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})


@app.get("/home", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/info", response_class=HTMLResponse)
async def get_info(request: Request):
    return templates.TemplateResponse("info.html", {"request": request})


@app.get("/documentacion", response_class=HTMLResponse)
async def get_documentation(request: Request):
    return templates.TemplateResponse("documentation.html", {"request": request})


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
