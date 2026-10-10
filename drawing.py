"""drawing.py — particles, all draw_* helpers, backgrounds, HUD, leaderboard block.

Sprite art: if a matching PNG exists in `assets/` (see assets/README.md), the
draw_* function will use it instead of the procedural drawing. Otherwise it
falls back to the original hand-drawn version, so the game keeps working
exactly as before."""
import pygame, pygame.gfxdraw, math, random
from sprites import get_sprite, get_animation

# Frame counts for the sprite strips in assets/. If you drop in a strip with
# a different number of frames, change these here.
POLAR_BEAR_FRAMES = 8    # frames in polar_bear.png (row 0 of the ZomBCool sheet)
CATCHER_FRAMES    = 10   # frames in catcher.png (row 0 of the Officer sheet)
LAVA_FRAMES       = 45   # frames in lava.png (matches the OpenGameArt 45-frame strip)
from constants import (
    SCREEN_W, SCREEN_H, GROUND_Y, cam_y_global,
    WHITE, BLACK, GOLD, ICE_BL, COIN_Y, SNOW_W, SNOW_S,
    FOX_OR, BELLY_C, PAW_C, EAR_PK,
    BEAR_W, BEAR_S, HUMAN_C, COAT_BR,
    SPIKE_G, SPIKE_L, NET_BR,
    PLAT_T, PLAT_B, PLAT_E,
    CAVE_BG, CAVE_MD, CAVE_PT, CAVE_PE,
    LAVA_O, LAVA_R, LAVA_Y,
    SKY_T, SKY_B,
    FONT_XL, FONT_LG, FONT_MD, FONT_SM, FONT_XS,
    dk, lt, txt, draw_rounded_rect,
)
from leaderboard import LEADERBOARD


# ── Particles ─────────────────────────────────────────────────────────────
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


# ── High-quality procedural sprites (supersampled + cached) ─────────────────
# Drawing at _SUPER× the final size and smoothscaling down anti-aliases every
# shape (circles, ellipses, polygons) — no jaggies, no pixelation, all at the
# game's real resolution. Each (key, flip) is rendered once and cached.
_SUPER = 4
_proc_cache = {}

def _cached_sprite(key, w, h, draw_fn, flip_x=False):
    ck = (key, flip_x)
    cached = _proc_cache.get(ck)
    if cached is not None:
        return cached
    if flip_x:
        base = _cached_sprite(key, w, h, draw_fn, False)
        out = pygame.transform.flip(base, True, False)
        _proc_cache[ck] = out
        return out
    big = pygame.Surface((w * _SUPER, h * _SUPER), pygame.SRCALPHA)
    draw_fn(big, _SUPER)
    small = pygame.transform.smoothscale(big, (w, h))
    _proc_cache[ck] = small
    return small


