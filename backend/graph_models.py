from cognee.low_level import DataPoint
from pydantic import Field
from typing import Optional

class EventType(DataPoint):
    name: str = "IdentityEventType"

class AnomalyType(DataPoint):
    name: str = "AnomalyType"

class UserEntity(DataPoint):
    user_id: str
    institution: Optional[str] = None
    metadata: dict = Field(default_factory=lambda: {"index_fields": ["user_id"]})

class SessionEntity(DataPoint):
    session_id: str
    session_type: str  # "exam", "kyc", "pension"
    metadata: dict = Field(default_factory=lambda: {"index_fields": ["session_id"]})

class IdentityEvent(DataPoint):
    event_id: str
    event_type: EventType
    confidence: float
    timestamp: str
    flag: Optional[str] = None
    belongs_to_session: SessionEntity
    performed_by: UserEntity
    anomaly: Optional[AnomalyType] = None
    metadata: dict = Field(default_factory=lambda: {"index_fields": ["event_id", "confidence", "flag"]})

IDENTITY_EXTRACTION_PROMPT = """
Extract identity verification events as a structured graph.
Identify: User entities, Session entities, Event types (pass/fail/anomaly),
Confidence scores, Timestamps, Anomaly flags, and the relationships between them.
A User PERFORMS an Event. An Event BELONGS_TO a Session.
An Anomaly IS_FLAGGED_IN an Event.
"""
