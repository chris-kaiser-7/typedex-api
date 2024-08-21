from pydantic import BaseModel, EmailStr
# from odmantic import ObjectId, Field, Model

class DB_User(BaseModel):
    username: str
    email: EmailStr
    hashed_password: str