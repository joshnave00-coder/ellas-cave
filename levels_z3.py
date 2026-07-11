"""levels_z3.py — Level 3 (The Deep Cave) level data factories.

Level overview (5800 px wide):
  Section 1 "Bat Cavern"    0-1980  : intro pits, slow moving platforms, first bats
  Section 2 "Guard Post"  1980-3480  : guards + stalactites
  Section 3 "Lava Depths" 3480-5800  : hardest pits, fastest platforms, treasure chest
"""
import random
from constants import GROUND_Y, FOX_OR
from entities import (
    Platform, Spike, Coin, MovingPlatform,
    CaveBat, FallingRock, HumanGuard, FoxFriend,
)

# ── Level constants ───────────────────────────────────────────────────────
LEVEL_W = 5800
CHEST_X = 5520
CHEST_Y = GROUND_Y

# Lava pits: (world_x, width) — gaps in the ground filled with lava
PITS = [
    (700,  180),   # Section 1 — intro pit, slow moving platform
    (1980, 200),   # Section 1 end
    (2700, 220),   # Section 2 — 220 px, barely ice-bridge-able
    (3480, 240),   # Section 2 end — widest pit, needs platform timing
    (4280, 220),   # Section 3
    (4850, 180),   # Section 3 final approach
]

# Ground segments that exist between pits (x, width)
_GROUND_SEGS = [
    (0,    700),   # 0-700
    (880,  1100),  # 880-1980
    (2180, 520),   # 2180-2700
    (2920, 560),   # 2920-3480
    (3720, 560),   # 3720-4280
    (4500, 350),   # 4500-4850
    (5030, 770),   # 5030-5800
]


# ── Platforms ─────────────────────────────────────────────────────────────
def make_level3_platforms():
    g = GROUND_Y
    P = []

    def p(x, y, w, h=25):
        P.append(Platform(x, y, w, h))

    def mp(x, y, w, x2, speed=1.0):
        P.append(MovingPlatform(x, y, w, 20, x2=x2, speed=speed))

    # ── Ground segments ───────────────────────────────────────────────────
    for (x, w) in _GROUND_SEGS:
        P.append(Platform(x, g, w, 40))

    # ── Floating platforms (section 1 — 0-1980) ───────────────────────────
    p(130,  g - 130, 110)
    p(340,  g - 195, 100)
    p(590,  g - 140, 115)
    p(920,  g - 165, 110)
    p(1160, g - 120, 100)
    p(1480, g - 175, 115)
    p(1720, g - 115, 105)
    p(1820, g - 175, 110)

    # ── Floating platforms (section 2 — 1980-3480) ────────────────────────
    p(2220, g - 150, 110)
    p(2420, g - 110, 100)
    p(2950, g - 165, 115)
    p(3140, g - 110, 100)
    p(3280, g - 185, 110)

    # ── Floating platforms (section 3 — 3480-5800) ────────────────────────
    p(3760, g - 140, 110)
    p(3980, g - 195, 100)
    p(4550, g - 155, 110)
    p(4720, g - 115, 100)
    p(5090, g - 170, 115)
    p(5310, g - 120, 100)
    p(5570, g - 145, 110)

    # ── Moving platforms over each pit ────────────────────────────────────
    mp(710,  g - 80, 90, 780,  speed=0.8)    # pit 1 (180 px) — slow intro
    mp(1990, g - 80, 90, 2070, speed=1.0)    # pit 2 (200 px)
    mp(2710, g - 85, 85, 2800, speed=1.15)   # pit 3 (220 px)
    mp(3490, g - 85, 88, 3605, speed=1.35)   # pit 4 (240 px) — widest/faster
    mp(4290, g - 85, 88, 4375, speed=1.45)   # pit 5 (220 px) — fastest
    mp(4860, g - 78, 88, 4920, speed=1.05)   # pit 6 (180 px)

    for pl in P:
        pl.is_cave = True
    return P


# ── Spikes ────────────────────────────────────────────────────────────────
def make_level3_spikes():
    g = GROUND_Y
    S = []
    # Ground-level spikes (on solid ground segments)
    for cx in [892, 2192, 2932, 3732, 4510, 5042]:
        S.append(Spike(cx, g))
    # Ledge spikes — anchored on top of a platform (cx within it, y = its top)
    for cx, y in [(1210, g - 120),   # ledge 1160-1260
                  (2475, g - 110),   # ledge 2420-2520
                  (3195, g - 110),   # ledge 3140-3240
                  (4775, g - 115)]:  # ledge 4720-4820
        S.append(Spike(cx, y))
    return S


