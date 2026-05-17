from datetime import datetime, timezone
from urllib.parse import quote

from fastapi import BackgroundTasks

from src.auth.schemas import PasswordResetRequest
from src.config import settings
from src.templates import templates
from src.users.models import User

from .config import create_message, mail
from .utils import mail_utils


class MailService:
    def __init__(self, bg_task: BackgroundTasks) -> None:
        self.bg_task = bg_task

    async def send_on_signup(self, new_user: User):
        token = mail_utils.create_email_verification_token(
            data={"email": new_user.email}
        )
        safe_token = quote(token, safe="")
        verification_link = f"{settings.api_url}/auth/verify-user/{safe_token}"

        template = templates.template.get_template("welcome.html")
        html_content = template.render(
            {
                "username": new_user.name,
                "verification_link": verification_link,
                "year": datetime.now(timezone.utc).year,
            }
        )
        message = create_message(
            recipients=[new_user.email],
            subject="Welcome to Probey — verify your email",
            body=html_content,
        )
        self.bg_task.add_task(mail.send_message, message)

    async def send_password_reset(self, email: PasswordResetRequest):
        token = mail_utils.create_password_reset_token(data={"email": email.email})
        safe_token = quote(token, safe="")
        reset_link = f"{settings.api_url}/auth/reset-password/{safe_token}"

        template = templates.template.get_template("password_reset.html")

        html_content = template.render(
            {
                "link": reset_link,
            }
        )

        message = create_message(
            recipients=[email.email],
            subject="Reset Password - Probey",
            body=html_content,
        )

        self.bg_task.add_task(mail.send_message, message)

        return {"message": "A link to reset your password has been sent to your mail"}
