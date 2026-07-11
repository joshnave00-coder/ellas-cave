# Ella's Cave — Claude Project Guide

## Run / Test
```
python ella_cave.py          # run the game
python -m py_compile constants.py leaderboard.py drawing.py entities.py player.py levels.py levels_z3.py levels_z4.py screens.py zones.py ella_cave.py sprites.py && echo OK   # syntax check all
```

## Stack
Python 3.8+ / Pygame 2.x — multi-module. Art is procedural by default; an
optional **sprite system** (`sprites.py` + `assets/`) lets PNG files override
specific draw functions, with graceful fallback to the procedural version
when a file is missing.

---

## Module Map

| File | Contents |
|------|---------|
| `constants.py` | `pygame.init()`, `screen`, `clock`, `FPS`, physics constants, colors, fonts, `dk`/`lt`/`txt`/`draw_rounded_rect`, `GROUND_Y`, `cam_y_global` |
| `leaderboard.py` | `LB_FILE`, `Leaderboard` class, `LEADERBOARD` singleton |
| `drawing.py` | `Particle`, `Particles`, `particles` singleton; all `draw_*` functions (incl. `draw_cave_bat`, `draw_falling_rock`, `draw_lava_pit`, `draw_house`, `draw_heart`, `draw_bunny`); snow system; **storm system** (`trigger_storm`/`update_storm`/`draw_storm`/`reset_storm`, `STORM_IN_ALL_LEVELS`); `draw_level1_bg`, `draw_level2_bg`, `draw_torch_cave`; `draw_hud`, `draw_leaderboard_block` |
| `entities.py` | `Platform`, `Spike`, `Coin`, `Tube`, `IceBridge`, `LavaPool`, `NetProjectile`, `PolarBear`, `HumanGuard`, `FoxFriend`, `MovingPlatform`, `CaveBat`, `FallingRock`, `HomeAnimal` (Level 4 huggable) |
| `player.py` | `Player` class — physics, input, ice bridge power, collision; coin pickup calls `trigger_storm()` |
| `levels.py` | `FOX_FRIEND_COLORS`, `make_level1_*` / `make_level2_*` factory functions, `make_fox_friends` |
| `levels_z3.py` | Level 3 factories: `make_level3_platforms` (incl. `MovingPlatform`), `make_level3_spikes`, `make_level3_coins`, `make_level3_bats`, `make_level3_falling_rocks`, `make_level3_guards`, `make_level3_fox_friends`; `LEVEL_W`, `CHEST_X`, `CHEST_Y`, `PITS` constants |
| `levels_z4.py` | Level 4 (Home) factories: `make_level4_platforms`, `make_level4_coins`, `make_level4_people`, `make_level4_animals`; `LEVEL_W`, `HOUSE_X`, `HOUSE_Y`, `DOOR_RECT` constants |
| `screens.py` | `MenuScreen`, `GameOverScreen`, `WinScreen`, `FoxJailScreen`, `LeaderboardScreen` |
| `zones.py` | `Level1`, `Level2`, `Level3`, `Level4` (note: code uses **Level** naming, not "Zone") |
| `ella_cave.py` | `STATE_*` constants, `Game` class (state machine + fade), entry point |
| `sprites.py` | Optional sprite loader: `get_sprite(name, target_size, flip_x)` and `get_animation(name, frames, target_size, flip_x)`. Reads PNGs from `assets/`; caches loaded/scaled/flipped surfaces; returns `None` for any name that has no file so callers can fall back to procedural drawing. Small (<100 px) sources scaled with nearest-neighbor (crisp pixel art); larger sources with `smoothscale`. |
| `assets/` | Optional PNG art (gitignored). See `assets/README.md` for the curated shopping list (polar_bear.png, catcher.png, volcano.png, lava.png) with direct OpenGameArt URLs and license/attribution info. |

### Dependency graph (no circular imports)
```
constants ← leaderboard ← drawing ← entities ← player
                                  ↑             ↑
                              levels ──────────┘
                           levels_z3 ────────────┐
                           levels_z4 ────────────┤
                                  ↓              ↓
                             screens ← zones ← ella_cave
```

---

## Key Constants (constants.py)
```python
SCREEN_W, SCREEN_H = 1200, 700
FPS        = 60
GRAVITY    = 0.52
MAX_FALL   = 18
JUMP_VEL   = -17      # negative = upward
MOVE_SPEED = 6
ICE_KEY    = pygame.K_x
DOWN_KEY   = pygame.K_DOWN
GROUND_Y   = 585      # y where the ground surface sits
```

