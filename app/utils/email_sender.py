from datetime import datetime

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from jinja2 import Template
from app.core.config import settings
from pathlib import Path


def render_alert_email(user_name, category, period, total_spent, limit, alert_type):
    """
    Renders the HTML content for budget alert emails.

    Args:
        user_name (str): The recipient's username.
        category (str): Budget category.
        period (str): Budget period (e.g., monthly).
        total_spent (float): Amount already spent.
        limit (float): Budget limit for the period.
        alert_type (str): Type of alert (e.g., 'half_limit', 'near_limit', 'limit_exceeded').

    Returns:
        str: Rendered HTML string for the email body.
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
    Sends an email using SendGrid.
    Args:
        to_email (str): Recipient's email address.
        subject (str): Subject of the email.
        html_content (str): HTML or plain-text message body.
    Returns:
        bool: True if email was sent successfully, False otherwise.
    """
    if not settings.sendgrid_api_key or not settings.email_from:
        print("Missing SendGrid configuration.")
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
        print(f"[EMAIL SENT] Status: {response.status_code}")
        return 200 <= response.status_code < 300
    except Exception as e:
        print(f"[EMAIL FAILED] {e}")
        return False