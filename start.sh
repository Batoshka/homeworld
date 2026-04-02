#!/bin/bash
echo "--- HOMEWORLD UNIFIED LAUNCHER ---"

# 1. Cleanup Ports
echo "[1/3] Clearing process IDs on Ports 3001, 3002, 3003..."
(fuser -k 3001/tcp || true) 2>/dev/null
(fuser -k 3002/tcp || true) 2>/dev/null
(fuser -k 3003/tcp || true) 2>/dev/null
(lsof -t -i:3001 | xargs kill -9 || true) 2>/dev/null
(lsof -t -i:3002 | xargs kill -9 || true) 2>/dev/null
(lsof -t -i:3003 | xargs kill -9 || true) 2>/dev/null

sleep 1

# 2. Start Admin Backend (Port 3002)
echo "[2/3] Launching Admin Dashboard (Port 3002)..."
cd /work/homeworld/admin/backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 3002 --reload > /work/homeworld/homeworld_admin.log 2>&1 &

# 3. Start Game Backend (Port 3003)
echo "[3/3] Launching Game Server (Port 3003)..."
cd /work/homeworld/backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 3003 --reload > /work/homeworld/homeworld_backend.log 2>&1 &

echo "----------------------------------"
echo "SUCCESS: Both servers are broadcasting across the network."
echo "Admin Dashboard: http://localhost:3002 (Local) or http://192.168.0.167:3002 (Network)"
echo "Game World:      http://localhost:3003 (Local) or http://192.168.0.167:3003 (Network)"
echo "Check /work/homeworld/*.log for tactical feeds."
echo "----------------------------------"