## Game States (ella_cave.py)
```
STATE_MENU | STATE_L1 | STATE_L2 | STATE_L3 | STATE_L4 | STATE_JAIL | STATE_GAMEOVER | STATE_WIN | STATE_LEADERBOARD
```
(`STATE_L4` = Level 4 "Home" — the safe free-roam ending; reached after Level 3's chest.)

## Level1 Constants (zones.py, Level1 class body)
```python
LEVEL_W         = 6600
LAVA_TRIGGER_X  = 3100
CAVE_ENTRANCE_X = 6100
```

## Level3 Constants (levels_z3.py)
```python
LEVEL_W = 5800
CHEST_X = 5520
PITS    = [(700,180),(1980,200),(2700,220),(3480,240),(4280,220),(4850,180)]
```

## Level4 Constants (levels_z4.py)
```python
LEVEL_W   = 3600
HOUSE_X   = 3380              # centre x of the cozy house (back of the cave)
HOUSE_Y   = GROUND_Y
DOOR_RECT = (HOUSE_X-36, GROUND_Y-120, 72, 120)   # walk into it → "Welcome home"
```

## LavaPool (entities.py)
```python
ANCHOR_X  = 3295   # right foot of volcano (world x)
MAX_WIDTH = 220    # px — jumpable with ice bridge or running jump
```

---

## Architecture Notes

- **Platform collision — top only**: vertical landing fires when `vy > 0` (falling) and `rect.bottom - vy <= pr.top + 10`. No horizontal (side) collision for platforms — Ella passes through them freely from the sides and below, eliminating diagonal-jump sliding against shelves. **Ice bridges** retain side-collision so Ella can walk up to and step onto them.
- **Fade system** (`Game.start_fade(target, score)` in `ella_cave.py`): fades to black, switches state at alpha=255, fades back in. Targets: `'l1'`, `'l2'`, `'l3'`, `'l4'`, `'menu'`, `'jail_return'`.
- **Level progression**: Level1 → (cave entrance) → Level2 → (chest opened, +200 pts) → Level3 → (chest opened, +500 pts) → **Level4 "Home"** → (player presses ENTER once home) → WinScreen.
- **Level 4 — Ella's Home** (`Level4` in `zones.py`, data in `levels_z4.py`): a warm, completely **safe free-roam ending** — no hazards, no death, no lives HUD, and it never auto-ends. A cozy `draw_house` sits at the back of the cave (`HOUSE_X`), five calm `draw_human` family members with floating `draw_heart`s stand near it, and ~15 huggable `HomeAnimal`s (foxes/bears/bunnies) roam. Walking into `door_rect` fires a one-time "Welcome home" banner + `HOME_BONUS` (250 pts). Pressing ENTER once home → `Level4.handle()` returns `'win'` → existing `WinScreen` (uses `Level4.fox_friends`, built from `make_fox_friends()`, for the party). Hugging: press **H** (or UP) within an animal's `hug_rect` → `HomeAnimal.hug()` (happy hop + heart puff); `hugged_count / total_animals` shown in HUD.
- **Storm on coin** (`drawing.py` storm system): `Player.update()` calls `trigger_storm()` on every coin pickup → rain + lightning flash that decays over `STORM_DECAY_FRAMES` (~4 s). A **cooldown** (`STORM_COOLDOWN_FRAMES`, ~20 s) makes `trigger_storm()` a no-op while active, so it stays an occasional treat instead of near-constant rain — tune this to change how often storms occur. All levels call `update_storm()`; `draw_storm()` is drawn in Level 4 always and in Levels 1-3 when `STORM_IN_ALL_LEVELS` is True (set False to limit storms to Level 4). `Level4.__init__` calls `reset_storm()` for a clean sky on arrival.
- **Creatures respect pits/gaps** (fairness with Ella): `FoxFriend` lands on **platform tops only** (no invisible `GROUND_Y` floor) and its edge check (look just past the leading edge) runs **every grounded frame**, so foxes turn around at any gap instead of strolling across it; a safety net catches any stray fox. `PolarBear.update()` clamps the bear to `[patrol_min, patrol_max]` even while chasing, so it never floats across a gap. Spawners place foxes only on solid ground.
- **Spike placement & art**: spikes sit on **solid surfaces only** — ground spikes on ground segments, "ledge" spikes anchored on a platform top (`cx` inside the platform, `y` = its top); no free-floating spikes. Art is `draw_spike_set` → anti-aliased shaded steel blades on a stone mount (uses `_aa_poly` / `pygame.gfxdraw`).
- **Jail return**: net catch in Level1 → `FoxJailScreen` → on done, `start_fade('jail_return')` → `Level1` created at `(guard.x − 500, GROUND_Y)`. Guards in Level3 are lethal (no jail — nets kill directly).
- **Level3 hazards**: `CaveBat` (swoops near player), `FallingRock` (stalactite shakes ~1 s then drops), `MovingPlatform` (oscillates across each lava pit), lava pits (fall below `GROUND_Y + 120` → death).
- **Death**: goes to `GameOverScreen`; ENTER retries from Level1, M goes to menu.
- **Initials entry**: direct typing (letter → cursor advances); BACKSPACE steps back; ENTER saves → menu; ESC skips → menu.
- **HumanGuard gender**: randomly male or female per instance via `random.choice`. `_render_catcher(surf, S, gender)` varies the jacket color + hair/cap (female = berry jacket + ponytail; male = olive jacket + ranger cap with brim); both hold a butterfly net.
- **High-quality procedural art (supersampled)**: `draw_polar_bear`, `draw_human` (the "fox catcher"), and the spikes are drawn at `_SUPER`× resolution and `smoothscale`-d down via `_cached_sprite(key, w, h, draw_fn, flip_x)` — this anti-aliases every shape (no jaggies) at the game's real resolution. Each `(key, flip)` is rendered once and cached in `_proc_cache`. Render helpers: `_render_bear` (8 walk frames, `_BEAR_W/_BEAR_H/_BEAR_FOOT/_BEAR_FRAMES`), `_render_catcher` (per-gender, `_CATCHER_W/_CATCHER_H/_CATCHER_FOOT`). Both anchor to `cy` (feet) via the `_*_FOOT` design-space y. `draw_volcano` is drawn directly (single instance) with `_aa_poly` cone + shading, snow cap, pulsing crater, smoke, embers; the volcano→pool lava ribbon lives in `LavaPool.draw` (`entities.py`).
- **Draw alignment**: `draw_polar_bear` and `draw_human` (both genders) interpret `cy` as `rect.bottom` (feet level). The blit is offset so the visual feet sit exactly at `cy`. Bear: `blit y = cy - 119`. Guards: `blit y = cy - 105`. `draw_treasure_chest` interprets `wy` as the desired box-bottom (ground level); internally `sy = wy - 58`.
- **FoxFriend flip cooldown**: `_flip_cd` (int, frames) is set to `20` on `__init__` and reset to `20` after any direction flip from edge/spike detection. Prevents rapid oscillation when spawning near hazards.
- **Fox friend spawn filtering**: `make_fox_friends()` (Level 2) and `make_level3_fox_friends()` pre-filter positions to keep foxes ≥70 px from any ground-spike cx and **only on solid ground** — Level 2 excludes the gaps between ground segments; Level 3 excludes pit x-ranges.
- **Scoring**: coins = 10 pts each; Level2 chest = +200 pts; Level3 chest = +500 pts; Level4 reaching home = +250 pts.
- **Leaderboard**: `LB_FILE` always resolves relative to the script directory (`os.path.dirname(os.path.abspath(__file__))`).
- **particles global**: defined in `drawing.py`, imported by `player.py` and `zones.py`.
- **Art is procedural by default, with optional sprite overrides**: `drawing.py` imports `get_sprite`/`get_animation` from `sprites.py`. Four draw functions check for an asset first and fall back to the hand-drawn art if it's missing: `draw_polar_bear` (`assets/polar_bear.png`, walk-strip, `POLAR_BEAR_FRAMES`), `draw_human` (`assets/catcher.png`, walk-strip, `CATCHER_FRAMES` — sprite path ignores `gender`), `draw_volcano` (`assets/volcano.png`, single image, anchored so its base sits at the original ground), `draw_lava_pit` + `LavaPool.draw` (`assets/lava.png`, tiled animated strip via `_blit_lava_tile`, `LAVA_FRAMES`). Frame-count and target-size constants live near each helper in `drawing.py` so artists can swap in differently-sized strips.
- **Easter eggs** (main menu, `MenuScreen.handle`): pressing `2`, `3`, or `4` five times within 3 seconds jumps directly to Level 2, 3, or 4 respectively (`l2_cheat`/`l3_cheat`/`l4_cheat`).

---

## Common Edit Targets

| Task | File | What to change |
|------|------|---------------|
| Physics tuning | `constants.py` | `GRAVITY`, `JUMP_VEL`, `MOVE_SPEED` |
| Level 1 spike/coin/bear/guard layout | `levels.py` | `make_level1_spikes()`, `make_level1_coins()`, `make_level1_bears()`, `make_level1_guards()` |
| Level 2 spike/coin layout | `levels.py` | `make_level2_spikes()`, `make_level2_coins()` |
| Level 3 layout (pits, spikes, coins) | `levels_z3.py` | `make_level3_*()` factory functions; `PITS` list |
| Level 3 bat count/speed | `levels_z3.py` | `make_level3_bats()` |
| Level 3 falling rock positions | `levels_z3.py` | `make_level3_falling_rocks()` |
| Level 3 guard behavior | `levels_z3.py` `make_level3_guards()`; `entities.py` `HumanGuard.__init__` |
| Level 3 moving platform speed | `levels_z3.py` | `make_level3_platforms()` — `speed=` param on each `mp()` call |
| Bear count/speed | `levels.py` `make_level1_bears()`; `entities.py` `PolarBear.__init__` (`chase_speed`) |
| Guard behavior (Level 1) | `entities.py` `HumanGuard.__init__` (`throw_interval`, `detect_range`, net `spd`) |
| Lava pool size | `entities.py` `LavaPool` (`MAX_WIDTH`, `GROW_RATE`) |
| Coin value | `player.py` `Player.update()` (`self.score += 10`) |
| Jail checkpoint offset | `zones.py` `Level1.update()` (`g.rect.left - 500`) |
| Fox friend colors | `levels.py` `FOX_FRIEND_COLORS` |
| Polar bear color / contrast | `constants.py` `BEAR_W`, `BEAR_S`; arm outlines in `drawing.py` `draw_polar_bear()` |
| Swap in real art for bear / catcher / volcano / lava | drop a correctly-named PNG into `assets/` (see `assets/README.md`); update frame-count constants in `drawing.py` (`POLAR_BEAR_FRAMES`, `CATCHER_FRAMES`, `LAVA_FRAMES`) and target-size tuples (`_BEAR_SPRITE_SIZE`, `_CATCHER_SPRITE_SIZE`, `_VOLCANO_SPRITE_SIZE`, `_LAVA_TILE_SIZE`) if needed |
| Catcher / guard visuals (both genders) | `drawing.py` `_render_catcher()` |
| Polar bear visuals | `drawing.py` `_render_bear()` |
| Volcano visuals | `drawing.py` `draw_volcano()`; lava stream in `entities.py` `LavaPool.draw()` |
| Cave crystals removed | (decorative crystals deleted from `draw_level2_bg` — they read as fake spikes) |
| Chest ground position | `drawing.py` `draw_treasure_chest()` (`sy = wy - 58`); `zones.py` `Level2.CHEST_Y`; `levels_z3.py` `CHEST_Y` |
| Ice bridge behavior | `entities.py` `IceBridge`; `player.py` `Player.use_ice()` |
| Cave bat appearance | `drawing.py` `draw_cave_bat()` |
| Falling rock appearance | `drawing.py` `draw_falling_rock()` |
| Lava pit appearance | `drawing.py` `draw_lava_pit()` |
| Spike appearance | `drawing.py` `draw_spike_set()` (steel blades, `_aa_poly`) |
| Spike placement | `levels.py` `make_level1_spikes()`/`make_level2_spikes()`; `levels_z3.py` `make_level3_spikes()` |
| Storm frequency / look | `drawing.py` `STORM_COOLDOWN_FRAMES`, `STORM_DECAY_FRAMES`, `STORM_IN_ALL_LEVELS`, `draw_storm()` |
| Creatures crossing gaps | `entities.py` `FoxFriend.update` (edge check), `PolarBear.update` (patrol clamp) |
| Screen layouts | `screens.py` — one class per screen |
| Level 1 / 2 level logic | `zones.py` — `Level1` or `Level2` |
| Level 3 level logic | `zones.py` — `Level3` |
| Level 4 (Home) layout | `levels_z4.py` — `make_level4_platforms/coins/people/animals`; `LEVEL_W`, `HOUSE_X`, `DOOR_RECT` |
| Level 4 logic / hug & welcome | `zones.py` — `Level4` (`HOME_BONUS`, `hug_cd`, `door_rect`) |
| Huggable animals | `entities.py` `HomeAnimal` (`hug()`, `hug_rect`, wander bounds); `levels_z4.py` `make_level4_animals()` |
| Family (5 people) | `levels_z4.py` `make_level4_people()`; drawn via `draw_human` in `Level4.draw` |
| House appearance | `drawing.py` `draw_house()` |
| Bunny / heart art | `drawing.py` `draw_bunny()`, `draw_heart()` |
| Storm look / intensity | `drawing.py` storm system (`STORM_IN_ALL_LEVELS`, `STORM_DECAY_FRAMES`, `trigger_storm`/`draw_storm`) |
| Game state flow | `ella_cave.py` `Game` class |

---

## Refactoring Checklist

- After any refactor that removes or renames variables/functions, grep the entire codebase for remaining references to the old names before considering the task complete.
