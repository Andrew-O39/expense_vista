from datetime import datetime
from pathlib import Path
import re
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from jinja2 import Template
from app.core.config import settings


def _load_template(name: str) -> str:
    """
    Load template from app/templates reliably whether running locally or in Docker.
    """
    # repo_root/app/utils/email_sender.py  ->  repo_root/app/templates/name.html
    base = Path(__file__).resolve().parents[1]  # .../app
    tpl_path = base / "templates" / name
    with open(tpl_path, "r", encoding="utf-8") as f:
        return f.read()


def render_alert_email(user_name, category, period, total_spent, limit, alert_type):
    html = _load_template("email_alert.html")
    template = Template(html)
    return template.render(
        user_name=user_name,
        category=category,
        period=period,
        total_spent=total_spent,
        limit=limit,
        alert_type=alert_type,
        year=datetime.now().year,
    )


def strip_html_for_text_fallback(html: str) -> str:
    try:
        return re.sub(r"<[^>]+>", "", html).strip()
    except Exception:
        return "You have a new alert from ExpenseVista."


def send_alert_email(to_email: str, subject: str, html_content: str) -> bool:
    """
    Send an HTML email via AWS SES (boto3). Returns True if SES accepts the message.
    """
    # Config validation
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
                    "Html": {"Data": html_content, "Charset": "UTF-8"},
                    "Text": {"Data": strip_html_for_text_fallback(html_content), "Charset": "UTF-8"},
                },
            },
            # ConfigurationSetName="your-config-set"  # only if you created one
        )
        print(f"[EMAIL SENT via SES] MessageId: {resp.get('MessageId')}")
        return True
    except (BotoCoreError, ClientError) as e:
        print(f"[EMAIL FAILED via SES] {e}")
        return False