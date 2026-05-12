from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional, Annotated
from models import Users
from database import SessionLocal
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from starlette import status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from datetime import timedelta, datetime
from zoneinfo import ZoneInfo
from fastapi.templating import Jinja2Templates


router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

templates = Jinja2Templates(directory= "templates")

SECRET_KEY="ab3120f7a9d26fa79c744825caa61cd112a198e9e83eae9abbe269d75071bb5d"
ALGORITHM= "HS256"
IST = ZoneInfo('Asia/Kolkata')

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated="auto")

OAuth_brearer = OAuth2PasswordBearer(tokenUrl='/auth/token')

class UsersRequest(BaseModel):
    id: Optional[int] = Field(description="In id optional , auto incremental", default=None)
    email: str = Field(description="Enter user email id")
    username: str = Field(description="Enter username", min_length=3, max_length=20)
    first_name: str = Field(description="Enter user first name", min_length=3)
    last_name: str = Field(description="Enter user last name", min_length=3)
    password: str = Field(description="Enter user password", min_length=3)
    # is_active: Optional[bool] = Field(description="set active", default=True)
    role: str = Field(description="Enter role of user")
    

    model_config={
        "json_schema_extra":{
            "example":{
                "id": "In id optional , auto incremental",
                "email": "Enter user email id",
                'username': "Enter username",
                'first_name': "Enter user first name",
                "last_name": "Enter user last name",
                "password": "Enter user password",
                "role": "Enter role of user"
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
        
database_dependancy = Annotated[Session, Depends(get_db)]

############Template

@router.get('/login-page', include_in_schema=False)
def login_page(request: Request):
    return templates.TemplateResponse('login.html', {"request": request})

@router.get('/register-page', include_in_schema=False)
def login_page(request: Request):
    return templates.TemplateResponse('register.html', {"request": request})


############End Template

#create new user
@router.post('/create-user', status_code=status.HTTP_201_CREATED)
def create_user(user_request: UsersRequest, db: database_dependancy):
    check_user = db.query(Users).filter(
        (Users.email == user_request.email) |
        (Users.username == user_request.username)
    ).first()
    
    if check_user:
        raise HTTPException(status_code=401, detail="Email or Username already exist")
    
    create_user_model = Users(
        email=user_request.email,
        username=user_request.username,
        first_name=user_request.first_name.capitalize(),
        last_name=user_request.last_name.capitalize(),
        role=user_request.role,
        hashsed_password= bcrypt_context.hash(user_request.password),
        is_active=True
    )

    db.add(create_user_model)
    db.commit()
    return {'message': "user created"}
    
#get all users
@router.get('/users', status_code=status.HTTP_200_OK)
async def get_users(db: database_dependancy):
    users = db.query(Users).all()
    
    return users

#token
@router.post('/token')
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db:database_dependancy):
    users = db.query(Users).filter(
        (Users.username == form_data.username) 
    ).first()
    
    if not users:
        raise HTTPException(status_code=401, detail="Failled authenticated")
    if not bcrypt_context.verify(form_data.password, users.hashsed_password):
        raise HTTPException(status_code=401, detail="Failled authenticated")
    token = create_access_token(users.username, users.id, users.role, timedelta(minutes=20))
    return {'access_token': token, 'token_type': 'bearer'}
    
def create_access_token(username: str, user_id: int, role: str, expire_time: timedelta):
    
    encode = {'sub': username, 'id': user_id, 'role': role}
    expires = datetime.now(IST) + expire_time
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: Annotated[str, Depends(OAuth_brearer)]):
    # return 1
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        user_role: int = payload.get("role")

        if username is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate user"
            )
        return {"username": username, "id": user_id, "role": user_role}

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )