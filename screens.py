"""screens.py — MenuScreen, GameOverScreen, WinScreen, FoxJailScreen."""
import pygame, math, random
from constants import (
    SCREEN_W, SCREEN_H, GROUND_Y,
    WHITE, BLACK, GOLD, FOX_OR, SKY_T, SKY_B,
    FONT_XL, FONT_LG, FONT_MD, FONT_SM, FONT_XS,
    CAVE_BG,
    lt, txt, draw_rounded_rect,
)
from leaderboard import LEADERBOARD
from drawing import (
    draw_fox, draw_level1_bg, draw_level2_bg, draw_jail_cell,
    draw_leaderboard_block, update_snow,
    draw_treasure_chest, draw_platform_cave,
)
from levels import FOX_FRIEND_COLORS, make_level2_platforms


class MenuScreen:
    def __init__(self):
        self.frame    = 0
        self.fox_anim = 0
        self._ee2_times = []  # timestamps of recent '2' key presses (easter egg)
        self._ee3_times = []  # timestamps of recent '3' key presses (easter egg)
        self._ee4_times = []  # timestamps of recent '4' key presses (easter egg)

    def update(self):
        self.frame += 1
        self.fox_anim += 1

    def draw(self, surf):
        for y in range(0, SCREEN_H, 3):
            t = y / SCREEN_H
            c = tuple(int(SKY_T[i] + (SKY_B[i]-SKY_T[i])*t) for i in range(3))
            pygame.draw.rect(surf, c, pygame.Rect(0, y, SCREEN_W, 3))

        update_snow()
        draw_level1_bg(surf, 0, self.frame)

        panel = pygame.Surface((680, 200), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 120))
        pygame.draw.rect(panel, (255, 200, 60, 60), panel.get_rect(), 3, border_radius=16)
        surf.blit(panel, (SCREEN_W//2 - 340, 100))

        pulse = 0.5 + 0.5*math.sin(self.frame*0.06)
        title_col = (int(255), int(200+pulse*40), int(50+pulse*30))
        txt(surf, "Ella's Cave", FONT_XL, title_col, SCREEN_W//2, 165)
        txt(surf, "A Fox's Snowy Adventure", FONT_SM, (228,240,255), SCREEN_W//2, 230)

        draw_fox(surf, SCREEN_W//2 - 160, 430, True, self.fox_anim, 1.2, FOX_OR, True)
        draw_fox(surf, SCREEN_W//2 + 160, 430, False, self.fox_anim+20, 0.85,
                 FOX_FRIEND_COLORS[2], False)

        btn_y = 480
        blink = int(self.frame * 0.05) % 2 == 0
        txt(surf, ">  Press ENTER to Play", FONT_MD,
            GOLD if blink else lt(GOLD, 40), SCREEN_W//2, btn_y)
        txt(surf, "Move: Arrow Keys  |  Jump: UP or SPACE  |  Ice: [X]  |  Tube: [DOWN]",
            FONT_XS, (200, 220, 255), SCREEN_W//2, btn_y + 48)
        txt(surf, "L  -  Leaderboard", FONT_XS, GOLD, SCREEN_W//2, btn_y + 76)

    def handle(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                return 'start'
            if event.key == pygame.K_l:
                return 'leaderboard'
            # Easter egg: press 2 five times within 3 seconds → skip to Level 2
            if event.key == pygame.K_2:
                now = pygame.time.get_ticks()
                self._ee2_times = [t for t in self._ee2_times if now - t < 3000]
                self._ee2_times.append(now)
                if len(self._ee2_times) >= 5:
                    self._ee2_times.clear()
                    return 'l2_cheat'
            # Easter egg: press 3 five times within 3 seconds → skip to Level 3
            if event.key == pygame.K_3:
                now = pygame.time.get_ticks()
                self._ee3_times = [t for t in self._ee3_times if now - t < 3000]
                self._ee3_times.append(now)
                if len(self._ee3_times) >= 5:
                    self._ee3_times.clear()
                    return 'l3_cheat'
            # Easter egg: press 4 five times within 3 seconds → skip to Level 4
            if event.key == pygame.K_4:
                now = pygame.time.get_ticks()
                self._ee4_times = [t for t in self._ee4_times if now - t < 3000]
                self._ee4_times.append(now)
                if len(self._ee4_times) >= 5:
                    self._ee4_times.clear()
                    return 'l4_cheat'
        return None


_DEATH_MESSAGES = {
    'fall': [
        "That hole was sneaky! Try to keep your paws on solid ground, Ella!",
        "Whoopsie-daisy! Even foxes need solid ground beneath their paws!",
        "Ella's tail vanished into the abyss... look before you leap next time!",
        "Down, down, down she goes! Try jumping OVER those gaps, Ella!",
        "The ground disappeared! Keep an eye out for those sneaky holes!",
        "Gravity: 1, Ella: 0. Watch those edges, brave fox!",
    ],
    'spike': [
        "Ouch! Those spikes are NOT cuddle buddies, Ella!",
        "Spiky surprise! Give those pointy things a little more personal space!",
        "Ella learned the hard way — spikes are terrible landing spots!",
        "Eek! Red glowing spikes = danger! Try jumping clean over them!",
        "Those spikes have been waiting there ALL along — jump over them next time!",
        "Pokey! Ella, those are NOT trampoline cushions. Try leaping over!",
    ],
    'lava': [
        "Too hot, too hot! Lava is NOT a swimming pool, Ella!",
        "Ella has discovered that lava and fox fur do not mix. At all.",
        "A little toasty, don't you think? Stay away from the glowing orange stuff!",
        "Lava: zero stars, would NOT recommend. Try the ice bridge trick!",
        "Even the bravest foxes know to keep their paws OUT of lava!",
        "That lava looked pretty but YIKES. Use the ice bridge or run fast!",
    ],
    'volcano': [
        "Ella, that volcano is NOT a slide! Stay off the hot rocks!",
        "Volcanoes are for looking at, not climbing — way too dangerous up there!",
        "That's a little too warm for Ella! Volcanoes and foxes don't mix.",
        "The volcano said 'NO VISITORS!' Try finding another way around it!",
        "Whoa, the volcano is cranky today! Sneak around the bottom next time.",
        "Hot rocks ahoy! The tube or an ice bridge might be a safer route, Ella!",
    ],
    'bear': [
        "Foxy popsicle alert! Let's not feed the polar bear next time!",
        "Ella got bear-hugged... in totally the wrong way. Jump over them!",
        "Polar bears might look fluffy, but they are NOT friendly! Run!",
        "That bear was VERY happy to see Ella. Ella was less happy about it.",
        "Bears 1, Ella 0! Try leaping over or sneaking past those big guys!",
        "Surprise snuggle from a polar bear! They mean business — stay nimble!",
    ],
    'bat': [
        "A cave bat swooped right into Ella! Watch for the swooping shadows!",
        "Wings in the dark are NOT to be trusted — dodge those bats, Ella!",
        "The bats of the deep cave are surprisingly effective defenders!",
        "Bonk! That bat had Ella's name on it. Try ducking or timing your run!",
        "Cave bats: small, fast, and very unfriendly. Keep moving, Ella!",
        "The bat didn't even apologize. Rude! Stay low and watch the ceiling!",
    ],
    None: [
        "Oops! That one stung a little. You've totally got this, Ella!",
        "Every great explorer makes mistakes! Ella is just learning the ropes.",
        "Shake it off, Ella! Even the best adventurers fall sometimes.",
        "Yikes! But now you know what NOT to do next time. Try again!",
        "Don't worry, Ella — practice makes perfect! Give it another go!",
        "The cave isn't going anywhere! Dust off those paws and try again!",
    ],
}


class GameOverScreen:
    def __init__(self, score, level, cause=None):
        self.score = score
        self.level = level
        self.frame = 0
        self.initials = ['A', 'A', 'A']
        self.cursor = 0
        self.qualifies = LEADERBOARD.qualifies(score)
        bank = _DEATH_MESSAGES.get(cause, _DEATH_MESSAGES[None])
        self.tip = random.choice(bank)

        # Math problem for levels 2+ (lets player restart same level if correct)
        if level > 1:
            self._gen_math()
            self.player_answer = ''
            self.next_phase = 'math'
        else:
            self.math_question = None
            self.math_answer   = None
            self.player_answer = ''
            self.next_phase = 'show'

        self.phase = 'enter_initials' if self.qualifies else self.next_phase

    def _gen_math(self):
        op = random.choice(['+', '-', '*'])
        if op == '+':
            a, b = random.randint(5, 20), random.randint(5, 15)
            ans = a + b
        elif op == '-':
            a = random.randint(12, 30)
            b = random.randint(2, a - 2)
            ans = a - b
        else:
            a, b = random.randint(2, 9), random.randint(2, 9)
            ans = a * b
        self.math_question = f"{a}  {op}  {b}"
        self.math_answer   = str(ans)

    def update(self):
        self.frame += 1
        update_snow()

    def draw(self, surf):
        for y in range(0, SCREEN_H, 3):
            t = y / SCREEN_H
            c = tuple(int(SKY_T[i] + (SKY_B[i]-SKY_T[i])*t) for i in range(3))
            pygame.draw.rect(surf, c, pygame.Rect(0, y, SCREEN_W, 3))
        draw_level1_bg(surf, 0, self.frame)

        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        surf.blit(overlay, (0, 0))

        txt(surf, "Oops!", FONT_XL, (255, 120, 60), SCREEN_W//2, 100)
        txt(surf, self.tip, FONT_SM, (255, 220, 180), SCREEN_W//2, 165)
        txt(surf, f"Score: {self.score:,}", FONT_MD, GOLD, SCREEN_W//2, 210)

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
            txt(surf, "Type your initials  |  BACKSPACE: Delete  |  ENTER: Save",
                FONT_XS, (180,180,180), SCREEN_W//2, 380)
            txt(surf, "ESC: Skip and return to main menu",
                FONT_XS, (150,150,150), SCREEN_W//2, 400)

        elif self.phase == 'math':
            pulse = 0.5 + 0.5 * math.sin(self.frame * 0.07)
            hdr_col = (int(255), int(190 + pulse * 50), int(80 + pulse * 40))
            txt(surf, f"Solve this to restart Level {self.level}:", FONT_SM, hdr_col,
                SCREEN_W//2, 275)
            txt(surf, self.math_question + " = ?", FONT_LG, GOLD, SCREEN_W//2, 325)
            ans_display = (self.player_answer if self.player_answer else "_")
            txt(surf, ans_display, FONT_LG, WHITE, SCREEN_W//2, 385)
            txt(surf, "Type your answer and press ENTER",
                FONT_XS, (180, 180, 180), SCREEN_W//2, 435)
            txt(surf, "ESC  —  give up and restart from Level 1",
                FONT_XS, (150, 150, 150), SCREEN_W//2, 458)

        else:  # 'show'
            draw_leaderboard_block(surf, SCREEN_W//2, 270, LEADERBOARD.top5(), None)
            blink = int(self.frame * 0.05) % 2 == 0
            txt(surf, "ENTER: Play Again  |  M / ESC: Main Menu",
                FONT_MD, GOLD if blink else lt(GOLD, 40), SCREEN_W//2, 570)

    def handle(self, event):
        if event.type != pygame.KEYDOWN:
            return None
        k = event.key
        if self.phase == 'enter_initials':
            if event.unicode and event.unicode.upper() in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                self.initials[self.cursor] = event.unicode.upper()
                self.cursor = min(2, self.cursor + 1)
            elif k == pygame.K_BACKSPACE:
                self.cursor = max(0, self.cursor - 1)
                self.initials[self.cursor] = 'A'
            elif k == pygame.K_LEFT:
                self.cursor = max(0, self.cursor - 1)
            elif k == pygame.K_RIGHT:
                self.cursor = min(2, self.cursor + 1)
            elif k in (pygame.K_RETURN, pygame.K_KP_ENTER):
                LEADERBOARD.add(''.join(self.initials), self.score)
                self.phase = self.next_phase  # math or show
            elif k == pygame.K_ESCAPE:
                return 'menu'

        elif self.phase == 'math':
            if event.unicode and event.unicode in '0123456789':
                if len(self.player_answer) < 6:
                    self.player_answer += event.unicode
            elif k == pygame.K_BACKSPACE:
                self.player_answer = self.player_answer[:-1]
            elif k in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if self.player_answer == self.math_answer:
                    return 'retry_same'
                return 'retry'
            elif k == pygame.K_ESCAPE:
                return 'retry'

        else:  # 'show'
            if k in (pygame.K_RETURN, pygame.K_KP_ENTER):
                return 'retry'
            if k in (pygame.K_m, pygame.K_ESCAPE):
                return 'menu'
        return None


_WIN_QUIPS = [
    "The polar bears are absolutely devastated. Ella could not be reached for comment.",
    "Scientists confirm: the jewels are 100% real and 100% Ella's now. Sorry, bears.",
    "Ella has officially outfoxed everyone. She is already planning her victory nap.",
    "The volcano is still erupting. Ella has decided that is someone else's problem.",
    "Local fox wins ALL the treasure! Local polar bears refuse to discuss the matter.",
    "That'll show those guards who's boss! (The guards still think they're the boss. Shh.)",
    "Ella found the loot! She's never sharing it. Okay, maybe with the fox friends. Maybe.",
]

# Gem sparkle colours for the party scene
_GEM_COLS = [
    (220,  50,  50),  # ruby
    ( 50, 210,  80),  # emerald
    ( 60, 130, 230),  # sapphire
    (190,  80, 230),  # amethyst
    (255, 215,  50),  # topaz
    (255, 255, 255),  # diamond
]

# World-x of the chest in Level2 (must match Level2.CHEST_X)
_Z2_CHEST_X = 4080
_Z2_LEVEL_W  = 4400


class WinScreen:
    def __init__(self, score, fox_friends):
        self.score = score
        self.fox_friends = fox_friends
        self.frame = 0
        self.qualifies = LEADERBOARD.qualifies(score)
        self.phase = 'enter_initials' if self.qualifies else 'celebrate'
        self.initials = ['A', 'A', 'A']
        self.cursor = 0
        self.quip = random.choice(_WIN_QUIPS)

        # Camera: show the far-right end of the cave where the chest lives
        self.cam_x = _Z2_LEVEL_W - SCREEN_W   # = 3200

        self.z2_platforms = make_level2_platforms()

        # Confetti pieces
        self.confetti = []
        for _ in range(220):
            self.confetti.append({
                'x': random.uniform(0, SCREEN_W),
                'y': random.uniform(-SCREEN_H, 0),
                'vx': random.uniform(-2, 2),
                'vy': random.uniform(1.5, 4),
                'r': random.uniform(4, 10),
                'hue': random.randint(0, 360),
                'spin': random.uniform(-0.2, 0.2),
                'angle': random.uniform(0, math.pi * 2),
                'shape': random.choice(['rect', 'circle']),
            })

        # Gem sparkles that orbit the chest
        self.gems = []
        chest_sx = _Z2_CHEST_X - self.cam_x   # = 880
        chest_sy = GROUND_Y - 45
        for i in range(18):
            angle = (i / 18) * math.pi * 2
            r = random.randint(50, 120)
            self.gems.append({
                'base_angle': angle,
                'radius': r,
                'cx': chest_sx,
                'cy': chest_sy,
                'col': _GEM_COLS[i % len(_GEM_COLS)],
                'size': random.randint(5, 11),
                'speed': random.uniform(0.018, 0.035),
                'phase': random.uniform(0, math.pi * 2),
            })

    # ── helpers ──────────────────────────────────────────────────────────────

    def _draw_confetti(self, surf):
        for c in self.confetti:
            color = pygame.Color(0)
            color.hsva = (c['hue'], 90, 90, 100)
            s = pygame.Surface((int(c['r'] * 2), int(c['r'])), pygame.SRCALPHA)
            if c['shape'] == 'rect':
                pygame.draw.rect(s, (*color[:3], 200), s.get_rect())
            else:
                pygame.draw.circle(s, (*color[:3], 200),
                    (int(c['r']), int(c['r'] // 2)), int(c['r'] // 2))
            rot = pygame.transform.rotate(s, math.degrees(c['angle']))
            surf.blit(rot, (int(c['x']) - rot.get_width() // 2,
                            int(c['y']) - rot.get_height() // 2))

    def _draw_gems(self, surf):
        for g in self.gems:
            a = g['base_angle'] + self.frame * g['speed']
            x = int(g['cx'] + math.cos(a) * g['radius'])
            y = int(g['cy'] + math.sin(a) * g['radius'] * 0.45)
            pulse = 0.5 + 0.5 * math.sin(self.frame * 0.18 + g['phase'])
            r = int(g['size'] * (0.8 + 0.4 * pulse))
            col = g['col']
            # Draw a simple diamond shape (rotated square)
            pts = [(x, y - r), (x + r, y), (x, y + r), (x - r, y)]
            pygame.draw.polygon(surf, col, pts)
            # Shine highlight
            pygame.draw.circle(surf, WHITE, (x - r // 3, y - r // 3),
                               max(1, r // 3))

    def _draw_chest_glow(self, surf):
        chest_sx = _Z2_CHEST_X - self.cam_x
        chest_sy = GROUND_Y - 10
        pulse = 0.5 + 0.5 * math.sin(self.frame * 0.08)
        for radius, alpha in [(110, 40), (75, 65), (45, 90)]:
            r = int(radius * (1 + 0.08 * pulse))
            gsurf = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
            pygame.draw.ellipse(gsurf, (255, 210, 40, int(alpha * (0.8 + 0.2 * pulse))),
                                pygame.Rect(0, 0, r * 2 + 4, r * 2 + 4))
            surf.blit(gsurf, (chest_sx - r - 2, chest_sy - r - 2))

    # ── lifecycle ─────────────────────────────────────────────────────────────

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

        # Always animate the party — visible regardless of initials/celebrate phase
        for f in self.fox_friends:
            f.update(self.z2_platforms)
            # Random party jumps
            if f.on_ground and random.random() < 0.018:
                f.vy = -13

    def draw(self, surf):
        draw_level2_bg(surf, self.cam_x, self.frame)

        # Cave platforms so foxes have visible ground
        for p in self.z2_platforms:
            draw_platform_cave(surf, p.rect, self.cam_x)

        # Party scene always visible — even during initials entry it plays behind the panel
        self._draw_chest_glow(surf)

        for f in self.fox_friends:
            f.draw(surf, self.cam_x)

        # Ella front and centre (slightly left of chest)
        ella_sx = (_Z2_CHEST_X - self.cam_x) - 160
        draw_fox(surf, ella_sx, GROUND_Y, True, self.frame, 1.2, FOX_OR, True)

        # Open treasure chest with orbiting gems
        draw_treasure_chest(surf, _Z2_CHEST_X, GROUND_Y - 10,
                             self.cam_x, self.frame, open_=True)
        self._draw_gems(surf)

        self._draw_confetti(surf)

        # ── Text panel ──────────────────────────────────────────────────────
        panel_h = 250 if self.phase == 'enter_initials' else 210
        panel = pygame.Surface((860, panel_h), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 170))
        pygame.draw.rect(panel, (255, 200, 60, 90), panel.get_rect(), 3, border_radius=16)
        surf.blit(panel, (SCREEN_W // 2 - 430, 36))

        pulse = 0.5 + 0.5 * math.sin(self.frame * 0.07)
        txt(surf, "YOU FOUND THE TREASURE!", FONT_LG,
            (int(255), int(200 + pulse * 40), int(50)), SCREEN_W // 2, 80)
        txt(surf, self.quip, FONT_XS, (255, 230, 180), SCREEN_W // 2, 120)
        txt(surf, f"Score: {self.score:,}", FONT_MD, GOLD, SCREEN_W // 2, 158)

        if self.phase == 'enter_initials':
            txt(surf, "High Score! Enter Your Initials:", FONT_SM,
                (255, 230, 120), SCREEN_W // 2, 198)
            for i, ch in enumerate(self.initials):
                col = GOLD if i == self.cursor else WHITE
                bx = SCREEN_W // 2 - 60 + i * 60
                pygame.draw.rect(surf, (30, 30, 60),
                    pygame.Rect(bx - 20, 220, 40, 50), border_radius=8)
                if i == self.cursor:
                    pygame.draw.rect(surf, GOLD,
                        pygame.Rect(bx - 20, 220, 40, 50), 2, border_radius=8)
                txt(surf, ch, FONT_LG, col, bx, 245)
            txt(surf, "Type your initials  |  BACKSPACE: Delete  |  ENTER: Save",
                FONT_XS, (180, 180, 180), SCREEN_W // 2, 272)
        else:
            blink = int(self.frame * 0.06) % 2 == 0
            txt(surf, "M - Main Menu  |  ENTER - Play Again",
                FONT_SM, GOLD if blink else lt(GOLD), SCREEN_W // 2, 205)

        if self.phase == 'celebrate' and self.frame > 60:
            draw_leaderboard_block(surf, 130, 320, LEADERBOARD.top5())

    def handle(self, event):
        if event.type != pygame.KEYDOWN:
            return None
        k = event.key
        if self.phase == 'enter_initials':
            if event.unicode and event.unicode.upper() in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                self.initials[self.cursor] = event.unicode.upper()
                self.cursor = min(2, self.cursor + 1)
            elif k == pygame.K_BACKSPACE:
                self.cursor = max(0, self.cursor - 1)
                self.initials[self.cursor] = 'A'
            elif k == pygame.K_LEFT:
                self.cursor = max(0, self.cursor - 1)
            elif k == pygame.K_RIGHT:
                self.cursor = min(2, self.cursor + 1)
            elif k in (pygame.K_RETURN, pygame.K_KP_ENTER):
                LEADERBOARD.add(''.join(self.initials), self.score)
                return 'menu'
            elif k == pygame.K_ESCAPE:
                return 'menu'
        else:
            if k == pygame.K_m:
                return 'menu'
            if k in (pygame.K_RETURN, pygame.K_KP_ENTER):
                return 'restart'
        return None


class LeaderboardScreen:
    def __init__(self):
        self.frame = 0

    def update(self):
        self.frame += 1
        update_snow()

    def draw(self, surf):
        # Same background as menu
        for y in range(0, SCREEN_H, 3):
            t = y / SCREEN_H
            c = tuple(int(SKY_T[i] + (SKY_B[i]-SKY_T[i])*t) for i in range(3))
            pygame.draw.rect(surf, c, pygame.Rect(0, y, SCREEN_W, 3))
        draw_level1_bg(surf, 0, self.frame)

        # Panel
        panel = pygame.Surface((540, 390), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 155))
        pygame.draw.rect(panel, (255, 200, 60, 80), panel.get_rect(), 3, border_radius=16)
        surf.blit(panel, (SCREEN_W//2 - 270, 120))

        txt(surf, "Top Scores", FONT_LG, GOLD, SCREEN_W//2, 158)

        scores = LEADERBOARD.top5()
        if scores:
            medals = ["#1", "#2", "#3", "#4", "#5"]
            medal_cols = [
                (255, 215,  30),   # gold
                (200, 200, 200),   # silver
                (205, 127,  50),   # bronze
                (220, 220, 220),
                (220, 220, 220),
            ]
            for i, s in enumerate(scores):
                col = medal_cols[i]
                row_y = 225 + i * 52
                txt(surf, medals[i], FONT_MD, col, SCREEN_W//2 - 130, row_y)
                txt(surf, s['initials'], FONT_MD, WHITE, SCREEN_W//2, row_y)
                txt(surf, f"{s['score']:,}", FONT_MD, col, SCREEN_W//2 + 130, row_y)
        else:
            txt(surf, "No scores yet — go play!", FONT_SM, (180, 180, 180),
                SCREEN_W//2, 310)

        blink = int(self.frame * 0.05) % 2 == 0
        txt(surf, "Press any key to go back", FONT_SM,
            GOLD if blink else lt(GOLD, 40), SCREEN_W//2, 545)

    def handle(self, event):
        if event.type == pygame.KEYDOWN:
            return 'back'
        return None


def _make_math_problem():
    """Return (a, op_str, b, answer) suitable for a 7-year-old."""
    if random.random() < 0.5:
        a = random.randint(1, 9)
        b = random.randint(1, 9)
        return a, '+', b, a + b
    else:
        a = random.randint(3, 12)
        b = random.randint(1, a - 1)
        return a, '-', b, a - b


class FoxJailScreen:
    PHASES = [
        (100, "Ella is caught in a net!"),
        (100, "A friend fox arrives..."),
        (999, "The friend fox has a key!"),   # held until math solved
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
        # Math puzzle
        self.math_q = None          # (a, op_str, b, answer) — generated on phase 2 entry
        self.math_input = ''
        self.math_solved = False
        self.math_wrong_timer = 0   # frames remaining for wrong-answer flash

    def _new_math_problem(self):
        self.math_q = _make_math_problem()
        self.math_input = ''

    def update(self):
        self.frame += 1
        self.phase_timer += 1

        if self.math_wrong_timer > 0:
            self.math_wrong_timer -= 1

        # Generate the puzzle the moment phase 2 starts
        if self.phase == 2 and self.math_q is None:
            self._new_math_problem()

        dur = self.PHASES[self.phase][0]
        # Phase 2 only advances once math is solved
        ready = self.math_solved if self.phase == 2 else self.phase_timer >= dur
        if ready and self.phase < len(self.PHASES) - 1:
            self.phase += 1
            self.phase_timer = 0

        if self.phase >= 1:
            self.friend_x += (self.friend_target - self.friend_x) * 0.06

    def handle(self, event):
        """Process keyboard input for the math puzzle."""
        if event.type != pygame.KEYDOWN:
            return
        if self.phase != 2 or self.math_solved or self.math_q is None:
            return
        k = event.key
        # ASCII digits only: str.isdigit() also accepts keys like '²' (AZERTY),
        # which int() then rejects.
        if event.unicode and event.unicode in '0123456789' and len(self.math_input) < 2:
            self.math_input += event.unicode
        elif k == pygame.K_BACKSPACE:
            self.math_input = self.math_input[:-1]
        elif k in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if self.math_input:
                if int(self.math_input) == self.math_q[3]:
                    self.math_solved = True
                else:
                    self.math_wrong_timer = 90
                    self._new_math_problem()

    def _draw_math_panel(self, surf):
        a, op, b, _ = self.math_q
        pw, ph = 620, 210
        px = SCREEN_W//2 - pw//2
        py = SCREEN_H//2 + 115

        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill((18, 8, 42, 220))
        border_col = (220, 60, 60, 200) if self.math_wrong_timer > 0 else (255, 200, 60, 160)
        pygame.draw.rect(panel, border_col, panel.get_rect(), 3, border_radius=14)
        surf.blit(panel, (px, py))

        # Header
        header = "Oops! Try a new one..." if self.math_wrong_timer > 0 else "Activate the magic key — solve this!"
        header_col = (255, 100, 100) if self.math_wrong_timer > 0 else (255, 225, 100)
        txt(surf, header, FONT_SM, header_col, SCREEN_W//2, py + 28)

        # Problem
        txt(surf, f"What is  {a} {op} {b} ?", FONT_LG, WHITE, SCREEN_W//2, py + 78)

        # Input box
        box_w, box_h = 90, 46
        bx = SCREEN_W//2 - box_w//2
        by = py + 108
        box_bg = (120, 30, 30) if self.math_wrong_timer > 0 else (30, 30, 80)
        pygame.draw.rect(surf, box_bg, pygame.Rect(bx, by, box_w, box_h), border_radius=8)
        pygame.draw.rect(surf, WHITE, pygame.Rect(bx, by, box_w, box_h), 2, border_radius=8)
        blink_cur = int(self.frame * 0.07) % 2 == 0
        display = self.math_input + ('|' if blink_cur else ' ')
        txt(surf, display, FONT_MD, WHITE, SCREEN_W//2, by + box_h//2 + 2)

        txt(surf, "Type your answer and press ENTER",
            FONT_XS, (180, 180, 210), SCREEN_W//2, py + 187)

    def draw(self, surf):
        surf.fill(CAVE_BG)
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 80))
        surf.blit(overlay, (0, 0))

        center_x = SCREEN_W//2 - 80
        center_y = SCREEN_H//2 - 30   # nudged up slightly to make room for math panel

        open_cell = self.phase >= 3
        draw_jail_cell(surf, center_x, center_y, open_cell)

        if self.phase < 3:
            draw_fox(surf, center_x, center_y + 55, True, self.frame, 0.8, FOX_OR, False)
        else:
            walk_x = center_x + (self.frame - self.PHASES[0][0] - self.PHASES[1][0] - 80) * 2
            draw_fox(surf, min(walk_x, center_x + 200), center_y + 55, True,
                     self.frame * 2, 0.9, FOX_OR, True)

        if self.phase >= 1:
            fx = int(self.friend_x)
            draw_fox(surf, fx, center_y + 55, False, self.frame, 0.7, FOX_FRIEND_COLORS[2], False)
            if self.phase >= 2:
                kx, ky = fx - 25, center_y - 40
                pygame.draw.circle(surf, GOLD, (kx, ky), 10, 3)
                pygame.draw.rect(surf, GOLD, pygame.Rect(kx+6, ky-3, 24, 6))
                pygame.draw.rect(surf, GOLD, pygame.Rect(kx+22, ky+3, 6, 8))
                pygame.draw.rect(surf, GOLD, pygame.Rect(kx+28, ky+3, 6, 8))

        # Caption (hidden during active math puzzle to avoid clutter)
        showing_math = self.phase == 2 and self.math_q is not None and not self.math_solved
        if not showing_math:
            caption = self.PHASES[min(self.phase, len(self.PHASES)-1)][1]
            txt(surf, caption, FONT_MD, WHITE, SCREEN_W//2, SCREEN_H - 60)

        if self.phase == len(self.PHASES) - 1:
            blink = int(self.frame * 0.07) % 2 == 0
            txt(surf, "(Returning to adventure...)", FONT_SM,
                GOLD if blink else lt(GOLD), SCREEN_W//2, SCREEN_H - 25)

        # Math puzzle panel
        if showing_math:
            self._draw_math_panel(surf)

    def done(self):
        return self.phase == len(self.PHASES) - 1 and self.phase_timer >= 60
