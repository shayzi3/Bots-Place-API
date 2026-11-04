from email.message import EmailMessage

import aiosmtplib

from bots_place.config.env import SmtpSettings


class SmtpEmailSender:
    def __init__(self, settings: SmtpSettings) -> None:
        self._settings = settings

    async def send_code(self, email: str, code: str) -> None:
        settings = self._settings
        if not settings.host:
            raise RuntimeError("SMTP_HOST is not configured")

        message = EmailMessage()
        message["From"] = settings.from_email
        message["To"] = email
        message["Subject"] = "Bots Place — код подтверждения"
        message.set_content(f"Ваш код подтверждения: {code}")

        await aiosmtplib.send(
            message,
            hostname=settings.host,
            port=settings.port,
            username=settings.user or None,
            password=settings.password or None,
            use_tls=settings.use_ssl,
            start_tls=settings.use_tls and not settings.use_ssl,
            timeout=settings.timeout,
        )
