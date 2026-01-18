from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class LoginRequest(BaseModel):
    loginType: str
    login_value: str
    authType: str
    auth_value: str

class RegisterRequest(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: str
    education: str
    email: EmailStr
    phone_number: str
    username: str
    password: str
    confirm_password: str

class UserResponse(BaseModel):
    id: str
    username: str
    name: str

class AuthCheckResponse(BaseModel):
    status: str
    authenticated: bool
    user: Optional[UserResponse] = None
