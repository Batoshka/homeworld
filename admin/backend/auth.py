from fastapi import Request, Depends, HTTPException, status
from sqlalchemy.orm import Session
import datetime
from models import get_auth_db, User, DbSession

async def get_current_admin(request: Request, db: Session = Depends(get_auth_db)):
    session_id = request.cookies.get("homeserver_session")
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    now = datetime.datetime.utcnow()
    session = db.query(DbSession).filter(
        DbSession.id == session_id,
        DbSession.expires_at > now
    ).first()
    
    if not session:
        raise HTTPException(status_code=401, detail="Session expired")
    
    user = db.query(User).filter(User.id == session.user_id).first()
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return user
