from fastapi import FastAPI, Depends, HTTPException, APIRouter
from pydantic import BaseModel, EmailStr
from forgot_password_utils import create_reset_token, send_reset_email, verify_reset_token

APIRouter = FastAPI()

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

@APIRouter.post("/request-password-reset")
async def request_password_reset(data: PasswordResetRequest):
    # Verify that the email exists in your database
    # email_exists = your_database_function(data.email)
    email_exists = True  # Placeholder, replace with actual check

    if not email_exists:
        raise HTTPException(status_code=404, detail="Email not found")

    token = create_reset_token(data.email)
    await send_reset_email(data.email, token)
    return {"msg": "Password reset email sent"}

@APIRouter.post("/reset-password")
async def reset_password(data: PasswordResetConfirm):
    email = verify_reset_token(data.token)
    # Update the user's password in your database
    # update_user_password(email, pwd_context.hash(data.new_password))
    return {"msg": "Password updated successfully"}