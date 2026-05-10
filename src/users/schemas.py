from pydantic import BaseModel, EmailStr, Field, field_validator
from .utils import normalize_email


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=255)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_user_email(cls, v):
        return normalize_email(v)


class UserLogin(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email", mode="before")
    @classmethod
    def normalize_user_email(cls, v):
        return normalize_email(v)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
