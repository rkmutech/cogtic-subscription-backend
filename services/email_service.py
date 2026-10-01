import httpx

from config.app_logger import logger
from config.config import settings

JMAP_SESSION_URL = "https://api.fastmail.com/jmap/session"
JMAP_USING = [
    "urn:ietf:params:jmap:core",
    "urn:ietf:params:jmap:mail",
    "urn:ietf:params:jmap:submission",
]


async def send_email(recipient: str, subject: str, body: str) -> bool:
    """Send mail through the Fastmail JMAP API to the configured test inbox."""
    delivery_recipient = settings.MAIL_TO  # keep testing mail going to the test inbox
    if not settings.FASTMAIL_API_TOKEN or not settings.FASTMAIL_FROM or not delivery_recipient:
        logger.warning(
            "Email was not sent: configure FASTMAIL_API_TOKEN, FASTMAIL_FROM, and MAIL_TO",
        )
        return False

    try:
        await _send_jmap(settings.FASTMAIL_FROM, delivery_recipient, subject, body)
        logger.info("Sent email subject=%r to %s", subject, delivery_recipient)
        return True
    except Exception:
        logger.exception("Could not send email subject=%r to %s", subject, delivery_recipient)
        return False


async def _jmap_call(client: httpx.AsyncClient, api_url: str, calls: list) -> list:
    resp = await client.post(api_url, json={"using": JMAP_USING, "methodCalls": calls})
    resp.raise_for_status()
    responses = resp.json()["methodResponses"]
    for name, args, _ in responses:
        if name == "error" or args.get("notCreated"):
            raise RuntimeError(f"JMAP error: {args}")
    return responses


async def _send_jmap(sender: str, recipient: str, subject: str, body: str) -> None:
    headers = {"Authorization": f"Bearer {settings.FASTMAIL_API_TOKEN}"}
    async with httpx.AsyncClient(headers=headers, timeout=15) as client:
        # 1. Discover account + API URL
        resp = await client.get(JMAP_SESSION_URL)
        resp.raise_for_status()
        session = resp.json()
        api_url = session["apiUrl"]
        account_id = session["primaryAccounts"]["urn:ietf:params:jmap:mail"]

        # 2. Find the Drafts mailbox and the sending identity
        lookup = await _jmap_call(client, api_url, [
            ["Mailbox/query", {"accountId": account_id, "filter": {"role": "drafts"}}, "0"],
            ["Identity/get", {"accountId": account_id}, "1"],
        ])
        drafts_id = lookup[0][1]["ids"][0]
        identities = lookup[1][1]["list"]
        identity = next(
            (i for i in identities if i["email"].lower() == sender.lower()),
            None,
        )
        if identity is None:
            raise RuntimeError(f"{sender} is not a sending identity in this Fastmail account")

        # 3. Create the message and submit it in a single request
        await _jmap_call(client, api_url, [
            ["Email/set", {
                "accountId": account_id,
                "create": {"msg": {
                    "mailboxIds": {drafts_id: True},
                    "keywords": {"$draft": True},
                    "from": [{"email": identity["email"]}],
                    "to": [{"email": recipient}],
                    "subject": subject,
                    "bodyValues": {"b": {"value": body}},
                    "textBody": [{"partId": "b", "type": "text/plain"}],
                }},
            }, "0"],
            ["EmailSubmission/set", {
                "accountId": account_id,
                "create": {"sub": {"identityId": identity["id"], "emailId": "#msg"}},
                "onSuccessUpdateEmail": {"#sub": {"keywords/$draft": None}},
            }, "1"],
        ])


async def send_welcome_email(email: str, account_name: str) -> bool:
    login_url = f"{settings.FRONTEND_URL.rstrip('/')}/login"
    body = (
        f"Hello {account_name},\n\n"
        "Your Cogtic account has been created.\n"
        f"Login email: {email}\n"
        f"Login: {login_url}\n\n"
        "Use the password you chose during registration. For security, "
        "we never send passwords by email. Choose a subscription plan after logging in.\n"
    )
    return await send_email(email, "Welcome to Cogtic", body)


async def send_usage_alert(
    email: str,
    account_name: str,
    plan_name: str,
    used: int,
    included: int,
    threshold: int,
    period_start: object,
    period_end: object,
) -> bool:
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
    return await send_email(email, subject, body)
