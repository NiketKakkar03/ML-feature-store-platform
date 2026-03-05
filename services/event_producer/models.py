from pydantic import BaseModel
from datetime import datetime
from typing import Literal
from enum import Enum

class EventType(str, Enum):
    VIEW = "view"
    CLICK = "click"

class UserEvent(BaseModel):
    user_id: int
    item_id: int
    event_type: EventType
    device: Literal["web", "mobile"]
    timestamp: datetime = None
