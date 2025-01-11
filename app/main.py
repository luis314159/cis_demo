from fastapi import FastAPI
from db import SessionDep, create_all_tables
from sqlmodel import select
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from models import Item
from routers import object_router, process_router, stage_router, test_jobs, ocr_routes, validate_csv, list_jobs, details, job_status, object_current_stage, item_router, user_router, auth_router, rest_password_router
from generate_qr import generate_qr, generate_pdf

qr_path = generate_qr()
generate_pdf(qr_path)

#from routers import add_stage

app = FastAPI(lifespan=create_all_tables)

# Not needed for token
app.include_router(rest_password_router.router)
app.include_router(auth_router.router)

@app.get("/cis_apk")
async def redirect_to_apk(request: Request):
    # Generar la URL base dinámicamente
    base_url = request.base_url
    return RedirectResponse(url=f"{base_url}apk/current_app.apk")


@app.get("/cis_qr_pdf")
async def redirect_to_qr_pdf(request: Request):
    # Generar la URL base dinámicamente
    base_url = request.base_url
    return RedirectResponse(url=f"{base_url}static/documents/qr.pdf")


@app.get("/item", response_model=list[Item])
def get_item(session: SessionDep):
    return session.exec(select(Item)).all()

#Token needed
app.include_router(test_jobs.router)
app.include_router(ocr_routes.router)
app.include_router(validate_csv.router)
app.include_router(list_jobs.router)
app.include_router(object_router.router)
app.include_router(details.router)
app.include_router(details.router)
app.include_router(process_router.router)
app.include_router(stage_router.router)
app.include_router(job_status.router)
app.include_router(object_current_stage.router)
app.include_router(item_router.router)
app.include_router(user_router.router)



# Show files
app.mount("/static", StaticFiles(directory="./static"), name="static")
app.mount("/apk", StaticFiles(directory="./apk"), name="apk")

# Template configuration
templates = Jinja2Templates(directory="templates")


# tamaplates

# No token needed

@app.get("/login", response_class=HTMLResponse, name="login")
async def admin(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

#token needed

# Render new job
@app.get("/new_job", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


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
async def admin_iobjects(request: Request):
    return templates.TemplateResponse("admin_objects.html", {"request": request})