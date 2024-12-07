from fastapi import FastAPI
from routers.ocr_routes import router as ocr_router
from routers.item_routes import router as item_router
from routers.job_routes import router as job_router
from routers.object_route import router as object_router
from db import SessionDep, create_all_tables
from db.init_db import init_db
from contextlib import asynccontextmanager
from models import Item, Job
from sqlmodel import select
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import HTTPException
from routers.test_route import  router as test_router
from routers.test_jobs import router as test_jobs

#@asynccontextmanager
def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=create_all_tables)


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

app.include_router(item_router)
app.include_router(ocr_router)
app.include_router(job_router)
app.include_router(test_router)
app.include_router(test_jobs)
app.include_router(object_router)