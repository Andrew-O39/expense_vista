"""
Imports all models so that SQLAlchemy can register them on the metadata.
"""

from app.db.models.user import User
from app.db.models.expense import Expense
from app.db.models.budget import Budget
from app.db.models.alert_log import AlertLog