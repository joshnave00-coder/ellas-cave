"""Headless regression tests for bugs found in the durability review.

Run from the project root:   python -m unittest discover -s tests -v

The game runs with SDL's dummy video driver (no window) and the leaderboard is
redirected to a temp file, so the real leaderboard.json is never written.
"""
import json, os, sys, tempfile, unittest

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame
import leaderboard

_TMP = tempfile.mkdtemp(prefix='ella_test_')
leaderboard.LB_FILE = os.path.join(_TMP, 'leaderboard.json')
leaderboard.LEADERBOARD.scores = []

import ella_cave
import screens
from ella_cave import Game, fit_to_display
from constants import GROUND_Y, SCREEN_W, SCREEN_H
from entities import IceBridge, NetProjectile, Platform
from player import Player
from screens import FoxJailScreen, GameOverScreen


def key(k, ch=''):
    return pygame.event.Event(pygame.KEYDOWN, key=k, unicode=ch)

ENTER = key(pygame.K_RETURN, '\r')
SUPERSCRIPT_TWO = key(178, '²')     # the "²" key on AZERTY keyboards


class Keys(dict):
    """Stand-in for pygame.key.get_pressed()."""
    def __missing__(self, k):
        return False


class Driver:
    """Runs the real Game.run() loop, feeding it scripted input. `script` is a
    generator taking (game, driver) that yields once per frame."""
    MAX_FRAMES = 20000

    def __init__(self, script):
        self.keys = Keys()
        self.events = []
        self.frames = 0
        self.game = Game()
        self._script = script(self.game, self)

    def tick(self, fps=0):
        self.frames += 1
        if self.frames > self.MAX_FRAMES:
            raise AssertionError(f'script stuck in state {self.game.state!r}')
        try:
            next(self._script)
        except StopIteration:
            self.events.append(pygame.event.Event(pygame.QUIT))

    def _get(self):
        ev, self.events = self.events, []
        return ev

    def wait(self, cond):
        while not cond():
            yield

    def run(self):
        saved = (ella_cave.clock, pygame.event.get, pygame.key.get_pressed,
                 pygame.quit)
        ella_cave.clock = self
        pygame.event.get = self._get
        pygame.key.get_pressed = lambda: self.keys
        pygame.quit = lambda: None          # keep pygame alive for later tests
        try:
            self.game.run()
        except SystemExit:
            pass
        finally:
            (ella_cave.clock, pygame.event.get, pygame.key.get_pressed,
             pygame.quit) = saved


def put(player, x, bottom=GROUND_Y):
    player.rect.x = x
    player.rect.bottom = bottom
    player.vx = player.vy = 0


class LeaderboardTests(unittest.TestCase):
    def setUp(self):
        for f in os.listdir(_TMP):
            os.remove(os.path.join(_TMP, f))

    def _write(self, text):
        with open(leaderboard.LB_FILE, 'w') as f:
            f.write(text)

    def test_malformed_entries_are_dropped_not_fatal(self):
        self._write(json.dumps({'scores': [
            {'initials': 'OK1', 'score': '300'}, {'initials': 'NOSCORE'},
            {'score': 50}, 'junk', {'initials': None, 'score': 'abc'},
            {'initials': 'ZED', 'score': 120}]}))
        lb = leaderboard.Leaderboard()
        self.assertEqual(lb.top5(), [{'initials': 'OKA', 'score': 300},
                                     {'initials': 'ZED', 'score': 120}])
        self.assertTrue(lb.qualifies(10))      # used to raise on str scores

    def test_corrupt_file_is_set_aside_not_overwritten(self):
        self._write('{"scores": [{"initials": "LIL", "score": 18')   # truncated
        lb = leaderboard.Leaderboard()
        self.assertEqual(lb.scores, [])
        lb.add('NEW', 10)
        with open(leaderboard.LB_FILE + '.corrupt') as f:
            self.assertIn('LIL', f.read())

    def test_save_roundtrip_and_no_temp_left_behind(self):
        lb = leaderboard.Leaderboard()
        for i in range(7):
            lb.add('abc', i * 10 + 10)
        self.assertEqual([s['score'] for s in leaderboard.Leaderboard().top5()],
                         [70, 60, 50, 40, 30])
        self.assertEqual(os.listdir(_TMP), ['leaderboard.json'])


