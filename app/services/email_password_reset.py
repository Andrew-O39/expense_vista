from datetime import datetime
from pathlib import Path
from jinja2 import Template
from app.core.config import settings
from app.utils.email_sender import send_alert_email  # SES wrapper


def render_password_reset_email(user_name: str, reset_url: str) -> str:
    """
    Render the HTML content for the password reset email using a Jinja2 template.

    This function loads and renders the `password_reset.html` template located in
    the `app/templates` directory. It injects dynamic values such as the user's
    name, the password reset URL, and the current year.

    Args:
        user_name (str): The username of the recipient.
        reset_url (str): A unique password reset link for the user.

    Returns:
        str: The rendered HTML email content ready to be sent via SES.
    """
    path = Path(__file__).resolve().parent.parent / "templates" / "password_reset.html"
    template = Template(path.read_text())
    return template.render(user_name=user_name, reset_url=reset_url, year=datetime.now().year)


def send_password_reset_email(to_email: str, user_name: str, reset_url: str) -> bool:
    """
    Send a password reset email to the specified user via AWS SES.

    This function prepares the password reset email by rendering the Jinja2 template
    and sends it using the centralized SES email sender (`send_alert_email`).

    Args:
        to_email (str): The recipient's email address.
        user_name (str): The username of the recipient.
        reset_url (str): A secure link for the user to reset their password.

    Returns:
        bool: True if the email was successfully accepted by AWS SES, False otherwise.
    """
    html = render_password_reset_email(user_name, reset_url)
    return send_alert_email(to_email, "Reset your ExpenseVista password", html)