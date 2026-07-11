# Changelog

All notable changes to Ella's Cave are documented here.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [v0.6] — Polish, Ground Alignment & Physics Fix

### Fixed

**Entity ground alignment (`drawing.py`)**
- `draw_polar_bear`: blit y corrected so bear feet land exactly at `cy` (= `rect.bottom`). Previously feet rendered ~49 px below the ground surface.
- `draw_human` (male and female): same fix — boot bottoms now sit at `cy`. Previously guards sank ~50 px below the snowy/cave floor.
- `draw_treasure_chest`: `sy` changed from `wy` to `wy - 58` so the box bottom aligns with `wy` (ground level). `CHEST_Y` updated to `GROUND_Y` in both `zones.py` (Zone 2) and `levels_z3.py` (Zone 3).

**Platform collision (`player.py`)**
- Removed horizontal side-collision for all level platforms. Platforms are now pass-through from the sides and below — only the top-landing check remains (`vy > 0`).
- Eliminates the backward slide / stall when Ella jumps diagonally into an elevated shelf.
- Ice bridges retain side-collision so Ella can walk up to and step onto them normally.

**Fox friend rapid-flip on load (`entities.py`)**
- Added `_flip_cd = 20` to `FoxFriend.__init__` and wrapped edge/spike detection in a frame cooldown (resets to 20 after any direction flip). Prevents entities near hazards from oscillating left-right every frame at startup.

**Fox friend spawn filtering (`levels.py`, `levels_z3.py`)**
- `make_fox_friends()`: excludes positions within 70 px of any Zone 2 spike cx.
- `make_z3_fox_friends()`: excludes positions within 70 px of Zone 3 spike cx values and positions inside any lava pit x-range. Foxes no longer spawn directly over holes or on spikes.

### Changed

**Polar bear visuals (`constants.py`, `drawing.py`)**
- `BEAR_W` changed from near-white bluish `(215,226,238)` to warm cream `(242,218,165)` for better contrast against the snowy blue-white background.
- `BEAR_S` updated to medium tan `(198,162,108)` to match.
- Added dark outlines around both arm rectangles in `draw_polar_bear` so they read as distinct limbs rather than blending into the body.

**Female guard hair (`drawing.py`)**
- Replaced the small side arcs with long flowing polygon strands that descend from the bun down past the shoulders.
- Character is now clearly readable as female at a glance.

---

## [v0.5] — Zone 3 & Cave Hazard Overhaul

### Added

**Zone 3 — The Deep Cave (new level)**
- New 5,800 px level that follows Zone 2; the Zone 2 chest now transitions here instead of winning
- `levels_z3.py` added as a standalone file for all Zone 3 level data (mirrors the `levels.py` pattern, easy to iterate independently)
- Six lava pits (180–240 px wide) replace the continuous floor; fall in → death
- One `MovingPlatform` oscillates across each pit — speed increases per pit (0.8× → 1.45×)
- The 220 px ice bridge can barely span some pits; moving platforms are the safer route for wider gaps
- Six `CaveBat` enemies patrol at height; dip aggressively toward Ella when within 200 px
- Six `FallingRock` stalactites: shakes for ~55 frames, then drops; lethal during fall phase
- Two `HumanGuard` enemies at x = 1,855 and x = 4,160; nets are **lethal** in Zone 3 (no jail)
- Ground spikes placed just past each pit landing zone to punish sloppy jumps
- HUD label "Zone 3: The Deep Cave"

**New entities (`entities.py`)**
- `MovingPlatform` — extends `Platform`; oscillates smoothly between two points via sine easing; `speed` param controls frequency
- `CaveBat` — horizontal patrol with dip behaviour; `base_y` + sinusoidal dip scaled by player proximity
- `FallingRock` — state machine: `IDLE → SHAKE → FALLING → LANDED`; trigger radius 70 px

**New draw functions (`drawing.py`)**
- `draw_cave_bat` — procedural bat silhouette with animated wing flap, red glowing eyes, ear details
- `draw_falling_rock` — stalactite shape with shake animation and dust flecks; debris sprite when landed
- `draw_lava_pit` — animated lava surface with wavy polygon, glow bubbles, and ambient heat bloom at pit mouth

**Easter egg**
- Pressing `2` five times within 3 seconds on the main menu skips directly to Zone 3 (score = 0)
- No on-screen hint — purely a secret shortcut

### Changed

**Zone 2 scoring & flow**
- Zone 2 treasure chest now awards **+200 pts** (was +500) and fades to Zone 3 instead of ending the game
- Zone 3 treasure chest awards **+500 pts** and triggers the win/celebration screen
- Win screen celebration scene continues to use the Zone 2 cave layout

**Fox friend AI (`entities.py` `FoxFriend.update`)**
- Added edge/ledge detection: fox friends now turn around 14 px before a pit edge or platform drop — they no longer walk into holes
- Added spike avoidance: fox friends reverse direction when a spike is within 55 px ahead
- `update(platforms, spikes=None)` — `spikes` is optional so the WinScreen call is unaffected

**Polar bear patrol bounds (`levels.py` `make_z1_bears`)**
- Bear 2: patrol adjusted from `3220–3680` to `3545–3900` — old range crossed the lava pool (`3295–3515`); bears no longer walk through lava
- Bear 3: patrol max clamped from `4870` to `4820` — old max overshot the platform edge at `4830`
- Bear 4: patrol max clamped from `5950` to `5770` — old range crossed the gap between platforms `5420–5780` and `5870–6400`

---

## [v0.4] — Module Split & Initials UX Polish

### Changed

