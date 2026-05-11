import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from src.config import get_settings

logger = logging.getLogger(__name__)


async def send_daily_digest(subject: str, html_body: str) -> bool:
    settings = get_settings()

    if not settings.smtp_user or not settings.email_recipients:
        logger.warning("SMTP credentials or recipients not configured, skipping email")
        return False

    recipients = [r.strip() for r in settings.email_recipients.split(",") if r.strip()]

    msg = MIMEMultipart("alternative")
    msg["From"] = settings.smtp_user
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user,
            password=settings.smtp_password,
            start_tls=True,
        )
        logger.info(f"Daily digest sent to {len(recipients)} recipient(s)")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False
