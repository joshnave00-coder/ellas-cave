"""sprites.py — optional sprite loader. Drop PNGs into assets/ to replace
the procedural drawings for specific things; the game keeps working with the
old hand-drawn art for anything that isn't there yet.

Public API:
    get_sprite(name, target_size=None, flip_x=False) -> pygame.Surface | None
    get_animation(name, frames, target_size=None, flip_x=False) -> list[Surface] | None

`name` is the filename (without `.png`) inside the assets/ directory.
`target_size` is (w, h) for the final size — pixel art is scaled with
nearest-neighbor (crisp), higher-res art with smoothscale.
Both functions cache aggressively (load + scale + flip once per variant).
"""
import os
import pygame

_ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

# Caches keyed by (name, target_size, flip_x) and (name, frames, target_size, flip_x)
_sprite_cache: dict = {}
_anim_cache:   dict = {}
# Track which names we've already tried and failed to load, so we don't hit the
# filesystem every frame for missing assets.
_missing: set = set()


def _load_raw(name):
    """Load and convert a PNG once. Returns None if the file isn't there.

    Handles both modern (per-pixel alpha) and classic (color-key) sprites:
    if all four corners share the same fully-opaque color, that color is
    treated as the transparency key (the old-school "magenta background"
    convention you'll see on a lot of OpenGameArt sprite sheets)."""
    if name in _missing:
        return None
    path = os.path.join(_ASSET_DIR, name + ".png")
    if not os.path.isfile(path):
        _missing.add(name)
        return None
    try:
        raw = pygame.image.load(path)
    except Exception:
        _missing.add(name)
        return None

    w, h = raw.get_size()
    corners = (raw.get_at((0, 0)),       raw.get_at((w - 1, 0)),
               raw.get_at((0, h - 1)),   raw.get_at((w - 1, h - 1)))
    rgb_set = {tuple(c)[:3] for c in corners}
    # Solid uniform opaque border = the sprite uses a color key, not alpha.
    if all(c[3] >= 250 for c in corners) and len(rgb_set) == 1:
        key = next(iter(rgb_set))
        raw.set_colorkey(key)
        return raw.convert()
    # Otherwise it's a normal per-pixel-alpha PNG.
    return raw.convert_alpha()


def _scale(surf, target_size):
    """Pixel art (small source) gets nearest-neighbor; high-res gets smoothscale."""
    if target_size is None or surf.get_size() == target_size:
        return surf
    sw, sh = surf.get_size()
    # Heuristic: anything tinier than 100 px on either side is treated as
    # pixel art and scaled with crisp nearest-neighbor.
    if sw < 100 and sh < 100:
        return pygame.transform.scale(surf, target_size)
    return pygame.transform.smoothscale(surf, target_size)


def get_sprite(name, target_size=None, flip_x=False):
    """Return a single PNG as a Surface (cached, scaled, optionally flipped),
    or None if the file isn't in assets/."""
    key = (name, target_size, flip_x)
    cached = _sprite_cache.get(key)
    if cached is not None:
        return cached
    raw = _load_raw(name)
    if raw is None:
        return None
    surf = _scale(raw, target_size)
    if flip_x:
        surf = pygame.transform.flip(surf, True, False)
    _sprite_cache[key] = surf
    return surf


def get_animation(name, frames, target_size=None, flip_x=False):
    """Treat the PNG as a horizontal strip of `frames` equal-width tiles and
    return a list of Surfaces. Each tile is scaled to `target_size` if given.
    Returns None if the file isn't in assets/."""
    key = (name, frames, target_size, flip_x)
    cached = _anim_cache.get(key)
    if cached is not None:
        return cached
    raw = _load_raw(name)
    if raw is None:
        return None
    sw, sh = raw.get_size()
    if frames < 1:
        frames = 1
    fw = sw // frames
    tiles = []
    for i in range(frames):
        tile = raw.subsurface(pygame.Rect(i * fw, 0, fw, sh)).copy()
        tile = _scale(tile, target_size)
        if flip_x:
            tile = pygame.transform.flip(tile, True, False)
        tiles.append(tile)
    _anim_cache[key] = tiles
    return tiles


def has_sprite(name):
    """Cheap check: is there a usable PNG for this name? (Cached.)"""
    if name in _missing:
        return False
    return _load_raw(name) is not None
