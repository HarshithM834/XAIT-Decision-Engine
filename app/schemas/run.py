from typing import Optional
from pydantic import BaseModel

class RestartRequest(BaseModel):
    restart_from_stage: str
    force: bool = False
    reason: Optional[str] = None
