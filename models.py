from database import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo('Asia/Kolkata')

class Users(Base):
    __tablename__ = "users_api"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True)
    username = Column(String(255), unique=True)
    first_name = Column(String(45))
    last_name = Column(String(45))
    hashsed_password = Column(String(255))
    is_active = Column(Boolean, default=True)
    role = Column(String(45))
    created_date = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(IST)
    )
    updated_date = Column(
        DateTime(timezone=True),
        onupdate= lambda: datetime.now(IST)
    )
    

class Todos(Base):
    
    __tablename__ = 'todos'
    
    id = Column(Integer,primary_key=True,index=True)
    title = Column(String(150))
    description = Column(String(255))
    priority = Column(String(50))
    complete = Column(Boolean, default=False)
    owner_id = Column(Integer,ForeignKey("users_api.id"))
    
    #timestamp
    created_date = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(IST)
    )
    updated_date = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(IST),
        onupdate= lambda: datetime.now(IST)
    )