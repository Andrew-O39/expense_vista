# app/services/verification_mailer.py
from pathlib import Path
from jinja2 import Template
from app.core.config import settings
from app.utils.email_sender import send_alert_email  # your SES utility

def render_verify_email(user_name: str, verify_url: str, ttl_hours: int = 24) -> str:
    path = Path(__file__).resolve().parents[1] / "templates" / "email_verify.html"
    html = Template(path.read_text(encoding="utf-8")).render(
        user_name=user_name,
        verify_url=verify_url,
        ttl_hours=ttl_hours,
    )
    return html

def send_verify_email(to_email: str, user_name: str, verify_url: str) -> bool:
    html = render_verify_email(user_name, verify_url)
    return send_alert_email(to_email, "Verify your email for ExpenseVista", html)