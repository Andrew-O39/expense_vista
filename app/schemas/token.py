from pydantic import BaseModel, Field

class Token(BaseModel):
    """
    Schema representing an authentication token response.

    Attributes:
        access_token (str): The JWT access token string.
        token_type (str): The token type, typically 'bearer'.
    """
    access_token: str = Field(..., example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    token_type: str = Field(..., example="bearer")
    how_welcome: bool | None = None