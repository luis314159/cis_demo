from fastapi import FastAPI
from db import SessionDep, create_all_tables
from sqlmodel import select
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from models import Item
from routers import object_router, process_router, stage_router, test_jobs, ocr_routes, validate_csv, list_jobs, details, job_status, object_current_stage, item_router
#from routers import add_stage

app = FastAPI(lifespan=create_all_tables)
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


# Show static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Template configuration
templates = Jinja2Templates(directory="templates")

# Render main
@app.get("/new_job", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/admin_login", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/item", response_model=list[Item])
def get_item(session: SessionDep):
    return session.exec(select(Item)).all()
