from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from .utils import normalize_email
from .models import UserRole
import uuid
import datetime


class UserCreate(BaseModel):
    name: str
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


class UserResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    role: UserRole
    avatar_url: str | None

    model_config = ConfigDict(from_attributes=True)


class GoogleUser(BaseModel):
    google_sub: str
    email: str
    name: str

    class Config:
        from_attributes = True
