"""zones.py — Level1 (Snowy Mountains), Level2 (The Cave), Level3 (The Deep Cave),
Level4 (Ella's Home — a warm, safe free-roam ending)."""
import pygame, math
from constants import (
    SCREEN_W, SCREEN_H, GROUND_Y, ICE_KEY, DOWN_KEY, GOLD,
    FONT_XS, FONT_SM, FONT_MD, FONT_LG, txt,
)
from drawing import (
    draw_level1_bg, draw_level2_bg,
    draw_platform_snow, draw_platform_cave,
    draw_spike_set, draw_coin, draw_tube,
    draw_volcano, draw_cave_entrance, draw_treasure_chest,
    draw_hud, update_snow, particles,
    draw_lava_pit,
    draw_human, draw_house, draw_heart,
    update_storm, draw_storm, reset_storm, STORM_IN_ALL_LEVELS,
)
from entities import LavaPool, MovingPlatform, FallingRock
from player import Player
from levels import (
    make_level1_platforms, make_level1_spikes, make_level1_coins,
    make_level1_bears, make_level1_guards, make_level1_tubes,
    make_level2_platforms, make_level2_spikes, make_level2_coins,
    make_fox_friends,
)
from levels_z3 import (
    make_level3_platforms, make_level3_spikes, make_level3_coins,
    make_level3_bats, make_level3_falling_rocks, make_level3_guards,
    make_level3_fox_friends,
    LEVEL_W as _Z3_LEVEL_W, CHEST_X as _Z3_CHEST_X,
    CHEST_Y as _Z3_CHEST_Y, PITS as _Z3_PITS,
)
from levels_z4 import (
    make_level4_platforms, make_level4_coins,
    make_level4_people, make_level4_animals,
    LEVEL_W as _Z4_LEVEL_W, HOUSE_X as _Z4_HOUSE_X,
    HOUSE_Y as _Z4_HOUSE_Y, DOOR_RECT as _Z4_DOOR_RECT,
)


