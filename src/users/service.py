from fastapi import status, HTTPException
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .utils import (
    ACCESS_TOKEN_EXPIRY,
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)
