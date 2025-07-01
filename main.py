from fastapi import FastAPI
from expense_tracker.app.api.routes import expense

# Create the FastAPI application instance
app = FastAPI(
    title="Expense Tracker API",
    description="A simple API to manage personal expenses.",
    version="1.0.0",
)


@app.get("/", tags=["Welcome"])
def read_root():
    """
    Root endpoint to confirm that the API is reachable.
    Returns a friendly welcome message.
    """
    return {"message": "Welcome to the Expense Tracker API"}


@app.get("/ping", tags=["Health Check"])
def health_check():
    """
    Health check endpoint to verify if the server is running.
    Commonly used by monitoring tools or load balancers.
    """
    return {"status": "ok"}

app.include_router(expense.router)
