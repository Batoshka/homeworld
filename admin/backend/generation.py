import random
import math
from models import WorldTile, WorldObject

def get_elevation_noise(x, y, seed_x, seed_y):
    """Ridged Multifractal-like noise for sharp mountain ridges."""
    nx, ny = (x + seed_x) / 22.0, (y + seed_y) / 22.0
    
    # Large scale mountain features (Ridged)
    def ridged(v): return 1.0 - abs(v)
    
    n1 = ridged(math.sin(nx) * math.cos(ny))
    n2 = 0.5 * ridged(math.sin(nx * 2.1 + 1.2) * math.cos(ny * 2.3))
    n3 = 0.25 * math.sin(nx * 4.4) * math.cos(ny * 4.1) # Small detail
    
    # Scale and bias
    return (n1 + n2 + n3) * 8.0 - 4.0

def generate_world_logic(db_game):
    """
    Advanced procedural generation: Biomes, Hydrology (Rivers/Lakes), and Cliffs.
    """
    # 1. Clear previous world data
    db_game.query(WorldTile).delete()
    db_game.query(WorldObject).delete()
    db_game.commit()

    size = 100
    # Biome ID: 0=Grass, 1=Forest, 2=Desert, 3=Water, 4=Snow, 5=Cliff, 6=Swamp
    biome_map = [[0 for _ in range(size)] for _ in range(size)]
    elevation_map = [[0.0 for _ in range(size)] for _ in range(size)]

    seed_x, seed_y = random.uniform(0, 1000), random.uniform(0, 1000)
    WATER_LEVEL = -1.8

    # 2. Step 1: Elevation Pass
    for x in range(size):
        for y in range(size):
            elevation_map[x][y] = get_elevation_noise(x, y, seed_x, seed_y)

    # 3. Step 2: Biome Seeding (Base Biomes)
    def seed_biome(target_id, num_seeds, min_rad, max_rad):
        for _ in range(num_seeds):
            sx, sy = random.randint(0, size-1), random.randint(0, size-1)
            radius = random.randint(min_rad, max_rad)
            for x in range(max(0, sx-radius), min(size, sx+radius)):
                for y in range(max(0, sy-radius), min(size, sy+radius)):
                    if math.sqrt((x-sx)**2 + (y-sy)**2) < radius * (0.8 + random.random() * 0.4):
                        biome_map[x][y] = target_id

    seed_biome(1, 14, 8, 18) # Forest
    seed_biome(2, 6, 12, 25) # Desert

    # 4. Step 3: Hydrology (Rivers)
    num_rivers = 8
    for _ in range(num_rivers):
        # Start high
        rx, ry = random.randint(0, size-1), random.randint(0, size-1)
        for _ in range(150): # Max river length
            biome_map[rx][ry] = 3 # Water
            elevation_map[rx][ry] = WATER_LEVEL - 0.2
            
            # Move to lowest neighbor
            best_h = elevation_map[rx][ry]
            next_step = None
            for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                nx, ny = rx+dx, ry+dy
                if 0 <= nx < size and 0 <= ny < size:
                    if elevation_map[nx][ny] < best_h:
                        best_h = elevation_map[nx][ny]
                        next_step = (nx, ny)
            
            if not next_step or best_h < WATER_LEVEL - 0.5: break
            rx, ry = next_step

    # 5. Step 4: Refine Biomes based on Elevation & Context
    for x in range(size):
        for y in range(size):
            h = elevation_map[x][y]
            
            # Cliffs (Check gradient)
            max_grad = 0
            for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                nx, ny = x+dx, y+dy
                if 0 <= nx < size and 0 <= ny < size:
                    max_grad = max(max_grad, abs(h - elevation_map[nx][ny]))
            
            if h < WATER_LEVEL:
                biome_map[x][y] = 3 # Water
            elif max_grad > 2.2: # Steep!
                biome_map[x][y] = 5 # Cliff
            elif h > 6.5:
                biome_map[x][y] = 4 # Snow
            elif biome_map[x][y] != 3: # Not water
                # Detect Swamp (Lower ground near water)
                is_near_water = False
                for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nx, ny = x+dx, y+dy
                    if 0 <= nx < size and 0 <= ny < size and biome_map[nx][ny] == 3:
                        is_near_water = True
                if is_near_water and h < 0.5:
                    biome_map[x][y] = 6 # Swamp

    # 5.5 Step 5: Advanced Hydrology (Lake Depth)
    # Give depth based on distance to nearest land
    for x in range(size):
        for y in range(size):
            if biome_map[x][y] == 3: # Water
                min_dist = 10
                for dx in range(-3, 4):
                    for dy in range(-3, 4):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < size and 0 <= ny < size:
                            if biome_map[nx][ny] != 3:
                                dist = math.sqrt(dx*dx + dy*dy)
                                if dist < min_dist: min_dist = dist
                # The further from land, the deeper it gets
                elevation_map[x][y] = WATER_LEVEL - (min_dist * 0.5)

    # 6. Populate Database
    tiles = []
    objects = []
    object_counts = {} # Diagnostic
    biome_names = {0:"grass", 1:"forest", 2:"desert", 3:"water", 4:"snow", 5:"cliff", 6:"swamp"}
    
    models = {
        "tree": ["Tree_1.gltf", "Tree_2.gltf", "Tree_3.gltf"],
        "rock": ["Rock1.gltf", "Rock2.gltf"],
        "flower": ["Flowers_1.gltf", "Flowers_2.gltf"],
        "mushroom": ["Mushroom.gltf"],
        "reed": ["Reed.gltf"],
        "lilypad": ["Lilypad.gltf"],
        "seaweed": ["Seaweed.gltf"],
        "grass_small": ["Grass_Small.gltf"],
        "grass_big": ["Grass_Big.gltf"],
        "bush": ["Bush.gltf"],
        "plant_small": ["Plant_2.gltf"],
        "plant_large": ["Plant_3.gltf"],
        "dead_tree": ["DeadTree_1.gltf", "DeadTree_2.gltf", "DeadTree_3.gltf"]
    }

    for x in range(size):
        for y in range(size):
            b_id = biome_map[x][y]
            h = elevation_map[x][y]
            tiles.append(WorldTile(x=x, y=y, biome=biome_names[b_id], elevation=h))

            # --- PASS 1: PRIMARY ASSETS (Trees, Flowers, Rocks) ---
            chance, otype, scale = 0, None, 1.0
            if b_id == 1: # Forest
                if random.random() < 0.12: chance, otype, scale = 0.45, "mushroom", random.uniform(0.8, 1.3)
                else: chance, otype, scale = 0.28, "tree", random.uniform(2.5, 4.0)
            elif b_id == 0: # Grassland
                if random.random() < 0.25: chance, otype, scale = 0.35, "flower", 1.0
                else: chance, otype, scale = 0.05, "tree", 2.0
            elif b_id == 2: # Desert
                chance, otype, scale = 0.08, "rock", random.uniform(0.8, 1.5)
            elif b_id == 5: # Cliff
                chance, otype, scale = 0.05, "rock", random.uniform(1.0, 2.0)
            elif b_id == 3: # Water
                depth = WATER_LEVEL - h
                if depth < 0.6: 
                    if random.random() < 0.6: chance, otype, scale = 0.18, "reed", random.uniform(1.5, 2.5)
                    else: chance, otype, scale = 0.08, "lilypad", random.uniform(0.8, 1.2)
                else:
                    if random.random() < 0.3: chance, otype, scale = 0.12, "seaweed", random.uniform(1.2, 2.0)
                    else: chance, otype, scale = 0.05, "lilypad", random.uniform(1.0, 1.5)
            elif b_id == 6: # Swamp
                chance, otype, scale = 0.15, "mushroom", 1.2

            if otype and random.random() < chance:
                object_counts[otype] = object_counts.get(otype, 0) + 1
                objects.append(WorldObject(
                    x=x + random.random(), y=y + random.random(),
                    object_type=otype, model_id=random.choice(models[otype]),
                    rotation_y=random.uniform(0,360), scale=scale
                ))

            # --- PASS 2: SECONDARY ASSETS (Grass/Foliage) ---
            # Grass grows in Forest, Grassland, and Swamp
            if b_id in [0, 1, 6]:
                g_chance = 0.45 if b_id == 0 else 0.25 # More in grassland
                if random.random() < g_chance:
                    g_type = "grass_big" if random.random() < 0.3 else "grass_small"
                    object_counts[g_type] = object_counts.get(g_type, 0) + 1
                    objects.append(WorldObject(
                        x=x + random.random(), y=y + random.random(),
                        object_type=g_type, model_id=random.choice(models[g_type]),
                        rotation_y=random.uniform(0,360), scale=random.uniform(1.0, 1.8)
                    ))

            # --- PASS 3: UNDERGROWTH (Bushes/Plants) ---
            # Focus on Forest and Swamp for density
            if b_id in [0, 1, 6]:
                u_chance = 0.12 if b_id == 1 else 0.05
                if random.random() < u_chance:
                    u_type = "bush" if random.random() < 0.7 else "plant_large"
                    object_counts[u_type] = object_counts.get(u_type, 0) + 1
                    objects.append(WorldObject(
                        x=x + random.random(), y=y + random.random(),
                        object_type=u_type, model_id=random.choice(models[u_type]),
                        rotation_y=random.uniform(0,360), scale=random.uniform(1.2, 2.2)
                    ))
                elif random.random() < 0.04: # Rare exotic plants
                    u_type = "plant_small"
                    object_counts[u_type] = object_counts.get(u_type, 0) + 1
                    objects.append(WorldObject(
                        x=x + random.random(), y=y + random.random(),
                        object_type=u_type, model_id=random.choice(models[u_type]),
                        rotation_y=random.uniform(0,360), scale=random.uniform(0.8, 1.3)
                    ))

            # Reduced density and size for better atmosphere
            d_chance = 0.015 if b_id in [2, 4, 5] else 0.005
            if random.random() < d_chance:
                object_counts["dead_tree"] = object_counts.get("dead_tree", 0) + 1
                objects.append(WorldObject(
                    x=x + random.random(), y=y + random.random(),
                    object_type="dead_tree", model_id=random.choice(models["dead_tree"]),
                    rotation_y=random.uniform(0,360), scale=random.uniform(1.2, 2.5)
                ))

            if len(tiles) >= 500:
                print(f"[REGEN] Saving batch. Tiles: {len(tiles)}, Objects in buffer: {len(objects)}")
                db_game.bulk_save_objects(tiles)
                db_game.bulk_save_objects(objects)
                db_game.commit()
                tiles, objects = [], []

    if tiles: db_game.bulk_save_objects(tiles)
    if objects: db_game.bulk_save_objects(objects)
    db_game.commit()

    print(f"[REGEN] COMPLETE. Total counts: {object_counts}")
    return {"tiles_count": size*size, "objects_count": db_game.query(WorldObject).count()}