class Level1:
    LEVEL_W = 6600
    LAVA_TRIGGER_X = 3100
    CAVE_ENTRANCE_X = 6100
    CAVE_ENTRANCE_Y = GROUND_Y - 130

    # Kill rect covering the volcano cone (upper slopes) — above GROUND_Y-100
    # so players walking at ground level past the base are unaffected.
    VOLCANO_KILL_RECT = pygame.Rect(3140, GROUND_Y - 185, 120, 100)

    def __init__(self, player_score=0, start_x=100, start_y=GROUND_Y, bear_freeze=0):
        self.platforms = make_level1_platforms()
        self.spikes    = make_level1_spikes()
        self.coins     = make_level1_coins()
        self.bears     = make_level1_bears()
        self.guards    = make_level1_guards()
        self.tubes     = make_level1_tubes()
        self.lava      = LavaPool()
        self.player    = Player(start_x, start_y)
        self.player.score = player_score
        if bear_freeze:
            for b in self.bears:
                b.freeze_timer = bear_freeze
        self.cam_x     = 0
        self.frame     = 0
        self.jail_return = None
        self.net_catch = False
        self.entering_tube = None  # tube currently being entered
        self.cave_bonus_awarded = False

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

            # Tube entry: teleport when player has sunk fully inside
            if self.entering_tube is not None:
                if self.player.rect.bottom >= self.entering_tube.rect.bottom:
                    t = self.entering_tube
                    self.player.rect.x = t.dest_x
                    self.player.rect.y = t.dest_y - self.player.H
                    self.player.vy = 0
                    self.player.in_tube = False
                    self.entering_tube = None
                    particles.burst(t.dest_x + 28, t.dest_y,
                                    (80, 200, 100), 15, 4, 4, 30, -0.1)
            else:
                for tube in self.tubes:
                    if tube.in_range and keys[DOWN_KEY]:
                        self.player.in_tube = True
                        self.player.vx = 0
                        self.player.vy = 4  # slow sink speed (px/frame)
                        self.entering_tube = tube
                        break

        if self.player.rect.x >= self.LAVA_TRIGGER_X and not self.lava.active:
            self.lava.active = True

        self.player.update(self.platforms, self.spikes, self.coins,
                           self.tubes, self.lava)

        for b in self.bears:
            b.update(self.player.rect.centerx, self.player.rect.centery)
            if self.player.vulnerable and b.rect.colliderect(self.player.rect):
                self.player.dead = True
                self.player.death_cause = 'bear'

        self.net_catch = False
        for g in self.guards:
            g.update(self.player.rect)
            if self.player.vulnerable and not self.net_catch:
                hit_nets = [n for n in g.nets if n.rect.colliderect(self.player.rect)]
                if hit_nets:
                    self.net_catch = True
                    self.player.jail_checkpoint_x = max(100, g.rect.left - 500)
                    self.player.jail_checkpoint_y = GROUND_Y
                    for n in hit_nets:
                        if n in g.nets:
                            g.nets.remove(n)

        self.lava.update()

        # Volcano kill zone: touching the upper cone is fatal (same as lava)
        if self.player.vulnerable and self.player.rect.colliderect(self.VOLCANO_KILL_RECT):
            self.player.dead = True
            self.player.death_cause = 'volcano'

        particles.update()
        update_snow()
        update_storm()
        self._cam()

    def draw(self, surf):
        draw_level1_bg(surf, self.cam_x, self.frame)

        for p in self.platforms:
            draw_platform_snow(surf, p.rect, self.cam_x)

        for tube in self.tubes:
            draw_tube(surf, tube.wx, tube.wy, self.cam_x)

        for s in self.spikes:
            draw_spike_set(surf, s.cx - self.cam_x, s.y, self.frame)

        for c in self.coins:
            if not c.collected:
                draw_coin(surf, c.cx - self.cam_x, c.cy, self.frame)

        self.lava.draw(surf, self.cam_x, self.frame)
        draw_volcano(surf, 3100, GROUND_Y - 185, self.cam_x, self.frame)
        draw_cave_entrance(surf, self.CAVE_ENTRANCE_X, self.CAVE_ENTRANCE_Y,
                           self.cam_x, self.frame)

        for b in self.bears:
            b.draw(surf, self.cam_x, self.frame)

        for g in self.guards:
            g.draw(surf, self.cam_x)

        if self.player.dead:
            show = self.frame % 8 < 4
        elif self.player.invincible_timer > 0:
            show = self.frame % 6 < 4
        else:
            show = True
        if show:
            self.player.draw(surf, self.cam_x)
        particles.draw(surf, self.cam_x)
        if STORM_IN_ALL_LEVELS:
            draw_storm(surf)
        draw_hud(surf, self.player.score, "Level 1: Snowy Mountains", self.frame)

        for tube in self.tubes:
            if tube.in_range:
                sx = tube.wx - self.cam_x
                txt(surf, "[DOWN] Enter Tube", FONT_XS, (255, 240, 100), sx+28, tube.wy - 30)

    @property
    def reached_cave(self):
        cave_rect = pygame.Rect(self.CAVE_ENTRANCE_X + 5, self.CAVE_ENTRANCE_Y,
                                130, 140)
        return cave_rect.colliderect(self.player.rect)


