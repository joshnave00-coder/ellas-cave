# Ella's Cave 🦊

A 2D platformer adventure starring Ella, a magical ice-powered fox, on a quest through snowy mountains, a warm glowing cave, and a deadly deep cavern to find the ultimate treasure chest — and reunite with a million fox friends.

---

## Requirements

- Python 3.8+
- pygame 2.x

```bash
pip install pygame
```

---

## Running the Game

```bash
python ella_cave.py
```

---

## Controls

| Key | Action |
|-----|--------|
| `← →` Arrow Keys | Move left / right |
| `↑` Arrow Key or `Space` | Jump |
| `↓` Arrow Key | Enter a tube / pipe |
| `X` | Activate ice bridge power |

---

## Gameplay

### Zone 1 — Snowy Mountains

Ella starts in a wide snowy mountain world and must navigate to the cave entrance at the far right.

**Obstacles & traps**

| Hazard | What happens |
|--------|-------------|
| **Spike traps** | Touch one → restart the zone |
| **Polar bears** | Chase Ella on sight → restart the zone |
| **Human guard** | Throws a net when Ella gets close → Fox Jail (see below) |
| **Volcano lava** | Once triggered, a lava pool spreads rightward from the volcano base |
| **Gaps / cliffs** | Use the ice bridge (`X`) to cross gaps that are too wide to jump |

**Tubes** — Green pipes scattered through the zone. Stand on one and press `↓` to warp to a shortcut exit past the volcano.

### Fox Jail

When a human guard's net hits Ella she is taken to Fox Jail instead of dying. A friend fox arrives, unlocks the cell, and Ella is freed at a checkpoint just before the guard.

### Ice Bridge

Press `X` to conjure a glowing ice platform ahead of Ella. The bridge builds left-to-right over ~45 frames, lasts 8 seconds, then melts. Recharges in ~5 seconds (shown by a bar in the top-right corner). Spans 220 px — useful for crossing lava or wide gaps.

---

### Zone 2 — The Cave

A warm amber cave filled with 80+ fox friends of every color and size. Spike traps stand between Ella and a glowing chest at the far end.

**Chest** — Reaching it awards **+200 pts** and opens a hidden passage deeper into the mountain, leading to Zone 3.

---

### Zone 3 — The Deep Cave

The hardest stretch. The cave goes dark and dangerous with entirely new hazards.

| Hazard | What happens |
|--------|-------------|
| **Lava pits** | Six gaps in the floor filled with lava — fall in → death |
| **Moving platforms** | Oscillate across each pit — time your jump |
| **Cave bats** | Patrol at height; swoop toward Ella when nearby → death on contact |
| **Falling rocks** | Stalactites shake for ~1 second then drop → lethal mid-fall |
| **Cave guards** | Throw nets like Zone 1 guards, but **nets are lethal** here (no jail) |
| **Spike traps** | Placed just past each pit landing zone — punish sloppy landings |

The ice bridge (220 px) can barely span some pits — moving platforms are often the safer bet.

**Win condition** — Reach the treasure chest at the far end of Zone 3. Ella is awarded **+500 pts** and the celebration screen begins: confetti, fox friends bouncing everywhere, and a leaderboard prompt if the score qualifies.

---

## Scoring & Leaderboard

- **Coins** — 10 points each
- **Zone 2 chest** — +200 pts (unlocks Zone 3)
- **Zone 3 chest** — +500 pts (triggers win)
- Top 5 scores are saved to `leaderboard.json` and shown on the game-over and win screens
- Enter your 3-character initials: type letters directly (cursor auto-advances), BACKSPACE to correct, ENTER to save, ESC to skip

---

## Project Structure

```
Ellas Cave/
├── ella_cave.py        # Entry point — Game state machine
├── constants.py        # pygame init, screen, physics, colors, fonts, helpers
├── leaderboard.py      # Score persistence, Leaderboard class, LEADERBOARD singleton
├── drawing.py          # All draw_* functions, particles system, backgrounds, HUD
├── entities.py         # Platform, Spike, Coin, Tube, IceBridge, LavaPool,
│                       #   NetProjectile, PolarBear, HumanGuard, FoxFriend,
│                       #   MovingPlatform, CaveBat, FallingRock
├── player.py           # Player class (Ella) — physics, input, ice bridge power
├── levels.py           # Zone 1 & 2 level data: make_z1_* / make_z2_*, FOX_FRIEND_COLORS
├── levels_z3.py        # Zone 3 level data: make_z3_* factories, PITS, LEVEL_W, CHEST_X
├── screens.py          # MenuScreen, GameOverScreen, WinScreen, FoxJailScreen
├── zones.py            # Zone1, Zone2, Zone3
├── leaderboard.json    # Auto-created on first score save
├── ella_cave_backup.py # Full single-file backup (pre-split)
├── CLAUDE.md           # AI project guide: module map, edit targets, architecture notes
└── CHANGELOG.md
```

### For AI-assisted development

The codebase is split into focused modules so that each feature request only requires
reading 1–2 small files. Always read `CLAUDE.md` first — it has the full module map,
dependency graph, and a quick-reference table of exactly which file to open for any
common edit.

**Dependency order (no circular imports):**
```
constants → leaderboard → drawing → entities → player
                                 ↑             ↑
                             levels ──────────┘
                          levels_z3 ────────────┐
                                 ↓              ↓
                            screens ← zones ← ella_cave
```

**Quick edit reference:**

| Want to change… | Read only… |
|-----------------|-----------|
| Physics (gravity, jump, speed) | `constants.py` |
| Zone 1 layout (spikes, bears, guards, platforms) | `levels.py` |
| Zone 2 layout (spikes, coins, platforms) | `levels.py` |
| Zone 3 layout (pits, bats, rocks, guards, platforms) | `levels_z3.py` |
| Bear or guard behavior | `entities.py` (`PolarBear`, `HumanGuard`) |
| Bat or falling rock behavior | `entities.py` (`CaveBat`, `FallingRock`) |
| Moving platform speed | `levels_z3.py` `make_z3_platforms()` |
| Lava pool (Zone 1) | `entities.py` (`LavaPool`) |
| Ella's movement / ice power | `player.py` |
| Visual appearance of any character | `drawing.py` |
| Zone 1 / 2 / 3 level logic | `zones.py` |
| Menu / game-over / win / jail screens | `screens.py` |
| Game state flow / transitions | `ella_cave.py` |
| Leaderboard / scoring persistence | `leaderboard.py` |

---

## Art Style

All sprites and backgrounds are drawn procedurally with pygame drawing calls — no external image assets required. Ella has a subtle ice-blue glow hinting at her magic powers. Zone 1 uses a cold blue-white snowy palette; Zones 2 and 3 shift to warm amber and orange cave tones with crystal glow accents and torch flicker.
