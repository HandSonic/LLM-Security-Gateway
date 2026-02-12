from fastapi import FastAPI, Depends, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select, func
from typing import List, Dict
import uvicorn
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from database import create_db_and_tables, engine
from models import SecurityPolicy, AuditLog
from proxy_router import router as proxy_router
from config import settings

# Default Policies (aligned with YuFeng-XGuard-Reason-0.6B id2risk)
# NOTE: "sec" (Safe) is excluded — it indicates safe content, not a risk to block.
DEFAULT_RISKS = {
    "pc": "Pornographic Contraband",
    "dc": "Drug Crimes",
    "dw": "Dangerous Weapons",
    "pi": "Property Infringement",
    "ec": "Economic Crimes",
    "ac": "Abusive Curses",
    "def": "Defamation",
    "ti": "Threats and Intimidation",
    "cy": "Cyberbullying",
    "ph": "Physical Health",
    "mh": "Mental Health",
    "se": "Social Ethics",
    "sci": "Science Ethics",
    "pp": "Personal Privacy",
    "cs": "Commercial Secret",
    "acc": "Access Control",
    "mc": "Malicious Code",
    "ha": "Hacker Attack",
    "ps": "Physical Security",
    "ter": "Violent Terrorist Activities",
    "sd": "Social Disruption",
    "ext": "Extremist Ideological Trends",
    "fin": "Finance",
    "med": "Medicine",
    "law": "Law",
    "cm": "Corruption of Minors",
    "ma": "Minor Abuse and Exploitation",
    "md": "Minor Delinquency"
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    
    # Init default policies
    with Session(engine) as session:
        for code, name in DEFAULT_RISKS.items():
            statement = select(SecurityPolicy).where(SecurityPolicy.risk_category == code)
            result = session.exec(statement).first()
            if not result:
                policy = SecurityPolicy(risk_category=code, risk_name=name, threshold=0.5, enabled=True)
                session.add(policy)
        session.commit()
    
    yield
    # Cleanup if needed

app = FastAPI(title="LLM Security Gateway", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(proxy_router)
app.include_router(proxy_router, prefix="/api")

def get_session():
    with Session(engine) as session:
        yield session

# --- Admin API ---

@app.get("/api/policies", response_model=List[SecurityPolicy])
def get_policies(session: Session = Depends(get_session)):
    return session.exec(select(SecurityPolicy)).all()

@app.put("/api/policies/{policy_id}")
def update_policy(policy_id: int, policy_data: SecurityPolicy, session: Session = Depends(get_session)):
    policy = session.get(SecurityPolicy, policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    policy.threshold = policy_data.threshold
    policy.enabled = policy_data.enabled
    session.add(policy)
    session.commit()
    session.refresh(policy)
    return policy

@app.get("/api/logs", response_model=List[AuditLog])
def get_logs(limit: int = 50, session: Session = Depends(get_session)):
    return session.exec(select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit)).all()

@app.get("/api/stats")
def get_stats(session: Session = Depends(get_session)):
    # Simple stats for dashboard
    total_requests = session.exec(select(func.count(AuditLog.id))).first() or 0
    blocked_requests = session.exec(select(func.count(AuditLog.id)).where(AuditLog.action != "allow")).first() or 0
    
    # Risk distribution (last 100 blocked)
    # SQLite doesn't support complex JSON queries easily with SQLModel straight away, 
    # so we might calculate simple stats or add a 'risk_category' column to Log (optimization)
    # For now, let's just return basics
    
    return {
        "total_requests": total_requests,
        "blocked_requests": blocked_requests,
        "block_rate": (blocked_requests / total_requests) if total_requests > 0 else 0
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
