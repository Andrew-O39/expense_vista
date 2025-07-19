from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from app.core.config import settings


def send_alert_email(to_email: str, subject: str, message: str) -> bool:
    """
    Sends an email using SendGrid.

    Args:
        to_email (str): Recipient's email address.
        subject (str): Subject of the email.
        message (str): HTML or plain-text message body.

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
        html_content=message,
    )

    try:
        sg = SendGridAPIClient(settings.sendgrid_api_key)
        response = sg.send(mail)
        print(f"[EMAIL SENT] Status: {response.status_code}")
        return 200 <= response.status_code < 300
    except Exception as e:
        print(f"[EMAIL FAILED] {e}")
        return False