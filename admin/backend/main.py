from fastapi import FastAPI, Request, HTTPException, Depends, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os
from models import get_auth_db, get_game_db, WorldTile, WorldObject, PlayerState, BaseItem, GearItem
from auth import get_current_admin
from generation import generate_world_logic
import httpx
import subprocess
import socket
import time
import json
import random
import uuid

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
            # Use /api/game/player/all (Public endpoint for local proxy sync)
            res = await client.get("http://localhost:3003/api/game/player/all", timeout=2.0)
            if res.status_code != 200:
                print(f"[Admin Proxy Error] Game server returned {res.status_code}")
                return []
            
            # The game backend now returns user_id, x, y, z which satisfies both 
            # the map markers and the oversight registry.
            return res.json()
        except (httpx.ConnectError, httpx.RequestError, ValueError, json.JSONDecodeError) as e:
            print(f"[Admin Proxy Error] {str(e)}")
            return []

@app.post("/api/admin/world/players/{uid}/add-item")
async def admin_add_loot(uid: int, db: Session = Depends(get_game_db), admin=Depends(get_current_admin)):
    """
    Directly inject a random GearItem into a player's inventory via the admin database connection.
    Bypasses proxy auth issues by logic duplication.
    """
    try:
        # 1. Find target player
        player_state = db.query(PlayerState).filter(PlayerState.user_id == uid).first()
        if not player_state:
            raise HTTPException(status_code=404, detail="Pilot not found in telemetry.")

        # 2. Pick a random base item
        base_templates = db.query(BaseItem).all()
        if not base_templates:
            raise HTTPException(status_code=404, detail="No base gear templates discovered.")
        
        template = random.choice(base_templates)
        
        # 3. Simple in-line generation logic (Match item_gen.py behavior)
        rarities = {
            "Common": {"weight": 60, "affixes": 0},
            "Uncommon": {"weight": 25, "affixes": 1},
            "Rare": {"weight": 10, "affixes": 2},
            "Epic": {"weight": 4, "affixes": 2, "extra_mult": 1.2},
            "Legendary": {"weight": 1, "affixes": 2, "extra_mult": 1.5}
        }
        r_keys = list(rarities.keys())
        r_weights = [rarities[r]["weight"] for r in r_keys]
        rarity_name = random.choices(r_keys, weights=r_weights, k=1)[0]
        
        item_id = str(uuid.uuid4())[:18].replace("-","")
        new_item = GearItem(
            id=item_id,
            base_item_id=template.id,
            instance_name=f"[Admin] {template.name}",
            level=player_state.stats.get("level", 1) if player_state.stats else 1,
            rarity=rarity_name,
            stats={"armor": template.base_armor * 1.5} # Simple admin gift logic
        )
        db.add(new_item)
        
        # 4. Update Inventory
        inv = list(player_state.inventory) if player_state.inventory else []
        while len(inv) < 20: inv.append(None)
        
        inserted = False
        for i in range(len(inv)):
            if inv[i] is None:
                inv[i] = item_id
                inserted = True
                break
        
        if not inserted:
            raise HTTPException(status_code=400, detail="Pilot inventory is completely theoretical (Full).")

        player_state.inventory = inv
        db.commit()
        # [Sync Lock] Ensure session is fully flushed and object is persistent
        db.refresh(player_state)
        db.refresh(new_item)
        
        return {
            "status": "success", 
            "item_name": new_item.instance_name,
            "rarity": rarity_name,
            "pilot": player_state.user_id
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database sync failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3002)
