
import sys
import os

# Add paths to imports
sys.path.append('/work/homeworld/admin/backend')

from models import GameSessionLocal, WorldTile, WorldObject
from generation import generate_world_logic

def run_standalone():
    print("--- STANDALONE WORLD REGENERATION START ---")
    db = GameSessionLocal()
    try:
        print("Executing world generation logic...")
        stats = generate_world_logic(db)
        print("Generation Complete.")
        print(f"Stats: {stats}")
        
        # Verify the database counts
        obj_count = db.query(WorldObject).count()
        print(f"Total objects in DB now: {obj_count}")
        
        types = db.query(WorldObject.object_type).distinct().all()
        print(f"Object types in DB: {[t[0] for t in types]}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
    print("--- STANDALONE WORLD REGENERATION END ---")

if __name__ == "__main__":
    run_standalone()
