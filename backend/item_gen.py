import random
import uuid
from models import BaseItem, GearItem

# PREFIXES: Modify Base Armor (Multiplier)
PREFIXES = {
    "Guardian": {"armor_mult": 1.25},
    "Sturdy": {"armor_mult": 1.15},
    "Reinforced": {"armor_mult": 1.1},
    "Heavy": {"armor_mult": 1.2},
    "Worn": {"armor_mult": 0.8},
    "Shiny": {"armor_mult": 1.05},
    "Ancient": {"armor_mult": 1.3}
}

# SUFFIXES: Add specific attributes (Flat)
SUFFIXES = {
    "of Life": {"life_regen": 2.0},
    "of the Bear": {"max_health": 20},
    "of Protection": {"armor_add": 5.0},
    "of the Wind": {"speed_bonus": 0.05},
    "of Vitality": {"max_health": 10, "life_regen": 0.5},
    "of Strength": {"physical_power": 5}
}

RARITIES = {
    "Common": {"weight": 60, "affixes": 0},
    "Uncommon": {"weight": 25, "affixes": 1},
    "Rare": {"weight": 10, "affixes": 2},
    "Epic": {"weight": 4, "affixes": 2, "extra_mult": 1.2},
    "Legendary": {"weight": 1, "affixes": 2, "extra_mult": 1.5}
}

def generate_item_instance(base_item: BaseItem, level: int = 1):
    """
    Generates a unique GearItem instance from a BaseItem template.
    """
    # 1. Roll Rarity
    r_keys = list(RARITIES.keys())
    r_weights = [RARITIES[r]["weight"] for r in r_keys]
    rarity_name = random.choices(r_keys, weights=r_weights, k=1)[0]
    rarity_conf = RARITIES[rarity_name]
    
    # 2. Roll Affixes
    prefix_name = None
    suffix_name = None
    num_affixes = rarity_conf["affixes"]
    
    if num_affixes >= 1:
        if random.random() > 0.5 or num_affixes == 2:
            prefix_name = random.choice(list(PREFIXES.keys()))
    
    if num_affixes == 2:
         suffix_name = random.choice(list(SUFFIXES.keys()))
    elif num_affixes == 1 and not prefix_name:
         suffix_name = random.choice(list(SUFFIXES.keys()))

    # 3. Calculate Stats
    # Level Scaling: +10% per level above 1
    level_mult = 1.0 + (level - 1) * 0.1
    base_armor = base_item.base_armor * level_mult
    
    # Rarity Multiplier (Epic/Legendary)
    base_armor *= rarity_conf.get("extra_mult", 1.0)
    
    # Apply Prefix
    if prefix_name:
        base_armor *= PREFIXES[prefix_name].get("armor_mult", 1.0)
        
    final_stats = {
        "armor": round(base_armor, 1),
        "life_regen": 0.0,
        "max_health": 0
    }
    
    # Apply Suffix
    if suffix_name:
        s_data = SUFFIXES[suffix_name]
        for key, val in s_data.items():
            if key == "armor_add":
                final_stats["armor"] += val
            else:
                final_stats[key] = val

    # 4. Final Name Generation
    name_parts = []
    if prefix_name: name_parts.append(prefix_name)
    name_parts.append(base_item.name)
    if suffix_name: name_parts.append(suffix_name)
    
    full_name = " ".join(name_parts)
    
    # Create GearItem instance
    item_instance = GearItem(
        id=str(uuid.uuid4())[:18].replace("-",""),
        base_item_id=base_item.id,
        instance_name=full_name,
        prefix=prefix_name,
        suffix=suffix_name,
        level=level,
        rarity=rarity_name,
        stats=final_stats
    )
    
    return item_instance
