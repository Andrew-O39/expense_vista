from pydantic import BaseModel

class MessageOut(BaseModel):
    msg: str