#!/usr/bin/env python3
"""
Ella's Cave — A 2D Side-Scrolling Platformer
Run with:  python ella_cave.py
Requires:  pip install pygame
"""

import pygame, sys
from constants import screen, clock, FPS, SCREEN_W, SCREEN_H, GROUND_Y, BLACK, game_surf, _display
from screens import MenuScreen, GameOverScreen, WinScreen, FoxJailScreen, LeaderboardScreen
from zones import Level1, Level2, Level3, Level4
from drawing import draw_lives_hud, particles

# ── Game States ───────────────────────────────────────────────────────────
STATE_MENU        = 'menu'
STATE_L1          = 'l1'
STATE_L2          = 'l2'
STATE_L3          = 'l3'
STATE_L4          = 'l4'
STATE_JAIL        = 'jail'
STATE_GAMEOVER    = 'gameover'
STATE_WIN         = 'win'
STATE_LEADERBOARD = 'leaderboard'


def fit_to_display(surf, display_w, display_h):
    """Return (surface, (x, y)) to blit: centred at native size when the window
    is big enough, otherwise shrunk (aspect kept) so the HUD and the bottom of
    the level are never cropped off a small window."""
    w, h = surf.get_size()
    k = min(display_w / w, display_h / h)
    if k < 1 and display_w > 0 and display_h > 0:
        w, h = max(1, int(w * k)), max(1, int(h * k))
        surf = pygame.transform.smoothscale(surf, (w, h))
    return surf, ((display_w - w) // 2, (display_h - h) // 2)


class Game:
    def __init__(self):
        self.state   = STATE_MENU
        self.menu    = MenuScreen()
        self.level1  = None
        self.level2  = None
        self.level3  = None
        self.level4  = None
        self.jail    = None
        self.gameover = None
        self.win     = None
        self.leaderboard = None
        self.score_carry = 0
        self.fade_alpha = 0
        self.fade_dir   = 0        # 1=fade out, -1=fade in
        self.fade_target_state = None
        self.fade_score = 0
        self._jail_rx    = 100
        self._jail_ry    = GROUND_Y
        self._jail_score = 0
        self._jail_coins = set()
        # Lives & death animation
        self.lives              = 3
        self.death_anim_timer   = 0   # frames remaining in death animation
        self.death_pending_level = 0  # which level the pending death is for

    def start_level1(self, score=0):
        self.death_anim_timer = 0
        self.level1 = Level1(score)
        self.state = STATE_L1
        self.fade_dir = -1

    def start_level2(self, score):
        self.death_anim_timer = 0
        self.level2 = Level2(score)
        self.state = STATE_L2
        self.fade_dir = -1

    def start_level3(self, score):
        self.death_anim_timer = 0
        self.level3 = Level3(score)
        self.state = STATE_L3
        self.fade_dir = -1

    def start_level4(self, score):
        self.death_anim_timer = 0
        self.level4 = Level4(score)
        self.state = STATE_L4
        self.fade_dir = -1

    def goto_jail(self, return_x, return_y, score):
        # Remember which coins are gone so the rebuilt level doesn't hand them
        # out a second time (the score is carried over).
        self._jail_coins = {(c.cx, c.cy) for c in self.level1.coins if c.collected}
        self.jail = FoxJailScreen(return_x, return_y, score)
        self.state = STATE_JAIL

    def goto_gameover(self, score, level, cause=None):
        self.gameover = GameOverScreen(score, level, cause)
        self.state = STATE_GAMEOVER

    def goto_win(self, score, fox_friends):
        self.win = WinScreen(score, fox_friends)
        self.state = STATE_WIN

    def _start_death_anim(self, level_num):
        level_obj = getattr(self, f'level{level_num}')
        cause = level_obj.player.death_cause
        self.death_anim_timer   = 30 if cause == 'fall' else 80
        self.death_pending_level = level_num
        if cause != 'fall':
            p = level_obj.player
            particles.burst(p.rect.centerx, p.rect.centery,
                            (255, 80, 50), 20, 4, 5, 42, -0.15)

    def _process_pending_death(self):
        level_num = self.death_pending_level
        level_obj = getattr(self, f'level{level_num}')
        p         = level_obj.player
        cause     = p.death_cause
        score     = p.score

        self.lives -= 1

        if self.lives > 0:
            # Revive in place — just clear dead flag and grant invincibility
            p.dead = False
            p.death_cause = None
            p.vy = 0
            p.vx = 0
            if p.rect.top > SCREEN_H + 30:
                # Fell off-screen — respawn at checkpoint
                p.rect.x = p.jail_checkpoint_x
                p.rect.bottom = p.jail_checkpoint_y
            p.invincible_timer = 120  # 2 seconds of post-revive invincibility
        else:
            # Last life gone — game over (math problem for levels 2+)
            self.goto_gameover(score, level_num, cause)

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
            if t == 'l1':    self.start_level1(self.fade_score)
            elif t == 'l2':  self.start_level2(self.fade_score)
            elif t == 'l3':  self.start_level3(self.fade_score)
            elif t == 'l4':  self.start_level4(self.fade_score)
            elif t == 'menu':
                self.state = STATE_MENU
                self.menu = MenuScreen()
            elif t == 'jail_return':
                self.level1 = Level1(self._jail_score, self._jail_rx, self._jail_ry,
                                     bear_freeze=60)
                for c in self.level1.coins:
                    if (c.cx, c.cy) in self._jail_coins:
                        c.collected = True
                self.state = STATE_L1
            self.fade_dir = -1
        elif self.fade_dir == -1 and self.fade_alpha <= 0:
            self.fade_dir = 0

    def run(self):
        running = True
        while running:
            clock.tick(FPS)
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    running = False
                    break

                if self.state == STATE_MENU:
                    result = self.menu.handle(event)
                    if result == 'start':
                        self.lives = 3
                        self.start_fade('l1', 0)
                    elif result == 'leaderboard':
                        self.leaderboard = LeaderboardScreen()
                        self.state = STATE_LEADERBOARD
                    elif result == 'l2_cheat':
                        self.lives = 3
                        self.start_fade('l2', 0)
                    elif result == 'l3_cheat':
                        self.lives = 3
                        self.start_fade('l3', 0)
                    elif result == 'l4_cheat':
                        self.lives = 3
                        self.start_fade('l4', 0)

                elif self.state == STATE_GAMEOVER and self.gameover:
                    result = self.gameover.handle(event)
                    if result == 'retry':
                        self.lives = 3
                        self.start_fade('l1', 0)
                    elif result == 'retry_same':
                        self.lives = 3
                        lvl = self.gameover.level
                        self.start_fade(f'l{lvl}', self.gameover.score)
                    elif result == 'menu':
                        self.start_fade('menu')

                elif self.state == STATE_WIN and self.win:
                    result = self.win.handle(event)
                    if result == 'menu':
                        self.start_fade('menu')
                    elif result == 'restart':
                        self.lives = 3
                        self.start_fade('l1', 0)

                elif self.state == STATE_L4 and self.level4:
                    if self.level4.handle(event) == 'win':
                        self.goto_win(self.level4.player.score, self.level4.fox_friends)

                elif self.state == STATE_JAIL and self.jail:
                    self.jail.handle(event)

                elif self.state == STATE_LEADERBOARD and self.leaderboard:
                    result = self.leaderboard.handle(event)
                    if result == 'back':
                        self.state = STATE_MENU
                        self.menu = MenuScreen()

            # ── UPDATE ──────────────────────────────────────────────────
            if self.state == STATE_MENU:
                self.menu.update()

            elif self.state == STATE_L1 and self.level1:
                self.level1.update()
                p = self.level1.player
                if self.death_anim_timer > 0:
                    self.death_anim_timer -= 1
                    if self.death_anim_timer == 0:
                        self._process_pending_death()
                elif self.level1.net_catch:
                    self.goto_jail(p.jail_checkpoint_x, p.jail_checkpoint_y, p.score)
                elif p.dead and self.fade_dir == 0:
                    self._start_death_anim(1)
                elif self.level1.reached_cave and not self.level1.cave_bonus_awarded:
                    self.level1.cave_bonus_awarded = True
                    p.score += 100
                    self.lives = 3
                    self.start_fade('l2', p.score)

            elif self.state == STATE_L2 and self.level2:
                self.level2.update()
                p = self.level2.player
                if self.death_anim_timer > 0:
                    self.death_anim_timer -= 1
                    if self.death_anim_timer == 0:
                        self._process_pending_death()
                elif p.dead and self.fade_dir == 0:
                    self._start_death_anim(2)
                elif self.level2.reached_level3:
                    self.lives = 3
                    self.start_fade('l3', p.score)

            elif self.state == STATE_L3 and self.level3:
                self.level3.update()
                p = self.level3.player
                if self.death_anim_timer > 0:
                    self.death_anim_timer -= 1
                    if self.death_anim_timer == 0:
                        self._process_pending_death()
                elif p.dead and self.fade_dir == 0:
                    self._start_death_anim(3)
                elif self.level3.won:
                    self.start_fade('l4', p.score)

            elif self.state == STATE_L4 and self.level4:
                self.level4.update()

            elif self.state == STATE_JAIL and self.jail:
                self.jail.update()
                if self.jail.done():
                    self._jail_rx    = self.jail.return_x
                    self._jail_ry    = self.jail.return_y
                    self._jail_score = self.jail.score
                    self.start_fade('jail_return', 0)

            elif self.state == STATE_GAMEOVER and self.gameover:
                self.gameover.update()

            elif self.state == STATE_WIN and self.win:
                self.win.update()

            elif self.state == STATE_LEADERBOARD and self.leaderboard:
                self.leaderboard.update()

            self._do_fade_transition()

            # ── DRAW ────────────────────────────────────────────────────
            if self.state == STATE_MENU:
                self.menu.draw(screen)
            elif self.state == STATE_L1 and self.level1:
                self.level1.draw(screen)
                draw_lives_hud(screen, self.lives)
            elif self.state == STATE_L2 and self.level2:
                self.level2.draw(screen)
                draw_lives_hud(screen, self.lives)
            elif self.state == STATE_L3 and self.level3:
                self.level3.draw(screen)
                draw_lives_hud(screen, self.lives)
            elif self.state == STATE_L4 and self.level4:
                self.level4.draw(screen)
            elif self.state == STATE_JAIL and self.jail:
                self.jail.draw(screen)
            elif self.state == STATE_GAMEOVER and self.gameover:
                self.gameover.draw(screen)
            elif self.state == STATE_WIN and self.win:
                self.win.draw(screen)
            elif self.state == STATE_LEADERBOARD and self.leaderboard:
                self.leaderboard.draw(screen)
            else:
                screen.fill(BLACK)

            if self.fade_alpha > 0:
                fade_surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
                fade_surf.fill((0, 0, 0, self.fade_alpha))
                screen.blit(fade_surf, (0, 0))

            # Center game_surf on actual display with black bars
            display_w, display_h = _display.get_size()
            _display.fill(BLACK)
            frame_surf, (dest_x, dest_y) = fit_to_display(game_surf, display_w, display_h)
            _display.blit(frame_surf, (dest_x, dest_y))

            pygame.display.flip()

        pygame.quit()
        sys.exit()


if __name__ == '__main__':
    game = Game()
    game.run()
