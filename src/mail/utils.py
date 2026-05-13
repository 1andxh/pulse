from fastapi import HTTPException, status
from src.config import settings
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
import logging
from typing import Any


class MailUtils:
    def __init__(self) -> None:
        self.email_serializer = URLSafeTimedSerializer(
            secret_key=settings.email_secret, salt="email-verification"
        )
        self.password_reset_serializer = URLSafeTimedSerializer(
            secret_key=settings.password_reset_secret, salt="password-reset"
        )

    def create_email_verification_token(self, data: dict):
        return self.email_serializer.dumps(data)

    def create_password_reset_token(self, data: dict):
        return self.password_reset_serializer.dumps(data)

    @staticmethod
    def decode_url_safe_token(
        token: str, serializer: URLSafeTimedSerializer, max_age: int = 3600
    ) -> dict[str, Any]:
        try:
            token_data = serializer.loads(token, max_age=max_age)
            return token_data
        except SignatureExpired:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired"
            )
        except BadSignature as e:
            logging.error(str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not verify token",
            )


mail_utils = MailUtils()