**Code architecture — monolith → modules**
- Split the single 2,300-line `ella_cave.py` into 9 focused modules to cut token cost
  on AI-assisted feature iterations (each task now reads 1–2 small files instead of
  the whole codebase)
- `ella_cave_backup.py` preserved as a full single-file safety backup

| New file | Responsibility |
|----------|---------------|
| `constants.py` | pygame init, screen, clock, physics, colors, fonts, helpers |
| `leaderboard.py` | `Leaderboard` class, `LEADERBOARD` singleton, `LB_FILE` path |
| `drawing.py` | `Particle`/`Particles`/`particles`, all `draw_*` functions, snow, backgrounds, HUD |
| `entities.py` | `Platform`, `Spike`, `Coin`, `Tube`, `IceBridge`, `LavaPool`, `NetProjectile`, `PolarBear`, `HumanGuard`, `FoxFriend` |
| `player.py` | `Player` class |
| `levels.py` | `FOX_FRIEND_COLORS`, `make_z1_*` / `make_z2_*` data factories |
| `screens.py` | `MenuScreen`, `GameOverScreen`, `WinScreen`, `FoxJailScreen` |
| `zones.py` | `Zone1`, `Zone2` |
| `ella_cave.py` | `Game` state machine + entry point (~130 lines, thin shell) |

- `GROUND_Y = 585` moved from the middle of the file to `constants.py`
- `cam_y_global = 0` moved to `constants.py`
- No circular imports; dependency order documented in `CLAUDE.md` and `README.md`
- `CLAUDE.md` added with module map, dependency graph, and per-task file quick-reference

**Initials entry — direct keyboard typing**
- Replaced up/down arrow scrolling with direct letter typing: press a key → that letter fills the slot and cursor advances automatically
- BACKSPACE steps cursor back and resets that slot to `A`
- ENTER saves the score and returns directly to the main menu
- ESC skips saving and returns to the main menu

**Leaderboard — save path fixed**
- `LB_FILE` changed from a bare relative path to `os.path.join(os.path.dirname(...), "leaderboard.json")` so scores persist regardless of launch directory

---

## [v0.3] — Kid-Friendly Difficulty Pass

### Changed

**Difficulty — hazards**
- Zone 1 spikes reduced from 32 to 11; Zone 2 spikes reduced from 16 to 6
- Polar bears reduced from 7 to 4; patrol speed lowered; chase speed reduced from 2.8 to 1.6 px/frame; detection range narrowed from 320 px to 200 px
- Human guards reduced from 3 to 2; net throw interval increased from 190 to 320 frames; net speed reduced from 4.0 to 2.5 px/frame; detection range narrowed from 250 px to 170 px

**Difficulty — physics**
- `JUMP_VEL` increased from -15 to -17 (higher jump)
- `MOVE_SPEED` increased from 5 to 6 (more responsive)
- `GRAVITY` reduced from 0.58 to 0.52 (floatier, more hang-time)

**Lava — redesigned from scratch**
- Removed the old screen-filling `LavaWall` chase mechanic
- Replaced with `LavaPool`: ground-level pool that flows from the volcano base rightward (max 220 px)
- Animated lava stream connects crater to pool; wavy surface with glowing hotspot bubbles

**Death / respawn**
- `GameOverScreen` shows a friendly tip message; ENTER retries, M returns to menu

**Scoring**
- Coin value doubled from 5 to 10 points

**Fox catchers — gender variety**
- `HumanGuard` randomly selects male or female on construction
- Added `_draw_human_female()`: teal-plum coat, A-line skirt, ankle boots, hair bun

**Fox Jail — fixed return-to-level bug**
- Checkpoint offset increased from 280 px to 500 px so both guard checkpoints always land on solid platform
- Transition now uses the fade system (`start_fade('jail_return')`) instead of abrupt state switch

---

## [v0.2] — Pygame Platformer

### Added

**Engine**
- Full side-scrolling platformer physics: gravity, variable jump, max-fall cap, AABB collision
- Horizontal camera following Ella, clamped to level bounds
- Global particle system (jump dust, coin pops, ice effects, lava sparks, win burst)
- Smooth fade transitions between all game states
- `leaderboard.json` persistence via Python's `json` module

**Zone 1 — Snowy Mountains**
- 6,600 px scrolling level with layered parallax mountain silhouettes and falling snow
- 38 elevated platforms, ~24 spike clusters
- 7 polar bears, 3 human guards, erupting volcano, lava wall chase
- 1 shortcut tube skipping the volcano approach
- 70+ coins

**Zone 2 — The Cave**
- 4,400 px cave with warm amber glow, torch lights, crystal formations
- 80 fox friends in 23 colors and varied scales
- 12 spike clusters, 40+ coins
- Glowing treasure chest at the far end

**Special mechanics**
- Ice Bridge, Fox Jail cutscene, one-way platforms

**Screens**
- Main menu, game-over, win/celebration, initials entry, top-5 leaderboard

**Procedural art (no image assets)**
- Ella fox, polar bear, human guards, spike clusters, spinning net, volcano, green tube, cave entrance, treasure chest, fox friends, ice bridge, fox jail cell

---

## [v0.1] — Initial Release

### Added

**Engine**
- Top-down camera with X/Y follow, clamped to world bounds
- Fade transitions, global particle system

**Zone 1 — Snowy Mountains**
- Parallax silhouettes, falling snow, tree clusters, boulder fields
- 24 spike clusters, human guard with net, volcano with lava balls, cave entrance

**Zone 2 — The Cave**
- Stone-tile floor, crystal glow, torch flames
- 10 spike clusters, treasure chest
- 260 fox friends in 25 colors

**Win celebration**
- Confetti rain, fox friends gradually appearing, win message panel
