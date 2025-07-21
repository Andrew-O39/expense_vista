# Expense Tracker

**Expense Tracker** is a personal finance web application that allows users to create budgets, log daily expenses, and receive email alerts when their spending approaches or exceeds their set limits. The application is designed to help users stay in control of their finances through proactive and timely notifications.

## Features

- Users can register and securely log in to their accounts using JWT-based authentication.
- Budgets can be created for different categories and tracked over specific time periods.
- Users are able to log individual expenses and assign them to specific categories.
- he application provides summaries of spending by category and time period to improve financial awareness.
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

## Getting Started

To run this project locally, follow the steps below:

1. **Clone the repository**

   ```
   git clone https://github.com/Andrew-O39/expense_tracker.git
   cd expense_tracker
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
 expense_tracker/
├── app/
│   ├── api/              # API route definitions
│   ├── core/             # Core configurations and settings
│   ├── crud/             # CRUD operations
│   ├── db/               # Database setup and session
│   ├── models/           # Database models
│   ├── services/         # Business logic (e.g., alerts)
│   ├── utils/            # Utility functions (e.g., email sender)
│   ├── templates/
│   │   └── email_alert.html  # Email template
├── alembic/              # Database migration scripts
├── .env                  # Environment variables
├── README.md             # Project documentation
└── requirements.txt      # Python dependencies
   ```
## Roadmap

**Planned features for upcoming development include:**  
•Building a web-based dashboard with visual analytics and charts.  
•Adding machine learning support for automated expense categorization.  
•Enabling users to share budgets with family or teams.  
•Improving mobile responsiveness for better usability on smaller screens.

## License

This project is licensed under the MIT License.

## Acknowledgements
	•FastAPI for the excellent web framework.
	•SendGrid for the robust and developer-friendly email service.
	•Jinja2 for templating
	•Special thanks to the open-source community for libraries and tools that power this project.

