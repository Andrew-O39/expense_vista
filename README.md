# ExpenseVista

**ExpenseVista** is a personal finance web application that allows users to create budgets, log daily expenses, track incomes, and receive email alerts when their spending approaches or exceeds their set limits. The application is designed to help users stay in control of their finances through proactive and timely notifications.

## Features

- Users can register and securely log in to their accounts using JWT-based authentication.
- Budgets can be created for different categories and tracked over specific time periods.
- Users are able to log individual expenses and assign them to specific categories.
- **Income tracking:** record income entries (salary, freelance, investments, etc.), categorized as active or passive.
- The application provides summaries of both spending and income by category and time period.
- **Financial overview dashboard:** shows total income, total expenses, and net balance, with breakdowns over time.
- Automated email alerts are sent when spending reaches 50% of the budget, nears the limit (80–99%), or exceeds the limit (100%+).
- Email notifications are designed using a styled HTML template with clear and friendly formatting.
- SendGrid integration ensures reliable delivery of notification emails.
- Emails include personalized content such as the user’s username, current category, and budget period, as well as the current year.

## Tech Stack

- **Backend Framework:** FastAPI
- **Database:** PostgreSQL (via SQLAlchemy ORM)
- **Templating Engine:** Jinja2
- **Email Service:** SendGrid API
- **Authentication:** OAuth2 with JWT Tokens
- **Data Validation:** Pydantic
- **Migrations:** Alembic
- **Income & Finance Tracking:** Added support for income records and net balance calculations

## Getting Started

To run this project locally, follow the steps below:

1. **Clone the repository**

   ```
   git clone https://github.com/Andrew-O39/expense_vista.git
   cd expense_vista
   ```
2. **Create and activate a virtual environment**
     ```
   python -m venv .venv
    source .venv/bin/activate
   ```
3. **Install the project dependencies**
    ```
   pip install -r requirements.txt
   ```
4.	**Configure environment variables**  
    Create a .env file in the root directory with the following keys:
   ```
# Security settings
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/expense_tracker_db

# Email (SendGrid)
MAIL_FROM=your-email@example.com
SENDGRID_API_KEY=your-sendgrid-api-key
   ```
5. **Run database migration**
     ```
   alembic upgrade head
   ```
6. **Start the development server**
    ```
   uvicorn app.main:app --reload
   ```
   
Once the server is running, you can access the interactive API docs at:
http://localhost:8000/docs

## Project Structure
```
 expense_vista/
│
├── app/
│   ├── __init__.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes/               ← Endpoints
│   │       ├── __init__.py
│   │       ├── auth.py
│   │       ├── budget.py
│   │       ├── expense.py
│   │       ├── income.py          
│   │       ├── alerts.py
│   │       └── summary.py         ← Includes income + grouping logic
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py              ← Pydantic Settings
│   │   └── security.py            ← JWT + password hashing
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py                ← Declarative Base
│   │   ├── base_class.py          ← Imports all models for Alembic
│   │   ├── session.py             ← Engine + get_db()
│   │   └── models/             ← Income ORM model
│   │       ├── __init__.py
│   │       ├── user.py
│   │       ├── expense.py
│   │       ├── budget.py
│   │       ├── alert_log.py
│   │       └── income.py          
│   │
│   ├── crud/                    ← CRUD operations
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── budget.py
│   │   ├── expense.py
│   │   ├── income.py        
│   │   └── alert.py
│   │
│   ├── schemas/                 ← Pydantic schemas
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── expense.py
│   │   ├── budget.py
│   │   ├── alert_log.py           
│   │   └── income.py             
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── email_service.py
│   │   └── alerts_service.py
│   │
│   └── utils/
│       ├── __init__.py
│       └── date_utils.py          ← Handles date range logic
│
├── alembic/
│   ├── versions/
│   │   └── <timestamp>_add_incomes_table.py  ← Alembic migration
│   ├── env.py
│   └── alembic.ini
│
├── .env
├── requirements.txt
├── main.py                        ← Includes all routers + docs metadata
├── CHANGELOG.md                   ← To be updated next
├── README.md
└── run.sh / Procfile (optional for deployment)
   ```
## Roadmap

**Planned features for upcoming development include:**  
•Building a web-based dashboard with visual analytics and charts.  
•Adding machine learning support for automated expense categorization.  
•Enabling users to share budgets with family or teams.  
•Improving mobile responsiveness for better usability on smaller screens.
•Savings tracking: automatically calculate potential savings (Income – Expenses – Budgets).
•Advanced reporting: quarterly and half-yearly summaries.

## License

This project is licensed under the MIT License.

## Acknowledgements
	•FastAPI for the excellent web framework.
	•SendGrid for the robust and developer-friendly email service.
	•Jinja2 for templating
	•Special thanks to the open-source community for libraries and tools that power this project.

