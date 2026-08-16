from typing import Any

from pydantic import BaseModel



class ErrorResponse(BaseModel):
    message: str
    message: str
    details: Any | None = None
    request_id: str | None = None