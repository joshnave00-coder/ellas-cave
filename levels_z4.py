"""levels_z4.py — Level 4 (Ella's Home) level data factories.

A warm, completely safe free-roam ending: a cozy house at the back of the cave,
a loving family of five, and a bunch of huggable friendly animals. No hazards —
the ground is one continuous strip so Ella can never fall, and nothing here can
hurt her. She keeps full keyboard control and can roam as long as she likes.
"""
import random
from constants import GROUND_Y, FOX_OR
from entities import Platform, Coin, HomeAnimal

# ── Level constants ───────────────────────────────────────────────────────
LEVEL_W = 3600
HOUSE_X = 3380          # centre x of the cozy house (the "back of the cave")
HOUSE_Y = GROUND_Y      # house sits on the ground
# Doorway region Ella walks into to "come home"
DOOR_RECT = (HOUSE_X - 36, GROUND_Y - 120, 72, 120)

_ANIMAL_FOX_COLORS = [
    FOX_OR, (245, 165, 35), (255, 255, 255), (255, 140, 200),
    (140, 170, 255), (196, 48, 40), (160, 80, 38), (244, 230, 140),
]


# ── Platforms ─────────────────────────────────────────────────────────────
def make_level4_platforms():
    g = GROUND_Y
    P = []
    # One continuous ground strip — no pits, so Ella can never fall.
    P.append(Platform(0, g, LEVEL_W, 40))
    # A few low, safe platforms to hop on.
    for (x, y, w) in [(380, g - 110, 120), (760, g - 150, 110),
                      (1240, g - 120, 120), (1700, g - 160, 110),
                      (2200, g - 120, 120), (2640, g - 150, 110)]:
        P.append(Platform(x, y, w, 22))
    for pl in P:
        pl.is_cave = True
    return P


# ── Coins (collecting one triggers a storm) ─────────────────────────────────
def make_level4_coins():
    g = GROUND_Y
    positions = [
        (240, g - 30), (300, g - 30), (520, g - 30), (640, g - 30),
        (900, g - 30), (1080, g - 30), (1360, g - 30), (1520, g - 30),
        (1820, g - 30), (2000, g - 30), (2320, g - 30), (2520, g - 30),
        (2820, g - 30), (3000, g - 30),
        (400, g - 140), (780, g - 180), (1260, g - 150),
        (1720, g - 190), (2220, g - 150), (2660, g - 180),
    ]
    return [Coin(x, y) for (x, y) in positions]


# ── The family of five ──────────────────────────────────────────────────────
def make_level4_people():
    """Five loving people who stand near the house and watch over Ella."""
    g = GROUND_Y
    data = [
        (3120, 'female'), (3215, 'male'), (3300, 'female'),
        (3470, 'male'),   (3545, 'female'),
    ]
    return [{'x': x, 'y': g, 'gender': gender, 'phase': i * 1.3}
            for i, (x, gender) in enumerate(data)]


# ── A bunch of friendly, huggable animals ───────────────────────────────────
def make_level4_animals():
    animals = []
    # Roaming foxes
    fox_x = [220, 520, 820, 1150, 1480, 1820, 2180, 2520]
    for i, x in enumerate(fox_x):
        animals.append(HomeAnimal(x, 'fox',
                                  _ANIMAL_FOX_COLORS[i % len(_ANIMAL_FOX_COLORS)],
                                  scale=random.uniform(0.55, 0.95),
                                  wander=True, min_x=120, max_x=2950))
    # Friendly polar bears (gentle here — they never chase)
    for x in (980, 2360):
        animals.append(HomeAnimal(x, 'bear', wander=True, min_x=140, max_x=2900))
    # Bunnies
    for x in (660, 1620, 2700):
        animals.append(HomeAnimal(x, 'bunny', (240, 240, 246),
                                  scale=random.uniform(0.8, 1.1),
                                  wander=True, min_x=120, max_x=2950))
    # A couple of calm animals waiting right by the house
    animals.append(HomeAnimal(3060, 'fox', (255, 255, 255), scale=0.8, wander=False))
    animals.append(HomeAnimal(3180, 'bunny', (245, 220, 230), scale=0.95, wander=False))
    return animals
