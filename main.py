from fastapi import FastAPI, Request
from database import engine
import models
from routers import auth, todos, admin
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from routers.auth import get_current_user

app = FastAPI(version="1.0.1")
# app.mount('/v1', "")

app.include_router(auth.router)
app.include_router(todos.todoapp)
app.include_router(admin.router)

# models.Base.metadata.drop_all(bind=engine)
models.Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="./templates")
app.mount("/static", StaticFiles(directory="./static"), name="static")

@app.get('/home')
@app.get('/')
def home(request: Request):
    if request.cookies.get("access_token"):
        user =  get_current_user(request.cookies.get("access_token"))
    else:
        user = None
        
    return templates.TemplateResponse('home.html', {"request": request, "developer": "Ravi Prakash Pandey", "user":user})