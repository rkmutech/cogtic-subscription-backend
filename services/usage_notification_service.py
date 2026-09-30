from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from config.app_logger import logger
from models.billing import Tenant, UsageAlert
from services.email_service import send_usage_alert


USAGE_THRESHOLDS = (50, 70, 90, 100)


def notify_usage_thresholds(db: Session, tenant: Tenant, summary: dict) -> None:
    """Email the tenant's first registered user once per threshold and billing period."""
    if tenant.plan is None:
        return

    included = tenant.plan.included_requests
    used = int(summary["totalUsage"])
    if included <= 0:
        return

    recipients = sorted(tenant.users, key=lambda user: user.id or 0)
    if not recipients:
        logger.warning("No user is available for usage email, tenant id=%s", tenant.id)
        return
    recipient = recipients[0]
    period_start = summary["periodStart"]

    for threshold in USAGE_THRESHOLDS:
        if used * 100 < included * threshold:
            continue

        already_sent = db.query(UsageAlert.id).filter_by(
            tenant_id=tenant.id,
            period_start=period_start,
            threshold=threshold,
        ).first()
        if already_sent:
            continue

        sent = send_usage_alert(
            email=recipient.email,
            account_name=tenant.name,
            plan_name=tenant.plan.name,
            used=used,
            included=included,
            threshold=threshold,
            period_start=summary["periodStart"],
            period_end=summary["periodEnd"],
        )
        if not sent:
            continue

        db.add(UsageAlert(
            tenant_id=tenant.id,
            period_start=period_start,
            threshold=threshold,
        ))
        try:
            db.commit()
        except SQLAlchemyError:
            db.rollback()
            logger.exception(
                "Could not record sent usage email for tenant id=%s threshold=%s",
                tenant.id,
                threshold,
            )
