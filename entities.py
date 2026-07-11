"""entities.py — game entity classes: Platform, Spike, Coin, Tube, IceBridge,
LavaPool, NetProjectile, PolarBear, HumanGuard, FoxFriend."""
import pygame, math, random
from constants import (
    SCREEN_W, SCREEN_H, GROUND_Y, GRAVITY,
    LAVA_O, LAVA_R, LAVA_Y,
    NET_BR,
    FOX_OR,
)
from drawing import (
    draw_polar_bear, draw_human, draw_net_proj, draw_ice_bridge, draw_fox,
    draw_cave_bat, draw_falling_rock, draw_bunny, draw_heart,
    _blit_lava_tile, _aa_poly,
)


class Platform:
    def __init__(self, x, y, w, h=25):
        self.rect = pygame.Rect(x, y, w, h)
        self.is_cave = False


class Spike:
    def __init__(self, cx, y):
        self.cx = cx
        self.y = y
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
        self.life = 960
        self.max_life = 960
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
    """Ground-level lava pool that flows from the volcano base rightward."""
    ANCHOR_X  = 3295
    MAX_WIDTH = 220
    GROW_RATE = 0.25
    HEIGHT    = 30

    def __init__(self):
        self.active = False
        self.width  = 0.0

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

        # Try the lava sprite for the pool body. If absent, draw the
        # procedural pool body (rect + animated surface + glow bubbles).
        used_sprite = _blit_lava_tile(surf, pool_x, pool_y, pool_w,
                                      self.HEIGHT + 50, frame)
        pulse = 0.5 + 0.5 * math.sin(frame * 0.14)
        if not used_sprite:
            pygame.draw.rect(surf, LAVA_R,
                pygame.Rect(int(pool_x), pool_y, pool_w, self.HEIGHT + 50))
            if pool_w > 6:
                pygame.draw.rect(surf, LAVA_O,
                    pygame.Rect(int(pool_x) + 2, pool_y + 4, pool_w - 4, self.HEIGHT - 6))
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
            for gi in range(0, pool_w, 25):
                gx = pool_x + gi + int(math.sin(frame * 0.12 + gi) * 6)
                gy = pool_y + 7
                gr = max(2, int(4 + math.sin(frame * 0.22 + gi * 0.5) * 2))
                brightness = int(215 + pulse * 40)
                pygame.draw.circle(surf, (brightness, 220, 0), (int(gx), int(gy)), gr)

        # Volcano → pool stream: a smooth tapering molten ribbon (always drawn,
        # sprite or not, so the volcano-to-pool connection reads cleanly).
        stream_sx = (3100 + 135) - cam_x
        stream_sy = GROUND_Y - 185 + 12
        stream_ex = pool_x + 4
        stream_ey = pool_y
        if stream_sx < SCREEN_W + 80 and stream_ex > -80:
            N = 16
            def _pt(t):
                lx = stream_sx + (stream_ex - stream_sx) * t
                ly = stream_sy + (stream_ey - stream_sy) * t
                lx += math.sin(frame * 0.14 + t * 5) * 3   # gentle wobble
                return lx, ly
            left, right, core = [], [], []
            for ti in range(N + 1):
                t = ti / N
                lx, ly = _pt(t)
                half = 2.5 + t * 8                          # widens toward the pool
                left.append((lx - half, ly))
                right.append((lx + half, ly))
                core.append((int(lx), int(ly)))
            _aa_poly(surf, left + right[::-1], (200, 34, 0))     # outer molten body
            if len(core) >= 2:
                pygame.draw.lines(surf, (255, 120, 10), False, core, 5)   # hot core
                pygame.draw.lines(surf, (255, 210, 70), False, core, 2)   # bright centre
            # glowing globs sliding down the flow
            for gi in range(3):
                gt = ((frame * 0.012 + gi / 3.0) % 1.0)
                gx, gy = _pt(gt)
                pygame.draw.circle(surf, (255, 200, 60),
                                   (int(gx), int(gy)), max(2, int(3 + gt * 3)))


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
        self.chase_speed = 1.6
        self.chasing = False
        self.freeze_timer = 0  # frames remaining where bear is frozen

    def update(self, player_x, player_y):
        if self.freeze_timer > 0:
            self.freeze_timer -= 1
            return
        dx = abs((self.rect.centerx) - player_x)
        dy = abs((self.rect.centery) - player_y)
        self.chasing = dx < 200 and dy < 130

        spd = self.chase_speed if self.chasing else self.speed
        if self.chasing:
            dx_signed = player_x - self.rect.centerx
            if abs(dx_signed) < 6:
                # Close enough horizontally — stand still to avoid rapid flip-flopping
                # when the player is on a ledge directly above
                self.vx = 0
            else:
                self.vx = spd if dx_signed > 0 else -spd
        else:
            if self.rect.left <= self.patrol_min:
                self.vx = spd
            elif self.rect.right >= self.patrol_max:
                self.vx = -spd

        if self.vx != 0:
            self.facing_right = self.vx > 0
        self.rect.x += int(self.vx)
        # Stay on the home platform — never drift or chase across a gap. Ella
        # can't walk on air over a hole, so neither should the bear.
        if self.rect.left < self.patrol_min:
            self.rect.left = self.patrol_min
        elif self.rect.right > self.patrol_max:
            self.rect.right = self.patrol_max
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
        self.throw_interval = 320
        self.frame = 0
        self.nets = []
        self.caught_timer = 0
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
            spd = 2.5
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
    def __init__(self, x, y, color, scale, level=2):
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
        self._flip_cd = 20  # start with a short cooldown so first-frame flips are suppressed

    def update(self, platforms, spikes=None):
        self.vy += GRAVITY * 0.5
        self.vy = min(self.vy, 12)

        # ── Edge & spike detection (only when grounded, with flip cooldown) ──
        # Foxes respect the same gaps Ella does: they turn around at the edge of
        # solid ground rather than strolling across a pit.
        if self.on_ground:
            # Edge safety ALWAYS runs (even during the flip cooldown) so a fox can
            # never stroll off the edge of solid ground into a pit. The cooldown
            # only debounces spike/idle turns, never the cliff check.
            lead   = (self.rect.right + 6) if self.vx > 0 else (self.rect.left - 6)
            foot_y = self.rect.bottom
            has_ground_ahead = any(
                p.rect.left <= lead <= p.rect.right
                and abs(p.rect.top - foot_y) < 6
                for p in platforms
            )
            if not has_ground_ahead:
                self.vx = -self.vx
                self._flip_cd = 20
            elif self._flip_cd > 0:
                self._flip_cd -= 1
            elif spikes:
                for spike in spikes:
                    sdx = spike.cx - self.rect.centerx
                    if 0 < sdx < 55 and self.vx > 0:
                        self.vx = -abs(self.vx)
                        self._flip_cd = 20
                        break
                    elif -55 < sdx < 0 and self.vx < 0:
                        self.vx = abs(self.vx)
                        self._flip_cd = 20
                        break

        self.x += self.vx
        self.y += self.vy
        self.rect.x = int(self.x - self.rect.width//2)
        self.rect.y = int(self.y - self.rect.height)

        # Land on platform tops only — the ground itself is made of platforms, so
        # over a pit there is no invisible floor to hover on.
        self.on_ground = False
        for p in platforms:
            if self.rect.colliderect(p.rect):
                if self.vy >= 0 and self.rect.bottom - self.vy <= p.rect.top + 8:
                    self.rect.bottom = p.rect.top
                    self.y = float(self.rect.bottom)
                    self.vy = 0
                    self.on_ground = True

        # Safety net: should a fox ever slip into a pit, bounce it back up onto
        # solid ground and turn it around so friends never vanish below.
        if not self.on_ground and self.rect.top > GROUND_Y + 40:
            self.vx = -self.vx
            self._flip_cd = 20
            self.rect.bottom = GROUND_Y
            self.y = float(GROUND_Y)
            self.vy = 0.0
            self.on_ground = True
            self.x += self.vx * 6
            self.rect.x = int(self.x - self.rect.width // 2)

        if self.on_ground:
            self.bounce_offset = math.sin(self.bounce_phase) * 4
            self.bounce_phase += 0.08
            if random.random() < 0.005:
                self.vx = -self.vx
        self.facing_right = self.vx >= 0
        self.anim += 1

    def draw(self, surf, cam_x):
        draw_fox(surf, self.rect.centerx - cam_x,
                 self.rect.bottom + int(self.bounce_offset),
                 self.facing_right, self.anim, self.scale, self.color, False)


# ── Moving Platform ───────────────────────────────────────────────────────
class MovingPlatform(Platform):
    """Platform that oscillates smoothly between two points."""
    def __init__(self, x, y, w, h=20, x2=None, y2=None, speed=1.0):
        super().__init__(x, y, w, h)
        self.ox = float(x);  self.oy = float(y)
        self.tx = float(x2 if x2 is not None else x)
        self.ty = float(y2 if y2 is not None else y)
        self.t  = 0.0
        self.dt = speed * 0.005
        self.is_cave = True
        self.dx = 0

    def update(self):
        prev_x = self.rect.x
        self.t += self.dt
        if self.t >= 1.0 or self.t <= 0.0:
            self.dt = -self.dt
            self.t  = max(0.0, min(1.0, self.t))
        frac = (math.sin(self.t * math.pi - math.pi / 2) + 1) * 0.5
        self.rect.x = int(self.ox + (self.tx - self.ox) * frac)
        self.rect.y = int(self.oy + (self.ty - self.oy) * frac)
        self.dx = self.rect.x - prev_x


# ── Cave Bat ──────────────────────────────────────────────────────────────
class CaveBat:
    """Bat enemy — patrols horizontally, dips aggressively when player is near."""
    def __init__(self, x, y, patrol_min, patrol_max, speed=1.5):
        self.x = float(x)
        self.base_y = float(y)
        self.y = float(y)
        self.patrol_min = float(patrol_min)
        self.patrol_max = float(patrol_max)
        self.speed = speed
        self.vx = speed
        self.anim = random.uniform(0, 100)
        self.facing_right = True
        self.w, self.h = 36, 22
        self.rect = pygame.Rect(int(x) - 18, int(y) - 11, 36, 22)

    def update(self, player_rect):
        dx = abs(self.x - player_rect.centerx)
        dip = math.sin(self.anim * 0.06) * (50 if dx < 200 else 18)
        self.y = self.base_y + dip
        self.x += self.vx
        if self.x <= self.patrol_min:
            self.vx = abs(self.speed)
        elif self.x >= self.patrol_max:
            self.vx = -abs(self.speed)
        self.facing_right = self.vx > 0
        self.anim += 1
        self.rect.center = (int(self.x), int(self.y))

    def draw(self, surf, cam_x, frame):
        draw_cave_bat(surf, self.x - cam_x, self.y, self.facing_right, self.anim)


# ── Falling Rock (Stalactite) ─────────────────────────────────────────────
class FallingRock:
    """Stalactite that shakes then plummets when the player walks below."""
    IDLE    = 0
    SHAKE   = 1
    FALLING = 2
    LANDED  = 3

    W, H = 28, 50

    def __init__(self, x, ceiling_y=10):
        self.x = float(x)
        self.y = float(ceiling_y)
        self.state = self.IDLE
        self.shake_timer = 0
        self.vy = 0.0
        self.anim = 0
        self.rect = pygame.Rect(int(x) - self.W // 2, int(ceiling_y), self.W, self.H)

    def update(self, player_rect):
        self.anim += 1
        if self.state == self.IDLE:
            if (abs(player_rect.centerx - self.x) < 70 and
                    player_rect.centery < GROUND_Y - 20):
                self.state = self.SHAKE
                self.shake_timer = 55
        elif self.state == self.SHAKE:
            self.shake_timer -= 1
            if self.shake_timer <= 0:
                self.state = self.FALLING
                self.vy = 1.0
        elif self.state == self.FALLING:
            self.vy += GRAVITY * 0.9
            self.y += self.vy
            self.rect.topleft = (int(self.x) - self.W // 2, int(self.y))
            if self.rect.bottom >= GROUND_Y:
                self.rect.bottom = GROUND_Y
                self.y = float(self.rect.top)
                self.state = self.LANDED
        return True

    def draw(self, surf, cam_x, frame):
        draw_falling_rock(surf, int(self.x - cam_x), int(self.y),
                          self.state, self.shake_timer, frame)


# ── Home Animal (Level 4 — friendly & huggable) ─────────────────────────────
class HomeAnimal:
    """A gentle, huggable animal for Ella's home. Never harms the player.
    Wanders slowly on the flat ground and hops happily with a puff of hearts
    when hugged. kind is one of 'fox', 'bear', 'bunny'."""

    def __init__(self, x, kind='fox', color=None, scale=1.0, wander=True,
                 min_x=80, max_x=3000):
        self.kind  = kind
        self.x     = float(x)
        self.base_y = GROUND_Y
        self.color = color if color is not None else FOX_OR
        self.scale = scale
        self.wander = wander
        self.min_x = min_x
        self.max_x = max_x
        self.vx = (random.choice([-1, 1]) * random.uniform(0.3, 0.8)) if wander else 0.0
        self.facing_right = self.vx >= 0
        self.anim = random.uniform(0, 100)
        self.bob_phase = random.uniform(0, math.pi * 2)
        self.hugged = False
        self.bounce = 0.0          # vertical hop offset (negative = up)
        self.bounce_vel = 0.0
        self.hearts = []
        self.w = max(34, int(48 * scale))
        self.h = max(40, int(56 * scale))

    @property
    def rect(self):
        return pygame.Rect(int(self.x - self.w / 2), int(self.base_y - self.h),
                           self.w, self.h)

    @property
    def hug_rect(self):
        return self.rect.inflate(54, 36)

    def hug(self):
        """Happy hop + a puff of hearts. Returns True if this is the first hug."""
        first = not self.hugged
        self.hugged = True
        if self.bounce == 0.0 and self.bounce_vel == 0.0:
            self.bounce_vel = -5.5
        for _ in range(5):
            self.hearts.append({
                'x': self.x + random.uniform(-14, 14),
                'y': self.base_y - self.h - random.uniform(0, 10),
                'vy': random.uniform(-1.8, -1.0),
                'life': random.randint(30, 44),
                'max': 44,
                'size': random.randint(8, 13),
            })
        return first

    def update(self):
        self.anim += 1
        self.bob_phase += 0.06
        if self.wander:
            self.x += self.vx
            if self.x <= self.min_x:
                self.x = self.min_x; self.vx = abs(self.vx)
            elif self.x >= self.max_x:
                self.x = self.max_x; self.vx = -abs(self.vx)
            elif random.random() < 0.008:
                self.vx = -self.vx
            if self.vx != 0:
                self.facing_right = self.vx > 0
        # happy hop physics
        if self.bounce_vel != 0.0 or self.bounce < 0.0:
            self.bounce += self.bounce_vel
            self.bounce_vel += 0.6
            if self.bounce >= 0.0:
                self.bounce = 0.0
                self.bounce_vel = 0.0
        for hh in self.hearts:
            hh['y'] += hh['vy']
            hh['life'] -= 1
        self.hearts = [hh for hh in self.hearts if hh['life'] > 0]

    def draw(self, surf, cam_x):
        sx = int(self.x - cam_x)
        bob = math.sin(self.bob_phase) * 2
        feet_y = int(self.base_y + self.bounce + bob)
        if self.kind == 'bear':
            draw_polar_bear(surf, sx, feet_y, self.facing_right, self.anim)
        elif self.kind == 'bunny':
            draw_bunny(surf, sx, feet_y, self.facing_right, self.anim,
                       self.scale, self.color)
        else:
            draw_fox(surf, sx, feet_y, self.facing_right, self.anim,
                     self.scale, self.color, False)
        for hh in self.hearts:
            a = hh['life'] / hh['max']
            draw_heart(surf, int(hh['x'] - cam_x), int(hh['y']),
                       int(hh['size'] * (0.6 + 0.4 * a)),
                       (255, int(90 + 70 * a), int(140 + 50 * a)))
