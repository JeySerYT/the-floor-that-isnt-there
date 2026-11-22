#!/usr/bin/env python3
"""Generate the texture pack for «Этаж, которого нет».

Batch 1: environment (floors, walls, doors, decals).
Native resolution matches the game's 640x360 viewport and 32 px tiles.
All textures are deterministic: same seed -> same pixels.
"""

from __future__ import annotations

import json
import math
import random
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
TEX = ROOT / "assets" / "textures"
PREVIEW = ROOT / "assets" / "previews"
FONT_PATH = "/usr/share/fonts/TTF/DejaVuSansMono.ttf"

# --- palette: cold, dirty hospital -----------------------------------------

INK = (10, 13, 14)
SHADOW = (17, 22, 23)
FLOOR_BASE = (62, 75, 72)
FLOOR_LIGHT = (88, 103, 97)
FLOOR_DARK = (42, 52, 50)
GROUT = (27, 33, 34)
GROUT_HI = (101, 114, 106)
WALL_BASE = (74, 87, 82)
WALL_LIGHT = (104, 118, 110)
WALL_DARK = (47, 56, 54)
TRIM = (39, 46, 45)
RUST = (117, 70, 40)
RUST_DARK = (72, 41, 24)
BLOOD = (92, 19, 21)
BLOOD_DARK = (54, 9, 11)
BLOOD_BRIGHT = (139, 38, 35)
METAL = (103, 112, 111)
METAL_DARK = (56, 63, 64)
METAL_LIGHT = (144, 152, 147)
GLASS = (57, 92, 96)
AMBER = (198, 149, 82)

MANIFEST: list[dict] = []


# --- low level helpers -----------------------------------------------------

def _one_noise(w: int, h: int, gx: int, gy: int, rng: np.random.Generator) -> np.ndarray:
    grid = rng.random((gy, gx)).astype(np.float32)
    xs = np.linspace(0.0, gx, w, endpoint=False, dtype=np.float32)
    ys = np.linspace(0.0, gy, h, endpoint=False, dtype=np.float32)
    x0 = np.floor(xs).astype(int) % gx
    y0 = np.floor(ys).astype(int) % gy
    x1 = (x0 + 1) % gx
    y1 = (y0 + 1) % gy
    tx = xs - np.floor(xs)
    ty = ys - np.floor(ys)
    tx = tx * tx * (3.0 - 2.0 * tx)
    ty = ty * ty * (3.0 - 2.0 * ty)
    v00 = grid[np.ix_(y0, x0)]
    v10 = grid[np.ix_(y0, x1)]
    v01 = grid[np.ix_(y1, x0)]
    v11 = grid[np.ix_(y1, x1)]
    top = v00 + (v10 - v00) * tx[None, :]
    bottom = v01 + (v11 - v01) * tx[None, :]
    return top + (bottom - top) * ty[:, None]


def noise(w: int, h: int, grid: int, seed: int, octaves: int = 3) -> np.ndarray:
    rng = np.random.default_rng(seed)
    total = np.zeros((h, w), dtype=np.float32)
    amplitude = 1.0
    norm = 0.0
    for octave in range(octaves):
        gx = max(2, grid * (2 ** octave))
        gy = max(2, grid * (2 ** octave))
        total += amplitude * _one_noise(w, h, gx, gy, rng)
        norm += amplitude
        amplitude *= 0.5
    return total / norm


def jitter(color: tuple[int, int, int], rng: random.Random, amount: int = 4) -> tuple[int, int, int]:
    return tuple(max(0, min(255, channel + rng.randint(-amount, amount))) for channel in color)


def mix(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def add_grime(arr: np.ndarray, seed: int, strength: float = 0.14, grid: int = 3) -> np.ndarray:
    h, w = arr.shape[:2]
    field = noise(w, h, grid, seed, 3)
    factor = 1.0 - strength * (field - 0.5) * 2.0
    rgb = arr[:, :, :3] * factor[:, :, None]
    arr[:, :, :3] = np.clip(rgb, 0, 255)
    return arr


def clusters(arr: np.ndarray, seed: int, count: int, dark: bool = True,
             amount: int = 16, size: int = 2, alpha: int = 255) -> None:
    """Small 1-2 px clumps instead of per-pixel television static."""
    rng = random.Random(seed)
    h, w = arr.shape[:2]
    for _ in range(count):
        x = rng.randrange(w)
        y = rng.randrange(h)
        cw = rng.randint(1, size)
        ch = rng.randint(1, size)
        tone = -amount if dark else amount
        for dy in range(ch):
            for dx in range(cw):
                px, py = (x + dx) % w, (y + dy) % h
                arr[py, px, :3] = np.clip(arr[py, px, :3] + tone, 0, 255)
                arr[py, px, 3] = max(arr[py, px, 3], alpha)


def scratches(arr: np.ndarray, seed: int, count: int, length: int = 5,
              light: bool = True) -> None:
    rng = random.Random(seed)
    h, w = arr.shape[:2]
    for _ in range(count):
        x = rng.randrange(w)
        y = rng.randrange(h)
        angle = rng.uniform(-0.5, 0.5) + (math.pi / 2 if rng.random() < 0.3 else 0)
        delta = 14 if light else -16
        for step in range(rng.randint(2, length)):
            px = int(x + math.cos(angle) * step)
            py = int(y + math.sin(angle) * step)
            if 0 <= px < w and 0 <= py < h:
                arr[py, px, :3] = np.clip(arr[py, px, :3] + delta, 0, 255)


def drip(arr: np.ndarray, x: int, y: int, length: int, color: tuple[int, int, int],
         width: int = 1, alpha: int = 120) -> None:
    h, w = arr.shape[:2]
    for step in range(length):
        py = y + step
        if not 0 <= py < h:
            break
        for dx in range(width):
            px = x + dx
            if 0 <= px < w:
                arr[py, px, :3] = blend(arr[py, px, :3], color, alpha / 255.0)
                arr[py, px, 3] = 255


def blend(base: np.ndarray, color: tuple[int, int, int], t: float) -> np.ndarray:
    return base * (1.0 - t) + np.array(color, dtype=np.float32) * t


def to_image(arr: np.ndarray) -> Image.Image:
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")


def blank(w: int, h: int, color: tuple[int, int, int] | tuple[int, int, int, int] = (0, 0, 0, 0)) -> np.ndarray:
    arr = np.zeros((h, w, 4), dtype=np.float32)
    arr[:, :, 0] = color[0]
    arr[:, :, 1] = color[1]
    arr[:, :, 2] = color[2]
    arr[:, :, 3] = color[3] if len(color) > 3 else 255
    return arr


def draw_rect(arr: np.ndarray, x: int, y: int, w: int, h: int,
              color: tuple[int, int, int], alpha: int = 255) -> None:
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(arr.shape[1], x + w), min(arr.shape[0], y + h)
    if x0 >= x1 or y0 >= y1:
        return
    arr[y0:y1, x0:x1, :3] = color
    arr[y0:y1, x0:x1, 3] = alpha


def draw_line(arr: np.ndarray, x0: int, y0: int, x1: int, y1: int,
              color: tuple[int, int, int], alpha: int = 255) -> None:
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        if 0 <= x0 < arr.shape[1] and 0 <= y0 < arr.shape[0]:
            arr[y0, x0, :3] = blend(arr[y0, x0, :3], color, alpha / 255.0)
            arr[y0, x0, 3] = max(arr[y0, x0, 3], alpha)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def fill_polygon(arr: np.ndarray, points: list[tuple[int, int]],
                 color: tuple[int, int, int], alpha: int = 255) -> None:
    from PIL import ImageDraw

    mask_image = Image.new("L", (arr.shape[1], arr.shape[0]), 0)
    ImageDraw.Draw(mask_image).polygon(points, fill=255)
    mask = np.array(mask_image) > 0
    arr[mask, :3] = color
    arr[mask, 3] = alpha


def blob_mask(w: int, h: int, seed: int, cx: float, cy: float,
              rx: float, ry: float, irregularity: float = 0.35) -> np.ndarray:
    yy, xx = np.mgrid[0:h, 0:w]
    field = noise(w, h, 3, seed, 3)
    dist = np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)
    return (dist + (field - 0.5) * irregularity) < 1.0


