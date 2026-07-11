#!/usr/bin/env python3
"""
Ella's Cave — A 2D Side-Scrolling Platformer
Run with:  python ella_cave.py
Requires:  pip install pygame
"""

import pygame, sys, json, os, math, random
pygame.init()

# ══════════════════════════════════════════════════════════════════════
#  SCREEN / CLOCK
# ══════════════════════════════════════════════════════════════════════
SCREEN_W, SCREEN_H = 1200, 700
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Ella's Cave")
clock = pygame.time.Clock()
FPS = 60

# ══════════════════════════════════════════════════════════════════════
#  PHYSICS
# ══════════════════════════════════════════════════════════════════════
GRAVITY    = 0.52          # slightly floatier — more forgiving
MAX_FALL   = 18
JUMP_VEL   = -17           # higher jump, easier to clear gaps
MOVE_SPEED = 6             # a bit snappier so Ella feels responsive
ICE_KEY    = pygame.K_x          # activate ice bridge
DOWN_KEY   = pygame.K_DOWN       # enter tube

# ══════════════════════════════════════════════════════════════════════
#  COLORS
# ══════════════════════════════════════════════════════════════════════
WHITE   = (255, 255, 255)
BLACK   = (  0,   0,   0)
FOX_OR  = (212,  98,  30)   # Ella's body
BELLY_C = (240, 215, 165)
PAW_C   = ( 55,  18,   4)
EAR_PK  = (255, 155, 155)
SKY_T   = (130, 192, 240)
SKY_B   = (200, 228, 255)
SNOW_W  = (228, 240, 255)
SNOW_S  = (170, 205, 235)
PLAT_T  = (218, 234, 255)
PLAT_B  = ( 95, 138, 182)
PLAT_E  = ( 70, 110, 155)
CAVE_BG = ( 20,  12,   6)
CAVE_MD = ( 38,  22,  10)
CAVE_LT = ( 55,  32,  14)
CAVE_PT = ( 65,  40,  18)
CAVE_PE = ( 40,  24,  10)
LAVA_O  = (255,  80,   0)
LAVA_R  = (220,  30,   0)
LAVA_Y  = (255, 200,  40)
GOLD    = (255, 210,  50)
ICE_BL  = (155, 225, 255)
COIN_Y  = (255, 200,  30)
BEAR_W  = (215, 226, 238)
BEAR_S  = (175, 190, 210)
HUMAN_C = (180, 120,  70)
COAT_BR = ( 90,  55,  20)
SPIKE_G = (155, 155, 170)
SPIKE_L = (195, 195, 210)
NET_BR  = (110,  80,  25)

# ══════════════════════════════════════════════════════════════════════
#  FONTS
# ══════════════════════════════════════════════════════════════════════
def _font(size, bold=False):
    for name in ('Georgia', 'Palatino Linotype', 'Book Antiqua', None):
        try:
            if name:
                return pygame.font.SysFont(name, size, bold=bold)
        except:
            pass
    return pygame.font.Font(None, int(size * 1.35))

FONT_XL = _font(60, True)
FONT_LG = _font(40, True)
FONT_MD = _font(28, True)
FONT_SM = _font(20)
FONT_XS = _font(15)

# ══════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════
def dk(c, a=25):  return tuple(max(0, v - a) for v in c[:3])
def lt(c, a=25):  return tuple(min(255, v + a) for v in c[:3])