# ── Fox ───────────────────────────────────────────────────────────────────
def draw_fox(surf, cx, cy, facing_right=True, anim=0, scale=1.0,
             body_color=FOX_OR, ice_glow=False):
    s = scale
    pad = int(72 * s)
    tmp = pygame.Surface((pad*2, pad*2), pygame.SRCALPHA)
    tc = pad
    bcy = int(tc - 14 * s)

    walk = math.sin(anim * 0.26) * int(5 * s)
    tw   = math.sin(anim * 0.14)

    if ice_glow:
        gsurf = pygame.Surface((pad*2, pad*2), pygame.SRCALPHA)
        pygame.draw.circle(gsurf, (160, 230, 255, 30), (tc, bcy), int(46*s))
        tmp.blit(gsurf, (0,0))

    tpts = [
        (tc - int(7*s),  bcy + int(10*s)),
        (tc - int(20*s), bcy - int(2*s) + int(tw*8*s)),
        (tc - int(32*s), bcy + int(10*s) + int(tw*12*s)),
        (tc - int(26*s), bcy + int(24*s) + int(tw*8*s)),
        (tc - int(10*s), bcy + int(20*s)),
    ]
    if len(set(tpts)) >= 3:
        pygame.draw.polygon(tmp, body_color, tpts)
    pygame.draw.circle(tmp, BELLY_C,
        (tc - int(28*s), bcy + int(17*s) + int(tw*8*s)), int(8*s))

    bw, bh = int(26*s), int(34*s)
    pygame.draw.ellipse(tmp, body_color,
        pygame.Rect(tc - bw//2, bcy - bh//2, bw, bh))

    belly_r = pygame.Rect(tc - int(7*s), bcy - int(10*s), int(14*s), int(24*s))
    pygame.draw.ellipse(tmp, BELLY_C, belly_r)

    lg = int(walk)
    foot_y = bcy + int(30*s)
    pygame.draw.rect(tmp, dk(body_color, 22),
        pygame.Rect(tc - int(10*s), bcy + int(12*s), int(7*s), int(18*s) + lg))
    pygame.draw.rect(tmp, dk(body_color, 22),
        pygame.Rect(tc + int(3*s),  bcy + int(12*s), int(7*s), int(18*s) - lg))
    pygame.draw.rect(tmp, PAW_C,
        pygame.Rect(tc - int(11*s), foot_y + lg, int(9*s), int(4*s)))
    pygame.draw.rect(tmp, PAW_C,
        pygame.Rect(tc + int(2*s),  foot_y - lg, int(9*s), int(4*s)))

    hcx = tc + int(12*s)
    hcy = bcy - int(16*s)
    pygame.draw.circle(tmp, body_color, (hcx, hcy), int(13*s))
    pygame.draw.circle(tmp, lt(body_color, 12), (hcx + int(4*s), hcy + int(2*s)), int(9*s))
    snout_r = pygame.Rect(hcx + int(7*s), hcy - int(4*s), int(13*s), int(9*s))
    pygame.draw.ellipse(tmp, BELLY_C, snout_r)
    pygame.draw.ellipse(tmp, (25, 8, 2),
        pygame.Rect(hcx + int(16*s), hcy - int(2*s), int(5*s), int(3*s)))
    pygame.draw.circle(tmp, (195, 118, 5), (hcx + int(6*s), hcy - int(5*s)), int(4*s))
    pygame.draw.circle(tmp, (12,  8,  0), (hcx + int(6*s), hcy - int(5*s)), int(2*s))
    pygame.draw.circle(tmp, WHITE,         (hcx + int(7*s), hcy - int(6*s)), int(1*s))

    ep = [(tc + int(3*s),  hcy - int(11*s)),
          (tc - int(2*s),  hcy - int(26*s)),
          (tc + int(14*s), hcy - int(13*s))]
    pygame.draw.polygon(tmp, body_color, ep)
    epi = [(tc + int(4*s),  hcy - int(13*s)),
           (tc + int(1*s),  hcy - int(23*s)),
           (tc + int(12*s), hcy - int(14*s))]
    pygame.draw.polygon(tmp, EAR_PK, epi)

    eb = [(tc - int(6*s),  hcy - int(10*s)),
          (tc - int(14*s), hcy - int(24*s)),
          (tc + int(2*s),  hcy - int(12*s))]
    pygame.draw.polygon(tmp, dk(body_color, 18), eb)

    pygame.draw.rect(tmp, dk(body_color, 15),
        pygame.Rect(tc + int(4*s),  bcy + int(8*s),  int(6*s), int(16*s) - lg))
    pygame.draw.rect(tmp, dk(body_color, 15),
        pygame.Rect(tc - int(8*s),  bcy + int(8*s),  int(6*s), int(16*s) + lg))
    pygame.draw.rect(tmp, PAW_C,
        pygame.Rect(tc + int(3*s),  bcy + int(23*s) - lg, int(8*s), int(4*s)))
    pygame.draw.rect(tmp, PAW_C,
        pygame.Rect(tc - int(9*s),  bcy + int(23*s) + lg, int(8*s), int(4*s)))

    if ice_glow and int(anim) % 10 < 3:
        for _ in range(3):
            sx2 = tc + random.randint(-int(30*s), int(30*s))
            sy2 = bcy + random.randint(-int(30*s), int(10*s))
            pygame.draw.circle(tmp, ICE_BL, (sx2, sy2), random.randint(1, int(2*s)+1))

    if not facing_right:
        tmp = pygame.transform.flip(tmp, True, False)
    surf.blit(tmp, (cx - pad, cy - pad - int(30*s)))


# ── Polar Bear ────────────────────────────────────────────────────────────
# Visual target size for the sprite version. Slightly larger than the
# collision rect (60x72) so the bear "feels" beefy at the same play area.
_BEAR_SPRITE_SIZE = (96, 96)

# Procedural bear render size (final px). Drawn facing RIGHT, feet at bottom.
_BEAR_W, _BEAR_H = 104, 116
_BEAR_FOOT = 111          # design-space y of the paw bottoms (anchor to cy)
_BEAR_FRAMES = 8

def _render_bear(surf, S, idx, num):
    """Draw a fluffy polar bear (facing right) into `surf` at S× scale."""
    R = lambda x, y, w, h: pygame.Rect(int(x*S), int(y*S), int(w*S), int(h*S))
    C = lambda x, y: (int(x*S), int(y*S))
    LW = max(1, int(1.6 * S))

    FUR    = (249, 248, 245)
    FUR_SH = (200, 210, 228)     # cool blue-gray shadow
    FUR_HI = (255, 255, 255)
    OUT    = (92, 100, 124)      # cool outline, reads on snow
    NOSE   = (46, 44, 54)
    EYE    = (40, 36, 48)
    INNER  = (208, 204, 214)

    ph  = 2 * math.pi * idx / num
    sw  = math.sin(ph)
    sw2 = -sw

    def leg(lx, swing, color):
        foot = lx + swing * 3
        pygame.draw.rect(surf, color, R(lx - 6, 80, 12, 24), border_radius=int(5*S))
        pygame.draw.rect(surf, OUT, R(lx - 6, 80, 12, 24), LW, border_radius=int(5*S))
        pygame.draw.ellipse(surf, color, R(foot - 8, 100, 17, 11))
        pygame.draw.ellipse(surf, OUT, R(foot - 8, 100, 17, 11), LW)

    # Far legs (behind, shadowed)
    leg(34, sw2, FUR_SH)
    leg(64, sw,  FUR_SH)

    # Body
    pygame.draw.ellipse(surf, FUR,    R(10, 44, 74, 54))
    pygame.draw.ellipse(surf, FUR,    R(48, 36, 32, 32))   # shoulder hump (head side)
    pygame.draw.ellipse(surf, FUR_SH, R(18, 66, 60, 30))   # belly shadow
    pygame.draw.ellipse(surf, FUR_HI, R(18, 47, 48, 17))   # back highlight
    pygame.draw.ellipse(surf, OUT,    R(10, 44, 74, 54), LW)

    # Near legs (front)
    leg(26, sw,  FUR)
    leg(70, sw2, FUR)

    # Head
    pygame.draw.ellipse(surf, FUR, R(52, 28, 40, 40))
    # far ear
    pygame.draw.circle(surf, FUR_SH, C(82, 30), int(7*S))
    pygame.draw.circle(surf, OUT,    C(82, 30), int(7*S), LW)
    # near ear
    pygame.draw.circle(surf, FUR,   C(60, 27), int(8*S))
    pygame.draw.circle(surf, INNER, C(60, 28), int(4*S))
    pygame.draw.circle(surf, OUT,   C(60, 27), int(8*S), LW)
    pygame.draw.ellipse(surf, OUT, R(52, 28, 40, 40), LW)
    pygame.draw.ellipse(surf, FUR_HI, R(58, 33, 18, 12))   # head highlight
    # snout
    pygame.draw.ellipse(surf, FUR_HI, R(74, 46, 23, 18))
    pygame.draw.ellipse(surf, OUT,    R(74, 46, 23, 18), LW)
    # nose
    pygame.draw.ellipse(surf, NOSE, R(88, 49, 11, 8))
    pygame.draw.circle(surf, (120, 118, 130), C(90, 50), max(1, int(1.4*S)))
    # mouth
    pygame.draw.line(surf, OUT, C(93, 57), C(93, 62), LW)
    pygame.draw.line(surf, OUT, C(88, 62), C(93, 62), LW)
    # eye
    pygame.draw.circle(surf, EYE,   C(74, 41), int(3.2*S))
    pygame.draw.circle(surf, WHITE, C(75, 40), max(1, int(1.3*S)))

def draw_polar_bear(surf, cx, cy, facing_right=True, anim=0):
    # Sprite path — only used when assets/polar_bear.png exists.
    frames = get_animation("polar_bear", POLAR_BEAR_FRAMES,
                           target_size=_BEAR_SPRITE_SIZE,
                           flip_x=not facing_right)
    if frames is not None:
        # Walk cycle advances every 8 game frames (snappy but not jittery).
        idx = int(anim // 8) % len(frames)
        img = frames[idx]
        w, h = img.get_size()
        # cy = rect.bottom (feet level): center the sprite horizontally and
        # rest its bottom at cy.
        surf.blit(img, (int(cx) - w // 2, int(cy) - h))
        return

    # Procedural (high-quality: supersampled + cached, animated walk) ────────
    idx = int(anim // 5) % _BEAR_FRAMES
    img = _cached_sprite(('bear', idx), _BEAR_W, _BEAR_H,
                         lambda b, S: _render_bear(b, S, idx, _BEAR_FRAMES),
                         flip_x=not facing_right)
    surf.blit(img, (int(cx) - _BEAR_W // 2, int(cy) - _BEAR_FOOT))


# ── Human Guard / Fox Catcher ───────────────────────────────────────────────
# Visual size for the sprite version. Slightly taller than the collision rect
# (44x68) so the catcher feels imposing without changing hit boxes.
_CATCHER_SPRITE_SIZE = (80, 104)

# Procedural catcher render size (final px). Drawn facing RIGHT, feet at bottom,
# holding a butterfly-style net (this is the "fox catcher" who throws nets).
_CATCHER_W, _CATCHER_H = 88, 120
_CATCHER_FOOT = 112       # design-space y of the boot bottoms (anchor to cy)

def _render_catcher(surf, S, gender):
    R = lambda x, y, w, h: pygame.Rect(int(x*S), int(y*S), int(w*S), int(h*S))
    C = lambda x, y: (int(x*S), int(y*S))
    LW = max(1, int(1.6 * S))
    poly = lambda pts, col: pygame.draw.polygon(
        surf, col, [(int(px*S), int(py*S)) for px, py in pts])
    poly_o = lambda pts, col: pygame.draw.polygon(
        surf, col, [(int(px*S), int(py*S)) for px, py in pts], LW)

    SKIN    = (238, 198, 160)
    SKIN_SH = (208, 166, 128)
    PANTS   = (62, 66, 82)
    PANTS_D = (46, 49, 62)
    BOOT    = (48, 38, 30)
    OUT     = (40, 34, 32)
    if gender == 'female':
        JACKET, JACKET_D, HAIR = (160, 96, 126), (122, 66, 94), (84, 54, 34)
    else:
        JACKET, JACKET_D, HAIR = (96, 116, 72), (68, 86, 50), (66, 46, 30)
    NETP = (124, 86, 32)      # net pole
    NETH = (225, 200, 120)    # net hoop / mesh

    # ground shadow
    sh = pygame.Surface((int(44*S), int(10*S)), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (0, 0, 0, 70), sh.get_rect())
    surf.blit(sh, (int(22*S), int(108*S)))

    # legs + boots
    for lx, col in [(36, PANTS_D), (48, PANTS)]:
        pygame.draw.rect(surf, col, R(lx - 6, 72, 12, 30), border_radius=int(3*S))
        pygame.draw.rect(surf, OUT, R(lx - 6, 72, 12, 30), LW, border_radius=int(3*S))
    for bx in [(30, BOOT), (48, BOOT)]:
        x, col = bx
        pygame.draw.rect(surf, col, R(x, 100, 18, 12), border_radius=int(3*S))
        pygame.draw.rect(surf, OUT, R(x, 100, 18, 12), LW, border_radius=int(3*S))

    # torso / jacket (slightly tapered)
    poly([(28, 44), (60, 44), (57, 76), (31, 76)], JACKET)
    poly([(44, 44), (60, 44), (57, 76), (44, 76)], JACKET_D)   # shaded right half
    poly_o([(28, 44), (60, 44), (57, 76), (31, 76)], OUT)
    pygame.draw.rect(surf, (40, 40, 48), R(30, 72, 26, 5))     # belt
    pygame.draw.circle(surf, (210, 180, 60), C(44, 74), int(2.4*S))  # buckle

    # back arm (down at side)
    pygame.draw.rect(surf, JACKET_D, R(24, 46, 9, 22), border_radius=int(4*S))
    pygame.draw.rect(surf, OUT, R(24, 46, 9, 22), LW, border_radius=int(4*S))
    pygame.draw.circle(surf, SKIN_SH, C(28, 69), int(4*S))

    # head + neck
    pygame.draw.rect(surf, SKIN_SH, R(37, 38, 10, 8))         # neck
    pygame.draw.circle(surf, SKIN, C(42, 29), int(13*S))
    pygame.draw.circle(surf, OUT, C(42, 29), int(13*S), LW)
    # ear
    pygame.draw.circle(surf, SKIN, C(34, 30), int(3*S))
    # face (facing right): eye + stern brow + nose + mouth
    pygame.draw.circle(surf, (40, 36, 44), C(47, 28), int(2.4*S))
    pygame.draw.line(surf, (60, 44, 30), C(44, 23), C(50, 25), LW)   # brow
    pygame.draw.line(surf, SKIN_SH, C(53, 30), C(53, 33), LW)        # nose
    pygame.draw.line(surf, (120, 70, 60), C(48, 35), C(52, 35), LW)  # mouth

    # hair / cap
    if gender == 'female':
        # hair cap + ponytail behind
        pygame.draw.ellipse(surf, HAIR, R(29, 16, 28, 20))
        poly([(30, 24), (24, 40), (30, 42), (34, 28)], HAIR)        # ponytail
        poly_o([(30, 24), (24, 40), (30, 42), (34, 28)], dk(HAIR, 20))
    else:
        # ranger cap: dome + brim pointing forward (right)
        pygame.draw.ellipse(surf, HAIR, R(30, 15, 26, 16))
        poly([(48, 22), (66, 20), (48, 26)], HAIR)                  # brim
        poly_o([(48, 22), (66, 20), (48, 26)], dk(HAIR, 25))
    pygame.draw.ellipse(surf, dk(HAIR, 25), R(30, 15, 26, 16), LW)

    # front arm raised, holding the net pole
    poly([(56, 47), (66, 52), (63, 58), (53, 54)], JACKET)         # upper arm/sleeve
    poly_o([(56, 47), (66, 52), (63, 58), (53, 54)], OUT)
    pygame.draw.circle(surf, SKIN, C(66, 55), int(4*S))           # hand

    # net: pole from hand up-forward, with a hoop + mesh
    pygame.draw.line(surf, NETP, C(66, 55), C(86, 30), max(1, int(2.4*S)))
    pygame.draw.circle(surf, NETH, C(80, 24), int(11*S), max(1, int(2*S)))
    # mesh
    for off in (-6, 0, 6):
        pygame.draw.line(surf, (235, 222, 170), C(80 + off, 14), C(80 + off, 34), max(1, int(0.7*S)))
        pygame.draw.line(surf, (235, 222, 170), C(70, 24 + off), C(90, 24 + off), max(1, int(0.7*S)))

def draw_human(surf, cx, cy, facing_right=True, alert=False, frame=0, gender='male'):
    # Sprite path — only used when assets/catcher.png exists.
    frames = get_animation("catcher", CATCHER_FRAMES,
                           target_size=_CATCHER_SPRITE_SIZE,
                           flip_x=not facing_right)
    if frames is not None:
        idx = int(frame // 8) % len(frames)
        img = frames[idx]
        w, h = img.get_size()
        # cy = rect.bottom (feet level): centre the sprite and rest its base at cy.
        surf.blit(img, (int(cx) - w // 2, int(cy) - h))
        if alert:
            # Yellow "!" above the head, same convention as the procedural art.
            s = FONT_MD.render('!', True, (255, 200, 30))
            surf.blit(s, (int(cx) - s.get_width() // 2, int(cy) - h - 24))
        return

    # Procedural (high-quality: supersampled + cached) ───────────────────────
    img = _cached_sprite(('catcher', gender), _CATCHER_W, _CATCHER_H,
                         lambda b, S: _render_catcher(b, S, gender),
                         flip_x=not facing_right)
    surf.blit(img, (int(cx) - _CATCHER_W // 2, int(cy) - _CATCHER_FOOT))
    if alert:
        s = FONT_MD.render('!', True, (255, 200, 30))
        surf.blit(s, (int(cx) - s.get_width() // 2, int(cy) - _CATCHER_FOOT - 6))


# (The old hand-drawn male/female guards were removed — draw_human now renders
#  the higher-quality procedural "fox catcher" via _render_catcher.)


# ── Spikes ────────────────────────────────────────────────────────────────
def _aa_poly(surf, pts, color):
    """Anti-aliased filled polygon (smoother edges than pygame.draw.polygon)."""
    ipts = [(int(x), int(y)) for (x, y) in pts]
    try:
        pygame.gfxdraw.filled_polygon(surf, ipts, color)
        pygame.gfxdraw.aapolygon(surf, ipts, color)
    except Exception:
        pygame.draw.polygon(surf, color, ipts)


def draw_spike_set(surf, cx, cy, frame=0):
    cx = int(cx); cy = int(cy)
    pulse = 0.5 + 0.5 * math.sin(frame * 0.08)
    # Soft danger glow
    gsurf = pygame.Surface((96, 56), pygame.SRCALPHA)
    pygame.draw.ellipse(gsurf, (225, 45, 45, int(20 + pulse * 30)),
                        pygame.Rect(0, 18, 96, 34))
    surf.blit(gsurf, (cx - 48, cy - 40))
    # Stone mount the blades rise from
    base = pygame.Rect(cx - 27, cy - 7, 54, 13)
    pygame.draw.rect(surf, (60, 62, 72), base, border_radius=4)
    pygame.draw.rect(surf, (96, 100, 114),
                     pygame.Rect(base.x + 2, base.y + 1, base.w - 4, 4), border_radius=3)
    pygame.draw.rect(surf, (32, 34, 42), base, 2, border_radius=4)
    # Three steel blades (taller in the middle), shaded for a 3-D look
    for ox, h in ((-17, 24), (0, 34), (17, 24)):
        bx    = cx + ox
        tip   = (bx, cy - h)
        left  = (bx - 9, cy - 1)
        right = (bx + 9, cy - 1)
        mid   = (bx, cy - 5)
        _aa_poly(surf, [left, right, tip], (150, 156, 172))   # blade body
        _aa_poly(surf, [left, tip, mid],   (198, 204, 218))   # lit (left) face
        _aa_poly(surf, [right, tip, mid],  (108, 113, 128))   # shaded (right) face
        pygame.draw.line(surf, (240, 244, 252), (bx - 1, cy - 5), tip, 2)  # edge highlight
        gl = max(1, int(1.5 + pulse * 2))
        pygame.draw.circle(surf, (255, 255, 255), tip, gl)    # cold tip glint


# ── Coin ──────────────────────────────────────────────────────────────────
def draw_coin(surf, cx, cy, frame=0):
    squeeze = abs(math.cos(frame * 0.1))
    w = max(6, int(18 * squeeze))
    h = 18
    r = pygame.Rect(cx - w//2, cy - h//2, w, h)
    pygame.draw.ellipse(surf, COIN_Y, r)
    pygame.draw.ellipse(surf, lt(COIN_Y, 40), pygame.Rect(cx-w//2+2, cy-h//2+2, max(2,w//3), h//3))
    pygame.draw.ellipse(surf, dk(COIN_Y, 20), r, 2)


# ── Net Projectile ────────────────────────────────────────────────────────
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


# ── Platforms ─────────────────────────────────────────────────────────────
def draw_platform_snow(surf, rect, cam_x=0, cam_y=0):
    r = pygame.Rect(rect.x - cam_x, rect.y - cam_y, rect.width, rect.height)
    if r.right < 0 or r.left > SCREEN_W or r.bottom < 0 or r.top > SCREEN_H:
        return
    pygame.draw.rect(surf, PLAT_B, r, border_radius=3)
    snow_r = pygame.Rect(r.x, r.y, r.width, min(12, r.height))
    pygame.draw.rect(surf, PLAT_T, snow_r, border_radius=3)
    pygame.draw.rect(surf, PLAT_E, r, 2, border_radius=3)
    for i in range(0, r.width - 20, 22):
        pygame.draw.ellipse(surf, SNOW_W,
            pygame.Rect(r.x + i + 2, r.y - 4, 18, 10))


def draw_platform_cave(surf, rect, cam_x=0, cam_y=0):
    r = pygame.Rect(rect.x - cam_x, rect.y - cam_y, rect.width, rect.height)
    if r.right < 0 or r.left > SCREEN_W or r.bottom < 0 or r.top > SCREEN_H:
        return
    pygame.draw.rect(surf, CAVE_PT, r, border_radius=3)
    pygame.draw.rect(surf, lt(CAVE_PT, 18), pygame.Rect(r.x, r.y, r.width, 8), border_radius=3)
    pygame.draw.rect(surf, CAVE_PE, r, 2, border_radius=3)
    gsurf = pygame.Surface((r.width, 6), pygame.SRCALPHA)
    gsurf.fill((255, 140, 40, 40))
    surf.blit(gsurf, (r.x, r.y - 2))


# ── Volcano ───────────────────────────────────────────────────────────────
# Sprite slot size matching the procedural volcano's footprint (~200 wide,
# 195 tall — base at sy+180, peak near sy-15).
_VOLCANO_SPRITE_SIZE = (220, 220)

def draw_volcano(surf, wx, wy, cam_x, frame=0):
    sx = wx - cam_x
    sy = wy
    if sx < -250 or sx > SCREEN_W + 50:
        return

    # Sprite path — only used when assets/volcano.png exists.
    img = get_sprite("volcano", target_size=_VOLCANO_SPRITE_SIZE)
    if img is not None:
        w, h = img.get_size()
        # Anchor the sprite so its base sits at GROUND_Y (sy + 180 in the
        # procedural version), centred over the procedural cone's mid x.
        base_x = sx + 100   # mid of the original 200-wide cone
        base_y = sy + 180   # ground level the original cone sits on
        surf.blit(img, (int(base_x) - w // 2, int(base_y) - h))
        # Keep an animated lava glow at the crater so it still feels alive.
        pulse = 0.5 + 0.5 * math.sin(frame * 0.1)
        glow = pygame.Surface((80, 36), pygame.SRCALPHA)
        alpha = int(150 + pulse * 80)
        pygame.draw.ellipse(glow, (255, 90, 0, alpha), pygame.Rect(0, 0, 80, 36))
        surf.blit(glow, (int(base_x) - 40, int(base_y) - h + 4))
        return

    # Procedural (high-quality) ──────────────────────────────────────────────
    pulse  = 0.5 + 0.5 * math.sin(frame * 0.1)
    base_y = sy + 180
    cxv    = sx + 100
    ROCK   = (98, 76, 66)
    ROCK_L = (128, 102, 86)
    ROCK_D = (66, 49, 43)
    OUTV   = (44, 31, 27)
    SNOW   = (226, 238, 251)
    SNOW_SH= (190, 208, 232)

    # Mountain silhouette: base -> left rim -> crater dip -> right rim -> base
    sil = [(sx+6, base_y), (sx+50, sy+74), (sx+82, sy+16),
           (sx+100, sy+30), (sx+118, sy+16), (sx+152, sy+74), (sx+194, base_y)]
    _aa_poly(surf, sil, ROCK)
    # Lit (left) face
    _aa_poly(surf, [(sx+6, base_y), (sx+50, sy+74), (sx+82, sy+16),
                    (sx+100, sy+30), (sx+78, base_y)], ROCK_L)
    # Shadowed (right) face
    _aa_poly(surf, [(sx+100, sy+30), (sx+118, sy+16), (sx+152, sy+74),
                    (sx+194, base_y), (sx+118, base_y)], ROCK_D)
    # Snow cap straddling the rim
    _aa_poly(surf, [(sx+82, sy+16), (sx+100, sy+30), (sx+118, sy+16),
                    (sx+128, sy+34), (sx+114, sy+42), (sx+100, sy+36),
                    (sx+86, sy+42), (sx+72, sy+34)], SNOW)
    _aa_poly(surf, [(sx+100, sy+36), (sx+114, sy+42), (sx+128, sy+34),
                    (sx+122, sy+48), (sx+100, sy+44)], SNOW_SH)

    # Crater glow (stacked translucent ellipses, pulsing)
    for rad, col, a in [(28, (255, 80, 0), 130), (18, (255, 140, 20), 190),
                        (10, (255, 210, 90), 240)]:
        gs = pygame.Surface((rad*2 + 2, rad + 14), pygame.SRCALPHA)
        pygame.draw.ellipse(gs, (*col, int(a * (0.7 + 0.3 * pulse))), gs.get_rect())
        surf.blit(gs, (cxv - rad, sy + 18))

    # Lava overflow down the right slope toward the pool
    lava_path = [(sx+104, sy+34), (sx+116, sy+70), (sx+128, sy+118), (sx+138, base_y-6)]
    for k in range(len(lava_path) - 1):
        x1, y1 = lava_path[k]; x2, y2 = lava_path[k+1]
        w = max(2, int(7 - k))
        pygame.draw.line(surf, (255, 90, 0), (int(x1), int(y1)), (int(x2), int(y2)), w + 2)
        pygame.draw.line(surf, (255, 180, 40), (int(x1), int(y1)), (int(x2), int(y2)), max(1, w - 1))

    # Silhouette outline for crisp definition
    pygame.draw.lines(surf, OUTV, False, [(int(px), int(py)) for px, py in sil], 2)

    # Rising smoke puffs
    for i in range(4):
        t = (frame * 0.012 + i * 0.27) % 1.0
        smx = cxv + int(math.sin(frame * 0.05 + i * 2) * 14)
        smy = sy + 22 - int(t * 90)
        sr  = int(8 + t * 20)
        ss = pygame.Surface((sr*2 + 2, sr*2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(ss, (180, 175, 180, int(110 * (1 - t))), (sr + 1, sr + 1), sr)
        surf.blit(ss, (smx - sr, smy - sr))

    # Embers shooting up from the crater
    for i in range(6):
        t = (frame * 0.08 + i * 0.5) % 1.0
        fx = cxv + math.sin(frame * 0.15 + i) * 20
        fy = sy + 24 - t * 96
        fr = max(2, int((1 - t) * 7))
        col = (255, int(70 + t * 140), 0)
        fsurf = pygame.Surface((fr*2 + 2, fr*2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(fsurf, (*col, int(230 * (1 - t))), (fr + 1, fr + 1), fr)
        surf.blit(fsurf, (int(fx) - fr - 1, int(fy) - fr - 1))


# ── Tube ──────────────────────────────────────────────────────────────────
def draw_tube(surf, wx, wy, cam_x):
    sx = wx - cam_x
    sy = wy
    pygame.draw.rect(surf, (30, 140, 55), pygame.Rect(sx, sy, 56, 60), border_radius=4)
    pygame.draw.rect(surf, (22, 110, 40), pygame.Rect(sx, sy, 56, 60), 3, border_radius=4)
    pygame.draw.rect(surf, (30, 155, 60), pygame.Rect(sx-6, sy, 68, 18), border_radius=5)
    pygame.draw.rect(surf, (18, 110, 38), pygame.Rect(sx-6, sy, 68, 18), 3, border_radius=5)
    pygame.draw.rect(surf, (60, 200, 90), pygame.Rect(sx+6, sy+4, 10, 50), border_radius=3)
    arrowY = sy - 22
    pygame.draw.polygon(surf, (255, 235, 60),
        [(sx+28, arrowY+14), (sx+14, arrowY), (sx+42, arrowY)])


# ── Cave Entrance ─────────────────────────────────────────────────────────
def draw_cave_entrance(surf, wx, wy, cam_x, frame=0):
    sx = wx - cam_x
    sy = wy
    if sx < -200 or sx > SCREEN_W + 50:
        return
    pulse = 0.5 + 0.5 * math.sin(frame * 0.07)
    gsurf = pygame.Surface((200, 200), pygame.SRCALPHA)
    pygame.draw.ellipse(gsurf, (255, 140, 40, int(50*pulse)),
        pygame.Rect(0, 0, 200, 200))
    surf.blit(gsurf, (sx - 20, sy - 30))
    frame_pts = [(sx-20, sy+130), (sx-15, sy+20), (sx+10, sy-20),
                 (sx+75, sy-35), (sx+140, sy-20), (sx+155, sy+20),
                 (sx+160, sy+130)]
    pygame.draw.polygon(surf, (55, 45, 38), frame_pts)
    arc_pts = [(sx+5, sy+125), (sx+8, sy+35),
               (sx+75, sy-15), (sx+142, sy+35), (sx+145, sy+125)]
    pygame.draw.polygon(surf, (12, 7, 3), arc_pts)
    igsurf = pygame.Surface((140, 130), pygame.SRCALPHA)
    pygame.draw.ellipse(igsurf, (255, 130, 40, int(90*pulse)),
        pygame.Rect(0, 0, 140, 130))
    surf.blit(igsurf, (sx + 5, sy - 5))
    pygame.draw.polygon(surf, (215, 232, 255),
        [(sx-14, sy+22), (sx+10, sy-18), (sx+75, sy-33),
         (sx+140, sy-18), (sx+158, sy+22), (sx+148, sy+28),
         (sx+75, sy-22), (sx+10, sy-8), (sx-4, sy+28)])
    if abs(sx - SCREEN_W//2) < 350:
        txt(surf, "ENTER CAVE  [DOWN]", FONT_SM, GOLD, sx+75, sy-50)


# ── Treasure Chest ────────────────────────────────────────────────────────
def draw_treasure_chest(surf, wx, wy, cam_x, frame=0, open_=False):
    sx = wx - cam_x
    sy = wy - 58  # shift up so the box bottom sits at wy (ground level)
    if sx < -100 or sx > SCREEN_W + 50:
        return
    pulse = 0.5 + 0.5 * math.sin(frame * 0.09)
    gsurf = pygame.Surface((120, 80), pygame.SRCALPHA)
    pygame.draw.ellipse(gsurf, (255, 200, 50, int(60*pulse)), pygame.Rect(0, 0, 120, 80))
    surf.blit(gsurf, (sx - 25, sy - 10))
    pygame.draw.rect(surf, (130, 80, 25), pygame.Rect(sx, sy+22, 70, 36), border_radius=4)
    pygame.draw.rect(surf, (90, 55, 14),  pygame.Rect(sx, sy+22, 70, 36), 2, border_radius=4)
    lid_angle = -0.85 if open_ else 0
    if open_:
        lid_pts = [(sx, sy+22), (sx+70, sy+22),
                   (sx+70, sy+22+int(math.cos(lid_angle)*22)),
                   (sx, sy+22+int(math.cos(lid_angle)*22))]
        pygame.draw.polygon(surf, (155, 95, 28), lid_pts)
    else:
        pygame.draw.rect(surf, (155, 95, 28), pygame.Rect(sx, sy, 70, 24), border_radius=4)
    pygame.draw.rect(surf, (90, 55, 14),  pygame.Rect(sx, sy, 70, 24), 2, border_radius=4)
    pygame.draw.circle(surf, (220, 185, 30), (sx+35, sy+12), 8)
    pygame.draw.circle(surf, (170, 130, 15), (sx+35, sy+12), 5)
    pygame.draw.line(surf, (220, 185, 30), (sx, sy+22), (sx+70, sy+22), 3)
    if open_:
        for i in range(8):
            a2 = (i / 8) * math.pi * 2 + frame * 0.06
            r2 = 35 + math.sin(frame*0.14+i) * 10
            sx2 = int(sx + 35 + math.cos(a2)*r2)
            sy2 = int(sy + 10 + math.sin(a2)*r2)
            pygame.draw.circle(surf, (255, int(150+i*10), 50), (sx2, sy2), 4)


# ── Ice Bridge ────────────────────────────────────────────────────────────
def draw_ice_bridge(surf, rect, cam_x, build_progress=1.0, frame=0):
    draw_w = int(rect.width * build_progress)
    if draw_w <= 0:
        return
    r = pygame.Rect(rect.x - cam_x, rect.y - cam_y_global, draw_w, rect.height)
    isurf = pygame.Surface((draw_w, rect.height), pygame.SRCALPHA)
    isurf.fill((150, 220, 255, 180))
    for i in range(0, draw_w, 18):
        for j in range(0, rect.height, 14):
            if (i + j) % 2 == 0:
                pygame.draw.circle(isurf, (200, 240, 255, 120), (i, j), 3)
    surf.blit(isurf, (r.x, r.y))
    pygame.draw.rect(surf, ICE_BL, r, 2, border_radius=4)
    for i in range(6, draw_w - 4, 18):
        bx = r.x + i
        by = r.y + 2
        twinkle = 0.5 + 0.5 * math.sin(frame * 0.18 + i * 0.4)
        radius = max(1, int(2 + twinkle * 2))
        brightness = int(200 + twinkle * 55)
        pygame.draw.circle(surf, (brightness, 245, 255), (bx, by), radius)


# ── Cave Bat ──────────────────────────────────────────────────────────────
def draw_cave_bat(surf, cx, cy, facing_right=True, anim=0):
    pad = 40
    tmp = pygame.Surface((pad * 2, pad * 2), pygame.SRCALPHA)
    tc  = pad
    flap    = math.sin(anim * 0.28) * 0.5 + 0.5   # 0..1
    wing_h  = int(12 + flap * 14)

    # Wing membranes
    lwing = [(tc, tc + 2), (tc - 30, tc - wing_h), (tc - 8, tc + 4)]
    rwing = [(tc, tc + 2), (tc + 30, tc - wing_h), (tc + 8, tc + 4)]
    for pts in (lwing, rwing):
        pygame.draw.polygon(tmp, (38, 22, 32), pts)
    # Vein lines
    for tip in ((tc - 30, tc - wing_h), (tc - 18, tc - wing_h // 2)):
        pygame.draw.line(tmp, (55, 35, 48), (tc, tc + 2), tip, 1)
    for tip in ((tc + 30, tc - wing_h), (tc + 18, tc - wing_h // 2)):
        pygame.draw.line(tmp, (55, 35, 48), (tc, tc + 2), tip, 1)

    # Body + head
    pygame.draw.ellipse(tmp, (50, 30, 42), pygame.Rect(tc - 7, tc - 5, 14, 12))
    pygame.draw.circle(tmp, (50, 30, 42), (tc + 6, tc - 10), 7)

    # Red glowing eyes
    for ex in (tc + 3, tc + 9):
        pygame.draw.circle(tmp, (220, 40, 30), (ex, tc - 12), 3)
        pygame.draw.circle(tmp, (255, 80, 60), (ex, tc - 12), 1)

    # Ears
    pygame.draw.polygon(tmp, (50, 30, 42), [(tc + 3, tc - 14), (tc + 1, tc - 22), (tc + 9, tc - 16)])
    pygame.draw.polygon(tmp, (50, 30, 42), [(tc + 9, tc - 14), (tc + 11, tc - 22), (tc + 14, tc - 16)])

    if not facing_right:
        tmp = pygame.transform.flip(tmp, True, False)
    surf.blit(tmp, (int(cx) - pad, int(cy) - pad))


# ── Falling Rock (Stalactite) ─────────────────────────────────────────────
def draw_falling_rock(surf, cx, top_y, state, shake_timer, frame):
    if state == 3:   # LANDED — draw flat rubble
        pygame.draw.ellipse(surf, (80, 65, 55),
            pygame.Rect(cx - 20, top_y + 36, 40, 14))
        pygame.draw.ellipse(surf, (105, 85, 72),
            pygame.Rect(cx - 14, top_y + 36, 28, 10))
        return

    shake_x = 0
    if state == 1:   # SHAKE
        progress = max(0, 55 - shake_timer)
        shake_x  = int(math.sin(frame * 1.2) * min(5, progress * 0.12))

    lx = cx + shake_x
    pts = [
        (lx - 14, int(top_y)),
        (lx + 14, int(top_y)),
        (lx,      int(top_y) + 50),
    ]
    pygame.draw.polygon(surf, (95, 75, 65), pts)
    pygame.draw.polygon(surf, (125, 100, 88), pts, 2)
    pygame.draw.line(surf, (155, 130, 115),
                     (lx - 4, int(top_y) + 6), (lx - 2, int(top_y) + 36), 2)

    if state == 1:   # dust flecks while shaking
        for i, ox in enumerate((-12, 0, 12)):
            pygame.draw.circle(surf, (140, 115, 100),
                (lx + ox, int(top_y) - 3), 2)


# ── Lava Pit ──────────────────────────────────────────────────────────────
# Visual size for one lava tile when the sprite is present. The lava strip
# tiles horizontally across the pit; height matches the molten body.
_LAVA_TILE_SIZE = (48, 48)

def _blit_lava_tile(surf, x, y, w, h, frame):
    """If assets/lava.png exists, tile its current frame across (x, y, w, h)
    and return True. Otherwise return False so the caller falls back to
    procedural drawing."""
    frames = get_animation("lava", LAVA_FRAMES, target_size=_LAVA_TILE_SIZE)
    if frames is None:
        return False
    idx = int(frame // 3) % len(frames)
    tile = frames[idx]
    tw, th = tile.get_size()
    # Tile horizontally; stretch one row vertically by repeating the tile.
    rows = max(1, (h + th - 1) // th)
    cols = max(1, (w + tw - 1) // tw)
    # Clip so we don't draw past the pit boundary.
    clip_prev = surf.get_clip()
    surf.set_clip(pygame.Rect(int(x), int(y), int(w), int(h)))
    for r in range(rows):
        for c in range(cols):
            surf.blit(tile, (int(x) + c * tw, int(y) + r * th))
    surf.set_clip(clip_prev)
    return True


def draw_lava_pit(surf, wx, width, cam_x, frame):
    sx = wx - cam_x
    if sx + width < 0 or sx > SCREEN_W:
        return
    pit_y  = GROUND_Y
    lava_y = pit_y + 32
    # Dark pit walls (always drawn — gives lava a recessed look)
    pygame.draw.rect(surf, (18, 10, 5),
                     pygame.Rect(int(sx), pit_y, int(width), 120))

    # Sprite path — tile the animated lava across the molten area.
    if _blit_lava_tile(surf, int(sx), lava_y, int(width), 88, frame):
        return

    # Procedural fallback ────────────────────────────────────────────────────
    # Lava body
    pygame.draw.rect(surf, LAVA_R,
                     pygame.Rect(int(sx), lava_y, int(width), 88))
    # Animated lava surface
    pts = [(int(sx), lava_y + 28), (int(sx), lava_y)]
    for i in range(0, int(width) + 1, 8):
        wx2 = sx + i
        wy2 = lava_y + int(math.sin(frame * 0.18 + i * 0.3) * 4)
        pts.append((int(wx2), int(wy2)))
    pts.append((int(sx) + int(width), lava_y + 28))
    if len(pts) >= 3:
        try:
            pygame.draw.polygon(surf, LAVA_Y, pts)
        except Exception:
            pass
    # Glow bubbles
    pulse = 0.5 + 0.5 * math.sin(frame * 0.1)
    for i in range(12, int(width), 28):
        bx = sx + i + math.sin(frame * 0.14 + i) * 4
        gr = max(2, int(3 + pulse * 2))
        pygame.draw.circle(surf, (255, int(190 + pulse * 40), 0), (int(bx), lava_y + 10), gr)


# ── Jail Cell ─────────────────────────────────────────────────────────────
def draw_jail_cell(surf, cx, cy, open_=False):
    w, h = 180, 200
    rx = cx - w//2
    ry = cy - h//2
    bar_color = (80, 80, 100)
    bar_cols = 7
    for i in range(bar_cols):
        x = rx + 10 + i * (w - 20) // (bar_cols - 1)
        bar_h = h if not (open_ and i == bar_cols//2) else h//2
        pygame.draw.rect(surf, bar_color, pygame.Rect(x-4, ry, 8, bar_h), border_radius=4)
    pygame.draw.rect(surf, dk(bar_color, 10), pygame.Rect(rx, ry, w, h), 6, border_radius=6)
    if not open_:
        pygame.draw.circle(surf, (180, 150, 20), (cx, ry + h//2), 10)


# ── Snow ──────────────────────────────────────────────────────────────────
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


# ── Level 1 Background ────────────────────────────────────────────────────
def draw_level1_bg(surf, cam_x, frame):
    for y in range(0, SCREEN_H, 4):
        t = y / SCREEN_H
        c = tuple(int(SKY_T[i] + (SKY_B[i]-SKY_T[i])*t) for i in range(3))
        pygame.draw.rect(surf, c, pygame.Rect(0, y, SCREEN_W, 4))

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
        for i in range(0, len(pts)-2, 2):
            if pts[i][1] < base_y - amplitude * 0.6:
                cx2 = pts[i][0]
                cy2 = pts[i][1]
                pygame.draw.circle(surf, SNOW_W, (cx2, cy2), 18)

    mtn_layer(-cam_x * 0.08, (165, 195, 220), 0.55, 120, 6)
    mtn_layer(-cam_x * 0.18, (118, 155, 195), 0.65, 160, 8)

    for y in range(int(SCREEN_H * 0.6), SCREEN_H, 3):
        t = (y - SCREEN_H*0.6) / (SCREEN_H*0.4)
        c = tuple(int(SNOW_W[i] + (SNOW_S[i]-SNOW_W[i])*t) for i in range(3))
        pygame.draw.rect(surf, c, pygame.Rect(0, y, SCREEN_W, 3))

    for s in _snow_cache:
        op = s['op']
        c = (int(220*op+35), int(235*op+20), int(255*op))
        pygame.draw.circle(surf, c, (int(s['x']), int(s['y'])), max(1, int(s['r'])))


# ── Level 2 Background ────────────────────────────────────────────────────
_cave_glow_cache = [(random.uniform(0, 4400), random.uniform(0, SCREEN_H),
                     random.uniform(20, 55), random.uniform(0, math.pi*2),
                     random.uniform(0.025, 0.06),
                     random.choice([28, 45, 200])) for _ in range(35)]

# The rock-tile pattern and the edge vignette never change, so they are built
# once and blitted — rebuilding them every frame was most of the cave's draw cost.
_cave_tile_cols = None
_cave_vignette = None

def _build_cave_bg_cache():
    global _cave_tile_cols, _cave_vignette
    # A column's tile rows depend only on (column index % 5).
    _cave_tile_cols = []
    for k in range(5):
        col = pygame.Surface((13, SCREEN_H + 20), pygame.SRCALPHA)
        for j in range(0, SCREEN_H + 20, 14):
            if (k * 31 + (j // 14) * 37) % 5 == 0:
                pygame.draw.rect(col, CAVE_MD, pygame.Rect(0, j, 13, 13))
        _cave_tile_cols.append(col)
    _cave_vignette = []
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
        pos = {'left': (0, 0), 'right': (SCREEN_W-80, 0),
               'top': (0, 0), 'bottom': (0, SCREEN_H-80)}[edge]
        _cave_vignette.append((vs, pos))


def draw_level2_bg(surf, cam_x, frame):
    surf.fill(CAVE_BG)

    if _cave_tile_cols is None:
        _build_cave_bg_cache()
    for i in range(0, SCREEN_W + 50, 14):
        surf.blit(_cave_tile_cols[int((i + cam_x) // 14) % 5], (i, 0))

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

    for vs, pos in _cave_vignette:
        surf.blit(vs, pos)

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
    gs2 = pygame.Surface((60, 60), pygame.SRCALPHA)
    pygame.draw.circle(gs2, (255, 140, 40, int(40+p*30)), (30, 30), 30)
    surf.blit(gs2, (sx-30, sy-30))


# ── Lives HUD (fox heads) ─────────────────────────────────────────────────
def draw_fox_head_icon(surf, cx, cy, alive=True):
    """Draw a small front-facing fox head for the lives HUD.
    alive=False draws it grayed-out with X eyes."""
    head_col  = FOX_OR if alive else (88, 84, 80)
    belly_col = BELLY_C if alive else (110, 106, 102)
    ear_in    = EAR_PK  if alive else (70, 66, 63)
    r = 13

    # Left pointy ear — outer orange triangle
    pygame.draw.polygon(surf, head_col, [
        (cx - 9,  cy - r + 2),
        (cx - 14, cy - r - 11),
        (cx - 1,  cy - r),
    ])
    # Left ear inner — pink triangle
    pygame.draw.polygon(surf, ear_in, [
        (cx - 9,  cy - r),
        (cx - 12, cy - r - 7),
        (cx - 3,  cy - r - 1),
    ])

    # Right pointy ear — outer orange triangle
    pygame.draw.polygon(surf, head_col, [
        (cx + 9,  cy - r + 2),
        (cx + 14, cy - r - 11),
        (cx + 1,  cy - r),
    ])
    # Right ear inner — pink triangle
    pygame.draw.polygon(surf, ear_in, [
        (cx + 9,  cy - r),
        (cx + 12, cy - r - 7),
        (cx + 3,  cy - r - 1),
    ])

    # Main head circle
    pygame.draw.circle(surf, head_col, (cx, cy), r)

    # Cream snout / muzzle (lower-face oval)
    pygame.draw.ellipse(surf, belly_col, pygame.Rect(cx - 7, cy + 1, 14, 11))

    if alive:
        # Eyes
        pygame.draw.circle(surf, (30, 15, 5),   (cx - 5, cy - 2), 3)
        pygame.draw.circle(surf, (30, 15, 5),   (cx + 5, cy - 2), 3)
        # Shine dots
        pygame.draw.circle(surf, WHITE, (cx - 4, cy - 3), 1)
        pygame.draw.circle(surf, WHITE, (cx + 6, cy - 3), 1)
        # Nose
        pygame.draw.ellipse(surf, (30, 10, 5),
                            pygame.Rect(cx - 3, cy + 4, 6, 4))
    else:
        # X eyes (used life)
        pygame.draw.line(surf, (55, 55, 55), (cx - 8, cy - 5), (cx - 3, cy), 2)
        pygame.draw.line(surf, (55, 55, 55), (cx - 3, cy - 5), (cx - 8, cy), 2)
        pygame.draw.line(surf, (55, 55, 55), (cx + 3, cy - 5), (cx + 8, cy), 2)
        pygame.draw.line(surf, (55, 55, 55), (cx + 8, cy - 5), (cx + 3, cy), 2)


def draw_lives_hud(surf, lives):
    """Draw 3 fox heads in the top-right corner; grayed-out heads = used lives."""
    for i in range(3):
        cx = SCREEN_W - 155 + i * 46
        cy = 29
        draw_fox_head_icon(surf, cx, cy, alive=(i < lives))


# ── HUD ───────────────────────────────────────────────────────────────────
def draw_hud(surf, score, level_name, frame):
    draw_rounded_rect(surf, (0,0,0,160), pygame.Rect(10, 10, 180, 38), 10)
    txt(surf, f"Score: {score}", FONT_SM, GOLD, 100, 29)
    # Box grows with the title so long names ("Level 1: Snowy Mountains") fit.
    box_w = max(200, FONT_SM.size(level_name)[0] + 28)
    draw_rounded_rect(surf, (0,0,0,160), pygame.Rect(SCREEN_W//2 - box_w//2, 10, box_w, 38), 10)
    txt(surf, level_name, FONT_SM, WHITE, SCREEN_W//2, 29)


# ── Leaderboard Block ─────────────────────────────────────────────────────
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


# ── Heart ───────────────────────────────────────────────────────────────────
def draw_heart(surf, cx, cy, size=10, color=(255, 120, 150)):
    """Small heart centred roughly at (cx, cy)."""
    s = max(4, int(size))
    r = max(2, s // 3)
    ty = cy - r
    pygame.draw.circle(surf, color, (cx - r, ty), r)
    pygame.draw.circle(surf, color, (cx + r, ty), r)
    pygame.draw.polygon(surf, color,
        [(cx - 2 * r, ty), (cx + 2 * r, ty), (cx, cy + 2 * r)])


# ── Bunny (friendly home animal) ─────────────────────────────────────────────
def draw_bunny(surf, cx, cy, facing_right=True, anim=0, scale=1.0,
               color=(238, 238, 244)):
    """Cute little bunny. cy is feet level (rect.bottom)."""
    s = scale
    d = 1 if facing_right else -1
    hop = int(abs(math.sin(anim * 0.12)) * 2 * s)
    cy = int(cy - hop)
    # Feet
    pygame.draw.ellipse(surf, dk(color, 14),
        pygame.Rect(cx - int(13 * s), cy - int(6 * s), int(13 * s), int(6 * s)))
    pygame.draw.ellipse(surf, dk(color, 14),
        pygame.Rect(cx + int(1 * s), cy - int(6 * s), int(13 * s), int(6 * s)))
    # Body
    bw, bh = int(28 * s), int(26 * s)
    pygame.draw.ellipse(surf, color,
        pygame.Rect(cx - bw // 2, cy - int(5 * s) - bh, bw, bh))
    # Fluffy tail
    pygame.draw.circle(surf, lt(color, 10),
        (cx - int(13 * s) * d, cy - int(12 * s)), int(6 * s))
    # Head
    hx = cx + int(9 * s) * d
    hy = cy - int(26 * s)
    pygame.draw.circle(surf, color, (hx, hy), int(11 * s))
    # Ears
    for off in (-int(5 * s), int(2 * s)):
        pygame.draw.ellipse(surf, color,
            pygame.Rect(hx + off, hy - int(28 * s), int(6 * s), int(24 * s)))
        pygame.draw.ellipse(surf, EAR_PK,
            pygame.Rect(hx + off + int(1 * s), hy - int(25 * s), int(3 * s), int(17 * s)))
    # Eye + nose
    pygame.draw.circle(surf, (40, 26, 26),
        (hx + int(4 * s) * d, hy - int(2 * s)), max(1, int(2 * s)))
    pygame.draw.circle(surf, EAR_PK,
        (hx + int(9 * s) * d, hy + int(2 * s)), max(1, int(2 * s)))


# ── Cozy House (Level 4 — the back of the cave) ──────────────────────────────
def draw_house(surf, wx, wy, cam_x, frame=0):
    """Warm cabin. wx = centre x (world), wy = ground level (house bottom)."""
    cx = wx - cam_x
    if cx < -320 or cx > SCREEN_W + 320:
        return
    W, H = 300, 200
    left = int(cx - W // 2)
    top  = int(wy - H)
    pulse = 0.5 + 0.5 * math.sin(frame * 0.05)
    # Warm glow behind the house
    glow = pygame.Surface((W + 200, H + 200), pygame.SRCALPHA)
    pygame.draw.ellipse(glow, (255, 190, 90, int(45 + pulse * 25)), glow.get_rect())
    surf.blit(glow, (left - 100, top - 90))
    # Walls (log cabin)
    wall = pygame.Rect(left, top, W, H)
    pygame.draw.rect(surf, (120, 78, 44), wall, border_radius=6)
    pygame.draw.rect(surf, (92, 58, 30), wall, 4, border_radius=6)
    for ly in range(top + 22, top + H - 6, 22):
        pygame.draw.line(surf, (92, 58, 30), (left + 3, ly), (left + W - 3, ly), 2)
    # Roof
    roof = [(left - 22, top + 6), (int(cx), top - 86), (left + W + 22, top + 6)]
    pygame.draw.polygon(surf, (96, 52, 40), roof)
    pygame.draw.polygon(surf, (70, 38, 28), roof, 4)
    # Chimney + smoke
    chim = pygame.Rect(left + W - 72, top - 64, 26, 46)
    pygame.draw.rect(surf, (80, 46, 34), chim)
    for i in range(4):
        t = (frame * 0.02 + i * 0.25) % 1.0
        sxk = chim.centerx + int(math.sin(frame * 0.06 + i) * 10)
        syk = chim.top - int(t * 60)
        rr = int(5 + t * 12)
        ssurf = pygame.Surface((rr * 2 + 2, rr * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(ssurf, (210, 210, 220, int(120 * (1 - t))), (rr + 1, rr + 1), rr)
        surf.blit(ssurf, (sxk - rr, syk - rr))
    # Door with warm light spilling out
    door = pygame.Rect(int(cx - 34), top + H - 96, 68, 96)
    pygame.draw.rect(surf, (70, 42, 22), door, border_radius=6)
    dl = pygame.Surface((door.width, door.height), pygame.SRCALPHA)
    dl.fill((255, 210, 120, int(70 + pulse * 30)))
    surf.blit(dl, (door.x, door.y))
    pygame.draw.rect(surf, (44, 26, 12), door, 3, border_radius=6)
    pygame.draw.circle(surf, (240, 210, 90), (door.right - 12, door.centery), 4)
    # Windows with flickering warm glow
    for wxk in (left + 40, left + W - 78):
        win = pygame.Rect(wxk, top + 40, 38, 40)
        flick = 0.6 + 0.4 * math.sin(frame * 0.12 + wxk * 0.05)
        pygame.draw.rect(surf, (255, int(190 * flick + 50), int(90 * flick)), win, border_radius=4)
        pygame.draw.rect(surf, (70, 40, 24), win, 3, border_radius=4)
        pygame.draw.line(surf, (70, 40, 24), (win.centerx, win.top), (win.centerx, win.bottom), 2)
        pygame.draw.line(surf, (70, 40, 24), (win.left, win.centery), (win.right, win.centery), 2)
    # A little heart over the door — this is home
    hb = int(math.sin(frame * 0.08) * 3)
    draw_heart(surf, int(cx), top - 6 + hb, 16, (255, 110, 140))


# ── Storm (triggered when a coin is collected) ───────────────────────────────
# When True, picking up a coin triggers a visible storm in EVERY level (Ella's
# wish). Set to False to limit the rain + lightning to Level 4 only.
STORM_IN_ALL_LEVELS = True

STORM_DECAY_FRAMES = 240            # ~4 seconds to fade back to clear
STORM_COOLDOWN_FRAMES = 1200        # ~20 s minimum between storms (no constant rain)
_storm = {'strength': 0.0, 'flash': 0.0, 'cooldown': 0}
_rain = []

def _build_rain(count=170):
    global _rain
    _rain = [{'x': random.uniform(0, SCREEN_W),
              'y': random.uniform(0, SCREEN_H),
              'len': random.uniform(12, 22),
              'v': random.uniform(9, 16)} for _ in range(count)]

_build_rain()

def reset_storm():
    """Clear the sky immediately (e.g. on entering a new level)."""
    _storm['strength'] = 0.0
    _storm['flash'] = 0.0
    _storm['cooldown'] = 0

def trigger_storm(strength=1.0):
    """Start a storm — called on coin pickup. Ignored while cooling down, so the
    storm stays an occasional treat instead of near-constant rain."""
    if _storm['cooldown'] > 0:
        return
    _storm['strength'] = min(1.4, _storm['strength'] + strength)
    _storm['flash'] = 1.0          # a bright lightning flash on pickup
    _storm['cooldown'] = STORM_COOLDOWN_FRAMES

def update_storm():
    s = _storm
    if s['cooldown'] > 0:
        s['cooldown'] -= 1
    if s['strength'] > 0:
        s['strength'] = max(0.0, s['strength'] - 1.0 / STORM_DECAY_FRAMES)
        for d in _rain:
            d['y'] += d['v'] * (0.6 + s['strength'])
            d['x'] -= d['v'] * 0.35
            if d['y'] > SCREEN_H:
                d['y'] = -d['len']
                d['x'] = random.uniform(0, SCREEN_W)
            if d['x'] < 0:
                d['x'] += SCREEN_W
    if s['flash'] > 0:
        s['flash'] = max(0.0, s['flash'] - 0.06)
    # occasional extra lightning while the storm is strong
    if s['strength'] > 0.5 and random.random() < 0.02:
        s['flash'] = 1.0

def draw_storm(surf):
    s = _storm
    if s['strength'] <= 0.02 and s['flash'] <= 0.02:
        return
    st = min(1.0, s['strength'])
    if st > 0.02:
        dim = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        dim.fill((24, 28, 48, int(95 * st)))
        surf.blit(dim, (0, 0))
        col = (165, 195, 235)
        for d in _rain:
            x = int(d['x']); y = int(d['y'])
            pygame.draw.line(surf, col, (x, y), (x - 3, y + int(d['len'])), 1)
    if s['flash'] > 0.02:
        fl = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        fl.fill((255, 255, 255, int(140 * s['flash'])))
        surf.blit(fl, (0, 0))
