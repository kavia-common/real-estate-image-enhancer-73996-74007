from sqlalchemy.orm import Session
from src.models.audit_log import AuditLog

async def log_audit_event(db: Session, user_id: int, action: str, details: dict, ip_address: str = None, user_agent: str = None):
    """Log an audit event to the database"""
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.add(audit_log)
    db.commit()
    return audit_log
