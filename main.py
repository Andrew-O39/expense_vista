from fastapi import FastAPI
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel, SecuritySchemeType
from fastapi.security import OAuth2PasswordBearer
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import expense, auth, budget, alerts, summary, income
from app.api.routes import ai

# -------------------------------
# Tag metadata for Swagger UI
# -------------------------------
tags_metadata = [
    {
        "name": "Authentication",
        "description": "User authentication endpoints including login and token generation."
    },
    {
        "name": "Budgets",
        "description": "Manage budget limits across different categories and time periods."
    },
    {
        "name": "Expenses",
        "description": "Add, update, view, and delete user expenses."
    },
    {
        "name": "Incomes",
        "description": "Record and manage income sources such as salary, freelance work, or investments."
    },
    {
        "name": "Alerts",
        "description": "Notifications triggered when budget thresholds are met or exceeded."
    },
    {
        "name": "Summary",
        "description": (
            "Endpoints for analyzing financial activity.\n\n"
            "- **`/summary/`** → Get statistical summaries of your spending habits (by period and category).\n"
            "- **`/summary/overview`** → Get an overview of both income and expenses, including net balance.\n"
            "   - Supports snapshots or grouped results (`monthly`, `quarterly`, `yearly`) for trend analysis."
        )
    },
    {
        "name": "Health Check",
        "description": "Simple endpoint to check API status."
    },
    {
        "name": "Welcome",
        "description": "API root. Introduction and welcome message."
    }
]

# -------------------------------
# FastAPI app
# -------------------------------
app = FastAPI(
    title="ExpenseVista",
    description="A simple app to manage your spending and budgets.",
    version="1.0.0",
    openapi_tags=tags_metadata  # Add tag metadata
)

# Allow CORS from React frontend
origins = [
    "http://localhost:5173",  # Vite dev server
    "http://127.0.0.1:5173",  # sometimes browsers use this
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,        # or ["*"] for all
    allow_credentials=True,
    allow_methods=["*"],          # GET, POST, PUT, DELETE, OPTIONS
    allow_headers=["*"],          # Authorization, Content-Type, etc.
)

# OAuth2 Bearer schema
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

# Custom OpenAPI schema with Bearer auth
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=app.openapi_tags
    )

    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }

    for path in openapi_schema["paths"].values():
        for operation in path.values():
            operation["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# -------------------------------
# Basic routes
# -------------------------------
@app.get("/", tags=["Welcome"])
def read_root():
    return {"message": "Welcome to the Expense Tracker API"}

@app.get("/ping", tags=["Health Check"])
def health_check():
    return {"status": "ok"}

# -------------------------------
# Include routers (order affects Swagger UI)
# -------------------------------
app.include_router(auth.router, tags=["Authentication"])
app.include_router(budget.router, tags=["Budgets"])
app.include_router(expense.router, tags=["Expenses"])
app.include_router(income.router, tags=["Incomes"])
app.include_router(alerts.router, tags=["Alerts"])
app.include_router(summary.router, tags=["Summary"])
app.include_router(ai.router, tags=["AI"])

