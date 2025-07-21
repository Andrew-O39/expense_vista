from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel, SecuritySchemeType
from fastapi.security import OAuth2PasswordBearer
from fastapi.openapi.utils import get_openapi

from app.api.routes import expense, auth, budget, alerts, summary


app = FastAPI(
    title="Expense Tracker API",
    description="A simple API to manage personal expenses.",
    version="1.0.0",
)

# Custom OAuth2 Bearer schema for Swagger
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

# Define custom OpenAPI schema to enable Bearer auth in Swagger UI
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
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

app.openapi = custom_openapi  # Attach the custom schema override


# Basic health and root routes
@app.get("/", tags=["Welcome"])
def read_root():
    return {"message": "Welcome to the Expense Tracker API"}

@app.get("/ping", tags=["Health Check"])
def health_check():
    return {"status": "ok"}


# Include routers
app.include_router(expense.router)
app.include_router(auth.router)
app.include_router(budget.router)
app.include_router(alerts.router)
app.include_router(summary.router)