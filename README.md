# 💰 ExpenseVista

**ExpenseVista** is a personal finance web application that helps users **plan budgets**, **track expenses and income**, and **analyze financial health** over time.  
It also includes an **AI-powered assistant** that understands natural-language questions like:  
> “How much did I spend this week?”  
> “Am I over budget on transport this month?”  
> “What’s my highest budget this year?”

---

## 🚀 Features

- 🔐 **JWT-based authentication** for secure login and registration.  
- 🧾 **Budgets by category and period** (weekly, monthly, quarterly, yearly, etc.).  
- 💸 **Expense tracking** with detailed categories and time filters.  
- 💰 **Income tracking** (salary, freelance, investments, passive income).  
- 📊 **Dashboard overview:** income, expenses, and net balance with trend summaries.  
- ✉️ **Automated budget alerts via AWS SES**:
  - 50% → Budget halfway used  
  - 80–99% → Approaching limit  
  - 100%+ → Exceeded budget  
- 🎨 **Clean HTML email templates** with category, username, and period context.  
- 🤖 **AI Financial Assistant** for natural-language queries:
  - Understands “since June”, “this quarter”, “last 20 days”, etc.
  - Returns summaries, category breakdowns, and over/under-budget insights.  

---

## 🧠 Tech Stack

| Layer | Technology |
|:------|:------------|
| **Backend Framework** | FastAPI |
| **Database** | PostgreSQL (SQLAlchemy ORM) |
| **Email Service** | AWS SES (Simple Email Service) |
| **Auth** | OAuth2 + JWT |
| **Templating** | Jinja2 |
| **Data Validation** | Pydantic |
| **Migrations** | Alembic |
| **AI Assistant** | OpenAI GPT model (`gpt-4o-mini`) with rules fallback |
| **Date Handling** | Custom deterministic period logic (`assistant_dates.py`) |

---

## ⚙️ Getting Started

### 1️⃣ Clone the Repository

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
# Security
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/expense_tracker_db

# Email (AWS SES)
MAIL_FROM=your-email@example.com
AWS_SES_ACCESS_KEY_ID=your-access-key-id
AWS_SES_SECRET_ACCESS_KEY=your-secret-access-key
AWS_SES_REGION=us-east-1

# AI Assistant
AI_ASSISTANT_ENABLED=true
AI_PROVIDER=openai
OPENAI_API_KEY=your-openai-api-key
AI_MODEL=gpt-4o-mini
   ```
5. **Run database migration**
     ```
   alembic upgrade head
   ```
6. **Start the development server**
    ```
   uvicorn main:app --reload
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
            ├── assistant.py      ← AI assistant endpoints
│   │       ├── auth.py
│   │       ├── budget.py
│   │       ├── expense.py
│   │       ├── income.py          
│   │       ├── alerts.py
│   │       └── summary.py         ← Includes income + grouping logic
│   │
│   ├── core/                      ← Configuration + security
│   │   ├── __init__.py
│   │   ├── config.py              ← Pydantic Settings
│   │   └── security.py            ← JWT + password hashing
│   │
│   ├── db/                        ← Database + ORM models
│   │   ├── __init__.py
│   │   ├── base.py                ← Declarative Base
│   │   ├── base_class.py          ← Imports all models for Alembic
│   │   ├── session.py             ← Engine + get_db()
│   │   └── models/                ← Income ORM model
│   │       ├── __init__.py
│   │       ├── user.py
│   │       ├── expense.py
│   │       ├── budget.py
│   │       ├── alert_log.py
│   │       └── income.py          
│   │
│   ├── crud/                      ← CRUD operations
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── budget.py
│   │   ├── expense.py
│   │   ├── income.py        
│   │   └── alert.py
│   │
│   ├── schemas/                   ← Pydantic schemas
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── expense.py
│   │   ├── budget.py
│   │   ├── alert_log.py           
│   │   └── income.py             
│   │
│   ├── services/
│   │   ├── email_service.py         ← AWS SES integration
│   │   ├── alerts_service.py
│   │   ├── llm_client.py            ← OpenAI API interface
│   │   └── nl_interpreter.py        ← Rule-based intent parser
│   │
│   └── utils/
│       ├── __init__.py
        └── assistant_dates.py       ← Deterministic period resolution
│       └── date_utils.py            ← Handles date range logic
│
├── alembic/
│   ├── versions/
│   │   └── <timestamp>_add_incomes_table.py  ← Alembic migration
│   ├── env.py
│   └── alembic.ini
│
├── .env
├── requirements.txt
├── main.py                          ← Includes all routers + docs metadata / ← FastAPI entrypoint
├── CHANGELOG.md                     ← To be updated next
├── README.md
├── docs/
│   └── assistant_behavior.md        ← AI Assistant documentation + flowchart
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

MIT License © 2025 Andrew O.

## Acknowledgements
    •	FastAPI — The excellent Python web framework.
	•	AWS SES — Reliable and scalable email delivery.
	•	Jinja2 — Clean HTML templating.
	•	OpenAI — For the natural language understanding powering the AI assistant.
	•	❤️ The open-source community for tools and libraries that make this project possible.

# 🧩 How to Extend the Assistant

Developers can easily add new AI or rule-based intents in just a few steps.

🪄 Example: Add savings_overview_period

1️⃣ Define intent logic

In routes/assistant.py, add a new if intent == "savings_overview_period": block:

```
if intent == "savings_overview_period":
    income_ts = func.coalesce(Income.received_at, Income.created_at)
    total_income = (
        db.query(func.coalesce(func.sum(Income.amount), 0.0))
          .filter(Income.user_id == user.id, income_ts >= start, income_ts <= end)
          .scalar()
    ) or 0.0
    total_expense = (
        db.query(func.coalesce(func.sum(Expense.amount), 0.0))
          .filter(Expense.user_id == user.id, Expense.created_at >= start, Expense.created_at <= end)
          .scalar()
    ) or 0.0
    savings = total_income - total_expense
    reply = f"Your savings in {period_label} is {_euro(savings)}."
    return AssistantReply(reply=reply)
```
2️⃣ Register the new intent

Add it to the allowed intents list in:\
	•	/ai/_intent_debug prompt \
	•	and /ai/assistant LLM prompt block.

3️⃣ Add rule fallback

In nl_interpreter.py, add a detection rule:
```
if "saving" in t or "savings" in t:
    return "savings_overview_period", {"period": period or "month"}
```