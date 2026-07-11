"""levels.py — Level 1 (Snowy Mountains) and Level 2 (The Cave) level data factories."""
import random
from constants import GROUND_Y, FOX_OR
from entities import Platform, Spike, Coin, Tube, PolarBear, HumanGuard, FoxFriend

FOX_FRIEND_COLORS = [
    FOX_OR, (140, 55, 12), (245, 165, 35), (255, 255, 255),
    (165, 170, 178), (50, 28, 14), (255, 108, 52), (196, 48, 40),
    (108, 72, 10), (244, 230, 140), (255, 145, 95), (168, 36, 18),
    (255, 215, 0),  (160, 80, 38), (222, 180, 140),
    (255, 68, 0),   (100, 65, 30), (255, 158, 118), (210, 105, 30),
    (188, 143, 95), (255, 140, 200),(140, 255, 200),(140, 170, 255),
]


def make_level1_platforms():
    P = []
    def p(x, y, w, h=25): P.append(Platform(x, y, w, h))

    p(0,      GROUND_Y, 620, 40)
    p(700,    GROUND_Y, 280, 40)
    p(1060,   GROUND_Y, 350, 40)
    p(1500,   GROUND_Y, 560, 40)
    p(2150,   GROUND_Y, 180, 40)
    p(2420,   GROUND_Y, 350, 40)
    p(2870,   GROUND_Y, 220, 40)
    p(3170,   GROUND_Y, 900, 40)
    p(4160,   GROUND_Y, 320, 40)
    p(4570,   GROUND_Y, 260, 40)
    p(4910,   GROUND_Y, 420, 40)
    p(5420,   GROUND_Y, 360, 40)
    p(5870,   GROUND_Y, 530, 40)

    p(150,  GROUND_Y-110, 120, 20)
    p(320,  GROUND_Y-160, 100, 20)
    p(490,  GROUND_Y-110, 130, 20)
    p(750,  GROUND_Y-120, 110, 20)
    p(920,  GROUND_Y-80,  90,  20)
    p(1100, GROUND_Y-140, 130, 20)
    p(1280, GROUND_Y-90,  100, 20)
    p(1580, GROUND_Y-150, 120, 20)
    p(1740, GROUND_Y-100, 110, 20)
    p(1920, GROUND_Y-160, 130, 20)
    p(2200, GROUND_Y-120, 100, 20)
    p(2480, GROUND_Y-180, 120, 20)
    p(2650, GROUND_Y-130, 100, 20)
    p(2900, GROUND_Y-160, 130, 20)
    p(3050, GROUND_Y-90,  110, 20)
    p(3300, GROUND_Y-120, 100, 20)
    p(3500, GROUND_Y-170, 120, 20)
    p(3700, GROUND_Y-100, 100, 20)
    p(3900, GROUND_Y-150, 130, 20)
    p(4200, GROUND_Y-110, 110, 20)
    p(4600, GROUND_Y-160, 120, 20)
    p(4800, GROUND_Y-90,  100, 20)
    p(5000, GROUND_Y-140, 130, 20)
    p(5200, GROUND_Y-100, 110, 20)
    p(5500, GROUND_Y-170, 120, 20)
    p(5700, GROUND_Y-120, 100, 20)
    p(5900, GROUND_Y-80,  110, 20)
    return P


def make_level1_spikes():
    S = []
    # Ground-level spikes (sit on solid ground between safe footing — jump over)
    for cx in [1320, 2000, 2930, 3600, 4650, 5100, 5750]:
        S.append(Spike(cx, GROUND_Y))
    # Ledge spikes — anchored on top of a platform (cx within it, y = its top)
    for cx, y in [(1795, GROUND_Y - 100),   # ledge 1740-1850
                  (3560, GROUND_Y - 170),   # ledge 3500-3620
                  (5065, GROUND_Y - 140)]:  # ledge 5000-5130
        S.append(Spike(cx, y))
    return S


def make_level1_coins():
    coins = []
    positions = [
        (160,GROUND_Y-30), (190,GROUND_Y-30), (220,GROUND_Y-30),
        (740,GROUND_Y-30), (760,GROUND_Y-30), (780,GROUND_Y-30),
        (1110,GROUND_Y-30),(1130,GROUND_Y-30),(1150,GROUND_Y-30),
        (1520,GROUND_Y-30),(1540,GROUND_Y-30),(1560,GROUND_Y-30),
        (1580,GROUND_Y-30),
        (2160,GROUND_Y-30),(2180,GROUND_Y-30),(2200,GROUND_Y-30),
        (2440,GROUND_Y-30),(2460,GROUND_Y-30),(2480,GROUND_Y-30),
        (2880,GROUND_Y-30),(2910,GROUND_Y-30),
        (4170,GROUND_Y-30),(4200,GROUND_Y-30),(4230,GROUND_Y-30),
        (4600,GROUND_Y-30),(4630,GROUND_Y-30),
        (4930,GROUND_Y-30),(4960,GROUND_Y-30),(4990,GROUND_Y-30),
        (5440,GROUND_Y-30),(5470,GROUND_Y-30),(5500,GROUND_Y-30),
        (5900,GROUND_Y-30),(5930,GROUND_Y-30),(5960,GROUND_Y-30),
        (160,GROUND_Y-130),(330,GROUND_Y-185),(510,GROUND_Y-130),
        (760,GROUND_Y-145),(1120,GROUND_Y-165),(1295,GROUND_Y-110),
        (1600,GROUND_Y-175),(1755,GROUND_Y-125),(1935,GROUND_Y-185),
        (2210,GROUND_Y-145),(2500,GROUND_Y-205),(2665,GROUND_Y-155),
        (2915,GROUND_Y-185),(3065,GROUND_Y-115),(3315,GROUND_Y-145),
        (3515,GROUND_Y-195),(3715,GROUND_Y-125),(3915,GROUND_Y-175),
        (4215,GROUND_Y-135),(4615,GROUND_Y-185),(4815,GROUND_Y-115),
        (5015,GROUND_Y-165),(5215,GROUND_Y-125),(5515,GROUND_Y-195),
        (5715,GROUND_Y-145),(5915,GROUND_Y-105),
    ]
    for (x, y) in positions:
        coins.append(Coin(x, y))
    return coins


