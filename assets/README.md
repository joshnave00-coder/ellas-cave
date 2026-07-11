# assets/ — sprite art (optional)

The sprite system in `sprites.py` lets you override specific draw functions by
dropping a correctly-named PNG into this folder. If a file isn't here, the game
uses its built-in drawing for that thing. Both paths are kept working.

## Currently installed

| File          | What it does                                    | Source / License                                                                                  |
| ------------- | ----------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| `lava.png`    | Animated lava body in the volcano pool and pits | "16x16 and animated lava tile (45 frames)", CC0 — https://opengameart.org/content/16x16-and-animated-lava-tile-45-frames |

## Drawn in code (no PNG needed — these now look good)

The polar bear, the fox catcher (the net-throwing guard), and the volcano are
drawn **procedurally at the game's real resolution** using a supersample +
smoothscale technique (draw at 4× then shrink → smooth, anti-aliased edges, no
pixelation). This deliberately replaced the earlier attempt to use 32×32
pixel-art sprites, which looked blocky when scaled up to character size.

- Polar bear → `_render_bear` in `drawing.py`
- Fox catcher → `_render_catcher` in `drawing.py`
- Volcano → `draw_volcano` in `drawing.py` (lava stream in `LavaPool.draw`, `entities.py`)

You can still override any of them by dropping a PNG here
(`polar_bear.png`, `catcher.png`, `volcano.png`) — the loader handles both
alpha-channel and color-keyed (e.g. magenta-background) sprites. But the
built-in art is now the recommended look. Frame counts / sizes for sprite
overrides live in `drawing.py` (`POLAR_BEAR_FRAMES`, `CATCHER_FRAMES`,
`LAVA_FRAMES`, and the `_*_SPRITE_SIZE` tuples).

## CREDITS

- **lava.png** — "16x16 and animated lava tile (45 frames)" (CC0),
  https://opengameart.org/content/16x16-and-animated-lava-tile-45-frames
