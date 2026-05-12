from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from .utils import normalize_email
import uuid
import datetime


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


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    is_verified: bool
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class GoogleUser(BaseModel):
    google_sub: str
    email: str
    full_name: str

    class Config:
        from_attributes = True
