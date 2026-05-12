from fastapi import APIRouter, Path, Query, HTTPException, Depends, Request
from database import SessionLocal
import models
from pydantic import Field, BaseModel
from typing import Optional, Annotated
from starlette import status
from sqlalchemy.orm import Session
from models import Todos
from enum import Enum
from .auth import get_current_user, login_page
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse


todoapp = APIRouter()

class PriorityEnum(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"

class TodoRequest(BaseModel):
    id : Optional[int] = Field(description="incremental ID", default=None)
    title : str = Field(description="Title of Todo")
    description : str = Field(description="Description of Todo")
    priority : PriorityEnum= Field(description="Priority of Todo")
    complete : Optional[bool] = Field(description="Complete of Todo", default=False)
    
    model_config ={
        "json_schema_extra":{
            "example":{
                "title" : "Title of Todo",
                "description" : "Description of Todo",
                "priority" : "Priority of Todo",
                "complete" : False
            }
        }
    }
        


#database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
#user
user_dependency = Annotated[dict, Depends(get_current_user)]
db_dependency = Annotated[Session, Depends(get_db)]
templates = Jinja2Templates(directory="templates")


########Template

def redirect_to_login():
    response = RedirectResponse(url='/auth/login-page', status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key='access_token')
    return response

@todoapp.get('/todos/todo-page')
async def todo_list_page(request: Request, db: db_dependency):
    try:
        user =  get_current_user(request.cookies.get("access_token"))
        if user is None:
            return redirect_to_login()
        todos = db.query(Todos).filter(Todos.owner_id == user.get('id')).all()
        return templates.TemplateResponse('todo.html',{'request': request, 'todos':todos, 'user':user})
    except HTTPException as e:
        return redirect_to_login()
    
@todoapp.get('/todos/add-todo-page')
def add_todo_page(request: Request):
    
    if request.cookies.get("access_token") is None:
       return redirect_to_login()
    else:
        user =  get_current_user(request.cookies.get("access_token"))
        
    return templates.TemplateResponse('add-todo.html', {"request": request, 'user':user})

@todoapp.get('/todos/edit-todo-page/{todo_id}')
def edit_todo_page(request: Request, db: db_dependency, todo_id: int = Path(gt=0)):
    
    if request.cookies.get("access_token") is None:
        return redirect_to_login()
    else:
        user =  get_current_user(request.cookies.get("access_token"))
        
    todo = db.query(Todos).filter(Todos.id == todo_id).first()
    if not todo:
        return RedirectResponse(url="/todos/add-todo-page")
    
    return templates.TemplateResponse('edit-todo.html', {"request": request, "todo":todo, 'user':user})


#######End Template

#get all Todos
@todoapp.get('/todos', status_code= status.HTTP_200_OK)
def get_all_todos(authuser: user_dependency, db: Session = Depends(get_db)):
    if not authuser:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unathorized")
    
    todos = db.query(Todos).all()
    return todos

#create Todo
@todoapp.post('/create-todos', status_code=status.HTTP_201_CREATED)
async def create_todos(authuser: user_dependency, todos_body: TodoRequest, db: Session = Depends(get_db)):
    if not authuser:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unathorized")
    
    new_todo = Todos(
        title = todos_body.title.title(),
        description=todos_body.description.capitalize(),
        priority=todos_body.priority,
        complete=todos_body.complete,
        owner_id = authuser.get('id')
    )
    db.add(new_todo)
    db.commit()
    db.refresh(new_todo)
    return todos_body

#Single Todo
@todoapp.get('/todos/{todo_id}', status_code=status.HTTP_200_OK)
async def get_todo_by_id(todo_id: int = Path(gt=0), db: Session = Depends(get_db)):
    """This will return single Todo by Id"""
    
    todo = db.query(Todos).filter(Todos.id == todo_id).first()
    
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo


#Update Todo
@todoapp.put('/update-todo', status_code=status.HTTP_204_NO_CONTENT)
def update_todo(todo_content: TodoRequest, db: Session = Depends(get_db)):
    todo_id = todo_content.id
    if not todo_id:
        raise HTTPException(status_code=401, detail="Id is not found")
    todo = db.query(Todos).filter(Todos.id == todo_id).first()
    todo.title = todo_content.title.title()
    todo.description=todo_content.description.capitalize(),
    todo.priority=todo_content.priority.value,
    todo.complete=todo_content.complete
    
    db.commit()
    
    db.refresh(todo)
    return todo

#Delete Todo
@todoapp.delete('/delete-todo', status_code=status.HTTP_200_OK)
async def delete_todo_by_id(todo_id: int = Query(gt=0), db:Session = Depends(get_db)):
    todo = db.query(Todos).filter(Todos.id == todo_id).first()
    
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    db.delete(todo)
    db.commit()
    return {'message': "Todo deleted successfully"}