class InputTests(unittest.TestCase):
    def test_jail_math_ignores_non_ascii_digit_keys(self):
        j = FoxJailScreen(100, GROUND_Y, 0)
        while j.math_q is None:
            j.update()
        j.handle(SUPERSCRIPT_TWO)              # str.isdigit() is True for this
        j.handle(ENTER)                        # used to raise ValueError
        self.assertEqual(j.math_input, '')
        for ch in str(j.math_q[3]):
            j.handle(key(ord(ch), ch))
        j.handle(ENTER)
        self.assertTrue(j.math_solved)

    def test_text_entry_survives_odd_keys(self):
        leaderboard.LEADERBOARD.scores = []
        g = GameOverScreen(500, 2, 'bat')
        self.assertEqual(g.phase, 'enter_initials')
        for ev in (key(pygame.K_LSHIFT), SUPERSCRIPT_TWO, key(pygame.K_F5),
                   key(pygame.K_BACKSPACE), key(pygame.K_BACKSPACE),
                   key(pygame.K_e, 'e'), key(pygame.K_1, '1'), key(pygame.K_l, 'L')):
            g.handle(ev)
        self.assertEqual(''.join(g.initials), 'ELA')


class PhysicsTests(unittest.TestCase):
    def test_jumping_up_through_ice_bridge_does_not_teleport(self):
        p = Player(300, GROUND_Y)
        ground = [Platform(0, GROUND_Y, 2000, 40)]
        p.ice_bridges.append(IceBridge(200, GROUND_Y - 110, 220))   # overhead
        p.vy = -17
        for _ in range(40):
            p.vx = 6
            x0 = p.rect.x
            p.update(ground, [], [], [])
            self.assertEqual(p.rect.x - x0, 6)   # used to snap ~150 px left

    def test_ice_bridge_still_blocks_from_the_side(self):
        p = Player(100, GROUND_Y)
        ground = [Platform(0, GROUND_Y, 2000, 40)]
        b = IceBridge(200, GROUND_Y - 20, 220)   # knee-high: a wall from the side
        p.ice_bridges.append(b)
        for _ in range(60):
            p.vx = 6
            p.update(ground, [], [], [])
        self.assertEqual(p.rect.right, b.rect.left)


class DisplayTests(unittest.TestCase):
    def test_small_window_shows_whole_frame(self):
        s = pygame.Surface((SCREEN_W, SCREEN_H))
        for dw, dh in ((800, 500), (640, 700), (1200, 400), (1, 1)):
            out, (x, y) = fit_to_display(s, dw, dh)
            w, h = out.get_size()
            self.assertTrue(x >= 0 and y >= 0 and x + w <= dw and y + h <= dh,
                            (dw, dh, x, y, w, h))

    def test_large_window_keeps_native_size_centred(self):
        s = pygame.Surface((SCREEN_W, SCREEN_H))
        out, pos = fit_to_display(s, 1920, 1080)
        self.assertIs(out, s)
        self.assertEqual(pos, (360, 190))


