from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Optional
from pydantic import BaseModel, EmailStr
from main import app
import os

class DB_User(BaseModel):
    username: str
    email: EmailStr
    hashed_password: str

class DB_UserInDB(DB_User):
    id: Optional[str] = None

class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: str

    class Config:
        orm_mode = True

router = APIRouter()

SECRET_KEY = os.getenv("AUTH_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/token")


async def get_user_by_username(username: str) -> DB_UserInDB:
    user = await app.user_collection.find_one({"username": username})
    if user:
        return DB_UserInDB(**user)

async def create_user_in_DB(user: DB_UserInDB) -> DB_UserInDB:
    user.hashed_password = pwd_context.hash(user.hashed_password)
    user_dict = user.model_dump()
    del user_dict["id"] #issue
    await app.user_collection.insert_one(user_dict)
    return user

async def authenticate_user(username: str, password: str):
    user = await get_user_by_username(username)
    if not user:
        return False
    if not pwd_context.verify(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub", "")
        if username == "":
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = await get_user_by_username(username)
    if user is None:
        raise credentials_exception
    return user

@router.post("/token", response_model=dict)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    print("testa")
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/users/", response_model=UserBase)
async def create_user(user: UserCreate):
    user_in_db = DB_UserInDB(username=user.username, email=user.email, hashed_password=user.password) #issue
    db_user = await get_user_by_username(username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    created_user = await create_user_in_DB(user=user_in_db)
    print('flag')
    print(type(created_user))
    print(created_user)
    return UserBase(username=created_user.username, email=created_user.email)

@router.get("/users/me/", response_model=UserBase)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user