from fastapi import FastAPI, Request, HTTPException, Depends, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os
from models import get_auth_db, get_game_db, WorldTile, WorldObject
from auth import get_current_admin
from generation import generate_world_logic
import httpx
import subprocess
import socket
import time
import json

app = FastAPI(title="Homeworld Admin Dashboard")

# Enable CORS for development flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def admin_root(request: Request, admin=Depends(get_current_admin)):
    try:
        with open("../frontend/index.html", "r") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Admin Dashboard</h1><p>Frontend not found.</p>")

@app.get("/api/admin/world/status")
async def get_world_status(db: Session = Depends(get_game_db), admin=Depends(get_current_admin)):
    tiles_count = db.query(WorldTile).count()
    objects_count = db.query(WorldObject).count()
    return {
        "tiles": tiles_count,
        "objects": objects_count,
        "size": "100x100"
    }

@app.post("/api/admin/world/generate")
async def trigger_generate_world(db: Session = Depends(get_game_db), admin=Depends(get_current_admin)):
    stats = generate_world_logic(db)
    return {"status": "success", "stats": stats}

@app.get("/api/admin/server/status")
async def get_server_status():
    # Check if Game Backend is listening on 3003
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1.0)
        is_online = s.connect_ex(('127.0.0.1', 3003)) == 0
    return {"status": "online" if is_online else "offline"}

@app.post("/api/admin/server/command")
async def server_command(data: dict, admin=Depends(get_current_admin)):
    cmd = data.get("command")
    if cmd == "stop":
        # Specific tactical shutdown
        subprocess.run(["fuser", "-k", "3003/tcp"], capture_output=True)
        subprocess.run(["fuser", "-k", "3002/tcp"], capture_output=True)
        subprocess.run(["fuser", "-k", "3001/tcp"], capture_output=True)
    
    if cmd == "restart" or cmd == "start":
        # Launch the unified start script in a detached way
        proc_cmd = "bash /work/homeworld/start.sh > /work/homeworld/homeworld_unified.log 2>&1 &"
        subprocess.Popen(proc_cmd, shell=True)
        
    return {"status": "success", "command": cmd, "details": "Unified Launch Script Triggered"}

@app.post("/api/admin/weather")
async def trigger_weather_change(data: dict, admin=Depends(get_current_admin)):
    async with httpx.AsyncClient() as client:
        # Game Backend is on Port 3003
        await client.post("http://localhost:3003/api/game/weather", json=data)
    return {"status": "success"}

@app.get("/api/admin/world/tiles")
async def get_all_tiles(db: Session = Depends(get_game_db), admin=Depends(get_current_admin)):
    # Standard 7-biome mapping for consistency
    mapping = {"grass":"g", "forest":"f", "desert":"d", "water":"w", "snow":"s", "cliff":"c", "swamp":"m"}
    tiles = db.query(WorldTile).order_by(WorldTile.x, WorldTile.y).all()
    return [{"x": t.x, "y": t.y, "b": mapping.get(t.biome, "g"), "e": t.elevation} for t in tiles]

@app.get("/api/admin/world/objects")
async def get_all_objects(db: Session = Depends(get_game_db), admin=Depends(get_current_admin)):
    objs = db.query(WorldObject).all()
    return [{"x": o.x, "y": o.y, "t": o.object_type} for o in objs]

@app.get("/api/admin/world/players")
async def admin_get_players(admin=Depends(get_current_admin)):
    async with httpx.AsyncClient() as client:
        try:
            # Fetch from the Game Backend (Port 3003)
            res = await client.get("http://localhost:3003/api/game/player/all", timeout=2.0)
            if res.status_code != 200:
                return []
            return res.json()
        except (httpx.ConnectError, httpx.RequestError, ValueError, json.JSONDecodeError):
            # Graceful fallback: return empty list if backend is offline or returns invalid data
            return []

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3002)
