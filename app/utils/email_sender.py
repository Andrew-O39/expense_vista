from datetime import datetime
from pathlib import Path

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from jinja2 import Template

from app.core.config import settings


def render_alert_email(user_name, category, period, total_spent, limit, alert_type):
    """
    Renders the HTML content for budget alert emails (Jinja template).
    """
    template_path = Path(__file__).resolve().parent.parent / "templates" / "email_alert.html"
    with open(template_path, "r") as f:
        template = Template(f.read())

    return template.render(
        user_name=user_name,
        category=category,
        period=period,
        total_spent=total_spent,
        limit=limit,
        alert_type=alert_type,
        year=datetime.now().year
    )


def send_alert_email(to_email: str, subject: str, html_content: str) -> bool:
    """
    Send an HTML email via AWS SES (boto3).
    Returns True if SES accepts the message (2xx), else False.
    """
    # Basic config checks
    missing = []
    if not settings.aws_region: missing.append("AWS_REGION")
    if not settings.aws_access_key_id: missing.append("AWS_ACCESS_KEY_ID")
    if not settings.aws_secret_access_key: missing.append("AWS_SECRET_ACCESS_KEY")
    if not settings.ses_sender: missing.append("EMAIL_FROM")
    if missing:
        print(f"[EMAIL FAILED] Missing SES configuration: {', '.join(missing)}")
        return False

    ses = boto3.client(
        "ses",
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )

    try:
        resp = ses.send_email(
            Source=settings.ses_sender,
            Destination={"ToAddresses": [to_email]},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {
                    # Provide both HTML and text for better deliverability
                    "Html": {"Data": html_content, "Charset": "UTF-8"},
                    "Text": {"Data": strip_html_for_text_fallback(html_content), "Charset": "UTF-8"},
                },
            },
            # ConfigurationSetName="optional-config-set",  # if you set one up for tracking
        )
        message_id = resp.get("MessageId")
        print(f"[EMAIL SENT via SES] MessageId: {message_id}")
        return True
    except (BotoCoreError, ClientError) as e:
        print(f"[EMAIL FAILED via SES] {e}")
        return False


def strip_html_for_text_fallback(html: str) -> str:
    """Very simple fallback text content; you can improve this if you want."""
    try:
        # Extremely light fallback to remove tags
        import re
        return re.sub(r"<[^>]+>", "", html).strip()
    except Exception:
        return "You have a new alert from ExpenseVista."