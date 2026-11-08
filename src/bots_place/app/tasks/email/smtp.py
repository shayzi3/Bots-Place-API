from email.message import EmailMessage

import aiosmtplib

from bots_place.config.env import SmtpSettings


class SmtpEmailSender:
    def __init__(self, settings: SmtpSettings) -> None:
        self._settings = settings

    async def send_code(self, email: str, code: str) -> None:
        await self._send(
            email,
            "Bots Place — код подтверждения",
            f"Ваш код подтверждения: {code}",
        )

    async def send_link(self, email: str, link: str) -> None:
        await self._send(
            email,
            "Bots Place — смена почты",
            f"Перейдите по ссылке, чтобы подтвердить смену почты: {link}",
        )

    async def _send(self, email: str, subject: str, body: str) -> None:
        settings = self._settings
        if not settings.host:
            raise RuntimeError("SMTP_HOST is not configured")

        message = EmailMessage()
        message["From"] = settings.from_email
        message["To"] = email
        message["Subject"] = subject
        message.set_content(body)

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
