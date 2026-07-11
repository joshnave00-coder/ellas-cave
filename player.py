"""player.py — Player class (Ella)."""
import pygame, math
from constants import (
    SCREEN_W, SCREEN_H, GROUND_Y,
    GRAVITY, MAX_FALL, JUMP_VEL, MOVE_SPEED, ICE_KEY,
    FOX_OR, SNOW_W, COIN_Y, ICE_BL,
    FONT_XS, lt, txt,
)
from drawing import draw_fox, draw_ice_bridge, particles, trigger_storm
from entities import IceBridge


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
        self.in_tube = False
        self.death_cause = None
        self.invincible_timer = 0  # frames of post-revive invincibility

    @property
    def vulnerable(self):
        return not self.dead and self.invincible_timer == 0

    def center(self):
        return self.rect.centerx, self.rect.centery

    def handle_input(self, keys):
        if self.in_tube:
            return
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
        if self.ice_cooldown > 0 or not self.has_ice:
            return False
        bx = self.rect.right + 10 if self.facing_right else self.rect.left - 230
        by = self.rect.bottom          # bridge surface flush with Ella's feet
        bridge = IceBridge(bx, by, 220)
        self.ice_bridges.append(bridge)
        self.ice_cooldown = 960        # matches bridge life exactly
        particles.burst(self.rect.centerx, self.rect.bottom,
                        ICE_BL, 25, 5, 5, 55, -0.15)
        return True

    def update(self, platforms, spikes, coins, tubes, lava_wall=None):
        self.ice_cooldown = max(0, self.ice_cooldown - 1)
        if self.invincible_timer > 0:
            self.invincible_timer -= 1

        self.ice_bridges = [b for b in self.ice_bridges if b.update()]
        for b in self.ice_bridges:
            if b.build_progress < 0.5:
                particles.burst(
                    b.rect.x + int(b.rect.width * b.build_progress),
                    b.rect.y, ICE_BL, 3, 2, 3, 20, 0)

        # Stop horizontal drift when dead
        if self.dead:
            self.vx = 0

        # While sinking into a tube: only move downward, skip all other physics
        if self.in_tube:
            self.rect.y += int(self.vy)
            self.anim += 1
            return

        self.vy += GRAVITY
        if self.vy > MAX_FALL:
            self.vy = MAX_FALL

        self.rect.x += int(self.vx)
        self.rect.x = max(0, self.rect.x)
        # Platforms are pass-through from the sides and below — top-only landing.
        # Ice bridges retain side-collision so Ella can walk up to and onto them.
        for b in self.ice_bridges:
            if self.rect.colliderect(b.rect):
                if self.vx > 0:
                    self.rect.right = b.rect.left
                elif self.vx < 0:
                    self.rect.left = b.rect.right

        self.rect.y += int(self.vy)
        self.on_ground = False
        # Tube tops act as one-way landing platforms
        all_rects = ([p.rect for p in platforms]
                     + [b.rect for b in self.ice_bridges]
                     + [t.rect for t in tubes])
        for pr in all_rects:
            if self.rect.colliderect(pr) and self.vy > 0:
                if self.rect.bottom - self.vy <= pr.top + 10:
                    self.rect.bottom = pr.top
                    self.vy = 0
                    self.on_ground = True

        if self.rect.top > SCREEN_H + 60:
            self.dead = True
            self.death_cause = 'fall'
            return

        for s in spikes:
            if self.rect.colliderect(s.rect) and self.invincible_timer == 0:
                self.dead = True
                self.death_cause = 'spike'
                return

        for c in coins:
            if not c.collected and self.rect.colliderect(c.rect.inflate(14, 14)):
                c.collected = True
                self.score += 10
                particles.burst(c.cx, c.cy, COIN_Y, 10, 3, 4, 30, 0)
                trigger_storm()   # grabbing a coin kicks off a storm

        # in_range: player is resting on top of the tube.
        # Use vy <= 1.5 instead of on_ground: integer gravity rounding causes
        # on_ground to toggle every other frame, producing visible text flicker.
        for tube in tubes:
            on_top = (self.vy <= 1.5
                      and abs(self.rect.bottom - tube.rect.top) <= 2
                      and self.rect.right > tube.rect.left + 4
                      and self.rect.left < tube.rect.right - 4)
            tube.in_range = on_top

        if lava_wall and lava_wall.active and lava_wall.width > 2:
            if self.rect.colliderect(lava_wall.rect) and self.invincible_timer == 0:
                self.dead = True
                self.death_cause = 'lava'
                return

        self.anim += 1

    def draw(self, surf, cam_x):
        draw_fox(surf, self.rect.centerx - cam_x, self.rect.bottom,
                 self.facing_right, self.anim, 1.0, FOX_OR, True)
        for b in self.ice_bridges:
            draw_ice_bridge(surf, b.rect, cam_x, b.build_progress, self.anim)

        if self.ice_cooldown > 0:
            frac = self.ice_cooldown / 960          # drains 1→0 as bridge expires
            last_20 = self.ice_cooldown < 192       # final 20% of bridge life
            if last_20:
                pulse = 0.5 + 0.5 * math.sin(self.anim * 0.35)
                bar_color = (int(220 + 35 * pulse), int(40 * (1 - pulse)), 20)
            else:
                bar_color = ICE_BL
            bar_r = pygame.Rect(SCREEN_W - 315, 20, 120, 14)
            pygame.draw.rect(surf, (30, 30, 50), bar_r, border_radius=7)
            pygame.draw.rect(surf, bar_color,
                pygame.Rect(bar_r.x, bar_r.y, int(bar_r.width * frac), bar_r.height),
                border_radius=7)
            pygame.draw.rect(surf, lt(ICE_BL), bar_r, 2, border_radius=7)
            label = "MELTING!" if last_20 else "ICE"
            txt(surf, label, FONT_XS, bar_color, SCREEN_W - 355, 27, shadow=False)
        else:
            txt(surf, "[X] ICE READY", FONT_XS, ICE_BL, SCREEN_W - 260, 27, shadow=False)