# ── Coins ─────────────────────────────────────────────────────────────────
def make_level3_coins():
    g = GROUND_Y
    coins = []
    positions = [
        (145, g-30), (175, g-30), (205, g-30),
        (945, g-30), (975, g-30), (1005, g-30),
        (2200, g-30), (2230, g-30), (2260, g-30),
        (2945, g-30), (2975, g-30),
        (3740, g-30), (3770, g-30), (3800, g-30),
        (4520, g-30), (4550, g-30),
        (5050, g-30), (5080, g-30), (5110, g-30),
        (5490, g-30), (5520, g-30), (5550, g-30),
        (140,  g-155), (350,  g-220), (600,  g-165),
        (930,  g-190), (1170, g-145), (1495, g-200),
        (1730, g-140), (1835, g-200),
        (2235, g-175), (2435, g-135),
        (2965, g-190), (3155, g-135), (3295, g-210),
        (3775, g-165), (3995, g-220),
        (4565, g-180), (4735, g-140),
        (5105, g-195), (5325, g-145), (5585, g-170),
        # High-risk pit-edge coins
        (692,  g-30), (878,  g-30),
        (1975, g-30), (2178, g-30),
    ]
    for (x, y) in positions:
        coins.append(Coin(x, y))
    return coins


# ── Bats ──────────────────────────────────────────────────────────────────
def make_level3_bats():
    g = GROUND_Y
    return [
        CaveBat(380,  g - 210,  150,  880,  speed=1.5),
        CaveBat(2350, g - 215, 2000,  3100, speed=2.0),
        CaveBat(3900, g - 220, 3600,  4600, speed=2.1),
    ]


# ── Falling rocks (stalactites) ───────────────────────────────────────────
def make_level3_falling_rocks():
    return [
        FallingRock(450,  12),
        FallingRock(1550, 15),
        FallingRock(2010, 12),
        FallingRock(3055, 15),
        FallingRock(4065, 12),
        FallingRock(5185, 15),
    ]


# ── Guards ────────────────────────────────────────────────────────────────
def make_level3_guards():
    """Nets are lethal in Level 3 — no jail escape in the deep cave."""
    return [
        HumanGuard(1855, GROUND_Y, detect_range=225),
        HumanGuard(4160, GROUND_Y, detect_range=255),
    ]


# ── Fox friends ───────────────────────────────────────────────────────────
_FOX_COLORS = [
    FOX_OR, (140, 55, 12),  (245, 165, 35), (255, 255, 255),
    (165, 170, 178), (50, 28, 14),   (255, 108, 52), (196, 48, 40),
    (108, 72, 10),   (244, 230, 140),(255, 145, 95), (168, 36, 18),
    (255, 215, 0),   (160, 80, 38),  (222, 180, 140),
    (255, 68, 0),    (100, 65, 30),  (255, 158, 118),(210, 105, 30),
    (188, 143, 95),  (255, 140, 200),(140, 255, 200),(140, 170, 255),
]

def make_level3_fox_friends():
    g = GROUND_Y
    # Keep foxes ≥70 px from any ground spike and outside all pit x-ranges
    # (ledge spikes are up on platforms, so ground-spawning foxes needn't avoid them)
    _Z3_SPIKE_CX = {892, 2192, 2932, 3732, 4510, 5042}
    _PIT_RANGES  = [(px, px + pw) for (px, pw) in PITS]
    def _safe(x):
        if any(abs(x - cx) < 70 for cx in _Z3_SPIKE_CX):
            return False
        if any(px <= x <= px2 for (px, px2) in _PIT_RANGES):
            return False
        return True
    positions = [x for x in range(200, 5600, 60) if _safe(x)]
    random.shuffle(positions)
    friends = []
    for i, x in enumerate(positions[:80]):
        col   = _FOX_COLORS[i % len(_FOX_COLORS)]
        scale = random.uniform(0.32, 0.85)
        friends.append(FoxFriend(x, g, col, scale))
    return friends