class JourneyTests(unittest.TestCase):
    """Whole flows through the real main loop. The player is teleported between
    checkpoints — these check state/score/lives plumbing, not level difficulty."""

    def setUp(self):
        leaderboard.LEADERBOARD.scores = []
        if os.path.exists(leaderboard.LB_FILE):
            os.remove(leaderboard.LB_FILE)

    def test_menu_to_win_and_score_saved(self):
        seen = {}

        def script(g, d):
            d.events.append(ENTER)
            yield from d.wait(lambda: g.state == 'l1' and g.fade_dir == 0)
            x0 = g.level1.player.rect.x
            d.keys[pygame.K_RIGHT] = True
            for _ in range(30):
                yield
            d.keys.clear()
            seen['walked'] = g.level1.player.rect.x - x0
            base = g.level1.player.score        # coins picked up while walking
            put(g.level1.player, g.level1.CAVE_ENTRANCE_X + 40)
            yield from d.wait(lambda: g.state == 'l2')
            seen['l2'] = g.level2.player.score - base   # before any L2 coin
            yield from d.wait(lambda: g.fade_dir == 0)
            base = g.level2.player.score - 100
            put(g.level2.player, g.level2.CHEST_X)
            yield from d.wait(lambda: g.state == 'l3' and g.fade_dir == 0)
            seen['l3'] = g.level3.player.score - base
            # lose one life on a spike, then carry on
            put(g.level3.player, g.level3.spikes[0].cx - 19)
            yield from d.wait(lambda: g.lives == 2)
            seen['revived'] = not g.level3.player.dead and g.state == 'l3'
            put(g.level3.player, g.level3.CHEST_X)
            yield from d.wait(lambda: g.state == 'l4' and g.fade_dir == 0)
            seen['l4'] = g.level4.player.score - base
            base4 = g.level4.player.score
            d.events.append(ENTER)              # not home yet: must be ignored
            yield
            seen['early_enter'] = g.state
            d.keys[pygame.K_RIGHT] = True       # walk the whole safe level
            yield from d.wait(lambda: g.level4.reached_home)
            d.keys.clear()
            seen['home'] = g.level4.player.score - base4
            seen['final'] = g.level4.player.score
            d.events.append(ENTER)
            yield from d.wait(lambda: g.state == 'win')
            seen['phase'] = g.win.phase
            for ch in 'ela':
                d.events.append(key(ord(ch), ch))
            d.events.append(ENTER)
            yield from d.wait(lambda: g.state == 'menu' and g.fade_dir == 0)

        Driver(script).run()
        self.assertEqual(seen['walked'], 180)
        self.assertEqual(seen['l2'], 100)
        self.assertEqual(seen['l3'], 300)
        self.assertTrue(seen['revived'])
        # +500 chest bonus, plus up to three coins that sit on the chest
        self.assertIn(seen['l4'], (800, 810, 820, 830))
        self.assertEqual(seen['early_enter'], 'l4')
        self.assertGreaterEqual(seen['home'], 250)      # bonus + coins on the way
        self.assertEqual(seen['phase'], 'enter_initials')
        saved = leaderboard.Leaderboard().top5()       # re-read from disk
        self.assertEqual(saved, [{'initials': 'ELA', 'score': seen['final']}])

    def test_three_deaths_game_over_math_retry_same_level(self):
        seen = {}

        def script(g, d):
            g.lives = 0                          # as left behind by a previous game over
            for _ in range(5):
                d.events.append(key(pygame.K_3, '3'))
            yield from d.wait(lambda: g.state == 'l3' and g.fade_dir == 0)
            seen['lives_at_start'] = g.lives
            g.level3.player.score = 40
            # fall into the first lava pit three times
            for left in (2, 1):
                put(g.level3.player, 770, GROUND_Y + 60)
                yield from d.wait(lambda: g.lives == left)
                seen[f'respawn{left}'] = g.level3.player.rect.bottom <= GROUND_Y
            put(g.level3.player, 770, GROUND_Y + 60)
            yield from d.wait(lambda: g.state == 'gameover')
            go = g.gameover
            seen['tip_is_lava'] = go.tip in screens._DEATH_MESSAGES['lava']
            seen['phase'] = go.phase
            d.events.append(ENTER)               # accept AAA
            yield
            yield
            seen['phase2'] = go.phase
            for ch in go.math_answer:
                d.events.append(key(ord(ch), ch))
            d.events.append(ENTER)
            yield from d.wait(lambda: g.state == 'l3' and g.fade_dir == 0)
            seen['retry'] = (g.lives, g.level3.player.score)

        Driver(script).run()
        self.assertEqual(seen['lives_at_start'], 3)
        self.assertTrue(seen['respawn2'] and seen['respawn1'])
        self.assertTrue(seen['tip_is_lava'])
        self.assertEqual((seen['phase'], seen['phase2']), ('enter_initials', 'math'))
        self.assertEqual(seen['retry'], (3, 40))

    def test_net_catch_jail_and_return_keeps_coins_collected(self):
        seen = {}

        def script(g, d):
            d.events.append(ENTER)
            yield from d.wait(lambda: g.state == 'l1' and g.fade_dir == 0)
            L = g.level1
            d.keys[pygame.K_RIGHT] = True        # pick up the first coins
            yield from d.wait(lambda: L.player.score >= 30)
            d.keys.clear()
            guard = L.guards[0]
            put(L.player, guard.rect.left - 150)
            yield
            seen['score'] = L.player.score
            guard.nets.append(NetProjectile(*L.player.rect.center, 0, 0))
            yield from d.wait(lambda: g.state == 'jail')
            yield from d.wait(lambda: g.jail.math_q is not None)
            d.events.append(ENTER)               # empty answer: ignored
            for ch in str(g.jail.math_q[3]):
                d.events.append(key(ord(ch), ch))
            d.events.append(ENTER)
            yield from d.wait(lambda: g.state == 'l1' and g.fade_dir == 0)
            L2 = g.level1
            seen['new_level'] = L2 is not L
            seen['after'] = (L2.player.score, sum(c.collected for c in L2.coins) * 10,
                             L2.player.rect.x, g.lives)
            seen['expect_x'] = max(100, guard.rect.left - 500)

        Driver(script).run()
        self.assertTrue(seen['new_level'])
        score, coin_pts, x, lives = seen['after']
        self.assertEqual(score, seen['score'])
        self.assertEqual(coin_pts, seen['score'])    # used to be 0: coins respawned
        self.assertLess(abs(x - seen['expect_x']), 60)
        self.assertEqual(lives, 3)


if __name__ == '__main__':
    unittest.main()
