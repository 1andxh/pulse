from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pathlib import Path

from src.config import settings

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_FOLDER = Path(BASE_DIR, "templates")


mail_config = ConnectionConfig(
    MAIL_USERNAME=settings.mail_username,
    MAIL_PASSWORD=settings.mail_password,
    MAIL_PORT=settings.mail_port,
    MAIL_SERVER=settings.mail_server,
    MAIL_STARTTLS=settings.mail_starttls,
    MAIL_SSL_TLS=settings.mail_ssl_tls,
    MAIL_FROM=settings.mail_from,
    MAIL_FROM_NAME=settings.mail_from_name,
    USE_CREDENTIALS=settings.use_credentials,
    VALIDATE_CERTS=settings.validate_certs,
)

mail = FastMail(mail_config)


def create_message(recipients, subject: str, body: str) -> MessageSchema:
    message = MessageSchema(
        recipients=recipients, subject=subject, body=body, subtype=MessageType.html
    )
    return message
