from fastapi import FastAPI, Request, HTTPException, Depends, Response, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import datetime
import os
import json
from models import get_auth_db, get_game_db, User, DbSession, PlayerState, WorldTile, WorldObject, Item
from auth import verify_password, generate_session_token, get_current_user
import random

import threading
import time
from pydantic import BaseModel
from typing import List, Optional

class ChatMessage(BaseModel):
    username: str
    message: str
    timestamp: datetime.datetime = None

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex="http://.*:[0-9]+", # Permissive for local network development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- WEATHER SYSTEM ---
class WeatherManager:
    def __init__(self):
        self.is_raining = False
        self.intensity = 0.0
        self.last_toggle = time.time()
        self.next_toggle = random.uniform(20.0, 40.0) # Start FAST
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        while True:
            now = time.time()
            if now - self.last_toggle > self.next_toggle:
                self.is_raining = not self.is_raining
                self.intensity = random.uniform(0.3, 0.8) if self.is_raining else 0.0
                self.last_toggle = now
                self.next_toggle = random.uniform(600, 1200) if self.is_raining else random.uniform(1200, 2400)
                print(f"[WEATHER] Toggled: Raining={self.is_raining}")
            time.sleep(5)

    def force_weather(self, raining: bool):
        self.is_raining = raining
        self.intensity = 0.6 if raining else 0.0
        self.last_toggle = time.time()
        self.next_toggle = random.uniform(600, 1200) if raining else random.uniform(1200, 2400)
        print(f"[WEATHER] Forced: Raining={self.is_raining}")

weather_system = WeatherManager()

# Mount models and frontend static directories
app.mount("/models", StaticFiles(directory="/work/homeworld/models"), name="models")
app.mount("/static", StaticFiles(directory="/work/homeworld/frontend/static"), name="static")

# Global Config from Environment
CONFIG = {
    "API_BASE": os.getenv("HOMEWORLD_API_BASE", "")
}
chat_history = [] # [Tactical] Global Chat Registry

@app.get("/")
async def read_root(request: Request, user: User = Depends(get_current_user)):
    if not user:
        return RedirectResponse(url="/login")
    
    try:
        with open("../frontend/index.html", "r") as f:
            content = f.read()
        
        # Dynamic API Base Detection
        host = request.base_url.hostname
        api_base = os.getenv("HOMEWORLD_API_BASE")
        if not api_base:
            # If port 3003 is NOT in the URL, assume we are behind a proxy path /homeworld
            if ":3003" not in str(request.url):
                api_base = "/homeworld"
            else:
                api_base = f"http://{host}:3003"
            
        config = {"API_BASE": api_base, "username": user.username}
        config_script = f"<script>window.CONFIG = {json.dumps(config)};</script>"
        content = content.replace("<head>", f"<head>{config_script}")
        
        return HTMLResponse(content=content)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Welcome to Homeworld</h1><p>Frontend not yet configured.</p>")

@app.get("/login")
async def login_page(request: Request, user: User = Depends(get_current_user)):
    if user:
        return RedirectResponse(url="/")
    
    try:
        with open("../frontend/login.html", "r") as f:
            content = f.read()
            
        # Dynamic API Base Detection
        host = request.base_url.hostname
        api_base = os.getenv("HOMEWORLD_API_BASE")
        if not api_base or "localhost" in api_base:
            api_base = f"http://{host}:3003"
            
        config = {"API_BASE": api_base}
        config_script = f"<script>window.CONFIG = {json.dumps(config)};</script>"
        content = content.replace("<head>", f"<head>{config_script}")
        
        return HTMLResponse(content=content)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Homeworld Login</h1><p>Login page not found.</p>")