def quantize(image: Image.Image, colors: int = 28) -> Image.Image:
    """Collapse the generated gradients into a tight pixel-art palette."""
    alpha = image.getchannel("A")
    rgb = image.convert("RGB")
    reduced = rgb.quantize(colors=colors, method=Image.Quantize.MEDIANCUT,
                           dither=Image.Dither.NONE)
    result = reduced.convert("RGB").convert("RGBA")
    result.putalpha(alpha)
    return result


def save(name: str, arr: np.ndarray, category: str, description: str,
         tileable: bool = False) -> None:
    folder = TEX / category
    folder.mkdir(parents=True, exist_ok=True)
    image = quantize(to_image(arr))
    image.save(folder / f"{name}.png")
    MANIFEST.append({
        "id": name,
        "file": f"assets/textures/{category}/{name}.png",
        "size": list(image.size),
        "category": category,
        "tileable": tileable,
        "batch": 1,
        "description": description,
    })


def write_manifest(entries: list[dict], batch: int) -> None:
    """Merge this batch into manifest.json without dropping other batches."""
    path = TEX / "manifest.json"
    existing: list[dict] = []
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8")).get("assets", [])
        except json.JSONDecodeError:
            existing = []
    ids = {entry["id"] for entry in entries}
    merged = [entry for entry in existing if entry["id"] not in ids]
    merged.extend(entries)
    batches = sorted({entry.get("batch", 1) for entry in merged} | {batch})
    path.write_text(
        json.dumps({"version": 1, "batches": batches, "assets": merged},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# --- floors ----------------------------------------------------------------

def floor_tiles(base: tuple[int, int, int], seed: int, tile_size: int = 16,
                variation: int = 5, damage: str = "") -> np.ndarray:
    rng = random.Random(seed)
    arr = blank(32, 32, base)
    for ty in range(2):
        for tx in range(2):
            shade = jitter(base, rng, variation)
            x, y = tx * tile_size, ty * tile_size
            draw_rect(arr, x, y, tile_size, tile_size, shade)
            # ceramic bevel: lit top/left, shaded bottom/right
            draw_line(arr, x, y, x + tile_size - 1, y, mix(shade, FLOOR_LIGHT, 0.65))
            draw_line(arr, x, y, x, y + tile_size - 1, mix(shade, FLOOR_LIGHT, 0.45))
            draw_line(arr, x, y + tile_size - 2, x + tile_size - 2, y + tile_size - 2,
                      mix(shade, FLOOR_DARK, 0.5), 200)
            draw_line(arr, x + tile_size - 2, y, x + tile_size - 2, y + tile_size - 2,
                      mix(shade, FLOOR_DARK, 0.45), 200)
            # dirt collects along the grout
            for i in range(3, tile_size - 2):
                arr[y + 1, x + i, :3] = blend(arr[y + 1, x + i, :3], FLOOR_DARK, 0.18)
                arr[y + i, x + 1, :3] = blend(arr[y + i, x + 1, :3], FLOOR_DARK, 0.12)
    for offset in (0, tile_size):
        draw_line(arr, offset, 0, offset, 31, GROUT)
        draw_line(arr, 0, offset, 31, offset, GROUT)
        draw_line(arr, (offset + 1) % 32, 0, (offset + 1) % 32, 31, GROUT_HI, 70)
        draw_line(arr, 0, (offset + 1) % 32, 31, (offset + 1) % 32, GROUT_HI, 55)

    add_grime(arr, seed + 1, 0.17, 3)
    clusters(arr, seed + 2, 10, dark=True, amount=12, size=2)
    clusters(arr, seed + 3, 5, dark=False, amount=10, size=2)
    scratches(arr, seed + 4, 3, 4)

    if damage == "crack":
        draw_line(arr, 28, 27, 30, 29, (36, 42, 42), 170)
        draw_line(arr, 27, 28, 28, 28, (126, 138, 128), 70)
    elif damage == "scuff":
        draw_line(arr, 5, 21, 11, 20, (50, 58, 56), 110)
        draw_line(arr, 8, 24, 14, 23, (52, 60, 58), 90)
        draw_line(arr, 6, 22, 10, 22, (88, 100, 95), 60)
    elif damage == "chip":
        draw_rect(arr, 29, 2, 2, 1, (28, 33, 34))
        draw_rect(arr, 30, 3, 1, 1, (28, 33, 34))
        draw_rect(arr, 29, 2, 1, 1, RUST_DARK, 190)
        drip(arr, 30, 4, 2, RUST, 1, 60)
    elif damage == "stain":
        mask = blob_mask(32, 32, seed + 7, 9, 24, 6, 4.5, 0.55)
        arr[mask, :3] = blend(arr[mask, :3], (38, 45, 43), 0.55)
        rim = mask & ~erode(mask, 1)
        arr[rim, :3] = blend(arr[rim, :3], (47, 55, 51), 0.5)
        clusters(arr, seed + 9, 3, dark=True, amount=12, size=1)
    elif damage == "wet":
        mask = blob_mask(32, 32, seed + 10, 10, 11, 6.5, 4.5, 0.55)
        arr[mask, :3] = blend(arr[mask, :3], (36, 46, 47), 0.65)
        draw_rect(arr, 7, 10, 4, 1, (104, 121, 118), 90)
        draw_rect(arr, 12, 12, 2, 1, (92, 110, 108), 80)

    return arr


def floor_concrete(seed: int) -> np.ndarray:
    rng = random.Random(seed)
    arr = blank(32, 32, (55, 63, 62))
    add_grime(arr, seed, 0.22, 3)
    for _ in range(24):
        x, y = rng.randrange(32), rng.randrange(32)
        tone = rng.choice([(94, 102, 99), (37, 43, 44), (73, 81, 79)])
        draw_rect(arr, x, y, rng.randint(1, 2), 1, tone, 220)
    for _ in range(4):
        x, y = rng.randrange(32), rng.randrange(32)
        draw_line(arr, x, y, x + rng.randint(-6, 6), y + rng.randint(-4, 4),
                  (34, 40, 41), 180)
    # worn painted guide line
    for x in range(32):
        if rng.random() > 0.25:
            arr[27, x, :3] = blend(arr[27, x, :3], (104, 110, 86), 0.5)
    return arr


def floor_lobby(seed: int) -> np.ndarray:
    rng = random.Random(seed)
    arr = blank(32, 32, (58, 66, 63))
    for ty in range(2):
        for tx in range(2):
            light = (tx + ty) % 2 == 0
            color = (74, 83, 78) if light else (44, 52, 51)
            draw_rect(arr, tx * 16, ty * 16, 16, 16, jitter(color, rng, 3))
    for offset in (0, 16):
        draw_line(arr, offset, 0, offset, 31, (25, 30, 31))
        draw_line(arr, 0, offset, 31, offset, (25, 30, 31))
    add_grime(arr, seed + 1, 0.18, 3)
    scratches(arr, seed + 2, 5, 6)
    clusters(arr, seed + 3, 9, amount=10, size=2)
    draw_rect(arr, 20, 4, 6, 2, (45, 52, 50), 120)
    draw_rect(arr, 20, 5, 6, 1, (96, 104, 98), 70)
    return arr


def floor_blood(seed: int) -> np.ndarray:
    arr = floor_tiles(FLOOR_BASE, seed)
    rng = random.Random(seed + 50)
    for step in range(24):
        x = 3 + step
        y = 24 - step // 2 + rng.randint(-1, 1)
        width = 2 + step // 9
        for dy in range(width):
            px, py = x, y + dy
            if 0 <= px < 32 and 0 <= py < 32:
                arr[py, px, :3] = (44, 9, 11) if dy in (0, width - 1) else (68, 15, 17)
                arr[py, px, 3] = 230
    for _ in range(9):
        x, y = rng.randrange(5, 30), rng.randrange(5, 30)
        draw_rect(arr, x, y, rng.randint(1, 2), rng.randint(1, 2), (42, 8, 10), 225)
    draw_rect(arr, 9, 18, 2, 1, (96, 26, 24), 190)
    draw_rect(arr, 15, 14, 1, 1, (88, 22, 21), 160)
    return arr


def floor_grate(seed: int) -> np.ndarray:
    arr = blank(32, 32, (0, 0, 0, 0))
    draw_rect(arr, 0, 0, 32, 32, (41, 48, 48))
    draw_line(arr, 0, 3, 31, 3, (78, 85, 81), 90)
    for x in range(2, 31, 5):
        draw_rect(arr, x, 3, 3, 26, (13, 17, 18))
        draw_rect(arr, x + 3, 3, 1, 26, (88, 95, 91), 140)
        draw_rect(arr, x + 1, 3, 1, 26, (28, 34, 35))
    draw_rect(arr, 0, 0, 32, 2, (64, 71, 68))
    draw_rect(arr, 0, 30, 32, 2, (29, 35, 36))
    draw_rect(arr, 0, 0, 2, 32, (54, 61, 59))
    draw_rect(arr, 30, 0, 2, 32, (54, 61, 59))
    rng = random.Random(seed)
    for _ in range(3):
        x, y = rng.randrange(5, 27), rng.randrange(5, 27)
        draw_rect(arr, x, y, 2, 1, RUST_DARK, 180)
    clusters(arr, seed + 1, 4, dark=True, amount=10, size=2)
    return arr


# --- walls -----------------------------------------------------------------

def wall_face(seed: int, variant: str = "a") -> np.ndarray:
    rng = random.Random(seed)
    arr = blank(32, 32, WALL_BASE)
    for y in range(32):
        t = y / 31.0
        color = mix(mix(WALL_LIGHT, WALL_BASE, t * 1.2), WALL_DARK, max(0.0, t - 0.5) * 1.5)
        draw_rect(arr, 0, y, 32, 1, color)
    add_grime(arr, seed + 1, 0.16, 3)

    # panel seam with a highlight lip
    draw_line(arr, 0, 14, 31, 14, (43, 51, 50), 230)
    draw_line(arr, 0, 15, 31, 15, (116, 129, 120), 80)

    # baseboard: clearly separate material
    draw_rect(arr, 0, 27, 32, 5, TRIM)
    draw_line(arr, 0, 26, 31, 26, (112, 123, 113), 120)
    draw_line(arr, 0, 28, 31, 28, (29, 36, 37), 200)
    draw_rect(arr, 0, 31, 32, 1, (19, 24, 25))

    if variant == "a":
        # a single hairline crack, a small dent and scuffs
        draw_line(arr, 4, 17, 6, 21, (40, 47, 46), 190)
        draw_line(arr, 6, 21, 5, 24, (40, 47, 46), 180)
        draw_line(arr, 5, 18, 7, 22, (124, 135, 126), 50)
        dent = [(25, 9), (27, 8), (28, 10), (26, 11)]
        fill_polygon(arr, dent, (105, 108, 95), 220)
        draw_line(arr, 26, 11, 28, 10, (53, 60, 56), 200)
        draw_line(arr, 20, 18, 26, 18, (57, 64, 60), 100)
        draw_line(arr, 22, 21, 27, 20, (59, 66, 62), 90)
        drip(arr, 6, 24, 3, (55, 61, 57), 1, 70)
        scratches(arr, seed + 3, 3, 4, light=False)
    elif variant == "b":
        # damp: a broad uneven darkening under the ceiling, no repeated blob
        field = noise(32, 32, 3, seed + 5, 4)
        band = (np.arange(32)[:, None] < 15)
        factor = 1.0 - band * (0.05 + 0.16 * field)
        arr[:, :, :3] *= factor[:, :, None]
        scratches(arr, seed + 4, 2, 3, light=False)
    elif variant == "c":
        # grubby hand-height smudges and scuffed paint; no repeating crack
        draw_line(arr, 4, 19, 13, 18, (58, 66, 61), 90)
        draw_line(arr, 8, 22, 17, 20, (60, 68, 63), 80)
        smudge = blob_mask(32, 32, seed + 8, 22, 20, 4.5, 2.8, 0.8)
        arr[smudge, :3] = blend(arr[smudge, :3], (54, 62, 58), 0.35)
        draw_line(arr, 19, 8, 27, 8, (57, 64, 60), 70)
        draw_rect(arr, 25, 9, 3, 1, (60, 67, 63), 90)
        draw_rect(arr, 6, 24, 2, 1, (52, 59, 55), 80)
        drip(arr, 27, 12, 3, (55, 62, 58), 1, 50)
        scratches(arr, seed + 9, 2, 3, light=False)
    elif variant == "pipe":
        for pipe_x in (5, 20):
            draw_rect(arr, pipe_x, 0, 5, 32, (52, 59, 58))
            draw_rect(arr, pipe_x + 1, 0, 3, 32, (88, 96, 93))
            draw_rect(arr, pipe_x + 1, 0, 1, 32, (140, 147, 140))
            draw_rect(arr, pipe_x + 3, 0, 2, 32, (45, 51, 51))
            draw_rect(arr, pipe_x - 1, 7, 7, 2, (41, 47, 47))
            draw_rect(arr, pipe_x - 1, 23, 7, 2, (41, 47, 47))
            draw_rect(arr, pipe_x - 1, 7, 7, 1, (103, 110, 104), 110)
            drip(arr, pipe_x, 9, 7, RUST_DARK, 1, 120)
            draw_rect(arr, pipe_x, 8, 1, 1, RUST, 180)
        # valve wheel
        draw_rect(arr, 13, 17, 4, 4, (74, 81, 78))
        draw_rect(arr, 14, 18, 2, 2, (40, 46, 46))
    return arr


def wall_tile_face(seed: int) -> np.ndarray:
    arr = blank(32, 32, WALL_BASE)
    for y in range(32):
        t = y / 31.0
        draw_rect(arr, 0, y, 32, 1, mix(WALL_LIGHT, WALL_BASE, t))
    # tiled wainscot
    draw_rect(arr, 0, 11, 32, 17, (95, 108, 101))
    for ty in range(11, 28, 8):
        for tx in range(0, 32, 8):
            shade = jitter((110, 124, 116), random.Random(seed + tx * 7 + ty), 4)
            draw_rect(arr, tx, ty, 7, 7, shade)
            draw_line(arr, tx, ty, tx + 6, ty, (146, 157, 146), 70)
            draw_line(arr, tx, ty, tx, ty + 6, (136, 147, 137), 55)
            draw_line(arr, tx + 6, ty, tx + 6, ty + 6, (79, 89, 85), 70)
            draw_line(arr, tx, ty + 6, tx + 6, ty + 6, (79, 89, 85), 70)
    for offset in range(0, 33, 8):
        draw_line(arr, offset, 11, offset, 27, (57, 65, 63), 220)
        draw_line(arr, 0, offset, 31, offset, (57, 65, 63), 220)
    draw_rect(arr, 0, 27, 32, 5, TRIM)
    draw_line(arr, 0, 26, 31, 26, (118, 129, 119), 130)
    draw_line(arr, 0, 28, 31, 28, (29, 36, 37), 180)
    draw_line(arr, 20, 18, 27, 17, (86, 97, 91), 80)
    draw_line(arr, 5, 23, 11, 22, (84, 95, 89), 70)
    add_grime(arr, seed + 1, 0.16, 3)
    clusters(arr, seed + 2, 6, amount=8, size=2)
    return arr


def wall_cap(seed: int) -> np.ndarray:
    rng = random.Random(seed)
    arr = blank(32, 32, (78, 84, 81))
    add_grime(arr, seed, 0.24, 3)
    for _ in range(22):
        x, y = rng.randrange(32), rng.randrange(32)
        arr[y, x, :3] = np.clip(arr[y, x, :3] + rng.choice([-18, 14, -10, 20]), 0, 255)
    draw_line(arr, 0, 0, 31, 0, (50, 56, 55), 200)
    draw_line(arr, 0, 1, 31, 1, (112, 119, 112), 70)
    draw_line(arr, 0, 0, 0, 31, (50, 56, 55), 200)
    draw_line(arr, 1, 0, 1, 31, (112, 119, 112), 70)
    for _ in range(3):
        x, y = rng.randrange(7, 26), rng.randrange(7, 26)
        draw_line(arr, x, y, x + rng.randint(2, 6), y + rng.randint(2, 7),
                  (52, 59, 58), 170)
    return arr


# --- doors -----------------------------------------------------------------

def door_leaf(width: int, height: int, seed: int, kind: str) -> np.ndarray:
    rng = random.Random(seed)
    arr = blank(width, height, (0, 0, 0, 0))

    if kind == "elevator":
        return elevator_door(width, height, seed)

    frame = (34, 40, 40) if kind != "morgue" else (29, 33, 35)
    inner = (63, 75, 71) if kind == "ward" else (78, 85, 82)
    if kind == "morgue":
        inner = (66, 73, 73)

    # frame + bevel
    draw_rect(arr, 0, 0, width, height, frame)
    draw_line(arr, 0, 0, width - 1, 0, (104, 112, 106), 140)
    draw_rect(arr, 3, 3, width - 6, height - 6, inner)
    for y in range(3, height - 3):
        t = (y - 3) / max(1, height - 4)
        draw_rect(arr, 3, y, width - 6, 1, mix(inner, (33, 39, 40), 0.12 + t * 0.3))
    draw_line(arr, 3, 3, width - 4, 3, (129, 138, 129), 150)
    draw_line(arr, 3, height - 4, width - 4, height - 4, (33, 39, 40), 220)

    if kind == "double":
        for x in (6, width // 2 + 2):
            draw_rect(arr, x, 5, width // 2 - 8, height - 10, (68, 79, 75), 255)
            draw_line(arr, x, 5, x + width // 2 - 9, 5, (92, 103, 98), 120)
            draw_line(arr, x, height - 6, x + width // 2 - 9, height - 6, (45, 52, 52), 200)
            draw_rect(arr, x + 3, height - 12, width // 2 - 14, 4, (54, 61, 60), 200)
            draw_line(arr, x + 3, height - 12, x + width // 2 - 11, height - 12, (98, 106, 101), 80)
        draw_line(arr, width // 2, 3, width // 2, height - 4, (33, 39, 39), 240)
        draw_line(arr, width // 2 + 1, 3, width // 2 + 1, height - 4, (116, 124, 115), 80)
        for x in (12, width - 30):
            draw_rect(arr, x, 14, 18, 3, (103, 111, 104))
            draw_rect(arr, x, 14, 18, 1, (148, 155, 145), 150)
            draw_rect(arr, x, 16, 18, 1, (52, 59, 59))
            draw_rect(arr, x + 2, 15, 14, 1, (76, 83, 80))
            draw_rect(arr, x + 7, 12, 4, 2, (63, 70, 67))
    elif kind == "ward":
        # recessed panels
        draw_rect(arr, 6, 6, width // 2 - 10, height - 12, (68, 80, 76))
        draw_rect(arr, width // 2 + 4, 6, width // 2 - 10, height - 12, (68, 80, 76))
        draw_line(arr, 6, 6, width // 2 - 5, 6, (47, 55, 54), 200)
        draw_line(arr, width // 2 + 4, 6, width - 7, 6, (47, 55, 54), 200)
        # wired glass window, narrower and taller
        draw_rect(arr, width // 2 - 9, 8, 18, 12, (29, 35, 37))
        draw_rect(arr, width // 2 - 7, 10, 14, 8, (48, 78, 82))
        draw_rect(arr, width // 2 - 6, 11, 4, 2, (75, 110, 113), 140)
        draw_rect(arr, width // 2 + 3, 13, 3, 2, (41, 67, 71), 160)
        draw_line(arr, width // 2 - 7, 15, width // 2 + 6, 11, (66, 101, 104), 70)
        draw_line(arr, width // 2 - 2, 10, width // 2 - 2, 17, (38, 47, 49), 180)
        draw_line(arr, width // 2 - 7, 13, width // 2 + 6, 13, (38, 47, 49), 180)
        # handle plate + lever
        draw_rect(arr, width - 17, 20, 9, 5, (77, 84, 79))
        draw_rect(arr, width - 16, 21, 7, 3, (126, 132, 121))
        draw_rect(arr, width - 13, 22, 6, 1, (62, 68, 65))
        draw_rect(arr, width - 18, 21, 2, 3, (61, 67, 64))
        # kick plate
        draw_rect(arr, 6, height - 11, width - 12, 4, (55, 62, 61))
        draw_line(arr, 6, height - 11, width - 7, height - 11, (100, 108, 102), 80)
        draw_rect(arr, 6, height - 7, width - 12, 1, (39, 45, 46))
    elif kind == "morgue":
        # one rivet per anchor: a 1 px specular dot avoids letter-like clumps
        for x in range(8, width - 6, 11):
            for y in (6, height - 7):
                draw_rect(arr, x, y, 1, 1, (122, 129, 124))
                draw_rect(arr, x + 1, y + 1, 1, 1, (46, 52, 53))
        draw_rect(arr, width // 2 - 14, 12, 28, 8, (55, 62, 62))
        draw_rect(arr, width // 2 - 14, 12, 28, 1, (112, 119, 112), 100)
        draw_rect(arr, width // 2 - 5, 15, 10, 2, (38, 44, 45))
        draw_rect(arr, width // 2 - 1, 13, 2, 6, (94, 101, 97))
        draw_rect(arr, width // 2 - 2, 14, 4, 1, (58, 64, 62))
        for _ in range(4):
            x, y = rng.randrange(7, width - 9), rng.randrange(8, height - 10)
            drip(arr, x, y, rng.randint(3, 8), RUST_DARK, 1, 90)
    scratches(arr, seed + 5, 3, 5, light=False)
    add_grime(arr, seed + 6, 0.14, 3)
    return arr


def door_frame(width: int, height: int, seed: int, kind: str) -> np.ndarray:
    """Static doorway behind the moving leaf: dark threshold and steel jambs."""
    rng = random.Random(seed)
    arr = blank(width, height, (0, 0, 0, 0))
    frame = (34, 40, 40) if kind != "morgue" else (29, 33, 35)

    draw_rect(arr, 0, 0, width, height, frame)
    draw_line(arr, 0, 0, width - 1, 0, (104, 112, 106), 140)
    draw_rect(arr, 3, 3, width - 6, height - 6, (7, 9, 10))
    for y in range(3, height - 3):
        t = (y - 3) / max(1, height - 4)
        shade = mix((11, 14, 15), (5, 7, 8), t)
        draw_rect(arr, 3, y, width - 6, 1, shade)
    # cold light from the ward above, faint floor sheen at the threshold
    draw_rect(arr, 4, 4, width - 8, 2, (22, 27, 28), 120)
    draw_rect(arr, 3, height - 7, width - 6, 4, (22, 27, 28), 255)
    draw_rect(arr, 3, height - 4, width - 6, 1, (14, 18, 19), 255)
    draw_line(arr, 3, 3, 3, height - 4, (8, 10, 11), 220)
    draw_line(arr, width - 4, 3, width - 4, height - 4, (8, 10, 11), 220)
    draw_line(arr, 3, 3, width - 4, 3, (16, 20, 21), 220)
    # worn paint and rust on the jambs
    for _ in range(3):
        x = rng.choice((0, 1, width - 2))
        y = rng.randrange(1, height - 4)
        draw_rect(arr, x, y, 1, rng.randint(1, 3), RUST_DARK, 160)
    return arr


def door_panel(seed: int, kind: str, side: str = "") -> np.ndarray:
    """Moving leaf cropped out of the flat door art, with a transparent margin."""
    full = door_leaf(64, 32, seed, kind)
    if kind == "double":
        if side == "left":
            return full[3:29, 3:32]
        return full[3:29, 32:61]
    return full[3:29, 3:61]


def elevator_door(width: int, height: int, seed: int) -> np.ndarray:
    rng = random.Random(seed)
    arr = blank(width, height, (0, 0, 0, 0))
    frame = (40, 46, 46)
    draw_rect(arr, 0, 0, width, height, frame)
    draw_line(arr, 0, 0, width - 1, 0, (122, 130, 122), 160)
    draw_line(arr, 0, height - 1, width - 1, height - 1, (24, 29, 30), 220)
    draw_line(arr, 0, 0, 0, height - 1, (96, 104, 100), 90)
    draw_line(arr, width - 1, 0, width - 1, height - 1, (26, 31, 32), 160)

    # recessed opening
    draw_rect(arr, 5, 5, width - 10, height - 10, (31, 36, 37))
    draw_rect(arr, 6, 6, width - 12, height - 12, (72, 81, 80))
    for y in range(6, height - 6):
        t = (y - 6) / max(1, height - 7)
        color = mix(mix((93, 102, 100), (66, 74, 74), t * 1.2), (44, 50, 50), max(0.0, t - 0.62) * 1.8)
        draw_rect(arr, 6, y, width - 12, 1, color)

    half = width // 2
    # two leaves, deep center seam
    draw_line(arr, half, 6, half, height - 7, (25, 30, 31), 255)
    draw_line(arr, half + 1, 6, half + 1, height - 7, (119, 127, 122), 90)
    draw_line(arr, half - 1, 6, half - 1, height - 7, (61, 68, 68), 120)

    # vertical grooves and panel edges
    for x in (13, width - 15):
        draw_line(arr, x, 12, x, height - 16, (50, 57, 57), 180)
        draw_line(arr, x + 1, 12, x + 1, height - 16, (103, 111, 106), 70)
    draw_line(arr, 9, 78, width - 10, 78, (52, 59, 59), 140)
    draw_line(arr, 9, 79, width - 10, 79, (101, 109, 104), 60)

    # brushed metal streaks
    for _ in range(46):
        x = rng.randrange(8, width - 8)
        y = rng.randrange(12, height - 18)
        draw_line(arr, x, y, x, y + rng.randint(2, 8), (99, 108, 104), 32)

    # floor indicator plate with a 5x7 "13"
    plate_x = half - 12
    draw_rect(arr, plate_x, 9, 24, 13, (30, 35, 36))
    draw_rect(arr, plate_x + 1, 10, 22, 11, (19, 23, 24))
    draw_line(arr, plate_x, 9, plate_x + 23, 9, (103, 111, 106), 80)
    digits = {
        "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
        "3": ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
    }
    for index, glyph in enumerate(("1", "3")):
        ox = plate_x + 6 + index * 6
        for row, line in enumerate(digits[glyph]):
            for col, char in enumerate(line):
                if char == "1":
                    draw_rect(arr, ox + col, 11 + row, 1, 1, (150, 49, 41))

    # bottom bumper and threshold
    draw_rect(arr, 6, height - 16, width - 12, 4, (55, 62, 62))
    draw_line(arr, 6, height - 16, width - 7, height - 16, (104, 112, 107), 80)
    draw_rect(arr, 6, height - 11, width - 12, 3, (43, 49, 50))
    draw_rect(arr, 6, height - 7, width - 12, 1, (21, 26, 27))

    # dents, scuffs and rust
    for _ in range(3):
        x = rng.randrange(12, width - 18)
        y = rng.randrange(30, height - 24)
        draw_line(arr, x, y, x + rng.randint(2, 6), y + rng.randint(1, 3),
                  (49, 56, 56), 160)
        draw_line(arr, x, y + 1, x + rng.randint(2, 5), y + 2,
                  (104, 112, 107), 45)
    for _ in range(5):
        x = rng.randrange(8, width - 9)
        y = rng.randrange(40, height - 22)
        drip(arr, x, y, rng.randint(3, 10), RUST_DARK, 1, 65)
    add_grime(arr, seed + 2, 0.12, 3)
    return arr


# --- decals ----------------------------------------------------------------

def erode(mask: np.ndarray, steps: int = 1) -> np.ndarray:
    result = mask.copy()
    for _ in range(steps):
        shifted = (
            np.roll(result, 1, axis=0) & np.roll(result, -1, axis=0)
            & np.roll(result, 1, axis=1) & np.roll(result, -1, axis=1)
            & result
        )
        result = shifted
    return result


def blood_pool(seed: int, width: int = 64, height: int = 64) -> np.ndarray:
    rng = random.Random(seed)
    arr = blank(width, height, (0, 0, 0, 0))
    cx, cy = width / 2, height / 2 + 2
    # an elongated puddle built from overlapping lobes, not one circle
    mask = blob_mask(width, height, seed, cx, cy, width * 0.34, height * 0.2, 0.5)
    mask |= blob_mask(width, height, seed + 1, cx + 13, cy + 2, width * 0.13, height * 0.12, 0.65)
    mask |= blob_mask(width, height, seed + 2, cx - 14, cy - 3, width * 0.15, height * 0.11, 0.6)
    mask |= blob_mask(width, height, seed + 3, cx - 5, cy + 7, width * 0.12, height * 0.08, 0.7)
    rim = mask & ~erode(mask, 1)
    field = noise(width, height, 5, seed + 3, 3)

    arr[mask, 0] = 78
    arr[mask, 1] = 17
    arr[mask, 2] = 19
    arr[mask, 3] = 235
    arr[rim, 0] = 46
    arr[rim, 1] = 9
    arr[rim, 2] = 11
    # coagulated darker patches follow noise, not a perfect circle
    dark = mask & (field > 0.46)
    arr[dark, :3] = blend(arr[dark, :3], BLOOD_DARK, 0.8)
    # wet specular highlights, sparse and small
    wet = mask & (noise(width, height, 4, seed + 4, 2) > 0.8)
    arr[wet, :3] = blend(arr[wet, :3], (102, 31, 29), 0.5)
    for _ in range(10):
        x, y = rng.randrange(8, width - 8), rng.randrange(8, height - 8)
        if mask[y, x]:
            arr[y, x, :3] = (40, 7, 9)
    # satellite droplets
    for _ in range(20):
        angle = rng.uniform(0, math.pi * 2)
        radius = rng.uniform(0.3, 0.62)
        x = int(cx + math.cos(angle) * radius * width)
        y = int(cy + math.sin(angle) * radius * height * 0.55)
        if 0 <= x < width - 1 and 0 <= y < height - 1:
            draw_rect(arr, x, y, rng.randint(1, 2), rng.randint(1, 2), BLOOD_DARK, 220)
    return arr


def blood_smear(seed: int, width: int = 64, height: int = 48) -> np.ndarray:
    rng = random.Random(seed)
    arr = blank(width, height, (0, 0, 0, 0))
    path: list[tuple[int, int, int]] = []
    for step in range(58):
        x = 5 + step
        y = 31 - int(step * 0.3) + int(math.sin(step * 0.15) * 2)
        thickness = max(3, 9 - step // 12)
        path.append((x, y, thickness))
    # one continuous tapered drag mark with a ragged edge
    for index, (x, y, thickness) in enumerate(path):
        for dy in range(thickness):
            px, py = x, y + dy
            if not (0 <= px < width and 0 <= py < height):
                continue
            if dy == thickness - 1 and index % 4 == 0 and thickness > 3:
                continue
            arr[py, px, :3] = BLOOD_DARK if dy == 0 or dy == thickness - 1 else (74, 15, 17)
            arr[py, px, 3] = 235
    # two solid streaks from the drag, kept close to the body
    for offset in (1, 2):
        for index in range(4, 42):
            x, y, thickness = path[index]
            py = y + thickness + offset
            if py < height:
                arr[py, x, :3] = BLOOD_DARK
                arr[py, x, 3] = 110
    # wet core flecks
    for index in range(8, 50, 6):
        x, y, thickness = path[index]
        arr[y + max(0, thickness // 2), x, :3] = (104, 28, 26)
        arr[y + max(0, thickness // 2), x, 3] = 220
    # pooled head
    head = blob_mask(width, height, seed + 7, 12, 34, 8, 5, 0.55)
    arr[head, :3] = blend(arr[head, :3], BLOOD_DARK, 0.55)
    arr[head, 3] = 235
    core = blob_mask(width, height, seed + 8, 12, 34, 5, 3, 0.6)
    arr[core, :3] = blend(arr[core, :3], BLOOD, 0.6)
    # droplets ahead of the body
    for _ in range(20):
        x = rng.randrange(10, width - 2)
        y = rng.randrange(8, height - 2)
        if rng.random() < 0.5:
            draw_rect(arr, x, y, rng.randint(1, 3), 1, BLOOD_DARK, 210)
        else:
            draw_rect(arr, x, y, 1, rng.randint(1, 2), BLOOD_DARK, 210)
    return arr


def stain_water(seed: int, width: int = 48, height: int = 48) -> np.ndarray:
    rng = random.Random(seed)
    arr = blank(width, height, (0, 0, 0, 0))
    cx, cy = width / 2 + 2, height / 2 - 1
    field = noise(width, height, 4, seed, 3)
    mask = blob_mask(width, height, seed + 1, cx, cy, width * 0.34, height * 0.36, 0.4)
    inner = blob_mask(width, height, seed + 2, cx + 1, cy, width * 0.2, height * 0.22, 0.5)
    arr[mask, :3] = (86, 74, 54)
    arr[mask, 3] = 88
    arr[inner, :3] = (100, 87, 63)
    arr[inner, 3] = 96
    rim = mask & ~erode(mask, 1)
    arr[rim, :3] = (65, 54, 38)
    arr[rim, 3] = 120
    # broken tide marks, radius wobbles with the noise field
    for base_radius, alpha in ((0.62, 120), (0.4, 80)):
        for step in range(0, 120):
            angle = step / 120 * math.pi * 2
            wobble = 1.0 + (field[int((cy + math.sin(angle) * 16) % height),
                                  int((cx + math.cos(angle) * 16) % width)] - 0.5) * 0.5
            radius = base_radius * width * wobble
            x = int(cx + math.cos(angle) * radius)
            y = int(cy + math.sin(angle) * radius * 0.95)
            if 0 <= x < width and 0 <= y < height and step % 3 != 0:
                arr[y, x, :3] = (69, 57, 40)
                arr[y, x, 3] = max(arr[y, x, 3], alpha)
    for _ in range(16):
        x, y = rng.randrange(8, width - 8), rng.randrange(8, height - 8)
        if mask[y, x]:
            arr[y, x, :3] = (80, 67, 47)
    return arr


def crack_decal(seed: int, width: int = 32, height: int = 32) -> np.ndarray:
    rng = random.Random(seed)
    arr = blank(width, height, (0, 0, 0, 0))
    points = [(4, 0), (7, 6), (6, 12), (10, 18), (9, 25), (13, 31)]
    for index in range(len(points) - 1):
        x0, y0 = points[index]
        x1, y1 = points[index + 1]
        draw_line(arr, x0, y0, x1, y1, (16, 21, 22), 230)
        draw_line(arr, x0 + 1, y0, x1 + 1, y1, (126, 138, 128), 90)
    branches = [
        ((6, 12), (2, 14)), ((10, 18), (15, 20)), ((9, 25), (14, 27)),
        ((7, 6), (12, 7)), ((10, 18), (10, 24)),
    ]
    for (x0, y0), (x1, y1) in branches:
        draw_line(arr, x0, y0, x1, y1, (19, 24, 25), 190)
        draw_line(arr, x0 + 1, y0, x1 + 1, y1, (119, 131, 121), 60)
    return arr


def brick_patch_decal(seed: int, width: int = 48, height: int = 32) -> np.ndarray:
    rng = random.Random(seed)
    arr = blank(width, height, (0, 0, 0, 0))
    patch = [(2, 7), (7, 4), (15, 5), (22, 2), (31, 4), (39, 3), (46, 6),
             (47, 15), (44, 22), (38, 27), (30, 26), (23, 30), (14, 27),
             (8, 29), (3, 24), (2, 15)]
    fill_polygon(arr, patch, (48, 33, 28), 245)
    mortar = (56, 42, 36)
    for row in range(6):
        offset = (row % 2) * 3
        for col in range(8):
            bx = 2 + col * 6 + offset
            by = 4 + row * 4
            shade = rng.choice([(84, 54, 42), (74, 47, 37), (66, 42, 34), (58, 37, 31)])
            draw_rect(arr, bx, by, 4, 3, shade, 245)
            draw_rect(arr, bx, by, 4, 1, mix(shade, (118, 82, 61), 0.4), 220)
            draw_rect(arr, bx, by + 2, 4, 1, mortar, 230)
            if (row, col) in ((1, 4), (3, 1), (4, 6)):
                draw_rect(arr, bx, by, 4, 3, (30, 24, 22), 240)
    # uneven plaster lip, shadows only on the lower edge
    draw_line(arr, 3, 24, 8, 29, (43, 50, 47), 200)
    draw_line(arr, 8, 29, 14, 27, (43, 50, 47), 210)
    draw_line(arr, 14, 27, 23, 30, (43, 50, 47), 210)
    draw_line(arr, 23, 30, 30, 26, (43, 50, 47), 200)
    draw_line(arr, 30, 26, 38, 27, (43, 50, 47), 200)
    draw_line(arr, 4, 25, 9, 28, (108, 112, 100), 70)
    draw_line(arr, 15, 28, 22, 29, (108, 112, 100), 55)
    # fine grit in the exposed area
    for _ in range(8):
        x, y = rng.randrange(4, width - 4), rng.randrange(5, height - 4)
        if arr[y, x, 3] > 0:
            arr[y, x, :3] = mix(tuple(int(c) for c in arr[y, x, :3]), (32, 26, 23), 0.5)
    return arr


def mold_decal(seed: int, width: int = 32, height: int = 32) -> np.ndarray:
    arr = blank(width, height, (0, 0, 0, 0))
    mask = blob_mask(width, height, seed, 12, 14, 9, 8, 0.7)
    mask |= blob_mask(width, height, seed + 1, 22, 20, 6, 5, 0.7)
    arr[mask, :3] = (38, 47, 42)
    arr[mask, 3] = 190
    core = mask & (noise(width, height, 4, seed + 2, 2) > 0.56)
    arr[core, :3] = (28, 36, 32)
    arr[core, 3] = 210
    rng = random.Random(seed)
    for _ in range(18):
        x, y = rng.randrange(width), rng.randrange(height)
        if mask[y, x]:
            arr[y, x, :3] = (24, 31, 28)
    for _ in range(8):
        x, y = rng.randrange(width), rng.randrange(height)
        if not mask[y, x]:
            arr[y, x, :3] = (44, 53, 47)
            arr[y, x, 3] = 120
    return arr


def wall_crack_decal(seed: int, width: int = 32, height: int = 48) -> np.ndarray:
    arr = blank(width, height, (0, 0, 0, 0))
    points = [(16, 0), (14, 7), (17, 13), (15, 20), (18, 27), (16, 34), (19, 41), (18, 47)]
    for index in range(len(points) - 1):
        x0, y0 = points[index]
        x1, y1 = points[index + 1]
        draw_line(arr, x0, y0, x1, y1, (30, 36, 36), 230)
        draw_line(arr, x0 + 1, y0, x1 + 1, y1, (116, 128, 118), 70)
    for (x0, y0), (x1, y1) in (
        ((14, 7), (9, 10)), ((17, 13), (22, 16)), ((15, 20), (10, 22)),
        ((18, 27), (23, 29)), ((16, 34), (11, 37)), ((19, 41), (24, 43)),
    ):
        draw_line(arr, x0, y0, x1, y1, (33, 39, 39), 180)
        draw_line(arr, x0 + 1, y0, x1 + 1, y1, (112, 124, 114), 45)
    return arr


# --- preview sheet ---------------------------------------------------------

def make_preview() -> None:
    from PIL import ImageDraw, ImageFont

    PREVIEW.mkdir(parents=True, exist_ok=True)
    font = ImageFont.truetype(FONT_PATH, 14)
    font_small = ImageFont.truetype(FONT_PATH, 11)
    title_font = ImageFont.truetype(FONT_PATH, 26)
    zoom = 4
    padding = 16
    gap = 14
    bg = (14, 17, 18)

    sections: dict[str, list[dict]] = {}
    for entry in MANIFEST:
        sections.setdefault(entry["category"], []).append(entry)

    order = ["floors", "walls", "doors", "decals"]
    titles = {
        "floors": "ПОЛЫ  ·  FLOORS",
        "walls": "СТЕНЫ  ·  WALLS",
        "doors": "ДВЕРИ  ·  DOORS",
        "decals": "ДЕКАЛИ  ·  DECALS",
    }

    def zoom_for(entry: dict) -> int:
        w, h = entry["size"]
        return 4 if max(w, h) <= 64 else 2

    width = 1600
    y = 112
    layout: list[tuple[str, list[tuple[dict, int, int, int, int]]]] = []
    for category in order:
        entries = sections.get(category, [])
        if not entries:
            continue
        x = padding
        row_height = 0
        placed: list[tuple[dict, int, int, int, int]] = []
        max_width = width - padding * 2
        for entry in entries:
            w, h = entry["size"]
            zoom = zoom_for(entry)
            dw, dh = w * zoom, h * zoom
            if x + dw + padding > padding + max_width:
                x = padding
                y += row_height + 34
                row_height = 0
            placed.append((entry, x, y, dw, dh))
            x += dw + gap
            row_height = max(row_height, dh)
        y += row_height + 86
        layout.append((category, placed))

    total_height = y + padding
    sheet = Image.new("RGB", (width, total_height), bg)
    draw = ImageDraw.Draw(sheet)
    draw.text((padding, 14), "ЭТАЖ, КОТОРОГО НЕТ — texture pack / batch 1",
              font=title_font, fill=(220, 216, 203))
    draw.text((padding, 45),
              "native 32 px tiles · 4x preview (2x for large assets) · deterministic procedural source",
              font=font_small, fill=(118, 126, 122))

    for category, placed in layout:
        if not placed:
            continue
        header_y = placed[0][2] - 34
        draw.text((padding, header_y), titles.get(category, category.upper()),
                  font=font, fill=(156, 140, 106))
        draw.line((padding, header_y + 20, width - padding, header_y + 20),
                  fill=(52, 58, 57))
        for entry, px, py, dw, dh in placed:
            image = Image.open(ROOT / entry["file"]).convert("RGBA")
            scaled = image.resize((dw, dh), Image.NEAREST)
            for cy in range(py, py + dh, 8):
                for cx in range(px, px + dw, 8):
                    tone = (26, 30, 31) if ((cx - px) // 8 + (cy - py) // 8) % 2 == 0 else (21, 24, 25)
                    draw.rectangle((cx, cy, cx + 7, cy + 7), fill=tone)
            sheet.paste(scaled, (px, py), scaled)
            draw.rectangle((px - 1, py - 1, px + dw, py + dh), outline=(58, 64, 62))
            w, h = entry["size"]
            draw.text((px, py + dh + 5), entry["id"], font=font_small, fill=(200, 196, 182))
            draw.text((px, py + dh + 19), f"{w}x{h}", font=font_small, fill=(104, 112, 108))

    sheet.save(PREVIEW / "batch1_environment.png")
    print(f"preview -> {PREVIEW / 'batch1_environment.png'} ({sheet.size[0]}x{sheet.size[1]})")


def make_tiling_preview() -> None:
    from PIL import ImageDraw, ImageFont

    tileable = [entry for entry in MANIFEST if entry["tileable"]]
    if not tileable:
        return
    zoom = 2
    cell = 32 * 3 * zoom
    gap = 14
    label_h = 34
    width = 1600
    per_row = max(1, (width - 32 + gap) // (cell + gap))
    rows = math.ceil(len(tileable) / per_row)
    height = 56 + rows * (cell + label_h + gap) + 16
    sheet = Image.new("RGB", (width, height), (14, 17, 18))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.truetype(FONT_PATH, 13)
    title_font = ImageFont.truetype(FONT_PATH, 24)
    draw.text((16, 12), "TILING CHECK / 3x3", font=title_font, fill=(220, 216, 203))
    draw.text((16, 40), "seams, repetition and grime continuity",
              font=ImageFont.truetype(FONT_PATH, 11), fill=(118, 126, 122))

    for index, entry in enumerate(tileable):
        row = index // per_row
        col = index % per_row
        px = 16 + col * (cell + gap)
        py = 56 + row * (cell + label_h + gap)
        image = Image.open(ROOT / entry["file"]).convert("RGBA")
        scaled = image.resize((32 * zoom, 32 * zoom), Image.NEAREST)
        for ty in range(3):
            for tx in range(3):
                sheet.paste(scaled, (px + tx * 64, py + ty * 64), scaled)
        draw.rectangle((px - 1, py - 1, px + cell, py + cell), outline=(58, 64, 62))
        draw.text((px, py + cell + 5), entry["id"], font=font, fill=(196, 192, 178))

    sheet.save(PREVIEW / "batch1_tiling.png")
    print(f"preview -> {PREVIEW / 'batch1_tiling.png'} ({sheet.size[0]}x{sheet.size[1]})")


# --- build batch -----------------------------------------------------------

def build() -> None:
    floors = [
        ("floor_corridor_a", floor_tiles(FLOOR_BASE, 101), "Коридор: целый кафель", True),
        ("floor_corridor_b", floor_tiles(FLOOR_BASE, 102, damage="scuff"), "Коридор: затёртый кафель", True),
        ("floor_corridor_c", floor_tiles(FLOOR_BASE, 103, damage="chip"), "Коридор: скол и ржавчина", True),
        ("floor_corridor_stain", floor_tiles(FLOOR_BASE, 104, damage="stain"), "Коридор: сырое пятно", False),
        ("floor_corridor_wet", floor_tiles(FLOOR_BASE, 105, damage="wet"), "Коридор: лужа", False),
        ("floor_ward", floor_tiles((82, 96, 89), 106, variation=4), "Палата: светлый кафель", True),
        ("floor_morgue", floor_concrete(107), "Морг: бетон", True),
        ("floor_lobby", floor_lobby(108), "Холл: шахматная плитка", True),
        ("floor_blood", floor_blood(109), "Коридор: кровь", False),
        ("floor_grate", floor_grate(110), "Морг: решётка слива", False),
    ]
    for name, arr, description, tileable in floors:
        save(name, arr, "floors", description, tileable)

    walls = [
        ("wall_cap", wall_cap(201), "Торец стены: бетон", True),
        ("wall_face_a", wall_face(202, "a"), "Стена: облупившаяся краска", True),
        ("wall_face_b", wall_face(203, "b"), "Стена: сырость и плесень", True),
        ("wall_face_c", wall_face(204, "c"), "Стена: трещины и кирпич", True),
        ("wall_tile", wall_tile_face(205), "Стена: кафельный низ", True),
        ("wall_pipe", wall_face(206, "pipe"), "Стена: трубы", True),
    ]
    for name, arr, description, tileable in walls:
        save(name, arr, "walls", description, tileable)

    doors = [
        ("door_ward", door_leaf(64, 32, 301, "ward"), "Дверь палаты: стекло и ручка"),
        ("door_morgue", door_leaf(64, 32, 302, "morgue"), "Дверь морга: сталь и заклёпки"),
        ("door_double", door_leaf(64, 32, 303, "double"), "Двустворчатая дверь с толкателями"),
        ("door_elevator", door_leaf(100, 140, 304, "elevator"), "Служебный лифт: створки"),
        ("door_ward_frame", door_frame(64, 32, 311, "ward"),
         "Проём палаты: тёмный порог и стальная рама"),
        ("door_ward_panel", door_panel(301, "ward"),
         "Створка двери палаты для анимации открытия"),
        ("door_morgue_frame", door_frame(64, 32, 312, "morgue"),
         "Проём морга: тёмный порог и стальная рама"),
        ("door_morgue_panel", door_panel(302, "morgue"),
         "Створка двери морга для анимации открытия"),
        ("door_double_frame", door_frame(64, 32, 313, "double"),
         "Проём двустворчатой двери: тёмный порог и рама"),
        ("door_double_panel_left", door_panel(303, "double", "left"),
         "Левая створка двустворчатой двери"),
        ("door_double_panel_right", door_panel(303, "double", "right"),
         "Правая створка двустворчатой двери"),
    ]
    for name, arr, description in doors:
        save(name, arr, "doors", description)

    decals = [
        ("decal_blood_pool", blood_pool(401), "Лужа крови"),
        ("decal_blood_smear", blood_smear(402), "Кровавый след волочения"),
        ("decal_stain", stain_water(403), "Водяное пятно"),
        ("decal_crack", crack_decal(404), "Трещина"),
        ("decal_brick_patch", brick_patch_decal(405), "Обрушенная штукатурка: кирпич"),
        ("decal_mold", mold_decal(406), "Плесень"),
        ("decal_wall_crack", wall_crack_decal(407), "Длинная трещина стены"),
    ]
    for name, arr, description in decals:
        save(name, arr, "decals", description)

    write_manifest(MANIFEST, 1)
    make_preview()
    make_tiling_preview()


if __name__ == "__main__":
    build()