from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
import re

# Strip control characters (newlines, tabs, etc.) from free-text fields to
# prevent prompt injection into the LLM extraction prompt.
_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")

def _sanitize(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    return _CONTROL_CHARS.sub(" ", value).strip()

class EventIngestRequest(BaseModel):
    event_id: str = Field(..., min_length=3, max_length=100, pattern=r"^[a-zA-Z0-9_-]+$")
    user_id: str = Field(..., min_length=3, max_length=100, pattern=r"^[a-zA-Z0-9_-]+$")
    institution: Optional[str] = Field(None, max_length=200)
    session_id: str = Field(..., min_length=3, max_length=100, pattern=r"^[a-zA-Z0-9_-]+$")
    session_type: Literal["exam", "kyc", "pension", "traffic"] = "exam"
    event_type: Literal["verification_pass", "verification_fail", "anomaly_detected"]
    confidence: float = Field(..., ge=0.0, le=1.0)
    timestamp: str = Field(..., min_length=10, max_length=50)
    location: Optional[str] = Field(None, max_length=200)
    device: Optional[str] = Field(None, max_length=100)
    flag: Optional[str] = Field(None, max_length=100)

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: str) -> str:
        try:
            datetime.fromisoformat(v.rstrip("Z"))
        except ValueError:
            raise ValueError("timestamp must be a valid ISO 8601 datetime string")
        return v

    @field_validator("institution", "location", "device", "flag", mode="before")
    @classmethod
    def sanitize_free_text(cls, v):
        return _sanitize(v)

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    session_id: Optional[str] = Field(None, min_length=3, max_length=100, pattern=r"^[a-zA-Z0-9_-]+$")

class ForgetReasonRequest(BaseModel):
    reason: str = Field(..., min_length=5, max_length=500)

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=4000)

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = Field(None, min_length=3, max_length=100, pattern=r"^[a-zA-Z0-9_-]+$")
    history: Optional[List[ChatMessage]] = Field(default_factory=list)