@app.post("/api/auth/login")
async def auth_login(
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_auth_db)
):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        return RedirectResponse(url="/login?error=invalid", status_code=303)
    
    # Create session in HOME SERVER database
    session_id = generate_session_token()
    now = datetime.datetime.utcnow()
    db_session = DbSession(
        id=session_id,
        user_id=user.id,
        expires_at=now + datetime.timedelta(days=7),
        last_activity=now
    )
    db.add(db_session)
    db.commit()
    
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key="homeserver_session",
        value=session_id,
        httponly=True,
        max_age=604800, # 7 days
        path="/",
        samesite="lax"
    )
    return response

@app.get("/api/auth/status")
def get_auth_status(request: Request, user: User = Depends(get_current_user)):
    if not user:
        return {"logged_in": False}
    return {
        "logged_in": True,
        "username": user.username,
        "full_name": f"{user.first_name} {user.last_name}" if user.first_name else user.username,
        "is_admin": user.is_admin
    }

@app.get("/api/game/weather")
def get_weather_status(response: Response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return {
        "is_raining": weather_system.is_raining,
        "intensity": weather_system.intensity
    }

@app.post("/api/game/weather")
async def post_weather_status(data: dict):
    raining = data.get("is_raining", False)
    weather_system.force_weather(raining)
    print(f"[WEATHER] Forced via API: Raining={raining}")
    return {"status": "success", "is_raining": weather_system.is_raining}

@app.get("/api/game/state")
def get_game_state(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_game_db)
):
    if not user:
        raise HTTPException(status_code=401)
    
    state = db.query(PlayerState).filter(PlayerState.user_id == user.id).first()
    if not state:
        state = PlayerState(
            user_id=user.id,
            inventory=[None] * 20,
            equipment={}
        )
        db.add(state)
        db.commit()
        db.refresh(state)
    
    return {
        "pos": {"x": state.pos_x, "y": state.pos_y, "z": state.pos_z},
        "rot_y": state.rot_y,
        "avatar_id": state.avatar_id,
        "inventory": state.inventory,
        "equipment": state.equipment,
        "stats": state.stats,
        "user_id": state.user_id,
        "last_saved": state.last_saved.isoformat() if state.last_saved else None
    }

@app.post("/api/game/save")
async def save_game_state(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_game_db)
):
    if not user:
        raise HTTPException(status_code=401)
    
    data = await request.json()
    state = db.query(PlayerState).filter(PlayerState.user_id == user.id).first()
    if not state:
        state = PlayerState(user_id=user.id)
        db.add(state)
    
    if "pos" in data:
        if "x" in data["pos"]: state.pos_x = data["pos"]["x"]
        if "y" in data["pos"]: state.pos_y = data["pos"]["y"]
        if "z" in data["pos"]: state.pos_z = data["pos"]["z"]
    if "rot_y" in data: state.rot_y = data["rot_y"]
    if "status" in data: state.status = data["status"]
    if "avatar_id" in data: state.avatar_id = data["avatar_id"]
    if "inventory" in data: state.inventory = data["inventory"]
    if "equipment" in data: state.equipment = data["equipment"]
    
    state.last_saved = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    db.commit()
    print(f"[HEARTBEAT] {user.username} at {state.last_saved.strftime('%H:%M:%S')}")
    return {"status": "success"}

@app.get("/api/game/world/tiles")
async def get_world_tiles(db: Session = Depends(get_game_db), user: User = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401)
    # Returns 10,000 tiles with height (e) and unique biome keys (b)
    # Mapping: g:grass, f:forest, d:desert, w:water, s:snow, c:cliff, m:swamp
    mapping = {"grass":"g", "forest":"f", "desert":"d", "water":"w", "snow":"s", "cliff":"c", "swamp":"m"}
    tiles = db.query(WorldTile).order_by(WorldTile.x, WorldTile.y).all()
    return [{"x": t.x, "y": t.y, "b": mapping.get(t.biome, "g"), "e": t.elevation} for t in tiles]

