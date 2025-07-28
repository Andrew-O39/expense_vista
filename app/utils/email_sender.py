from datetime import datetime
from pathlib import Path

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from jinja2 import Template

from app.core.config import settings


def render_alert_email(user_name, category, period, total_spent, limit, alert_type) -> str:
    """
    Render HTML for a budget alert email.
    """
    template_path = Path(__file__).resolve().parent.parent / "templates" / "email_alert.html"
    template_content = template_path.read_text()
    template = Template(template_content)

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
    Send an email via SendGrid.
    """
    if not settings.sendgrid_api_key or not settings.email_from:
        print("❌ SendGrid config missing: check API key and sender email.")
        return False

    mail = Mail(
        from_email=settings.email_from,
        to_emails=to_email,
        subject=subject,
        html_content=html_content,
    )

    try:
        sg = SendGridAPIClient(settings.sendgrid_api_key)
        response = sg.send(mail)
        print(f"✅ Email sent → Status: {response.status_code}")
        return 200 <= response.status_code < 300
    except Exception as e:
        print(f"❌ Email failed: {type(e).__name__} - {e}")
        return False