def txt(surf, text, font, color, cx, cy, shadow=True):
    if shadow:
        s = font.render(text, True, (0, 0, 0))
        surf.blit(s, (cx - s.get_width()//2 + 2, cy - s.get_height()//2 + 2))
    r = font.render(text, True, color)
    surf.blit(r, (cx - r.get_width()//2, cy - r.get_height()//2))

def draw_rounded_rect(surf, color, rect, radius=8, border=0, border_color=BLACK):
    pygame.draw.rect(surf, color, rect, border_radius=radius)
    if border:
        pygame.draw.rect(surf, border_color, rect, border, border_radius=radius)

# ══════════════════════════════════════════════════════════════════════
#  LEADERBOARD
# ══════════════════════════════════════════════════════════════════════
# Always resolve relative to this script's directory, not the launch cwd
LB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "leaderboard.json")

class Leaderboard:
    def __init__(self):
        self.scores = []
        self._load()

    def _load(self):
        if os.path.exists(LB_FILE):
            try:
                with open(LB_FILE) as f:
                    self.scores = json.load(f).get('scores', [])
            except Exception:
                self.scores = []

    def save(self):
        try:
            with open(LB_FILE, 'w') as f:
                json.dump({'scores': self.scores}, f, indent=2)
        except Exception as e:
            print(f"Leaderboard save error: {e}", file=sys.stderr)  # log but never crash

    def qualifies(self, score):
        if score <= 0:
            return False
        if len(self.scores) < 5:
            return True
        return score > min(s['score'] for s in self.scores)

    def add(self, initials, score):
        init = (initials.upper() + 'AAA')[:3]
        self.scores.append({'initials': init, 'score': int(score)})
        self.scores.sort(key=lambda s: s['score'], reverse=True)
        self.scores = self.scores[:5]
        self.save()

    def top5(self):
        return self.scores[:5]

LEADERBOARD = Leaderboard()

# ══════════════════════════════════════════════════════════════════════
#  PARTICLES
# ══════════════════════════════════════════════════════════════════════
class Particle:
    __slots__ = ('x','y','vx','vy','r','color','life','max_life','gravity')
    def __init__(self, x, y, vx, vy, r, color, life, gravity=0.1):
        self.x=x; self.y=y; self.vx=vx; self.vy=vy
        self.r=r; self.color=color; self.life=life; self.max_life=life
        self.gravity=gravity

    def update(self):
        self.x+=self.vx; self.y+=self.vy; self.vy+=self.gravity
        self.r = max(0.5, self.r * 0.97)
        self.life -= 1
        return self.life > 0

    def draw(self, surf, cam_x=0, cam_y=0):
        a = self.life / self.max_life
        c = tuple(int(v * a) for v in self.color[:3])
        pygame.draw.circle(surf, c, (int(self.x-cam_x), int(self.y-cam_y)), max(1, int(self.r)))

class Particles:
    def __init__(self):  self.ps = []
    def add(self, p):    self.ps.append(p)
    def burst(self, x, y, color, n=12, speed=3, r=4, life=40, gravity=0.1):
        for _ in range(n):
            a = random.uniform(0, math.pi*2)
            spd = random.uniform(speed*0.4, speed)
            self.ps.append(Particle(x, y, math.cos(a)*spd, math.sin(a)*spd,
                                    random.uniform(r*0.5, r), color, random.randint(life//2, life), gravity))
    def update(self):    self.ps = [p for p in self.ps if p.update()]
    def draw(self, surf, cam_x=0, cam_y=0):
        for p in self.ps: p.draw(surf, cam_x, cam_y)

particles = Particles()

# ══════════════════════════════════════════════════════════════════════
#  DRAWING — FOX (Ella and friends)
# ══════════════════════════════════════════════════════════════════════
def draw_fox(surf, cx, cy, facing_right=True, anim=0, scale=1.0,
             body_color=FOX_OR, ice_glow=False):
    """Draw a cute side-view fox. cx,cy = horizontal center, feet level."""
    s = scale
    pad = int(72 * s)
    tmp = pygame.Surface((pad*2, pad*2), pygame.SRCALPHA)
    tc = pad  # local center x
    # fox origin: feet at (tc, tc+30*s) → body center at (tc, tc)
    bcy = int(tc - 14 * s)   # body center y in tmp

    walk = math.sin(anim * 0.26) * int(5 * s)
    tw   = math.sin(anim * 0.14)  # tail wag -1..1

    # ── ice glow halo ──────────────────────────────────────────
    if ice_glow:
        gsurf = pygame.Surface((pad*2, pad*2), pygame.SRCALPHA)
        pygame.draw.circle(gsurf, (160, 230, 255, 30), (tc, bcy), int(46*s))
        tmp.blit(gsurf, (0,0))

    # ── tail ──────────────────────────────────────────────────
    tpts = [
        (tc - int(7*s),  bcy + int(10*s)),
        (tc - int(20*s), bcy - int(2*s) + int(tw*8*s)),
        (tc - int(32*s), bcy + int(10*s) + int(tw*12*s)),
        (tc - int(26*s), bcy + int(24*s) + int(tw*8*s)),
        (tc - int(10*s), bcy + int(20*s)),
    ]
    if len(set(tpts)) >= 3:
        pygame.draw.polygon(tmp, body_color, tpts)
    # tail tip (white)
    pygame.draw.circle(tmp, BELLY_C,
        (tc - int(28*s), bcy + int(17*s) + int(tw*8*s)), int(8*s))

    # ── body ──────────────────────────────────────────────────
    bw, bh = int(26*s), int(34*s)
    pygame.draw.ellipse(tmp, body_color,
        pygame.Rect(tc - bw//2, bcy - bh//2, bw, bh))

    # ── belly ─────────────────────────────────────────────────
    belly_r = pygame.Rect(tc - int(7*s), bcy - int(10*s), int(14*s), int(24*s))
    pygame.draw.ellipse(tmp, BELLY_C, belly_r)

    # ── back legs ─────────────────────────────────────────────
    lg = int(walk)
    foot_y = bcy + int(30*s)
    pygame.draw.rect(tmp, dk(body_color, 22),
        pygame.Rect(tc - int(10*s), bcy + int(12*s), int(7*s), int(18*s) + lg))
    pygame.draw.rect(tmp, dk(body_color, 22),
        pygame.Rect(tc + int(3*s),  bcy + int(12*s), int(7*s), int(18*s) - lg))
    # paws
    pygame.draw.rect(tmp, PAW_C,
        pygame.Rect(tc - int(11*s), foot_y + lg, int(9*s), int(4*s)))
    pygame.draw.rect(tmp, PAW_C,
        pygame.Rect(tc + int(2*s),  foot_y - lg, int(9*s), int(4*s)))

    # ── head ──────────────────────────────────────────────────
    hcx = tc + int(12*s)
    hcy = bcy - int(16*s)
    pygame.draw.circle(tmp, body_color, (hcx, hcy), int(13*s))

    # face marking (lighter patch)
    pygame.draw.circle(tmp, lt(body_color, 12), (hcx + int(4*s), hcy + int(2*s)), int(9*s))
    # snout
    snout_r = pygame.Rect(hcx + int(7*s), hcy - int(4*s), int(13*s), int(9*s))
    pygame.draw.ellipse(tmp, BELLY_C, snout_r)
    # nose
    pygame.draw.ellipse(tmp, (25, 8, 2),
        pygame.Rect(hcx + int(16*s), hcy - int(2*s), int(5*s), int(3*s)))
    # eye
    pygame.draw.circle(tmp, (195, 118, 5), (hcx + int(6*s), hcy - int(5*s)), int(4*s))
    pygame.draw.circle(tmp, (12,  8,  0), (hcx + int(6*s), hcy - int(5*s)), int(2*s))
    pygame.draw.circle(tmp, WHITE,         (hcx + int(7*s), hcy - int(6*s)), int(1*s))

    # ── ear (front) ───────────────────────────────────────────
    ep = [(tc + int(3*s),  hcy - int(11*s)),
          (tc - int(2*s),  hcy - int(26*s)),
          (tc + int(14*s), hcy - int(13*s))]
    pygame.draw.polygon(tmp, body_color, ep)
    epi = [(tc + int(4*s),  hcy - int(13*s)),
           (tc + int(1*s),  hcy - int(23*s)),
           (tc + int(12*s), hcy - int(14*s))]
    pygame.draw.polygon(tmp, EAR_PK, epi)

    # ── ear (back, slightly darker) ───────────────────────────
    eb = [(tc - int(6*s),  hcy - int(10*s)),
          (tc - int(14*s), hcy - int(24*s)),
          (tc + int(2*s),  hcy - int(12*s))]
    pygame.draw.polygon(tmp, dk(body_color, 18), eb)

    # ── front legs ────────────────────────────────────────────
    pygame.draw.rect(tmp, dk(body_color, 15),
        pygame.Rect(tc + int(4*s),  bcy + int(8*s),  int(6*s), int(16*s) - lg))
    pygame.draw.rect(tmp, dk(body_color, 15),
        pygame.Rect(tc - int(8*s),  bcy + int(8*s),  int(6*s), int(16*s) + lg))
    pygame.draw.rect(tmp, PAW_C,
        pygame.Rect(tc + int(3*s),  bcy + int(23*s) - lg, int(8*s), int(4*s)))
    pygame.draw.rect(tmp, PAW_C,
        pygame.Rect(tc - int(9*s),  bcy + int(23*s) + lg, int(8*s), int(4*s)))

    # ── ice shimmer sparkles on Ella ──────────────────────────
    if ice_glow and int(anim) % 10 < 3:
        for _ in range(3):
            sx2 = tc + random.randint(-int(30*s), int(30*s))
            sy2 = bcy + random.randint(-int(30*s), int(10*s))
            pygame.draw.circle(tmp, ICE_BL, (sx2, sy2), random.randint(1, int(2*s)+1))

    if not facing_right:
        tmp = pygame.transform.flip(tmp, True, False)

    # draw feet at cy
    surf.blit(tmp, (cx - pad, cy - pad - int(30*s)))


# ══════════════════════════════════════════════════════════════════════
#  DRAWING — POLAR BEAR
# ══════════════════════════════════════════════════════════════════════
def draw_polar_bear(surf, cx, cy, facing_right=True, anim=0):
    s = 1.0
    pad = 65
    tmp = pygame.Surface((pad*2, pad*2), pygame.SRCALPHA)
    tc = pad

    walk = math.sin(anim * 0.22) * 5

    # body
    pygame.draw.ellipse(tmp, BEAR_W, pygame.Rect(tc-22, tc-10, 44, 50))
    # belly
    pygame.draw.ellipse(tmp, lt(BEAR_W, 8), pygame.Rect(tc-12, tc, 24, 30))
    # back legs
    lg = int(walk)
    pygame.draw.rect(tmp, BEAR_S, pygame.Rect(tc-16, tc+30, 13, 20+lg))
    pygame.draw.rect(tmp, BEAR_S, pygame.Rect(tc+3,  tc+30, 13, 20-lg))
    pygame.draw.rect(tmp, dk(BEAR_W,30), pygame.Rect(tc-17, tc+49+lg, 15, 5))
    pygame.draw.rect(tmp, dk(BEAR_W,30), pygame.Rect(tc+2,  tc+49-lg, 15, 5))
    # head
    pygame.draw.circle(tmp, BEAR_W, (tc+20, tc-18), 22)
    # snout
    pygame.draw.ellipse(tmp, lt(BEAR_W, 5), pygame.Rect(tc+28, tc-22, 20, 14))
    pygame.draw.circle(tmp, (40, 30, 30), (tc+38, tc-18), 4)
    # ears
    pygame.draw.circle(tmp, BEAR_W, (tc+8,  tc-38), 9)
    pygame.draw.circle(tmp, BEAR_S, (tc+8,  tc-38), 5)
    pygame.draw.circle(tmp, BEAR_W, (tc+28, tc-38), 9)
    pygame.draw.circle(tmp, BEAR_S, (tc+28, tc-38), 5)
    # eyes
    pygame.draw.circle(tmp, (25, 18, 5), (tc+18, tc-22), 3)
    pygame.draw.circle(tmp, WHITE,       (tc+19, tc-23), 1)
    # arms
    pygame.draw.rect(tmp, BEAR_W, pygame.Rect(tc-30, tc-8, 12, 22+lg))
    pygame.draw.rect(tmp, BEAR_W, pygame.Rect(tc+28, tc-8, 12, 22-lg))

    if not facing_right:
        tmp = pygame.transform.flip(tmp, True, False)
    surf.blit(tmp, (cx - pad, cy - pad - 5))


# ══════════════════════════════════════════════════════════════════════
#  DRAWING — HUMAN GUARD
# ══════════════════════════════════════════════════════════════════════
def draw_human(surf, cx, cy, facing_right=True, alert=False, frame=0, gender='male'):
    if gender == 'female':
        _draw_human_female(surf, cx, cy, facing_right, alert, frame)
    else:
        _draw_human_male(surf, cx, cy, facing_right, alert, frame)


def _draw_human_male(surf, cx, cy, facing_right=True, alert=False, frame=0):
    pad = 55
    tmp = pygame.Surface((pad*2, pad*2), pygame.SRCALPHA)
    tc = pad
    sway = math.sin(frame * 0.05) * 2

    # shadow
    pygame.draw.ellipse(tmp, (0, 0, 0, 40), pygame.Rect(tc-16, tc+42, 32, 8))
    # boots
    pygame.draw.rect(tmp, (35, 22, 8), pygame.Rect(tc-14, tc+38, 12, 12))
    pygame.draw.rect(tmp, (35, 22, 8), pygame.Rect(tc+2,  tc+38, 12, 12))
    # trousers
    pygame.draw.rect(tmp, (55, 65, 85), pygame.Rect(tc-13, tc+18, 12, 22))
    pygame.draw.rect(tmp, (55, 65, 85), pygame.Rect(tc+1,  tc+18, 12, 22))
    # coat
    coat_pts = [(tc-16, tc+18), (tc+16, tc+18), (tc+14, tc-14), (tc-14, tc-14)]
    pygame.draw.polygon(tmp, COAT_BR, coat_pts)
    pygame.draw.rect(tmp, dk(COAT_BR, 15), pygame.Rect(tc-3, tc-14, 6, 34))
    # belt
    pygame.draw.rect(tmp, (22, 14, 5),  pygame.Rect(tc-16, tc+16, 32, 5))
    pygame.draw.rect(tmp, (200, 165, 30), pygame.Rect(tc-4, tc+15, 8, 7))
    # arms
    pygame.draw.rect(tmp, COAT_BR, pygame.Rect(tc-24, tc-12, 10, 26))
    pygame.draw.rect(tmp, COAT_BR, pygame.Rect(tc+14, tc-12, 10, 26))
    # hands
    pygame.draw.circle(tmp, HUMAN_C, (tc-20, tc+16), 6)
    pygame.draw.circle(tmp, HUMAN_C, (tc+20, tc+16), 6)
    # head
    pygame.draw.circle(tmp, HUMAN_C, (tc, tc-22), 16)
    # hat
    pygame.draw.rect(tmp, (22, 22, 22), pygame.Rect(tc-18, tc-36, 36, 8))
    pygame.draw.rect(tmp, (22, 22, 22), pygame.Rect(tc-12, tc-52, 24, 18))
    # eyes
    pygame.draw.circle(tmp, (20, 15, 5), (tc-5, tc-24), 2)
    pygame.draw.circle(tmp, (20, 15, 5), (tc+5, tc-24), 2)
    # alert !
    if alert:
        txt_surf = FONT_MD.render('!', True, (255, 200, 30))
        tmp.blit(txt_surf, (tc - txt_surf.get_width()//2, tc - 70))

    if not facing_right:
        tmp = pygame.transform.flip(tmp, True, False)
    surf.blit(tmp, (cx - pad, cy - pad + int(sway)))


def _draw_human_female(surf, cx, cy, facing_right=True, alert=False, frame=0):
    pad = 55
    tmp = pygame.Surface((pad*2, pad*2), pygame.SRCALPHA)
    tc = pad
    sway = math.sin(frame * 0.05) * 2

    COAT_TL = (155, 80, 110)   # teal-plum coat colour
    BOOT_C  = (50, 32, 60)
    SKIRT_C = (80, 50, 100)

    # shadow
    pygame.draw.ellipse(tmp, (0, 0, 0, 40), pygame.Rect(tc-16, tc+42, 32, 8))
    # boots (ankle-height)
    pygame.draw.rect(tmp, BOOT_C, pygame.Rect(tc-14, tc+34, 12, 16))
    pygame.draw.rect(tmp, BOOT_C, pygame.Rect(tc+2,  tc+34, 12, 16))
    # skirt (A-line triangle)
    skirt_pts = [(tc-16, tc+34), (tc+16, tc+34), (tc+20, tc+18), (tc-20, tc+18)]
    pygame.draw.polygon(tmp, SKIRT_C, skirt_pts)
    # coat body
    coat_pts = [(tc-15, tc+18), (tc+15, tc+18), (tc+13, tc-14), (tc-13, tc-14)]
    pygame.draw.polygon(tmp, COAT_TL, coat_pts)
    pygame.draw.rect(tmp, dk(COAT_TL, 15), pygame.Rect(tc-3, tc-14, 6, 34))
    # collar / lapels
    pygame.draw.polygon(tmp, lt(COAT_TL, 30),
        [(tc-3, tc-14), (tc-10, tc-2), (tc-3, tc+2)])
    pygame.draw.polygon(tmp, lt(COAT_TL, 30),
        [(tc+3, tc-14), (tc+10, tc-2), (tc+3, tc+2)])
    # arms
    pygame.draw.rect(tmp, COAT_TL, pygame.Rect(tc-23, tc-12, 9, 24))
    pygame.draw.rect(tmp, COAT_TL, pygame.Rect(tc+14, tc-12, 9, 24))
    # hands
    pygame.draw.circle(tmp, HUMAN_C, (tc-19, tc+14), 5)
    pygame.draw.circle(tmp, HUMAN_C, (tc+19, tc+14), 5)
    # head
    pygame.draw.circle(tmp, HUMAN_C, (tc, tc-22), 15)
    # hair — dark bun on top + side strands
    pygame.draw.circle(tmp, (40, 25, 15), (tc, tc-36), 10)   # bun
    pygame.draw.circle(tmp, (40, 25, 15), (tc, tc-30), 13)   # top volume
    # side hair strands framing the face
    pygame.draw.arc(tmp, (40, 25, 15),
        pygame.Rect(tc-18, tc-36, 12, 24), math.pi*0.1, math.pi*0.9, 4)
    pygame.draw.arc(tmp, (40, 25, 15),
        pygame.Rect(tc+6,  tc-36, 12, 24), math.pi*0.1, math.pi*0.9, 4)
    # eyes (with small lash lines)
    pygame.draw.circle(tmp, (20, 15, 5), (tc-5, tc-23), 2)
    pygame.draw.circle(tmp, (20, 15, 5), (tc+5, tc-23), 2)
    pygame.draw.line(tmp, (20, 15, 5), (tc-7, tc-25), (tc-3, tc-25), 2)
    pygame.draw.line(tmp, (20, 15, 5), (tc+3, tc-25), (tc+7, tc-25), 2)
    # alert !
    if alert:
        txt_surf = FONT_MD.render('!', True, (255, 200, 30))
        tmp.blit(txt_surf, (tc - txt_surf.get_width()//2, tc - 70))

    if not facing_right:
        tmp = pygame.transform.flip(tmp, True, False)
    surf.blit(tmp, (cx - pad, cy - pad + int(sway)))


# ══════════════════════════════════════════════════════════════════════
#  DRAWING — SPIKE
# ══════════════════════════════════════════════════════════════════════
def draw_spike_set(surf, cx, cy, frame=0):
    """Draw 3-spike cluster, cx=center bottom."""
    pulse = 0.5 + 0.5 * math.sin(frame * 0.08)
    # danger glow
    gsurf = pygame.Surface((80, 60), pygame.SRCALPHA)
    pygame.draw.ellipse(gsurf, (220, 30, 30, int(30 + pulse*30)), pygame.Rect(0, 10, 80, 40))
    surf.blit(gsurf, (cx - 40, cy - 44))
    # 3 spikes
    for i, ox in enumerate((-18, 0, 18)):
        bx = cx + ox
        pts = [(bx-8, cy), (bx+8, cy), (bx, cy-36)]
        pygame.draw.polygon(surf, SPIKE_G, pts)
        pygame.draw.polygon(surf, SPIKE_L, [(bx, cy-36), (bx+2, cy-20), (bx+8, cy)])
        pygame.draw.line(surf, WHITE, (bx, cy-36), (bx+3, cy-22), 1)


# ══════════════════════════════════════════════════════════════════════
#  DRAWING — COIN
# ══════════════════════════════════════════════════════════════════════
def draw_coin(surf, cx, cy, frame=0):
    squeeze = abs(math.cos(frame * 0.1))
    w = max(6, int(18 * squeeze))
    h = 18
    r = pygame.Rect(cx - w//2, cy - h//2, w, h)
    pygame.draw.ellipse(surf, COIN_Y, r)
    pygame.draw.ellipse(surf, lt(COIN_Y, 40), pygame.Rect(cx-w//2+2, cy-h//2+2, max(2,w//3), h//3))
    pygame.draw.ellipse(surf, dk(COIN_Y, 20), r, 2)


# ══════════════════════════════════════════════════════════════════════
#  DRAWING — NET PROJECTILE
# ══════════════════════════════════════════════════════════════════════
def draw_net_proj(surf, cx, cy, frame=0):
    spin = frame * 0.2
    r = 14
    for a in [spin, spin+1.1, spin+2.2, spin+3.3]:
        x1 = int(cx + math.cos(a)*r)
        y1 = int(cy + math.sin(a)*r)
        x2 = int(cx + math.cos(a+math.pi)*r)
        y2 = int(cy + math.sin(a+math.pi)*r)
        pygame.draw.line(surf, NET_BR, (x1,y1), (x2,y2), 2)
    pygame.draw.circle(surf, NET_BR, (int(cx), int(cy)), r, 2)
    pygame.draw.circle(surf, lt(NET_BR, 30), (int(cx), int(cy)), 4)


# ══════════════════════════════════════════════════════════════════════
#  DRAWING — PLATFORM (Zone 1 snowy)
# ══════════════════════════════════════════════════════════════════════
def draw_platform_snow(surf, rect, cam_x=0, cam_y=0):
    r = pygame.Rect(rect.x - cam_x, rect.y - cam_y, rect.width, rect.height)
    if r.right < 0 or r.left > SCREEN_W or r.bottom < 0 or r.top > SCREEN_H:
        return
    # body
    pygame.draw.rect(surf, PLAT_B, r, border_radius=3)
    # top snow layer
    snow_r = pygame.Rect(r.x, r.y, r.width, min(12, r.height))
    pygame.draw.rect(surf, PLAT_T, snow_r, border_radius=3)
    # edge shading
    pygame.draw.rect(surf, PLAT_E, r, 2, border_radius=3)
    # snow bumps on top
    for i in range(0, r.width - 20, 22):
        pygame.draw.ellipse(surf, SNOW_W,
            pygame.Rect(r.x + i + 2, r.y - 4, 18, 10))


# ══════════════════════════════════════════════════════════════════════
#  DRAWING — PLATFORM (Zone 2 cave)
# ══════════════════════════════════════════════════════════════════════
def draw_platform_cave(surf, rect, cam_x=0, cam_y=0):
    r = pygame.Rect(rect.x - cam_x, rect.y - cam_y, rect.width, rect.height)
    if r.right < 0 or r.left > SCREEN_W or r.bottom < 0 or r.top > SCREEN_H:
        return
    pygame.draw.rect(surf, CAVE_PT, r, border_radius=3)
    pygame.draw.rect(surf, lt(CAVE_PT, 18), pygame.Rect(r.x, r.y, r.width, 8), border_radius=3)
    pygame.draw.rect(surf, CAVE_PE, r, 2, border_radius=3)
    # warm glow on top
    gsurf = pygame.Surface((r.width, 6), pygame.SRCALPHA)
    gsurf.fill((255, 140, 40, 40))
    surf.blit(gsurf, (r.x, r.y - 2))


# ══════════════════════════════════════════════════════════════════════
#  DRAWING — VOLCANO
# ══════════════════════════════════════════════════════════════════════
def draw_volcano(surf, wx, wy, cam_x, frame=0):
    sx = wx - cam_x
    sy = wy
    if sx < -250 or sx > SCREEN_W + 50:
        return
    pulse = 0.5 + 0.5 * math.sin(frame * 0.1)
    # mountain body
    pts = [(sx, sy+180), (sx+60, sy+40), (sx+100, sy+5),
           (sx+140, sy+40), (sx+200, sy+180)]
    pygame.draw.polygon(surf, (65, 40, 35), pts)
    pygame.draw.polygon(surf, (48, 28, 22), pts, 3)
    # snow patches on sides
    pygame.draw.polygon(surf, (210, 228, 250, 180),
        [(sx+60, sy+40), (sx+75, sy+18), (sx+88, sy+40)])
    pygame.draw.polygon(surf, (210, 228, 250, 180),
        [(sx+112, sy+40), (sx+125, sy+18), (sx+140, sy+40)])
    # crater rim
    pygame.draw.ellipse(surf, (50, 30, 25), pygame.Rect(sx+75, sy+8, 50, 20))
    # crater glow
    gsurf = pygame.Surface((60, 30), pygame.SRCALPHA)
    alpha = int(180 + pulse * 60)
    pygame.draw.ellipse(gsurf, (255, 80, 0, alpha), pygame.Rect(0, 0, 60, 30))
    surf.blit(gsurf, (sx+72, sy+6))
    # eruption flames
    for i in range(5):
        t = (frame * 0.08 + i * 0.55) % 1.0
        fx = sx + 90 + math.sin(frame*0.15 + i) * 18
        fy = sy + 18 - t * 80
        fr = max(2, int((1-t) * 14))
        col = (255, int(60 + t*120), 0)
        fsurf = pygame.Surface((fr*2+2, fr*2+2), pygame.SRCALPHA)
        pygame.draw.circle(fsurf, (*col, int(220*(1-t))), (fr+1, fr+1), fr)
        surf.blit(fsurf, (int(fx)-fr-1, int(fy)-fr-1))


# ══════════════════════════════════════════════════════════════════════
#  DRAWING — TUBE / PIPE
# ══════════════════════════════════════════════════════════════════════
def draw_tube(surf, wx, wy, cam_x):
    sx = wx - cam_x
    sy = wy
    # main pipe body
    pygame.draw.rect(surf, (30, 140, 55), pygame.Rect(sx, sy, 56, 60), border_radius=4)
    pygame.draw.rect(surf, (22, 110, 40), pygame.Rect(sx, sy, 56, 60), 3, border_radius=4)
    # pipe rim (top lip)
    pygame.draw.rect(surf, (30, 155, 60), pygame.Rect(sx-6, sy, 68, 18), border_radius=5)
    pygame.draw.rect(surf, (18, 110, 38), pygame.Rect(sx-6, sy, 68, 18), 3, border_radius=5)
    # highlight
    pygame.draw.rect(surf, (60, 200, 90), pygame.Rect(sx+6, sy+4, 10, 50), border_radius=3)
    # down arrow hint
    arrowY = sy - 22
    pygame.draw.polygon(surf, (255, 235, 60),
        [(sx+28, arrowY+14), (sx+14, arrowY), (sx+42, arrowY)])


# ══════════════════════════════════════════════════════════════════════
#  DRAWING — CAVE ENTRANCE
# ══════════════════════════════════════════════════════════════════════
def draw_cave_entrance(surf, wx, wy, cam_x, frame=0):
    sx = wx - cam_x
    sy = wy
    if sx < -200 or sx > SCREEN_W + 50:
        return
    pulse = 0.5 + 0.5 * math.sin(frame * 0.07)
    # outer glow
    gsurf = pygame.Surface((200, 200), pygame.SRCALPHA)
    pygame.draw.ellipse(gsurf, (255, 140, 40, int(50*pulse)),
        pygame.Rect(0, 0, 200, 200))
    surf.blit(gsurf, (sx - 20, sy - 30))
    # rocky frame
    frame_pts = [(sx-20, sy+130), (sx-15, sy+20), (sx+10, sy-20),
                 (sx+75, sy-35), (sx+140, sy-20), (sx+155, sy+20),
                 (sx+160, sy+130)]
    pygame.draw.polygon(surf, (55, 45, 38), frame_pts)
    # dark opening
    arc_pts = [(sx+5, sy+125), (sx+8, sy+35),
               (sx+75, sy-15), (sx+142, sy+35), (sx+145, sy+125)]
    pygame.draw.polygon(surf, (12, 7, 3), arc_pts)
    # warm glow inside
    igsurf = pygame.Surface((140, 130), pygame.SRCALPHA)
    pygame.draw.ellipse(igsurf, (255, 130, 40, int(90*pulse)),
        pygame.Rect(0, 0, 140, 130))
    surf.blit(igsurf, (sx + 5, sy - 5))
    # snow on arch
    pygame.draw.polygon(surf, (215, 232, 255),
        [(sx-14, sy+22), (sx+10, sy-18), (sx+75, sy-33),
         (sx+140, sy-18), (sx+158, sy+22), (sx+148, sy+28),
         (sx+75, sy-22), (sx+10, sy-8), (sx-4, sy+28)])
    # label
    if abs(sx - SCREEN_W//2) < 350:
        txt(surf, "ENTER CAVE  [DOWN]", FONT_SM, GOLD, sx+75, sy-50)


# ══════════════════════════════════════════════════════════════════════
#  DRAWING — TREASURE CHEST
# ══════════════════════════════════════════════════════════════════════
def draw_treasure_chest(surf, wx, wy, cam_x, frame=0, open_=False):
    sx = wx - cam_x
    sy = wy
    if sx < -100 or sx > SCREEN_W + 50:
        return
    pulse = 0.5 + 0.5 * math.sin(frame * 0.09)
    # glow
    gsurf = pygame.Surface((120, 80), pygame.SRCALPHA)
    pygame.draw.ellipse(gsurf, (255, 200, 50, int(60*pulse)), pygame.Rect(0, 0, 120, 80))
    surf.blit(gsurf, (sx - 25, sy - 10))
    # body
    pygame.draw.rect(surf, (130, 80, 25), pygame.Rect(sx, sy+22, 70, 36), border_radius=4)
    pygame.draw.rect(surf, (90, 55, 14),  pygame.Rect(sx, sy+22, 70, 36), 2, border_radius=4)
    # lid
    lid_angle = -0.85 if open_ else 0
    if open_:
        # Draw open lid angled back
        lid_pts = [(sx, sy+22), (sx+70, sy+22),
                   (sx+70, sy+22+int(math.cos(lid_angle)*22)),
                   (sx, sy+22+int(math.cos(lid_angle)*22))]
        pygame.draw.polygon(surf, (155, 95, 28), lid_pts)
    else:
        pygame.draw.rect(surf, (155, 95, 28), pygame.Rect(sx, sy, 70, 24), border_radius=4)
    pygame.draw.rect(surf, (90, 55, 14),  pygame.Rect(sx, sy, 70, 24), 2, border_radius=4)
    # lock
    pygame.draw.circle(surf, (220, 185, 30), (sx+35, sy+12), 8)
    pygame.draw.circle(surf, (170, 130, 15), (sx+35, sy+12), 5)
    # gold trim
    pygame.draw.line(surf, (220, 185, 30), (sx, sy+22), (sx+70, sy+22), 3)
    # sparkles when open
    if open_:
        for i in range(8):
            a2 = (i / 8) * math.pi * 2 + frame * 0.06
            r2 = 35 + math.sin(frame*0.14+i) * 10
            sx2 = int(sx + 35 + math.cos(a2)*r2)
            sy2 = int(sy + 10 + math.sin(a2)*r2)
            pygame.draw.circle(surf, (255, int(150+i*10), 50), (sx2, sy2), 4)


# ══════════════════════════════════════════════════════════════════════
#  DRAWING — ICE BRIDGE
# ══════════════════════════════════════════════════════════════════════
def draw_ice_bridge(surf, rect, cam_x, build_progress=1.0, frame=0):
    """build_progress 0..1 — bridge forms left to right."""
    draw_w = int(rect.width * build_progress)
    if draw_w <= 0:
        return
    r = pygame.Rect(rect.x - cam_x, rect.y - cam_y_global, draw_w, rect.height)
    # ice body
    isurf = pygame.Surface((draw_w, rect.height), pygame.SRCALPHA)
    isurf.fill((150, 220, 255, 180))
    # sparkle pattern
    for i in range(0, draw_w, 18):
        for j in range(0, rect.height, 14):
            if (i + j) % 2 == 0:
                pygame.draw.circle(isurf, (200, 240, 255, 120), (i, j), 3)
    surf.blit(isurf, (r.x, r.y))
    pygame.draw.rect(surf, ICE_BL, r, 2, border_radius=4)
    # Glinting sparkle dots along the top edge — clearly not spikes
    for i in range(6, draw_w - 4, 18):
        bx = r.x + i
        by = r.y + 2
        twinkle = 0.5 + 0.5 * math.sin(frame * 0.18 + i * 0.4)
        radius = max(1, int(2 + twinkle * 2))
        brightness = int(200 + twinkle * 55)
        pygame.draw.circle(surf, (brightness, 245, 255), (bx, by), radius)


cam_y_global = 0  # horizontal camera only; y is fixed

# ══════════════════════════════════════════════════════════════════════
#  DRAWING — FOX JAIL CELL
# ══════════════════════════════════════════════════════════════════════
def draw_jail_cell(surf, cx, cy, open_=False):
    w, h = 180, 200
    rx = cx - w//2
    ry = cy - h//2
    # bars
    bar_color = (80, 80, 100)
    bar_cols = 7
    for i in range(bar_cols):
        x = rx + 10 + i * (w - 20) // (bar_cols - 1)
        bar_h = h if not (open_ and i == bar_cols//2) else h//2
        pygame.draw.rect(surf, bar_color, pygame.Rect(x-4, ry, 8, bar_h), border_radius=4)
    # frame
    pygame.draw.rect(surf, dk(bar_color, 10), pygame.Rect(rx, ry, w, h), 6, border_radius=6)
    # lock (gone when open)
    if not open_:
        pygame.draw.circle(surf, (180, 150, 20), (cx, ry + h//2), 10)

# ══════════════════════════════════════════════════════════════════════
#  GAME ENTITIES
# ══════════════════════════════════════════════════════════════════════

class Platform:
    def __init__(self, x, y, w, h=25):
        self.rect = pygame.Rect(x, y, w, h)
        self.is_cave = False


class Spike:
    def __init__(self, cx, y):
        self.cx = cx
        self.y = y  # bottom of spikes
        self.rect = pygame.Rect(cx - 26, y - 36, 52, 36)


class Coin:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x - 9, y - 9, 18, 18)
        self.collected = False
        self.cx = x
        self.cy = y


class Tube:
    def __init__(self, x, y, dest_x, dest_y):
        self.rect = pygame.Rect(x, y, 56, 60)
        self.wx = x
        self.wy = y
        self.dest_x = dest_x
        self.dest_y = dest_y
        self.in_range = False


class IceBridge:
    def __init__(self, x, y, w=220):
        self.rect = pygame.Rect(x, y, w, 16)
        self.life = 480   # 8 seconds
        self.max_life = 480
        self.build_timer = 45
        self.build_max = 45

    @property
    def build_progress(self):
        return 1.0 - (self.build_timer / self.build_max)

    def update(self):
        if self.build_timer > 0:
            self.build_timer -= 1
        self.life -= 1
        return self.life > 0


class LavaPool:
    """Ground-level lava pool that flows from the volcano base rightward.
    Much more readable for young players — you can see it, jump over it,
    or use the ice bridge.  Replaces the old screen-filling lava wall."""

    ANCHOR_X  = 3295   # world x where pool starts (right foot of volcano)
    MAX_WIDTH = 220    # max rightward spread in pixels — clearly jumpable
    GROW_RATE = 0.25   # px per frame; fully grown in ~15 seconds
    HEIGHT    = 30     # pool height above ground

    def __init__(self):
        self.active = False
        self.width  = 0.0    # current pool width, grows rightward

    @property
    def rect(self):
        return pygame.Rect(self.ANCHOR_X, GROUND_Y - self.HEIGHT,
                           max(1, int(self.width)), self.HEIGHT + 50)

    def update(self):
        if self.active:
            self.width = min(self.MAX_WIDTH, self.width + self.GROW_RATE)

    def draw(self, surf, cam_x, frame):
        if self.width < 2:
            return
        pool_x = self.ANCHOR_X - cam_x
        pool_w = int(self.width)
        pool_y = GROUND_Y - self.HEIGHT

        if pool_x + pool_w < 0 or pool_x > SCREEN_W:
            return

        # Base fill — deep red
        pygame.draw.rect(surf, LAVA_R,
            pygame.Rect(int(pool_x), pool_y, pool_w, self.HEIGHT + 50))

        # Bright molten orange core
        if pool_w > 6:
            pygame.draw.rect(surf, LAVA_O,
                pygame.Rect(int(pool_x) + 2, pool_y + 4, pool_w - 4, self.HEIGHT - 6))

        # Animated wavy top surface
        pulse = 0.5 + 0.5 * math.sin(frame * 0.14)
        pts = [(int(pool_x), pool_y + self.HEIGHT),
               (int(pool_x), pool_y + 4)]
        for i in range(0, pool_w + 1, 8):
            wx_s = pool_x + i
            wy_s = pool_y + 4 + int(math.sin(frame * 0.18 + i * 0.3) * 5)
            pts.append((int(wx_s), int(wy_s)))
        pts.append((int(pool_x) + pool_w, pool_y + self.HEIGHT))
        try:
            pygame.draw.polygon(surf, LAVA_Y, pts)
        except Exception:
            pass

        # Hot yellow glints bubbling on the surface
        for gi in range(0, pool_w, 25):
            gx = pool_x + gi + int(math.sin(frame * 0.12 + gi) * 6)
            gy = pool_y + 7
            gr = max(2, int(4 + math.sin(frame * 0.22 + gi * 0.5) * 2))
            brightness = int(215 + pulse * 40)
            pygame.draw.circle(surf, (brightness, 220, 0), (int(gx), int(gy)), gr)

        # Lava stream flowing down the volcano's right slope into the pool
        stream_sx = (3100 + 135) - cam_x   # world x=3235, right crater edge
        stream_sy = GROUND_Y - 185 + 12    # just below crater rim
        stream_ex = pool_x                 # pool left edge (screen space)
        stream_ey = pool_y                 # top of pool
        if stream_sx < SCREEN_W + 80 and stream_ex > -80:
            for ti in range(9):
                t = ti / 8
                lx = int(stream_sx + (stream_ex - stream_sx) * t)
                ly = int(stream_sy + (stream_ey - stream_sy) * t)
                flow_off = int(math.sin(frame * 0.2 + t * 4) * 3)
                r = max(3, int(4 + t * 10))
                red_fade = int(t * 35)
                col = (255, max(0, 80 - red_fade), 0)
                pygame.draw.circle(surf, col, (lx + flow_off, ly), r)


class NetProjectile:
    def __init__(self, x, y, vx, vy):
        self.x = float(x); self.y = float(y)
        self.vx = vx; self.vy = vy
        self.life = 120
        self.frame = 0
        self.rect = pygame.Rect(int(x)-14, int(y)-14, 28, 28)

    def update(self):
        self.x += self.vx; self.y += self.vy
        self.vy += 0.08
        self.life -= 1; self.frame += 1
        self.rect.center = (int(self.x), int(self.y))
        return self.life > 0


class PolarBear:
    def __init__(self, x, y, patrol_min, patrol_max, speed=1.4):
        self.x = float(x); self.y = float(y)
        self.w = 60; self.h = 72
        self.rect = pygame.Rect(int(x), int(y) - self.h, self.w, self.h)
        self.patrol_min = patrol_min
        self.patrol_max = patrol_max
        self.speed = speed
        self.vx = speed
        self.facing_right = True
        self.anim = 0
        self.chase_speed = 1.6    # kid-friendly: was 2.8
        self.chasing = False

    def update(self, player_x, player_y):
        dx = abs((self.rect.centerx) - player_x)
        dy = abs((self.rect.centery) - player_y)
        self.chasing = dx < 200 and dy < 130    # kid-friendly: shorter detection (was 320/180)

        spd = self.chase_speed if self.chasing else self.speed
        if self.chasing:
            self.vx = spd if player_x > self.rect.centerx else -spd
        else:
            if self.rect.left <= self.patrol_min:
                self.vx = spd
            elif self.rect.right >= self.patrol_max:
                self.vx = -spd

        self.facing_right = self.vx > 0
        self.rect.x += int(self.vx)
        self.anim += 1

    def draw(self, surf, cam_x, frame):
        draw_polar_bear(surf, self.rect.centerx - cam_x, self.rect.bottom, self.facing_right, self.anim)


class HumanGuard:
    def __init__(self, x, y, detect_range=250):
        self.x = x; self.y = y
        self.w = 44; self.h = 68
        self.rect = pygame.Rect(x - self.w//2, y - self.h, self.w, self.h)
        self.detect_range = detect_range
        self.facing_right = True
        self.alert = False
        self.throw_cd = 0
        self.throw_interval = 320    # kid-friendly: throws much less often (was 190)
        self.frame = 0
        self.nets = []
        self.caught_timer = 0  # >0 = net just hit
        self.gender = random.choice(['male', 'female'])

    def update(self, player_rect):
        self.frame += 1
        self.throw_cd = max(0, self.throw_cd - 1)
        pc = player_rect.centerx
        gc = self.rect.centerx
        dist = abs(pc - gc)
        dy = abs(player_rect.centery - self.rect.centery)
        self.alert = dist < self.detect_range and dy < 200
        self.facing_right = pc > gc

        if self.alert and self.throw_cd <= 0:
            dx = pc - gc
            dy2 = player_rect.centery - self.rect.centery
            length = max(1, math.hypot(dx, dy2))
            spd = 2.5    # kid-friendly: slower nets (was 4.0) — easier to dodge
            self.nets.append(NetProjectile(gc, self.rect.centery,
                dx/length*spd, dy2/length*spd))
            self.throw_cd = self.throw_interval

        self.nets = [n for n in self.nets if n.update()]

    def draw(self, surf, cam_x):
        draw_human(surf, self.rect.centerx - cam_x, self.rect.bottom,
                   self.facing_right, self.alert, self.frame, self.gender)
        for n in self.nets:
            draw_net_proj(surf, n.x - cam_x, n.y, n.frame)


class FoxFriend:
    def __init__(self, x, y, color, scale, zone=2):
        self.x = float(x); self.y = float(y)
        self.color = color
        self.scale = scale
        self.anim = random.uniform(0, 100)
        self.vx = random.choice([-1, 1]) * random.uniform(0.4, 1.4)
        self.vy = 0.0
        self.facing_right = self.vx > 0
        self.rect = pygame.Rect(int(x)-int(20*scale), int(y)-int(50*scale),
                                int(40*scale), int(50*scale))
        self.bounce_offset = 0.0
        self.bounce_phase = random.uniform(0, math.pi*2)
        self.on_ground = False

    def update(self, platforms):
        self.vy += GRAVITY * 0.5
        self.vy = min(self.vy, 12)
        self.x += self.vx
        self.y += self.vy
        self.rect.x = int(self.x - self.rect.width//2)
        self.rect.y = int(self.y - self.rect.height)
        self.on_ground = False
        # Ground floor fallback
        if self.rect.bottom >= GROUND_Y:
            self.rect.bottom = GROUND_Y
            self.y = float(GROUND_Y)
            self.vy = 0
            self.on_ground = True
        for p in platforms:
            if self.rect.colliderect(p.rect):
                if self.vy >= 0 and self.rect.bottom - self.vy <= p.rect.top + 8:
                    self.rect.bottom = p.rect.top
                    self.y = float(self.rect.bottom)
                    self.vy = 0
                    self.on_ground = True
        # bounce gently
        if self.on_ground:
            self.bounce_offset = math.sin(self.bounce_phase) * 4
            self.bounce_phase += 0.08
            # random direction change
            if random.random() < 0.005:
                self.vx = -self.vx
        self.facing_right = self.vx >= 0
        self.anim += 1

    def draw(self, surf, cam_x):
        draw_fox(surf, self.rect.centerx - cam_x,
                 self.rect.bottom + int(self.bounce_offset),
                 self.facing_right, self.anim, self.scale, self.color, False)


# ══════════════════════════════════════════════════════════════════════
#  PLAYER (Ella)
# ══════════════════════════════════════════════════════════════════════
class Player:
    W, H = 38, 52

    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y - self.H, self.W, self.H)
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False
        self.facing_right = True
        self.anim = 0
        self.dead = False
        self.score = 0
        self.has_ice = True
        self.ice_bridges = []
        self.ice_cooldown = 0
        self.jail_checkpoint_x = x
        self.jail_checkpoint_y = y

    def center(self):
        return self.rect.centerx, self.rect.centery

    def handle_input(self, keys):
        self.vx = 0
        if keys[pygame.K_LEFT]:
            self.vx = -MOVE_SPEED
            self.facing_right = False
        if keys[pygame.K_RIGHT]:
            self.vx = MOVE_SPEED
            self.facing_right = True
        if (keys[pygame.K_UP] or keys[pygame.K_SPACE]) and self.on_ground:
            self.vy = JUMP_VEL
            self.on_ground = False
            particles.burst(self.rect.centerx, self.rect.bottom, SNOW_W, 8, 3, 3, 20, -0.05)

    def use_ice(self):
        """Create ice bridge ahead of player if no ground below."""
        if self.ice_cooldown > 0 or not self.has_ice:
            return False
        # Spawn bridge 10px ahead in facing direction at player feet
        bx = self.rect.right + 10 if self.facing_right else self.rect.left - 230
        by = self.rect.bottom - 16
        bridge = IceBridge(bx, by, 220)
        self.ice_bridges.append(bridge)
        self.ice_cooldown = 300  # 5 sec recharge
        particles.burst(self.rect.centerx, self.rect.bottom,
                        ICE_BL, 25, 5, 5, 55, -0.15)
        return True

    def update(self, platforms, spikes, coins, tubes, lava_wall=None):
        self.ice_cooldown = max(0, self.ice_cooldown - 1)

        # Update ice bridges
        self.ice_bridges = [b for b in self.ice_bridges if b.update()]
        for b in self.ice_bridges:
            if b.build_progress < 0.5:
                particles.burst(
                    b.rect.x + int(b.rect.width * b.build_progress),
                    b.rect.y, ICE_BL, 3, 2, 3, 20, 0)

        # Gravity
        self.vy += GRAVITY
        if self.vy > MAX_FALL:
            self.vy = MAX_FALL

        # Move X
        self.rect.x += int(self.vx)
        self.rect.x = max(0, self.rect.x)
        for p in platforms + [b.rect for b in self.ice_bridges]:
            pr = p if isinstance(p, pygame.Rect) else p.rect
            if self.rect.colliderect(pr):
                if self.vx > 0:
                    self.rect.right = pr.left
                elif self.vx < 0:
                    self.rect.left = pr.right

        # Move Y
        self.rect.y += int(self.vy)
        self.on_ground = False
        # Y collision — all platforms are one-way: land on top, jump through from below
        all_rects = [p.rect for p in platforms] + [b.rect for b in self.ice_bridges]
        for pr in all_rects:
            if self.rect.colliderect(pr) and self.vy > 0:
                # Only land if the player's feet were above (or very near) the platform top
                # before this frame's movement — prevents sticking from the side
                if self.rect.bottom - self.vy <= pr.top + 10:
                    self.rect.bottom = pr.top
                    self.vy = 0
                    self.on_ground = True

        # Kill zone (fall off screen)
        if self.rect.top > SCREEN_H + 60:
            self.dead = True
            return

        # Spike check
        for s in spikes:
            if self.rect.colliderect(s.rect):
                self.dead = True
                return

        # Coin collection
        for c in coins:
            if not c.collected and self.rect.colliderect(c.rect):
                c.collected = True
                self.score += 10    # kid-friendly: double coin value (was 5) — more reward!
                particles.burst(c.cx, c.cy, COIN_Y, 10, 3, 4, 30, 0)

        # Tube check
        for tube in tubes:
            if self.rect.colliderect(tube.rect):
                tube.in_range = True
            else:
                tube.in_range = False

        # Lava pool — die if Ella steps into the ground-level pool
        if lava_wall and lava_wall.active and lava_wall.width > 2:
            if self.rect.colliderect(lava_wall.rect):
                self.dead = True
                return

        self.anim += 1

    def draw(self, surf, cam_x):
        draw_fox(surf, self.rect.centerx - cam_x, self.rect.bottom,
                 self.facing_right, self.anim, 1.0, FOX_OR, True)
        # draw ice bridges
        for b in self.ice_bridges:
            draw_ice_bridge(surf, b.rect, cam_x, b.build_progress, self.anim)

        # ice power HUD indicator
        if self.ice_cooldown > 0:
            frac = 1 - self.ice_cooldown / 300
            bar_r = pygame.Rect(SCREEN_W - 140, 20, 120, 14)
            pygame.draw.rect(surf, (30, 30, 50), bar_r, border_radius=7)
            pygame.draw.rect(surf, ICE_BL,
                pygame.Rect(bar_r.x, bar_r.y, int(bar_r.width * frac), bar_r.height),
                border_radius=7)
            pygame.draw.rect(surf, lt(ICE_BL), bar_r, 2, border_radius=7)
            txt(surf, "ICE", FONT_XS, ICE_BL, SCREEN_W-180, 27, shadow=False)
        else:
            txt(surf, "[X] ICE READY", FONT_XS, ICE_BL, SCREEN_W - 85, 27, shadow=False)


# ══════════════════════════════════════════════════════════════════════
#  LEVEL DATA
# ══════════════════════════════════════════════════════════════════════
GROUND_Y = 585   # top of ground / floor

def make_z1_platforms():
    P = []
    def p(x, y, w, h=25): P.append(Platform(x, y, w, h))

    # ── Ground segments (with deliberate gaps) ──
    p(0,      GROUND_Y, 620, 40)
    p(700,    GROUND_Y, 280, 40)   # gap: 620-700
    p(1060,   GROUND_Y, 350, 40)   # gap: 980-1060
    p(1500,   GROUND_Y, 560, 40)
    p(2150,   GROUND_Y, 180, 40)   # gap: 2060-2150
    p(2420,   GROUND_Y, 350, 40)   # gap: 2330-2420  ← ICE BRIDGE SPOT
    p(2870,   GROUND_Y, 220, 40)
    p(3170,   GROUND_Y, 900, 40)   # volcano section ground
    p(4160,   GROUND_Y, 320, 40)
    p(4570,   GROUND_Y, 260, 40)   # gap
    p(4910,   GROUND_Y, 420, 40)
    p(5420,   GROUND_Y, 360, 40)
    p(5870,   GROUND_Y, 530, 40)   # final stretch
    # ── Elevated platforms ──────────────────────────────────────
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

def make_z1_spikes():
    # Kid-friendly: reduced from 32 spikes to 11 — well spaced, never near zone start
    S = []
    for cx in [1320, 2000, 2930,
               3600,              # volcano section
               4650, 5100, 5750]:
        S.append(Spike(cx, GROUND_Y))
    # just a few elevated spikes to teach the mechanic
    for cx in [1750, 3520, 5020]:
        S.append(Spike(cx, GROUND_Y - 80 + 20))
    return S

def make_z1_coins():
    coins = []
    positions = [
        # ground level
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
        # elevated
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

def make_z1_bears():
    # Kid-friendly: 4 bears (down from 7), all slower patrol speed
    bears = []
    data = [
        (1600, GROUND_Y, 1510, 1810, 1.0),
        (3400, GROUND_Y, 3220, 3680, 1.1),  # volcano section
        (4700, GROUND_Y, 4590, 4870, 1.0),
        (5700, GROUND_Y, 5640, 5950, 0.9),
    ]
    for (x, y, mn, mx, spd) in data:
        bears.append(PolarBear(x, y, mn, mx, spd))
    return bears

def make_z1_guards():
    # Kid-friendly: 2 guards (down from 3), shorter detection range
    guards = []
    guards.append(HumanGuard(2300, GROUND_Y, 180))
    guards.append(HumanGuard(4400, GROUND_Y, 170))
    return guards

def make_z1_tubes():
    tubes = []
    # Tube A at x=2700 → Tube B at x=3300 (skips over gap/volcano approach)
    tubes.append(Tube(2720, GROUND_Y - 60, 3350, GROUND_Y))
    return tubes


def make_z2_platforms():
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
    p(3850, g, 550, 40)   # treasure here

    # elevated
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

def make_z2_spikes():
    # Kid-friendly: reduced from 16 spikes to 6 — clear paths always available
    S = []
    g = GROUND_Y
    for cx in [1140, 2140, 3180]:
        S.append(Spike(cx, g))
    for cx in [870, 2410, 3240]:
        S.append(Spike(cx, g - 80 + 20))
    return S

def make_z2_coins():
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
        # elevated
        (130,g-155),(310,g-205),(670,g-165),
        (1160,g-185),(1365,g-125),(1620,g-185),
        (1835,g-135),(2165,g-195),(2395,g-145),
        (2765,g-185),(2975,g-125),(3215,g-185),
        (3465,g-135),(3715,g-175),(3915,g-115),
    ]
    for (x, y) in positions:
        coins.append(Coin(x, y))
    return coins

FOX_FRIEND_COLORS = [
    FOX_OR, (140, 55, 12), (245, 165, 35), (255, 255, 255),
    (165, 170, 178), (50, 28, 14), (255, 108, 52), (196, 48, 40),
    (108, 72, 10), (244, 230, 140), (255, 145, 95), (168, 36, 18),
    (255, 215, 0),  (160, 80, 38), (222, 180, 140),
    (255, 68, 0),   (100, 65, 30), (255, 158, 118), (210, 105, 30),
    (188, 143, 95), (255, 140, 200),(140, 255, 200),(140, 170, 255),
]

def make_fox_friends():
    friends = []
    g = GROUND_Y
    positions = []
    for x in range(200, 4200, 60):
        positions.append(x)
    random.shuffle(positions)
    for i, x in enumerate(positions[:80]):
        col = FOX_FRIEND_COLORS[i % len(FOX_FRIEND_COLORS)]
        scale = random.uniform(0.32, 0.85)
        y = g
        friends.append(FoxFriend(x, y, col, scale))
    return friends


# ══════════════════════════════════════════════════════════════════════
#  BACKGROUND RENDERERS
# ══════════════════════════════════════════════════════════════════════
_snow_cache = []

def build_snow_cache(count=200):
    global _snow_cache
    _snow_cache = [{'x': random.uniform(0, SCREEN_W),
                    'y': random.uniform(0, SCREEN_H),
                    'r': random.uniform(0.8, 2.5),
                    'vy': random.uniform(0.5, 1.5),
                    'vx': random.uniform(-0.3, 0.3),
                    'op': random.uniform(0.2, 0.7)} for _ in range(count)]

build_snow_cache()

def update_snow():
    for s in _snow_cache:
        s['y'] += s['vy']
        s['x'] += s['vx']
        if s['y'] > SCREEN_H + 6:
            s['y'] = -4
            s['x'] = random.uniform(0, SCREEN_W)
        if s['x'] < -4 or s['x'] > SCREEN_W + 4:
            s['x'] = random.uniform(0, SCREEN_W)

def draw_zone1_bg(surf, cam_x, frame):
    # Sky gradient
    for y in range(0, SCREEN_H, 4):
        t = y / SCREEN_H
        c = tuple(int(SKY_T[i] + (SKY_B[i]-SKY_T[i])*t) for i in range(3))
        pygame.draw.rect(surf, c, pygame.Rect(0, y, SCREEN_W, 4))

    # Far mountain silhouettes (parallax)
    def mtn_layer(scroll_x, color, base_frac, amplitude, count):
        base_y = int(SCREEN_H * base_frac)
        seg = (SCREEN_W + 300) // count
        pts = [(0, SCREEN_H)]
        for i in range(count + 2):
            x = -150 + i * seg + int(scroll_x) % (seg * 2)
            h = int(amplitude * (0.6 + 0.4 * math.sin(i * 2.1 + 0.5)))
            pts.append((x, base_y - h))
            pts.append((x + seg//2, base_y - h//2))
        pts.append((SCREEN_W + 50, SCREEN_H))
        if len(pts) >= 3:
            try: pygame.draw.polygon(surf, color, pts)
            except: pass
        # snow caps
        for i in range(0, len(pts)-2, 2):
            if pts[i][1] < base_y - amplitude * 0.6:
                cx2 = pts[i][0]
                cy2 = pts[i][1]
                pygame.draw.circle(surf, SNOW_W, (cx2, cy2), 18)

    mtn_layer(-cam_x * 0.08, (165, 195, 220), 0.55, 120, 6)
    mtn_layer(-cam_x * 0.18, (118, 155, 195), 0.65, 160, 8)

    # Snowy ground
    for y in range(int(SCREEN_H * 0.6), SCREEN_H, 3):
        t = (y - SCREEN_H*0.6) / (SCREEN_H*0.4)
        c = tuple(int(SNOW_W[i] + (SNOW_S[i]-SNOW_W[i])*t) for i in range(3))
        pygame.draw.rect(surf, c, pygame.Rect(0, y, SCREEN_W, 3))

    # Snowflakes (screen-space, no world parallax needed)
    for s in _snow_cache:
        op = s['op']
        c = (int(220*op+35), int(235*op+20), int(255*op))
        pygame.draw.circle(surf, c, (int(s['x']), int(s['y'])), max(1, int(s['r'])))


_cave_glow_cache = [(random.uniform(0, 4400), random.uniform(0, SCREEN_H),
                     random.uniform(20, 55), random.uniform(0, math.pi*2),
                     random.uniform(0.025, 0.06),
                     random.choice([28, 45, 200])) for _ in range(35)]

def draw_zone2_bg(surf, cam_x, frame):
    # Dark cave floor
    surf.fill(CAVE_BG)

    # Stone texture patches
    for i in range(0, SCREEN_W + 50, 14):
        for j in range(0, SCREEN_H + 20, 14):
            wx2 = i + cam_x
            wy2 = j
            h = (int(wx2//14)*31 + int(wy2//14)*37) % 5
            if h == 0:
                pygame.draw.rect(surf, CAVE_MD, pygame.Rect(i, j, 13, 13))

    # Ambient glow spots (crystals / torches)
    for (gx, gy, gr, phase, spd, hue) in _cave_glow_cache:
        sx2 = gx - cam_x
        if sx2 < -100 or sx2 > SCREEN_W + 100:
            continue
        bright = 0.5 + 0.5 * math.sin(phase + frame * spd)
        a = int(30 + bright * 35)
        r = int(gr * (1 + bright * 0.2))
        gsurf = pygame.Surface((r*2+2, r*2+2), pygame.SRCALPHA)
        if hue == 28:
            col = (255, 140, 40, a)
        elif hue == 45:
            col = (255, 200, 50, a)
        else:
            col = (80, 160, 255, a)
        pygame.draw.circle(gsurf, col, (r+1, r+1), r)
        surf.blit(gsurf, (int(sx2) - r - 1, int(gy) - r - 1))

    # Warm edge vignette
    for edge, axis in [('left', True), ('right', True), ('top', False), ('bottom', False)]:
        vs = pygame.Surface((80, SCREEN_H) if axis else (SCREEN_W, 80), pygame.SRCALPHA)
        vs.fill((0, 0, 0, 0))
        for xi in range(80):
            alpha = int(180 * (1 - xi/80)**2)
            col = (0, 0, 0, alpha)
            if axis:
                pygame.draw.line(vs, col, (xi if edge=='left' else 79-xi, 0),
                                 (xi if edge=='left' else 79-xi, SCREEN_H))
            else:
                pygame.draw.line(vs, col, (0, xi if edge=='top' else 79-xi),
                                 (SCREEN_W, xi if edge=='top' else 79-xi))
        if edge == 'left':   surf.blit(vs, (0, 0))
        elif edge == 'right': surf.blit(vs, (SCREEN_W-80, 0))
        elif edge == 'top':  surf.blit(vs, (0, 0))
        else:                surf.blit(vs, (0, SCREEN_H-80))

    # Crystal formations
    crystal_pos = [(150,GROUND_Y-20),(400,GROUND_Y-40),(750,GROUND_Y-25),
                   (1050,GROUND_Y-35),(1400,GROUND_Y-20),(1700,GROUND_Y-40),
                   (2050,GROUND_Y-25),(2400,GROUND_Y-30),(2750,GROUND_Y-20),
                   (3100,GROUND_Y-35),(3400,GROUND_Y-25),(3750,GROUND_Y-30)]
    for (wx2, wy2) in crystal_pos:
        sx2 = wx2 - cam_x
        if sx2 < -40 or sx2 > SCREEN_W + 40:
            continue
        p2 = 0.5 + 0.5*math.sin(frame*0.05 + wx2*0.01)
        for k in range(3):
            ang = k * 0.55 + p2 * 0.2
            pts = [(sx2, wy2), (sx2+int(6*math.cos(ang-0.3)), wy2+5),
                   (sx2+int(4*math.cos(ang)), wy2-int(18+k*4)),
                   (sx2+int(6*math.cos(ang+0.3)), wy2+5)]
            try: pygame.draw.polygon(surf, (int(180+p2*60), int(220+p2*30), 255), pts)
            except: pass

    # Torches on walls
    for tx2 in range(100, 4400, 320):
        for ty2 in [18, GROUND_Y - 10]:
            draw_torch_cave(surf, tx2 - cam_x, ty2, frame)


def draw_torch_cave(surf, sx, sy, frame):
    if sx < -20 or sx > SCREEN_W + 20:
        return
    pygame.draw.rect(surf, (88, 55, 22), pygame.Rect(sx-3, sy, 6, 14))
    pygame.draw.rect(surf, (66, 40, 14), pygame.Rect(sx-8, sy+10, 16, 5))
    p = 0.5 + 0.5*math.sin(frame*0.2 + sx*0.1)
    for i in range(3):
        fr = int((8-i*1.8) * (0.8+p*0.4))
        fy = sy - 6 - i*5 - int(p*4)
        col = (255, int(60+i*60+p*60), 0)
        fsurf = pygame.Surface((fr*2+2, fr*2+2), pygame.SRCALPHA)
        pygame.draw.circle(fsurf, (*col, int(220*(1-i*0.25))), (fr+1, fr+1), max(1,fr))
        surf.blit(fsurf, (sx-fr-1, fy-fr-1))
    # glow
    gs2 = pygame.Surface((60, 60), pygame.SRCALPHA)
    pygame.draw.circle(gs2, (255, 140, 40, int(40+p*30)), (30, 30), 30)
    surf.blit(gs2, (sx-30, sy-30))


# ══════════════════════════════════════════════════════════════════════
#  HUD
# ══════════════════════════════════════════════════════════════════════
def draw_hud(surf, score, zone_name, frame):
    # Score
    draw_rounded_rect(surf, (0,0,0,160), pygame.Rect(10, 10, 180, 38), 10)
    txt(surf, f"Score: {score}", FONT_SM, GOLD, 100, 29)
    # Zone label
    draw_rounded_rect(surf, (0,0,0,160), pygame.Rect(SCREEN_W//2-100, 10, 200, 38), 10)
    txt(surf, zone_name, FONT_SM, WHITE, SCREEN_W//2, 29)


# ══════════════════════════════════════════════════════════════════════
#  SCREENS
# ══════════════════════════════════════════════════════════════════════

def draw_leaderboard_block(surf, cx, y_start, scores, highlight_score=None):
    txt(surf, "TOP SCORES", FONT_MD, GOLD, cx, y_start)
    if not scores:
        txt(surf, "No scores yet!", FONT_SM, (180,180,180), cx, y_start+44)
        return
    for i, s in enumerate(scores):
        color = (255,220,60) if s['score'] == highlight_score else (
            (220,200,140) if i == 0 else WHITE)
        rank = ["#1", "#2", "#3", "#4", "#5"][i]
        line = f"{rank}  {s['initials']}  {s['score']:,}"
        txt(surf, line, FONT_SM, color, cx, y_start + 44 + i*34)


class MenuScreen:
    def __init__(self):
        self.frame = 0
        self.fox_anim = 0

    def update(self):
        self.frame += 1
        self.fox_anim += 1

    def draw(self, surf):
        # Background
        for y in range(0, SCREEN_H, 3):
            t = y / SCREEN_H
            c = tuple(int(SKY_T[i] + (SKY_B[i]-SKY_T[i])*t) for i in range(3))
            pygame.draw.rect(surf, c, pygame.Rect(0, y, SCREEN_W, 3))

        # Snowflakes
        update_snow()
        draw_zone1_bg(surf, 0, self.frame)

        # Title panel
        panel = pygame.Surface((680, 200), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 120))
        pygame.draw.rect(panel, (255, 200, 60, 60), panel.get_rect(), 3, border_radius=16)
        surf.blit(panel, (SCREEN_W//2 - 340, 100))

        pulse = 0.5 + 0.5*math.sin(self.frame*0.06)
        title_col = (int(255), int(200+pulse*40), int(50+pulse*30))
        txt(surf, "Ella's Cave", FONT_XL, title_col, SCREEN_W//2, 165)
        txt(surf, "A Fox's Snowy Adventure", FONT_SM, SNOW_W, SCREEN_W//2, 230)

        # Draw Ella on menu
        draw_fox(surf, SCREEN_W//2 - 160, 430, True, self.fox_anim, 1.2, FOX_OR, True)
        draw_fox(surf, SCREEN_W//2 + 160, 430, False, self.fox_anim+20, 0.85,
                 FOX_FRIEND_COLORS[2], False)

        # Buttons
        btn_y = 480
        blink = int(self.frame * 0.05) % 2 == 0
        txt(surf, ">  Press ENTER to Play", FONT_MD,
            GOLD if blink else lt(GOLD, 40), SCREEN_W//2, btn_y)
        txt(surf, "Move: Arrow Keys  |  Jump: UP or SPACE  |  Ice: [X]  |  Tube: [DOWN]",
            FONT_XS, (200, 220, 255), SCREEN_W//2, btn_y + 48)

        # Leaderboard preview
        scores = LEADERBOARD.top5()
        if scores:
            draw_leaderboard_block(surf, SCREEN_W//2, 580, scores)

    def handle(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            return 'start'
        return None


class GameOverScreen:
    def __init__(self, score, zone):
        self.score = score
        self.zone = zone
        self.frame = 0
        self.phase = 'show'  # 'show' | 'enter_initials'
        self.initials = ['A', 'A', 'A']
        self.cursor = 0
        self.qualifies = LEADERBOARD.qualifies(score)
        if self.qualifies:
            self.phase = 'enter_initials'

    def update(self):
        self.frame += 1
        update_snow()

    def draw(self, surf):
        # Background
        for y in range(0, SCREEN_H, 3):
            t = y / SCREEN_H
            c = tuple(int(SKY_T[i] + (SKY_B[i]-SKY_T[i])*t) for i in range(3))
            pygame.draw.rect(surf, c, pygame.Rect(0, y, SCREEN_W, 3))
        draw_zone1_bg(surf, 0, self.frame)

        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        surf.blit(overlay, (0, 0))

        txt(surf, "Oops!", FONT_XL, (255, 120, 60), SCREEN_W//2, 100)
        txt(surf, "Let's try again, Ella!", FONT_MD, WHITE, SCREEN_W//2, 165)
        txt(surf, f"Score: {self.score:,}", FONT_MD, GOLD, SCREEN_W//2, 215)

        if self.phase == 'enter_initials':
            txt(surf, "New High Score! Enter Your Initials:", FONT_SM, (255, 230, 120),
                SCREEN_W//2, 275)
            for i, ch in enumerate(self.initials):
                col = GOLD if i == self.cursor else WHITE
                bx = SCREEN_W//2 - 60 + i*60
                pygame.draw.rect(surf, (30,30,60), pygame.Rect(bx-20, 305, 40, 50), border_radius=8)
                if i == self.cursor:
                    pygame.draw.rect(surf, GOLD, pygame.Rect(bx-20, 305, 40, 50), 2, border_radius=8)
                txt(surf, ch, FONT_LG, col, bx, 330)
            txt(surf, "Type your initials  |  BACKSPACE: Delete  |  ENTER: Save & go to menu",
                FONT_XS, (180,180,180), SCREEN_W//2, 380)
            txt(surf, "ESC: Skip and return to main menu",
                FONT_XS, (150,150,150), SCREEN_W//2, 400)
        else:
            draw_leaderboard_block(surf, SCREEN_W//2, 270, LEADERBOARD.top5(), None)
            blink = int(self.frame * 0.05) % 2 == 0
            txt(surf, "ENTER: Play Again  |  M: Main Menu",
                FONT_MD, GOLD if blink else lt(GOLD, 40), SCREEN_W//2, 570)

    def handle(self, event):
        if event.type != pygame.KEYDOWN:
            return None
        k = event.key
        if self.phase == 'enter_initials':
            if event.unicode and event.unicode.upper() in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                # Direct typing — fill slot and advance cursor automatically
                self.initials[self.cursor] = event.unicode.upper()
                self.cursor = min(2, self.cursor + 1)
            elif k == pygame.K_BACKSPACE:
                # Step back and clear the previous slot
                self.cursor = max(0, self.cursor - 1)
                self.initials[self.cursor] = 'A'
            elif k == pygame.K_LEFT:
                self.cursor = max(0, self.cursor - 1)
            elif k == pygame.K_RIGHT:
                self.cursor = min(2, self.cursor + 1)
            elif k in (pygame.K_RETURN, pygame.K_KP_ENTER):
                LEADERBOARD.add(''.join(self.initials), self.score)
                return 'menu'   # score saved — go straight to main menu
            elif k == pygame.K_ESCAPE:
                return 'menu'   # skip saving — go straight to main menu
        else:
            if k in (pygame.K_RETURN, pygame.K_KP_ENTER):
                return 'retry'
            if k == pygame.K_m:
                return 'menu'
        return None


class WinScreen:
    def __init__(self, score, fox_friends):
        self.score = score
        self.fox_friends = fox_friends
        self.frame = 0
        self.qualifies = LEADERBOARD.qualifies(score)
        self.phase = 'enter_initials' if self.qualifies else 'celebrate'
        self.initials = ['A', 'A', 'A']
        self.cursor = 0
        self.confetti = []
        for _ in range(200):
            self.confetti.append({
                'x': random.uniform(0, SCREEN_W),
                'y': random.uniform(-SCREEN_H, 0),
                'vx': random.uniform(-2, 2),
                'vy': random.uniform(1.5, 4),
                'r': random.uniform(4, 10),
                'hue': random.randint(0, 360),
                'spin': random.uniform(-0.2, 0.2),
                'angle': random.uniform(0, math.pi*2),
                'shape': random.choice(['rect','circle'])
            })
        # center cam on treasure for friends
        self.cam_x = max(0, 1750 - SCREEN_W//2)
        self.z2_platforms = make_z2_platforms()

    def update(self):
        self.frame += 1
        for c in self.confetti:
            c['x'] += c['vx']
            c['y'] += c['vy']
            c['vy'] += 0.04
            c['angle'] += c['spin']
            if c['y'] > SCREEN_H + 20:
                c['y'] = -20
                c['x'] = random.uniform(0, SCREEN_W)
                c['vy'] = random.uniform(1.5, 3)
        if self.phase == 'celebrate':
            for f in self.fox_friends:
                f.update(self.z2_platforms)

    def draw(self, surf):
        # Cave background
        draw_zone2_bg(surf, self.cam_x, self.frame)

        if self.phase == 'celebrate':
            # Draw ALL fox friends
            for f in self.fox_friends:
                f.draw(surf, self.cam_x)
            # Draw Ella centered
            draw_fox(surf, SCREEN_W//2, GROUND_Y, True,
                     self.frame, 1.15, FOX_OR, True)

        # Confetti
        for c in self.confetti:
            color = pygame.Color(0)
            color.hsva = (c['hue'], 90, 90, 100)
            s = pygame.Surface((int(c['r']*2), int(c['r'])), pygame.SRCALPHA)
            if c['shape'] == 'rect':
                pygame.draw.rect(s, (*color[:3], 200), s.get_rect())
            else:
                pygame.draw.circle(s, (*color[:3], 200),
                    (int(c['r']), int(c['r']//2)), int(c['r']//2))
            rot = pygame.transform.rotate(s, math.degrees(c['angle']))
            surf.blit(rot, (int(c['x'])-rot.get_width()//2, int(c['y'])-rot.get_height()//2))

        # Panel overlay
        panel_h = 240 if self.phase == 'enter_initials' else 180
        panel = pygame.Surface((720, panel_h), pygame.SRCALPHA)
        panel.fill((0,0,0,160))
        pygame.draw.rect(panel, (255,200,60,80), panel.get_rect(), 3, border_radius=16)
        surf.blit(panel, (SCREEN_W//2-360, 50))

        pulse = 0.5 + 0.5*math.sin(self.frame*0.07)
        txt(surf, "YOU FOUND THE TREASURE!", FONT_LG,
            (int(255), int(200+pulse*40), int(50)), SCREEN_W//2, 100)
        txt(surf, f"Ella celebrates with all her fox friends!  Score: {self.score:,}",
            FONT_SM, WHITE, SCREEN_W//2, 148)

        if self.phase == 'enter_initials':
            txt(surf, "High Score! Enter Initials:", FONT_SM, (255,230,120), SCREEN_W//2, 195)
            for i, ch in enumerate(self.initials):
                col = GOLD if i == self.cursor else WHITE
                bx = SCREEN_W//2 - 60 + i*60
                pygame.draw.rect(surf, (30,30,60), pygame.Rect(bx-20, 218, 40, 50), border_radius=8)
                if i == self.cursor:
                    pygame.draw.rect(surf, GOLD, pygame.Rect(bx-20, 218, 40, 50), 2, border_radius=8)
                txt(surf, ch, FONT_LG, col, bx, 243)
            txt(surf, "Type your initials  |  BACKSPACE: Delete  |  ENTER: Save",
                FONT_XS, (180,180,180), SCREEN_W//2, 280)
            txt(surf, "ESC: Skip and return to main menu",
                FONT_XS, (150,150,150), SCREEN_W//2, 298)
        else:
            blink = int(self.frame*0.06) % 2 == 0
            txt(surf, "M - Main Menu  |  ENTER - Play Again",
                FONT_SM, GOLD if blink else lt(GOLD), SCREEN_W//2, 198)

        # Leaderboard on the side
        if self.phase == 'celebrate' and self.frame > 60:
            draw_leaderboard_block(surf, 120, 300, LEADERBOARD.top5())

    def handle(self, event):
        if event.type != pygame.KEYDOWN:
            return None
        k = event.key
        if self.phase == 'enter_initials':
            if event.unicode and event.unicode.upper() in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                # Direct typing — fill slot and advance cursor automatically
                self.initials[self.cursor] = event.unicode.upper()
                self.cursor = min(2, self.cursor + 1)
            elif k == pygame.K_BACKSPACE:
                # Step back and clear the previous slot
                self.cursor = max(0, self.cursor - 1)
                self.initials[self.cursor] = 'A'
            elif k == pygame.K_LEFT:
                self.cursor = max(0, self.cursor - 1)
            elif k == pygame.K_RIGHT:
                self.cursor = min(2, self.cursor + 1)
            elif k in (pygame.K_RETURN, pygame.K_KP_ENTER):
                LEADERBOARD.add(''.join(self.initials), self.score)
                return 'menu'   # score saved — go straight to main menu
            elif k == pygame.K_ESCAPE:
                return 'menu'   # skip saving — go straight to main menu
        else:
            if k == pygame.K_m:
                return 'menu'
            if k in (pygame.K_RETURN, pygame.K_KP_ENTER):
                return 'restart'
        return None


class FoxJailScreen:
    """Cutscene: Ella jailed → friend fox appears with key → freed."""
    PHASES = [
        (100, "Ella is caught in a net!"),
        (100, "A friend fox arrives..."),
        (80,  "The friend fox has a key!"),
        (80,  "Ella is FREE!"),
    ]

    def __init__(self, return_x, return_y, score):
        self.frame = 0
        self.phase = 0
        self.phase_timer = 0
        self.return_x = return_x
        self.return_y = return_y
        self.score = score
        self.friend_x = SCREEN_W + 80.0
        self.friend_target = SCREEN_W//2 + 100.0

    def update(self):
        self.frame += 1
        self.phase_timer += 1
        dur = self.PHASES[self.phase][0]
        if self.phase_timer >= dur:
            if self.phase < len(self.PHASES) - 1:
                self.phase += 1
                self.phase_timer = 0
        # Friend fox walks in
        if self.phase >= 1:
            self.friend_x += (self.friend_target - self.friend_x) * 0.06

    def draw(self, surf):
        # Background
        surf.fill(CAVE_BG)
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 80))
        surf.blit(overlay, (0, 0))

        center_x = SCREEN_W//2 - 80
        center_y = SCREEN_H//2

        # Jail cell
        open_cell = self.phase >= 3
        draw_jail_cell(surf, center_x, center_y, open_cell)

        # Ella inside (or just freed)
        if self.phase < 3:
            draw_fox(surf, center_x, center_y + 55, True, self.frame, 0.8, FOX_OR, False)
        else:
            # Ella walking out
            walk_x = center_x + (self.frame - self.PHASES[0][0] - self.PHASES[1][0] - self.PHASES[2][0]) * 2
            draw_fox(surf, min(walk_x, center_x + 200), center_y + 55, True,
                     self.frame * 2, 0.9, FOX_OR, True)

        # Friend fox with key
        if self.phase >= 1:
            fx = int(self.friend_x)
            draw_fox(surf, fx, center_y + 55, False, self.frame, 0.7, FOX_FRIEND_COLORS[2], False)
            if self.phase >= 2:
                # Draw key
                kx, ky = fx - 25, center_y - 40
                pygame.draw.circle(surf, GOLD, (kx, ky), 10, 3)
                pygame.draw.rect(surf, GOLD, pygame.Rect(kx+6, ky-3, 24, 6))
                pygame.draw.rect(surf, GOLD, pygame.Rect(kx+22, ky+3, 6, 8))
                pygame.draw.rect(surf, GOLD, pygame.Rect(kx+28, ky+3, 6, 8))

        # Caption
        caption = self.PHASES[min(self.phase, len(self.PHASES)-1)][1]
        txt(surf, caption, FONT_MD, WHITE, SCREEN_W//2, SCREEN_H - 80)

        if self.phase == len(self.PHASES) - 1:
            blink = int(self.frame * 0.07) % 2 == 0
            txt(surf, "(Returning to adventure...)", FONT_SM,
                GOLD if blink else lt(GOLD), SCREEN_W//2, SCREEN_H - 40)

    def done(self):
        return self.phase == len(self.PHASES) - 1 and self.phase_timer >= 60


# ══════════════════════════════════════════════════════════════════════
#  ZONE RUNNERS
# ══════════════════════════════════════════════════════════════════════

class Zone1:
    LEVEL_W = 6600
    LAVA_TRIGGER_X = 3100   # activate lava pool when Ella reaches the volcano
    CAVE_ENTRANCE_X = 6100
    CAVE_ENTRANCE_Y = GROUND_Y - 130

    def __init__(self, player_score=0, start_x=100, start_y=GROUND_Y):
        self.platforms = make_z1_platforms()
        self.spikes    = make_z1_spikes()
        self.coins     = make_z1_coins()
        self.bears     = make_z1_bears()
        self.guards    = make_z1_guards()
        self.tubes     = make_z1_tubes()
        self.lava      = LavaPool()   # ground-level pool at volcano base
        self.player    = Player(start_x, start_y)
        self.player.score = player_score
        self.cam_x     = 0
        self.frame     = 0
        self.jail_return = None
        self.net_catch = False  # flag: caught by net this frame

    def _cam(self):
        target = self.player.rect.centerx - SCREEN_W // 2
        self.cam_x = max(0, min(target, self.LEVEL_W - SCREEN_W))

    def update(self):
        self.frame += 1
        keys = pygame.key.get_pressed()

        if not self.player.dead:
            self.player.handle_input(keys)

            # Ice power
            if keys[ICE_KEY]:
                self.player.use_ice()

            # Tube entry
            for tube in self.tubes:
                if tube.in_range and keys[DOWN_KEY]:
                    self.player.rect.x = tube.dest_x
                    self.player.rect.y = tube.dest_y - self.player.H
                    self.player.vy = 0
                    particles.burst(tube.dest_x + 28, tube.dest_y,
                                    (80, 200, 100), 15, 4, 4, 30, -0.1)

        # Lava trigger
        if self.player.rect.x >= self.LAVA_TRIGGER_X and not self.lava.active:
            self.lava.active = True

        self.player.update(self.platforms, self.spikes, self.coins,
                           self.tubes, self.lava)

        # Bears
        for b in self.bears:
            b.update(self.player.rect.centerx, self.player.rect.centery)
            if not self.player.dead and b.rect.colliderect(self.player.rect):
                self.player.dead = True

        # Guards / nets — net hit → Fox Jail (not death)
        self.net_catch = False
        for g in self.guards:
            g.update(self.player.rect)
            if not self.player.dead and not self.net_catch:
                hit_nets = [n for n in g.nets if n.rect.colliderect(self.player.rect)]
                if hit_nets:
                    self.net_catch = True
                    # 500 px back guarantees solid ground before either guard
                    self.player.jail_checkpoint_x = max(100, g.rect.left - 500)
                    self.player.jail_checkpoint_y = GROUND_Y
                    # Remove the nets that hit
                    for n in hit_nets:
                        if n in g.nets:
                            g.nets.remove(n)

        self.lava.update()
        particles.update()
        update_snow()
        self._cam()

    def draw(self, surf):
        draw_zone1_bg(surf, self.cam_x, self.frame)

        # Platforms
        for p in self.platforms:
            draw_platform_snow(surf, p.rect, self.cam_x)

        # Tubes
        for tube in self.tubes:
            draw_tube(surf, tube.wx, tube.wy, self.cam_x)

        # Spikes
        for s in self.spikes:
            draw_spike_set(surf, s.cx - self.cam_x, s.y, self.frame)

        # Coins
        for c in self.coins:
            if not c.collected:
                draw_coin(surf, c.cx - self.cam_x, c.cy, self.frame)

        # Lava pool drawn BEFORE the volcano so the volcano base sits on top of it naturally
        self.lava.draw(surf, self.cam_x, self.frame)

        # Volcano (drawn near its world x)
        draw_volcano(surf, 3100, GROUND_Y - 185, self.cam_x, self.frame)

        # Cave entrance
        draw_cave_entrance(surf, self.CAVE_ENTRANCE_X, self.CAVE_ENTRANCE_Y,
                           self.cam_x, self.frame)

        # Bears
        for b in self.bears:
            b.draw(surf, self.cam_x, self.frame)

        # Guards
        for g in self.guards:
            g.draw(surf, self.cam_x)

        # Player
        self.player.draw(surf, self.cam_x)

        # Particles
        particles.draw(surf, self.cam_x)

        # HUD
        draw_hud(surf, self.player.score, "Zone 1: Snowy Mountains", self.frame)

        # Tube hint
        for tube in self.tubes:
            if tube.in_range:
                sx = tube.wx - self.cam_x
                txt(surf, "[DOWN] Enter Tube", FONT_XS, (255, 240, 100), sx+28, tube.wy - 30)

    @property
    def reached_cave(self):
        cave_rect = pygame.Rect(self.CAVE_ENTRANCE_X + 5, self.CAVE_ENTRANCE_Y,
                                130, 140)
        return cave_rect.colliderect(self.player.rect)


class Zone2:
    LEVEL_W = 4400
    CHEST_X = 1820
    CHEST_Y = GROUND_Y - 10

    def __init__(self, player_score=0):
        self.platforms  = make_z2_platforms()
        self.spikes     = make_z2_spikes()
        self.coins      = make_z2_coins()
        self.fox_friends = make_fox_friends()
        self.player     = Player(80, GROUND_Y)
        self.player.score = player_score
        self.cam_x      = 0
        self.frame      = 0
        self.chest_open = False
        self.net_catch  = False

    def _cam(self):
        target = self.player.rect.centerx - SCREEN_W // 2
        self.cam_x = max(0, min(target, self.LEVEL_W - SCREEN_W))

    def update(self):
        self.frame += 1
        keys = pygame.key.get_pressed()

        if not self.player.dead:
            self.player.handle_input(keys)
            if keys[ICE_KEY]:
                self.player.use_ice()

        self.player.update(self.platforms, self.spikes, self.coins, [])

        for f in self.fox_friends:
            f.update(self.platforms)

        # Check treasure chest
        chest_rect = pygame.Rect(self.CHEST_X - 35, self.CHEST_Y - 52, 70, 52)
        if not self.chest_open and self.player.rect.colliderect(chest_rect):
            self.chest_open = True
            self.player.score += 500
            particles.burst(self.CHEST_X, self.CHEST_Y - 30, GOLD, 40, 6, 6, 80, -0.1)

        particles.update()
        self._cam()

    def draw(self, surf):
        draw_zone2_bg(surf, self.cam_x, self.frame)

        for p in self.platforms:
            draw_platform_cave(surf, p.rect, self.cam_x)

        for s in self.spikes:
            draw_spike_set(surf, s.cx - self.cam_x, s.y, self.frame)

        for c in self.coins:
            if not c.collected:
                draw_coin(surf, c.cx - self.cam_x, c.cy, self.frame)

        draw_treasure_chest(surf, self.CHEST_X, self.CHEST_Y, self.cam_x,
                            self.frame, self.chest_open)

        for f in self.fox_friends:
            f.draw(surf, self.cam_x)

        self.player.draw(surf, self.cam_x)
        particles.draw(surf, self.cam_x)
        draw_hud(surf, self.player.score, "Zone 2: The Cave", self.frame)

    @property
    def won(self):
        return self.chest_open


# ══════════════════════════════════════════════════════════════════════
#  MAIN GAME STATE MACHINE
# ══════════════════════════════════════════════════════════════════════
STATE_MENU    = 'menu'
STATE_Z1      = 'z1'
STATE_Z2      = 'z2'
STATE_JAIL    = 'jail'
STATE_GAMEOVER= 'gameover'
STATE_WIN     = 'win'

class Game:
    def __init__(self):
        self.state   = STATE_MENU
        self.menu    = MenuScreen()
        self.zone1   = None
        self.zone2   = None
        self.jail    = None
        self.gameover= None
        self.win     = None
        self.score_carry = 0
        self.fade_alpha = 0
        self.fade_dir   = 0   # 1=fade out, -1=fade in
        self.fade_target_state = None
        self.fade_score = 0
        # Jail return — stored so the fade system can spawn Zone1 at the right spot
        self._jail_rx    = 100
        self._jail_ry    = GROUND_Y
        self._jail_score = 0

    def start_zone1(self, score=0):
        self.zone1 = Zone1(score)
        self.state = STATE_Z1
        self.fade_dir = -1

    def start_zone2(self, score):
        self.zone2 = Zone2(score)
        self.state = STATE_Z2
        self.fade_dir = -1

    def goto_jail(self, return_x, return_y, score):
        self.jail = FoxJailScreen(return_x, return_y, score)
        self.state = STATE_JAIL

    def goto_gameover(self, score, zone):
        self.gameover = GameOverScreen(score, zone)
        self.state = STATE_GAMEOVER

    def goto_win(self, score, fox_friends):
        self.win = WinScreen(score, fox_friends)
        self.state = STATE_WIN

    def start_fade(self, target_state, score=0):
        self.fade_dir = 1
        self.fade_target_state = target_state
        self.fade_score = score

    def _do_fade_transition(self):
        if self.fade_dir == 0:
            return
        self.fade_alpha += self.fade_dir * 8
        self.fade_alpha = max(0, min(255, self.fade_alpha))
        if self.fade_dir == 1 and self.fade_alpha >= 255:
            t = self.fade_target_state
            if t == 'z1':    self.start_zone1(self.fade_score)
            elif t == 'z2':  self.start_zone2(self.fade_score)
            elif t == 'menu': self.state = STATE_MENU; self.menu = MenuScreen()
            elif t == 'jail_return':
                # Restore Ella at her checkpoint, keeping her score
                self.zone1 = Zone1(self._jail_score, self._jail_rx, self._jail_ry)
                self.state = STATE_Z1
            self.fade_dir = -1
        elif self.fade_dir == -1 and self.fade_alpha <= 0:
            self.fade_dir = 0

    def run(self):
        running = True
        while running:
            dt = clock.tick(FPS)
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    running = False
                    break

                # ── Menu ──────────────────────────────────────────
                if self.state == STATE_MENU:
                    result = self.menu.handle(event)
                    if result == 'start':
                        self.start_fade('z1', 0)

                # ── Game Over ─────────────────────────────────────
                elif self.state == STATE_GAMEOVER and self.gameover:
                    result = self.gameover.handle(event)
                    if result == 'retry':
                        self.start_fade('z1', 0)
                    elif result == 'menu':
                        self.start_fade('menu')

                # ── Win ───────────────────────────────────────────
                elif self.state == STATE_WIN and self.win:
                    result = self.win.handle(event)
                    if result == 'menu':
                        self.start_fade('menu')
                    elif result == 'restart':
                        self.start_fade('z1', 0)

            # ── UPDATE ────────────────────────────────────────────
            if self.state == STATE_MENU:
                self.menu.update()

            elif self.state == STATE_Z1 and self.zone1:
                self.zone1.update()
                p = self.zone1.player
                if self.zone1.net_catch:
                    self.goto_jail(p.jail_checkpoint_x, p.jail_checkpoint_y, p.score)
                elif p.dead:
                    self.goto_gameover(p.score, 1)
                elif self.zone1.reached_cave:
                    self.start_fade('z2', p.score)

            elif self.state == STATE_Z2 and self.zone2:
                self.zone2.update()
                p = self.zone2.player
                if p.dead:
                    self.goto_gameover(p.score, 2)
                elif self.zone2.won:
                    self.goto_win(p.score, self.zone2.fox_friends)

            elif self.state == STATE_JAIL and self.jail:
                self.jail.update()
                if self.jail.done():
                    # Store checkpoint coords, then trigger a proper fade-out → fade-in
                    # so Ella reappears smoothly at her safe spot before the guard
                    self._jail_rx    = self.jail.return_x
                    self._jail_ry    = self.jail.return_y
                    self._jail_score = self.jail.score
                    self.start_fade('jail_return', 0)

            elif self.state == STATE_GAMEOVER and self.gameover:
                self.gameover.update()

            elif self.state == STATE_WIN and self.win:
                self.win.update()

            self._do_fade_transition()

            # ── DRAW ──────────────────────────────────────────────
            if self.state == STATE_MENU:
                self.menu.draw(screen)
            elif self.state == STATE_Z1 and self.zone1:
                self.zone1.draw(screen)
            elif self.state == STATE_Z2 and self.zone2:
                self.zone2.draw(screen)
            elif self.state == STATE_JAIL and self.jail:
                self.jail.draw(screen)
            elif self.state == STATE_GAMEOVER and self.gameover:
                self.gameover.draw(screen)
            elif self.state == STATE_WIN and self.win:
                self.win.draw(screen)
            else:
                screen.fill(BLACK)

            # Fade overlay
            if self.fade_alpha > 0:
                fade_surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
                fade_surf.fill((0, 0, 0, self.fade_alpha))
                screen.blit(fade_surf, (0, 0))

            pygame.display.flip()

        pygame.quit()
        sys.exit()


# ══════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    game = Game()
    game.run()