class Level2:
    """The Cave — original relaxed cave with fox friends and a treasure chest.
    Reaching the chest transitions to Level 3 instead of winning outright."""
    LEVEL_W = 4400
    CHEST_X = 4080
    CHEST_Y = GROUND_Y

    def __init__(self, player_score=0):
        self.platforms   = make_level2_platforms()
        self.spikes      = make_level2_spikes()
        self.coins       = make_level2_coins()
        self.fox_friends = make_fox_friends()
        self.player      = Player(80, GROUND_Y)
        self.player.score = player_score
        self.cam_x       = 0
        self.frame       = 0
        self.chest_open  = False

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

        if self.player.rect.right > self.LEVEL_W:
            self.player.rect.right = self.LEVEL_W
            self.player.vx = 0

        for f in self.fox_friends:
            f.update(self.platforms, self.spikes)

        chest_rect = pygame.Rect(self.CHEST_X - 35, self.CHEST_Y - 52, 70, 52)
        if not self.chest_open and self.player.rect.colliderect(chest_rect):
            self.chest_open = True
            self.player.score += 200   # smaller bonus — the big chest is in Level 3
            particles.burst(self.CHEST_X, self.CHEST_Y - 30, GOLD, 30, 5, 5, 60, -0.1)

        particles.update()
        update_storm()
        self._cam()

    def draw(self, surf):
        draw_level2_bg(surf, self.cam_x, self.frame)

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

        if self.player.dead:
            show = self.frame % 8 < 4
        elif self.player.invincible_timer > 0:
            show = self.frame % 6 < 4
        else:
            show = True
        if show:
            self.player.draw(surf, self.cam_x)
        particles.draw(surf, self.cam_x)
        if STORM_IN_ALL_LEVELS:
            draw_storm(surf)
        draw_hud(surf, self.player.score, "Level 2: The Cave", self.frame)

    @property
    def reached_level3(self):
        """True once the chest has been opened — triggers fade to Level 3."""
        return self.chest_open


class Level3:
    """The Deep Cave — hard level with lava pits, bats, stalactites, and lethal guards."""
    LEVEL_W = _Z3_LEVEL_W
    CHEST_X = _Z3_CHEST_X
    CHEST_Y = _Z3_CHEST_Y

    def __init__(self, player_score=0):
        all_plats             = make_level3_platforms()
        self.platforms        = all_plats
        self.moving_platforms = [p for p in all_plats if isinstance(p, MovingPlatform)]
        self.spikes           = make_level3_spikes()
        self.coins            = make_level3_coins()
        self.bats             = make_level3_bats()
        self.rocks            = make_level3_falling_rocks()
        self.guards           = make_level3_guards()
        self.fox_friends      = make_level3_fox_friends()
        self.player           = Player(80, GROUND_Y)
        self.player.score     = player_score
        self.cam_x            = 0
        self.frame            = 0
        self.chest_open       = False

    def _cam(self):
        target = self.player.rect.centerx - SCREEN_W // 2
        self.cam_x = max(0, min(target, self.LEVEL_W - SCREEN_W))

    def update(self):
        self.frame += 1
        keys = pygame.key.get_pressed()

        for mp in self.moving_platforms:
            mp.update()

        # Carry Ella with any moving platform she's standing on
        if not self.player.dead:
            for mp in self.moving_platforms:
                if (abs(self.player.rect.bottom - mp.rect.top) <= 4
                        and self.player.rect.right > mp.rect.left + 2
                        and self.player.rect.left < mp.rect.right - 2):
                    self.player.rect.x += mp.dx

        if not self.player.dead:
            self.player.handle_input(keys)
            if keys[ICE_KEY]:
                self.player.use_ice()

        self.player.update(self.platforms, self.spikes, self.coins, [])

        if self.player.rect.right > self.LEVEL_W:
            self.player.rect.right = self.LEVEL_W
            self.player.vx = 0

        # Pit death — fell below ground into lava
        if not self.player.dead and self.player.rect.top > GROUND_Y + 120:
            self.player.dead = True
            self.player.death_cause = 'lava'

        for bat in self.bats:
            bat.update(self.player.rect)
            if self.player.vulnerable and bat.rect.colliderect(self.player.rect):
                self.player.dead = True
                self.player.death_cause = 'bat'

        for rock in self.rocks:
            rock.update(self.player.rect)
            if (self.player.vulnerable and rock.state == FallingRock.FALLING
                    and rock.rect.colliderect(self.player.rect)):
                self.player.dead = True
                self.player.death_cause = 'spike'

        # Guard nets are lethal in Level 3 — no jail in the deep cave
        for g in self.guards:
            g.update(self.player.rect)
            if self.player.vulnerable:
                hit = [n for n in g.nets if n.rect.colliderect(self.player.rect)]
                if hit:
                    self.player.dead = True
                    self.player.death_cause = None

        for f in self.fox_friends:
            f.update(self.platforms, self.spikes)

        chest_rect = pygame.Rect(self.CHEST_X - 35, self.CHEST_Y - 52, 70, 52)
        if not self.chest_open and self.player.rect.colliderect(chest_rect):
            self.chest_open = True
            self.player.score += 500
            particles.burst(self.CHEST_X, self.CHEST_Y - 30, GOLD, 40, 6, 6, 80, -0.1)

        particles.update()
        update_storm()
        self._cam()

    def draw(self, surf):
        draw_level2_bg(surf, self.cam_x, self.frame)   # same dark cave background

        for (px, pw) in _Z3_PITS:
            draw_lava_pit(surf, px, pw, self.cam_x, self.frame)

        for p in self.platforms:
            draw_platform_cave(surf, p.rect, self.cam_x)

        for s in self.spikes:
            draw_spike_set(surf, s.cx - self.cam_x, s.y, self.frame)

        for c in self.coins:
            if not c.collected:
                draw_coin(surf, c.cx - self.cam_x, c.cy, self.frame)

        for rock in self.rocks:
            rock.draw(surf, self.cam_x, self.frame)

        for bat in self.bats:
            bat.draw(surf, self.cam_x, self.frame)

        for g in self.guards:
            g.draw(surf, self.cam_x)

        draw_treasure_chest(surf, self.CHEST_X, self.CHEST_Y, self.cam_x,
                            self.frame, self.chest_open)

        for f in self.fox_friends:
            f.draw(surf, self.cam_x)

        if self.player.dead:
            show = self.frame % 8 < 4
        elif self.player.invincible_timer > 0:
            show = self.frame % 6 < 4
        else:
            show = True
        if show:
            self.player.draw(surf, self.cam_x)
        particles.draw(surf, self.cam_x)
        if STORM_IN_ALL_LEVELS:
            draw_storm(surf)
        draw_hud(surf, self.player.score, "Level 3: The Deep Cave", self.frame)

    @property
    def won(self):
        return self.chest_open


