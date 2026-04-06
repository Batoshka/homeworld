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
    email = Column(String, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    is_admin = Column(Boolean, default=False)

class DbSession(Base): # Renamed to avoid sqlalchemy.orm.Session conflict
    __tablename__ = "sessions"
    id = Column(String(64), primary_key=True)
    user_id = Column(Integer) # No foreign key across different DBs
    last_activity = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime)

class PlayerState(Base):
    __tablename__ = "player_states"
    # Keyed by HomeServer user_id, but no physical FK constraint
    user_id = Column(Integer, primary_key=True)
    avatar_id = Column(String(50))
    pos_x = Column(Float, default=0.0)
    pos_y = Column(Float, default=0.0)
    pos_z = Column(Float, default=0.0)
    rot_y = Column(Float, default=0.0)
    status = Column(String(20), default="Idle")
    inventory = Column(JSONB, default=[]) # list of 20 slots
    equipment = Column(JSONB, default={}) # dict of named slots
    stats = Column(JSONB, default={"health": 100, "level": 1})
    visuals = Column(JSONB, default={"hair": 0, "eyes": "brown", "skin": "light"})
    last_saved = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

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

class Item(Base):
    __tablename__ = "items"
    id = Column(String(50), primary_key=True)
    name = Column(String(100))
    type = Column(String(20)) # WEAPON, TOOL, MATERIAL, etc.
    icon = Column(String(100)) # Emoji or path
    model = Column(String(255), nullable=True) # GLTF path
    stackable = Column(Boolean, default=False)
    max_stack = Column(Integer, default=100)

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
