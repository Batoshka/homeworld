from fastapi import Request, Depends
from sqlalchemy.orm import Session
import datetime
import secrets
from passlib.context import CryptContext
from models import get_auth_db, User, DbSession

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def generate_session_token():
    return secrets.token_hex(32)

async def get_current_user(request: Request, db: Session = Depends(get_auth_db)):
    # Using the same cookie name as homeserver allows session sharing
    session_id = request.cookies.get("homeserver_session")
    if not session_id:
        return None
    
    now = datetime.datetime.utcnow()
    session = db.query(DbSession).filter(
        DbSession.id == session_id,
        DbSession.expires_at > now
    ).first()
    
    if not session:
        return None
    
    # Extend session (sliding window)
    session.expires_at = now + datetime.timedelta(days=7)
    session.last_activity = now
    db.commit()
    
    user = db.query(User).filter(User.id == session.user_id).first()
    return user
