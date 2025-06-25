"""
Imports all models so that SQLAlchemy can register them on the metadata.
"""

from expense_tracker.app.db.models.user import User
from expense_tracker.app.db.models.expense import Expense
from expense_tracker.app.db.models.budget import Budget