"""
Imports all models so that SQLAlchemy can register them on the metadata.
"""

from app.db.models.user import User
from app.db.models.expense import Expense
from app.db.models.budget import Budget
from app.db.models.alert_log import AlertLog
from app.db.models.income import Income
from app.db.models.password_reset import PasswordResetToken
from app.db.models.ml_category_map import MLCategoryMap