class Level4:
    """Ella's Home — a warm, completely safe free-roam ending.

    A cozy house at the back of the cave, a loving family of five who watch over
    her, and a bunch of huggable friendly animals. No hazards: Ella cannot be
    hurt and the level never ends on its own. Once she reaches the house she can
    keep roaming and hugging; pressing ENTER goes to the celebration screen."""
    LEVEL_W    = _Z4_LEVEL_W
    HOUSE_X    = _Z4_HOUSE_X
    HOUSE_Y    = _Z4_HOUSE_Y
    HOME_BONUS = 250

    def __init__(self, player_score=0):
        self.platforms   = make_level4_platforms()
        self.coins       = make_level4_coins()
        self.people      = make_level4_people()
        self.animals     = make_level4_animals()
        self.fox_friends = make_fox_friends()   # used only for the win celebration
        self.player      = Player(80, GROUND_Y)
        self.player.score = player_score
        self.cam_x       = 0
        self.frame       = 0
        self.hug_cd      = 0
        self.hugged_count = 0
        self.total_animals = len(self.animals)
        self.reached_home = False
        self.banner_timer = 0
        self.door_rect   = pygame.Rect(*_Z4_DOOR_RECT)
        reset_storm()    # clear sky on arrival — storms come from coins here

    def _cam(self):
        target = self.player.rect.centerx - SCREEN_W // 2
        self.cam_x = max(0, min(target, self.LEVEL_W - SCREEN_W))

    def update(self):
        self.frame += 1
        if self.banner_timer > 0:
            self.banner_timer -= 1
        keys = pygame.key.get_pressed()

        self.player.handle_input(keys)
        if keys[ICE_KEY]:
            self.player.use_ice()

        self.player.update(self.platforms, [], self.coins, [])

        if self.player.rect.right > self.LEVEL_W:
            self.player.rect.right = self.LEVEL_W
            self.player.vx = 0

        # Hugging — press H (or UP) next to an animal
        self.hug_cd = max(0, self.hug_cd - 1)
        if (keys[pygame.K_h] or keys[pygame.K_UP]) and self.hug_cd == 0:
            hugged_any = False
            for a in self.animals:
                if self.player.rect.colliderect(a.hug_rect):
                    if a.hug():
                        self.hugged_count += 1
                    hugged_any = True
            if hugged_any:
                self.hug_cd = 12
                particles.burst(self.player.rect.centerx,
                                self.player.rect.centery - 10,
                                (255, 130, 160), 8, 3, 4, 26, -0.06)

        for a in self.animals:
            a.update()

        # Reaching the house → warm welcome + one-time bonus
        if not self.reached_home and self.player.rect.colliderect(self.door_rect):
            self.reached_home = True
            self.player.score += self.HOME_BONUS
            self.banner_timer = 260
            particles.burst(self.HOUSE_X, GROUND_Y - 90, (255, 180, 90),
                            36, 5, 5, 70, -0.08)

        update_storm()
        particles.update()
        self._cam()

    def draw(self, surf):
        draw_level2_bg(surf, self.cam_x, self.frame)

        for p in self.platforms:
            draw_platform_cave(surf, p.rect, self.cam_x)

        draw_house(surf, self.HOUSE_X, self.HOUSE_Y, self.cam_x, self.frame)

        # The family — calm, watching Ella, with little hearts floating above
        for pp in self.people:
            facing = self.player.rect.centerx > pp['x']
            draw_human(surf, pp['x'] - self.cam_x, pp['y'], facing,
                       False, self.frame, pp['gender'])
            for k in range(2):
                hy = pp['y'] - 118 - k * 16 + int(math.sin(self.frame * 0.06 + pp['phase'] + k) * 4)
                hx = int(pp['x'] - self.cam_x + math.sin(self.frame * 0.04 + k) * 6)
                draw_heart(surf, hx, hy, 12 - k * 3, (255, 120, 150))

        for c in self.coins:
            if not c.collected:
                draw_coin(surf, c.cx - self.cam_x, c.cy, self.frame)

        for a in self.animals:
            a.draw(surf, self.cam_x)

        if self.player.invincible_timer > 0:
            show = self.frame % 6 < 4
        else:
            show = True
        if show:
            self.player.draw(surf, self.cam_x)

        particles.draw(surf, self.cam_x)
        draw_storm(surf)   # weather is always visible at home

        draw_hud(surf, self.player.score, "Level 4: Home", self.frame)

        # Hug counter
        txt(surf, f"Hugs: {self.hugged_count} / {self.total_animals}",
            FONT_SM, (255, 175, 205), 100, 66)
        if self.hugged_count >= self.total_animals:
            txt(surf, "You hugged all your friends!", FONT_SM,
                (255, 205, 120), SCREEN_W // 2, 66)

        # Hints / welcome banner
        if not self.reached_home:
            blink = int(self.frame * 0.05) % 2 == 0
            txt(surf, "Walk home to your family  -->", FONT_SM,
                (255, 230, 150) if blink else (210, 190, 130),
                SCREEN_W // 2, SCREEN_H - 42)
            txt(surf, "Press H next to an animal to hug it!", FONT_XS,
                (220, 230, 255), SCREEN_W // 2, SCREEN_H - 18)
        else:
            if self.banner_timer > 0:
                panel = pygame.Surface((760, 92), pygame.SRCALPHA)
                panel.fill((0, 0, 0, 150))
                pygame.draw.rect(panel, (255, 190, 90, 120), panel.get_rect(),
                                 3, border_radius=14)
                surf.blit(panel, (SCREEN_W // 2 - 380, 150))
                txt(surf, "Welcome home, Ella!", FONT_LG, (255, 210, 110),
                    SCREEN_W // 2, 180)
                txt(surf, "Your family is so happy to see you.", FONT_SM,
                    (255, 235, 200), SCREEN_W // 2, 216)
            blink = int(self.frame * 0.05) % 2 == 0
            txt(surf, "Hug your animal friends  —  press ENTER to celebrate",
                FONT_SM, (255, 230, 150) if blink else (210, 190, 130),
                SCREEN_W // 2, SCREEN_H - 28)

    def handle(self, event):
        """ENTER (once home) → go celebrate on the win screen."""
        if event.type == pygame.KEYDOWN and self.reached_home:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                return 'win'
        return None