def make_level1_bears():
    bears = []
    data = [
        # (start_x, y, patrol_min, patrol_max, speed)
        # Bear 1 — platform 1500-2060, clear of hazards
        (1600, GROUND_Y, 1510, 1810, 1.0),
        # Bear 2 — platform 3170-4070; patrol stays right of lava max (3295+220=3515)
        #   rect.left at patrol_min 3545 → bear right edge clears lava before reversing
        (3600, GROUND_Y, 3545, 3900, 1.1),
        # Bear 3 — platform 4570-4830; old max 4870 overshot into the gap
        #   rect.right at 4820 → center 4790, safely inside platform
        (4700, GROUND_Y, 4590, 4820, 1.0),
        # Bear 4 — platforms 5420-5780 and 5870-6400 with gap between them
        #   capped to stay on the first platform only
        (5700, GROUND_Y, 5640, 5770, 0.9),
    ]
    for (x, y, mn, mx, spd) in data:
        bears.append(PolarBear(x, y, mn, mx, spd))
    return bears


def make_level1_guards():
    guards = []
    guards.append(HumanGuard(2300, GROUND_Y, 180))
    guards.append(HumanGuard(4400, GROUND_Y, 170))
    return guards


def make_level1_tubes():
    tubes = []
    # Destination x=4200: on the platform at 4160-4480, ~330px past Bear 2's
    # max reach (3900) and outside its 200px chase radius — safe landing.
    tubes.append(Tube(2720, GROUND_Y - 60, 4200, GROUND_Y))
    return tubes


# ── Level 2 — The Cave ────────────────────────────────────────────────────

def make_level2_platforms():
    P = []
    def p(x, y, w, h=25): P.append(Platform(x, y, w, h))
    g = GROUND_Y

    p(0,    g, 500, 40)
    p(600,  g, 400, 40)
    p(1100, g, 350, 40)
    p(1550, g, 450, 40)
    p(2100, g, 500, 40)
    p(2700, g, 350, 40)
    p(3150, g, 600, 40)
    p(3850, g, 550, 40)

    p(120,  g-130, 120, 20)
    p(300,  g-180, 100, 20)
    p(660,  g-140, 110, 20)
    p(850,  g-90,  100, 20)
    p(1140, g-160, 120, 20)
    p(1350, g-100, 100, 20)
    p(1600, g-160, 120, 20)
    p(1820, g-110, 110, 20)
    p(2150, g-170, 130, 20)
    p(2380, g-120, 110, 20)
    p(2750, g-160, 120, 20)
    p(2960, g-100, 100, 20)
    p(3200, g-160, 130, 20)
    p(3450, g-110, 110, 20)
    p(3700, g-150, 120, 20)
    p(3900, g-90,  110, 20)

    for pl in P:
        pl.is_cave = True
    return P


def make_level2_spikes():
    S = []
    g = GROUND_Y
    for cx in [1140, 2140, 3180]:
        S.append(Spike(cx, g))
    # Ledge spikes — anchored on top of a platform
    for cx, y in [(895,  g - 90),    # ledge 850-950
                  (2435, g - 120),   # ledge 2380-2490
                  (3255, g - 160)]:  # ledge 3200-3330
        S.append(Spike(cx, y))
    return S


def make_level2_coins():
    coins = []
    g = GROUND_Y
    positions = [
        (120,g-30),(150,g-30),(180,g-30),
        (620,g-30),(650,g-30),(680,g-30),
        (1120,g-30),(1150,g-30),(1180,g-30),
        (1570,g-30),(1600,g-30),(1630,g-30),
        (2120,g-30),(2150,g-30),(2180,g-30),
        (2720,g-30),(2750,g-30),(2780,g-30),
        (3170,g-30),(3200,g-30),(3230,g-30),
        (3870,g-30),(3900,g-30),(3930,g-30),
        (130,g-155),(310,g-205),(670,g-165),
        (1160,g-185),(1365,g-125),(1620,g-185),
        (1835,g-135),(2165,g-195),(2395,g-145),
        (2765,g-185),(2975,g-125),(3215,g-185),
        (3465,g-135),(3715,g-175),(3915,g-115),
    ]
    for (x, y) in positions:
        coins.append(Coin(x, y))
    return coins


def make_fox_friends():
    friends = []
    g = GROUND_Y
    # Spawn foxes only on solid ground (not over the gaps between ground
    # segments) and clear of the ground spikes, so none start stranded over a hole.
    ground_segs = [(p.rect.left, p.rect.right)
                   for p in make_level2_platforms() if p.rect.top == g]
    _Z2_SPIKE_CX = {1140, 2140, 3180}
    def _safe(x):
        on_ground   = any(lo + 30 <= x <= hi - 30 for (lo, hi) in ground_segs)
        clear_spike = all(abs(x - cx) >= 70 for cx in _Z2_SPIKE_CX)
        return on_ground and clear_spike
    positions = [x for x in range(200, 4200, 60) if _safe(x)]
    random.shuffle(positions)
    for i, x in enumerate(positions[:80]):
        col = FOX_FRIEND_COLORS[i % len(FOX_FRIEND_COLORS)]
        scale = random.uniform(0.32, 0.85)
        friends.append(FoxFriend(x, g, col, scale))
    return friends