@app.get("/api/game/world/objects")
async def get_world_objects(db: Session = Depends(get_game_db), user: User = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401)
    # Returns all environmental assets
    objs = db.query(WorldObject).all()
    return [{"x": o.x, "y": o.y, "t": o.object_type, "m": o.model_id, "r": o.rotation_y, "s": o.scale} for o in objs]

@app.post("/api/game/world/dig")
async def dig_terrain(request: Request, db: Session = Depends(get_game_db), user: User = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401)
    data = await request.json()
    x, y = data.get("x"), data.get("y")
    tile = db.query(WorldTile).filter(WorldTile.x == x, WorldTile.y == y).first()
    if not tile:
        raise HTTPException(status_code=404, detail="Tile not found")
    
    # Lower elevation
    tile.elevation -= 0.8
    
    # Biome Transformation
    # If we hit water level, turn to water
    if tile.elevation < -1.8:
        tile.biome = "water"
    elif tile.biome == "snow" and tile.elevation < 5.5:
        tile.biome = "grass" # Melted
    elif tile.biome == "cliff" and tile.elevation < 2.0:
        tile.biome = "grass" # Erosion?

    db.commit()
    
    mapping = {"grass":"g", "forest":"f", "desert":"d", "water":"w", "snow":"s", "cliff":"c", "swamp":"m"}
    return {
        "x": tile.x,
        "y": tile.y,
        "e": tile.elevation,
        "b": mapping.get(tile.biome, "g")
    }

@app.get("/api/game/player/all")
def get_all_players(db: Session = Depends(get_game_db), auth_db: Session = Depends(get_auth_db)):
    # Use consistent UTC-based timezone for filtering
    threshold = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) - datetime.timedelta(seconds=60)
    states = db.query(PlayerState).filter(PlayerState.last_saved >= threshold).all()
    
    if not states:
        return []
        
    user_ids = [s.user_id for s in states]
    
    # Batch fetch usernames from HomeServer DB
    users = auth_db.query(User).filter(User.id.in_(user_ids)).all()
    user_map = {u.id: u.username for u in users}
    
    return [
        {
            "username": user_map.get(s.user_id, "Unknown"),
            "x": s.pos_x,
            "z": s.pos_z,
            "y": s.pos_y,
            "rot_y": s.rot_y,
            "status": s.status,
            "avatar_id": s.avatar_id,
            "equipment": s.equipment,
            "last_saved": s.last_saved.isoformat() if s.last_saved else None
        } for s in states
    ]

@app.get("/api/game/items")
def get_items(db: Session = Depends(get_game_db)):
    return db.query(Item).all()

def seed_items():
    db = next(get_game_db())
    existing = db.query(Item).count()
    if existing > 0:
        return
        
    items = [
        Item(id="sword_stone", name="Stone Sword", type="WEAPON", icon="⚔️", model="Sword_Stone.gltf", stackable=False),
        Item(id="wood", name="Raw Wood", type="MATERIAL", icon="🪵", model=None, stackable=True, max_stack=100),
        Item(id="stone", name="Rough Stone", type="MATERIAL", icon="🪨", model=None, stackable=True, max_stack=100)
    ]
    db.add_all(items)
    db.commit()
    print("[INIT] Database Seeded with Items")

# Run seeding in a separate thread to avoid blocking startup
threading.Thread(target=seed_items, daemon=True).start()

# [Tactical] Chat Endpoints
@app.post("/api/game/chat/send")
async def send_chat(msg: ChatMessage, user: User = Depends(get_current_user)):
    chat_msg = {
        "username": user.username,
        "message": msg.message,
        "timestamp": datetime.utcnow().isoformat()
    }
    chat_history.append(chat_msg)
    if len(chat_history) > 50:
        chat_history.pop(0)
    return {"status": "sent"}

@app.get("/api/game/chat/messages")
async def get_chat_messages(since: str = None):
    if not since:
        return chat_history
    return [m for m in chat_history if m["timestamp"] > since]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3003)
