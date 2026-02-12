from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel

class AuditLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_input: str
    model_response: Optional[str] = None
    risk_score: Optional[float] = None
    risk_details: Optional[str] = None  # JSON string
    action: str  # 'allow', 'block_prompt', 'block_response'
    latency_ms: float

class SecurityPolicy(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    risk_category: str = Field(unique=True) # e.g., 'dw', 'pc'
    risk_name: str
    threshold: float = 0.5
    enabled: bool = True
