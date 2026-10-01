import asyncio

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

from config.app_logger import logger
from config.config import settings


def send_email(recipient: str, subject: str, body: str) -> bool:
    """Send mail through FastAPI-Mail to the configured test account."""
    sender = settings.SMTP_USERNAME
    # Keep testing mail directed to the explicitly configured test inbox.
    delivery_recipient = settings.MAIL_TO
    if (
        not settings.SMTP_HOST
        or not sender
        or not settings.SMTP_PASSWORD
        or not delivery_recipient
    ):
        logger.warning(
            "Email was not sent: configure SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD, and MAIL_TO",
        )
        return False

    try:
        asyncio.run(_send_fastapi_mail(sender, delivery_recipient, subject, body))
        logger.info("Sent email subject=%r to %s", subject, delivery_recipient)
        return True
    except Exception:
        logger.exception("Could not send email subject=%r to %s", subject, delivery_recipient)
        return False


async def _send_fastapi_mail(sender: str, recipient: str, subject: str, body: str) -> None:
    mail_config = ConnectionConfig(
        MAIL_USERNAME=settings.SMTP_USERNAME,
        MAIL_PASSWORD=settings.SMTP_PASSWORD,
        MAIL_FROM=sender,
        MAIL_PORT=settings.SMTP_PORT,
        MAIL_SERVER=settings.SMTP_HOST,
        MAIL_STARTTLS=settings.SMTP_USE_TLS and settings.SMTP_PORT != 465,
        MAIL_SSL_TLS=settings.SMTP_PORT == 465,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True,
    )
    message = MessageSchema(
        subject=subject,
        recipients=[recipient],
        body=body,
        subtype=MessageType.plain,
    )
    await FastMail(mail_config).send_message(message)


def send_welcome_email(email: str, account_name: str) -> bool:
    login_url = f"{settings.FRONTEND_URL.rstrip('/')}/login"
    body = (
        f"Hello {account_name},\n\n"
        "Your Cogtic account has been created.\n"
        f"Login email: {email}\n"
        f"Login: {login_url}\n\n"
        "Use the password you chose during registration. For security, "
        "we never send passwords by email. Choose a subscription plan after logging in.\n"
    )
    return send_email(email, "Welcome to Cogtic", body)


def send_usage_alert(email: str, account_name: str, plan_name: str,
                     used: int, included: int, threshold: int,
                     period_start: object, period_end: object) -> bool:
    subject = f"Cogtic usage reached {threshold}%"
    body = (
        f"Hello {account_name},\n\n"
        f"Your {plan_name} plan has reached {threshold}% usage for this billing period.\n"
        f"Usage: {used:,} of {included:,} included requests\n"
        f"Billing period: {period_start} to {period_end}\n\n"
        "Your plan includes 20 additional free requests after the included limit; "
        "requests beyond that allowance are charged at your plan's overage rate.\n\n"
        "Sign in to Cogtic to review your usage and plan.\n"
    )
    return send_email(email, subject, body)
