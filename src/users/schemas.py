import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from .models import UserRole
from .utils import normalize_email


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
    name: str | None = None
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
