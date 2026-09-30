import smtplib
import ssl
from email.message import EmailMessage

from config.app_logger import logger
from config.config import settings


def send_email(recipient: str, subject: str, body: str) -> bool:
    """Send one email via configured SMTP. Return False if mail is unavailable."""
    sender = settings.MAIL_FROM or settings.SMTP_USERNAME
    if not settings.SMTP_HOST or not sender:
        logger.warning(
            "Email to %s was not sent: configure SMTP_HOST and MAIL_FROM or SMTP_USERNAME",
            recipient,
        )
        return False

    message = EmailMessage()
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)

    try:
        if settings.SMTP_PORT == 465:
            with smtplib.SMTP_SSL(
                settings.SMTP_HOST,
                settings.SMTP_PORT,
                timeout=15,
                context=ssl.create_default_context(),
            ) as smtp:
                _send_with_auth(smtp, message)
        else:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as smtp:
                if settings.SMTP_USE_TLS:
                    smtp.starttls(context=ssl.create_default_context())
                _send_with_auth(smtp, message)
        logger.info("Sent email subject=%r to %s", subject, recipient)
        return True
    except Exception:
        logger.exception("Could not send email subject=%r to %s", subject, recipient)
        return False


def _send_with_auth(smtp: smtplib.SMTP, message: EmailMessage) -> None:
    if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
        smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
    smtp.send_message(message)


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
        "Sign in to Cogtic to review your usage and plan.\n"
    )
    return send_email(email, subject, body)
