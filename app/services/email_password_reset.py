# app/services/email_password_reset.py
from datetime import datetime
from pathlib import Path
from jinja2 import Template
from app.core.config import settings
from app.utils.email_sender import send_alert_email  # SES wrapper

def render_password_reset_email(user_name: str, reset_url: str) -> str:
    path = Path(__file__).resolve().parent.parent / "templates" / "password_reset.html"
    template = Template(path.read_text())
    return template.render(user_name=user_name, reset_url=reset_url, year=datetime.now().year)

def send_password_reset_email(to_email: str, user_name: str, reset_url: str) -> bool:
    html = render_password_reset_email(user_name, reset_url)
    return send_alert_email(to_email, "Reset your ExpenseVista password", html)