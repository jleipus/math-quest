from backend.models.game import AttackSubtype

_MAGIC_NAMES = [
    "Fireball",
    "Ice Lance",
    "Shadow Bolt",
    "Arcane Missile",
    "Lava Burst",
    "Void Rift",
    "Frost Nova",
    "Chain Lightning",
]

_BOW_NAMES = [
    "Poison Dart",
    "Eagle Eye",
    "Piercing Shot",
    "Volley",
    "Snipe",
    "Hunters Mark",
]

_SWORD_NAMES = [
    "Thunder Strike",
    "Dragon Breath",
    "Slash",
    "Riposte",
    "Whirlwind",
    "Cleave",
]

_AXE_NAMES = [
    "Skull Splitter",
    "Ravage",
    "Headbutt",
    "Reckless Swing",
    "Bloodlust",
    "Brutal Strike",
]

_ATTACK_SUBTYPES: list[tuple[AttackSubtype, list[str]]] = [
    ("magic", _MAGIC_NAMES),
    ("bow", _BOW_NAMES),
    ("sword", _SWORD_NAMES),
    ("axe", _AXE_NAMES),
]

_HEAL_NAMES = [
    "Holy Light",
    "Mending Touch",
    "Nature's Grasp",
    "Sacred Bloom",
    "Regenerate",
]
_SHIELD_NAMES = [
    "Stone Wall",
    "Iron Aegis",
    "Frost Ward",
    "Barrier",
    "Bulwark",
]

_POWER_BY_DIFFICULTY: dict[str, tuple[int, int]] = {
    "easy": (5, 10),
    "medium": (11, 25),
    "hard": (26, 40),
}

_ENERGY_BY_DIFFICULTY: dict[str, int] = {
    "easy": 1,
    "medium": 2,
    "hard": 3,
}
