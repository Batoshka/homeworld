export const WEARING_MAP = {
    "Superhero_Female_FullBody": {
        "head": ["Face", "Eyes", "Eyebrows"],
        "body": ["SuperHero_Female"],
        "hands": ["SuperHero_Female"], // Defaulting to hide body if gloves/arms overlap
        "foot": ["SuperHero_Female"],
        "chest": ["SuperHero_Female"],
        "shoulder": [],
        "waist": [],
        "legs": ["SuperHero_Female"]
    },
    "Superhero_Male_FullBody": {
        "head": ["Face", "Eyes", "Eyebrows"],
        "body": ["SuperHero_Male"],
        "hands": ["SuperHero_Male"],
        "foot": ["SuperHero_Male"],
        "chest": ["SuperHero_Male"],
        "shoulder": [],
        "waist": [],
        "legs": ["SuperHero_Male"]
    }
};

export const ANIMATION_MAP = [
    "A_TPose", "Crouch_Fwd_Loop", "Crouch_Idle_Loop", "Dance_Loop", 
    "Death01", "Driving_Loop", "Fixing_Kneeling", "Hit_Chest", 
    "Hit_Head", "Idle_Loop", "Idle_Talking_Loop", "Idle_Torch_Loop", 
    "Interact", "Jog_Fwd_Loop", "Jump_Land", "Jump_Loop", 
    "Jump_Start", "PickUp_Table", "Pistol_Aim_Down", "Pistol_Aim_Neutral", 
    "Pistol_Aim_Up", "Pistol_Idle_Loop", "Pistol_Reload", "Pistol_Shoot", 
    "Punch_Cross", "Punch_Jab", "Push_Loop", "Roll", "Roll_RM", 
    "Sitting_Enter", "Sitting_Exit", "Sitting_Idle_Loop", "Sitting_Talking_Loop", 
    "Spell_Simple_Enter", "Spell_Simple_Exit", "Spell_Simple_Idle_Loop", 
    "Spell_Simple_Shoot", "Sprint_Loop", "Swim_Fwd_Loop", "Swim_Idle_Loop", 
    "Sword_Attack", "Sword_Attack_RM", "Sword_Idle", "Walk_Formal_Loop", 
    "Walk_Loop"
];

export const HAIR_MAP = {
    'Buns': 'Hairstyles/Rigged to Head Bone/glTF (Godot -Unreal)/Hair_Buns.gltf',
    'Buzzed': 'Hairstyles/Rigged to Head Bone/glTF (Godot -Unreal)/Hair_Buzzed.gltf',
    'BuzzedFemale': 'Hairstyles/Rigged to Head Bone/glTF (Godot -Unreal)/Hair_BuzzedFemale.gltf',
    'Long': 'Hairstyles/Rigged to Head Bone/glTF (Godot -Unreal)/Hair_Long.gltf',
    'SimpleParted': 'Hairstyles/Rigged to Head Bone/glTF (Godot -Unreal)/Hair_SimpleParted.gltf',
    'Beard': 'Hairstyles/Rigged to Head Bone/glTF (Godot -Unreal)/Hair_Beard.gltf'
};

export const HAIR_TEXTURE_MAP = {
    'Style1': { base: 'T_Hair_1_BaseColor.png', normal: 'T_Hair_1_Normal.png' },
    'Style2': { base: 'T_Hair_2_BaseColor.png', normal: 'T_Hair_2_Normal.png' }
};
