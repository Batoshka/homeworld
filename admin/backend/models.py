# --- CRITICAL DATABASE DISCLOSURE ---
# This project is strictly configured to use POSTGRESQL. 
# DO NOT SWITCH TO SQLITE. The game.db file has been removed to avoid confusion.
# Active Databases: 'homeworld' (Game) and 'homeserver' (Auth) on port 5432.
# ------------------------------------

from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# HomeServer Database (Auth/Users)
AUTH_DATABASE_URL = os.getenv("AUTH_DATABASE_URL", "postgresql://postgres:1234@localhost:5432/homeserver")
# Homeworld Database (Game Data)
GAME_DATABASE_URL = os.getenv("GAME_DATABASE_URL", "postgresql://postgres:1234@localhost:5432/homeworld")

auth_engine = create_engine(AUTH_DATABASE_URL)
AuthSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=auth_engine)

game_engine = create_engine(GAME_DATABASE_URL)
GameSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=game_engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    is_admin = Column(Boolean, default=False)

class DbSession(Base):
    __tablename__ = "sessions"
    id = Column(String(64), primary_key=True)
    user_id = Column(Integer)
    expires_at = Column(DateTime)

class WorldTile(Base):
    __tablename__ = "world_tiles"
    x = Column(Integer, primary_key=True)
    y = Column(Integer, primary_key=True)
    biome = Column(String(20))
    elevation = Column(Float, default=0.0)

class WorldObject(Base):
    __tablename__ = "world_objects"
    id = Column(Integer, primary_key=True, autoincrement=True)
    x = Column(Float)
    y = Column(Float)
    object_type = Column(String(20))
    model_id = Column(String(50))
    rotation_y = Column(Float, default=0.0)
    scale = Column(Float, default=1.0)

def get_auth_db():
    db = AuthSessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_game_db():
    db = GameSessionLocal()
    try:
        yield db
    finally:
        db.close()
