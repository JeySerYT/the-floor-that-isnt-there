#!/usr/bin/env python3
"""Generate batch 4: UI panels, buttons, paper, icons, vignette, logo, title art.

Everything is drawn at native 640x360 UI scale (the game viewport is 640x360,
exported at 2x). Nine-patch assets keep their decorated border inside the
`nine_patch` margins from the manifest.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_textures as g

ROOT = g.ROOT
TEX = g.TEX
UI = TEX / "ui"
MANIFEST: list[dict] = []

W, H = 640, 360

INK = (11, 14, 14)
INK_SOFT = (19, 23, 23)
STEEL = (96, 106, 100)
STEEL_L = (136, 146, 138)
STEEL_D = (60, 68, 64)
BONE = (200, 194, 174)
BONE_D = (146, 140, 120)
AMBER = (208, 168, 96)
AMBER_D = (146, 108, 52)
RUST = (140, 74, 52)
RUST_D = (88, 42, 30)
BLOOD = (122, 26, 24)
PAPER = (188, 182, 166)
PAPER_L = (208, 202, 186)
PAPER_D = (150, 144, 128)


def rect(arr: np.ndarray, x: int, y: int, w: int, h: int,
         color: tuple[int, int, int], alpha: int = 255) -> None:
    g.draw_rect(arr, x, y, w, h, color, alpha)


def border(arr: np.ndarray, x: int, y: int, w: int, h: int,
           color: tuple[int, int, int], alpha: int = 255) -> None:
    rect(arr, x, y, w, 1, color, alpha)
    rect(arr, x, y + h - 1, w, 1, color, alpha)
    rect(arr, x, y, 1, h, color, alpha)
    rect(arr, x + w - 1, y, 1, h, color, alpha)


def vgradient(arr: np.ndarray, x: int, y: int, w: int, h: int,
              top: tuple[int, int, int], bottom: tuple[int, int, int],
              alpha: int = 255) -> None:
    for row in range(h):
        t = row / max(1, h - 1)
        color = tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(3))
        rect(arr, x, y + row, w, 1, color, alpha)


def add_outline(arr: np.ndarray, color: tuple[int, int, int] = (13, 16, 16),
                alpha: int = 255) -> None:
    solid = arr[:, :, 3] > 0
    grown = solid.copy()
    grown[1:, :] |= solid[:-1, :]
    grown[:-1, :] |= solid[1:, :]
    grown[:, 1:] |= solid[:, :-1]
    grown[:, :-1] |= solid[:, 1:]
    edge = grown & ~solid
    arr[edge, :3] = color
    arr[edge, 3] = alpha


def tint(arr: np.ndarray, mask: np.ndarray, color: tuple[int, int, int],
         strength: float) -> None:
    """Blend colour into the existing pixels; never touches alpha."""
    target = np.array(color, dtype=np.float32)
    arr[mask, :3] = arr[mask, :3] * (1.0 - strength) + target * strength


def grime(arr: np.ndarray, x: int, y: int, w: int, h: int, seed: int,
          amount: int = 18, strength: float = 0.10) -> None:
    """A few darkened pixels; kept out of stretchable regions on purpose."""
    rng = np.random.default_rng(seed)
    for _ in range(amount):
        px = x + int(rng.integers(0, max(1, w)))
        py = y + int(rng.integers(0, max(1, h)))
        if 0 <= px < arr.shape[1] and 0 <= py < arr.shape[0]:
            if arr[py, px, 3] > 0:
                arr[py, px, :3] *= 1.0 - strength


# --- panels -----------------------------------------------------------------

def panel(w: int, h: int, margin: int, border_color: tuple[int, int, int],
          accent: tuple[int, int, int], fill_top: tuple[int, int, int],
          fill_bottom: tuple[int, int, int], alpha: int, seed: int,
          rivets: bool = True, bracket: bool = True,
          rivet_light: tuple[int, int, int] = (118, 126, 118),
          rivet_dark: tuple[int, int, int] = (44, 50, 48)) -> np.ndarray:
    arr = g.blank(w, h, (0, 0, 0, 0))
    vgradient(arr, 0, 0, w, h, fill_top, fill_bottom, alpha)
    border(arr, 0, 0, w, h, border_color)
    # inner bevel: light from the top left
    rect(arr, 1, 1, w - 2, 1, tuple(min(255, c + 18) for c in fill_top), alpha)
    rect(arr, 1, 1, 1, h - 2, tuple(min(255, c + 12) for c in fill_top), alpha)
    rect(arr, 1, h - 2, w - 2, 1, (12, 15, 15))
    rect(arr, w - 2, 1, 1, h - 2, (12, 15, 15))
    # thin accent line just inside the frame
    inset = margin - 5
    rect(arr, inset, inset, w - inset * 2, 1, accent, 120)
    rect(arr, inset, h - inset - 1, w - inset * 2, 1, accent, 90)
    rect(arr, inset, inset, 1, h - inset * 2, accent, 100)
    rect(arr, w - inset - 1, inset, 1, h - inset * 2, accent, 100)
    if bracket:
        corner = [
            (inset, inset, 1, 7), (inset, inset, 7, 1),
            (w - inset - 1, inset, 1, 7), (w - inset - 7, inset, 7, 1),
            (inset, h - inset - 7, 1, 7), (inset, h - inset - 1, 7, 1),
            (w - inset - 1, h - inset - 7, 1, 7), (w - inset - 7, h - inset - 1, 7, 1),
        ]
        for x, y, cw, chh in corner:
            rect(arr, x, y, cw, chh, accent, 190)
    if rivets:
        for rx, ry in ((6, 6), (w - 8, 6), (6, h - 8), (w - 8, h - 8)):
            rect(arr, rx, ry, 2, 2, rivet_light)
            rect(arr, rx, ry + 1, 1, 1, rivet_dark)
    grime(arr, 0, 0, margin, margin, seed, 10, 0.10)
    grime(arr, w - margin, h - margin, margin, margin, seed + 1, 10, 0.10)
    return arr


def ui_panel() -> np.ndarray:
    return panel(64, 64, 12, (58, 66, 62), (104, 96, 70),
                 (30, 35, 34), (23, 27, 27), 238, 9001)


def ui_panel_alert() -> np.ndarray:
    return panel(64, 64, 12, (124, 58, 44), (150, 62, 48),
                 (34, 30, 29), (24, 21, 21), 238, 9002,
                 rivet_light=(150, 84, 66), rivet_dark=(72, 30, 24))


def ui_panel_paper() -> np.ndarray:
    arr = g.blank(64, 64, (0, 0, 0, 0))
    vgradient(arr, 0, 0, 64, 64, PAPER_L, PAPER, 255)
    border(arr, 0, 0, 64, 64, PAPER_D)
    # worn edge: the pattern runs along the border, so nine-patch scaling is safe
    rng = np.random.default_rng(9003)
    for x in range(64):
        if rng.random() < 0.18:
            rect(arr, x, 0, 1, 1, (172, 162, 140))
        if rng.random() < 0.18:
            rect(arr, x, 63, 1, 1, (172, 162, 140))
    for y in range(64):
        if rng.random() < 0.16:
            rect(arr, 0, y, 1, 1, (172, 162, 140))
        if rng.random() < 0.16:
            rect(arr, 63, y, 1, 1, (172, 162, 140))
    # aged edges: constant lines, so they survive nine-patch stretching
    border(arr, 1, 1, 62, 62, (176, 170, 154))
    border(arr, 2, 2, 60, 60, (198, 192, 176), 120)
    rect(arr, 0, 0, 64, 1, (166, 158, 142))
    rect(arr, 0, 63, 64, 1, (158, 150, 134))
    # coffee stain, kept fully inside the bottom-left corner block (never stretched)
    yy, xx = np.mgrid[0:64, 0:64]
    for cx, cy, r, strength in ((8, 56, 5, 0.34), (6, 55, 2, 0.46), (10, 58, 1, 0.26)):
        mask = (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r
        tint(arr, mask, (128, 100, 66), strength)
    # a few foxing specks in the corners only
    for cx, cy in ((13, 9), (55, 12), (14, 57), (52, 54)):
        tint(arr, (xx == cx) & (yy == cy), (132, 108, 78), 0.25)
    # torn corner: a small staircase cut out of the sheet
    for i in range(7):
        arr[63 - i, 0:max(0, 6 - i), 3] = 0
    return arr


def ui_button(state: str) -> np.ndarray:
    arr = g.blank(64, 28, (0, 0, 0, 0))
    if state == "normal":
        vgradient(arr, 0, 0, 64, 28, (42, 46, 44), (30, 34, 33))
        border_color, accent = (70, 68, 58), (128, 112, 76)
    elif state == "hover":
        vgradient(arr, 0, 0, 64, 28, (52, 50, 40), (38, 37, 31))
        border_color, accent = (150, 118, 60), (208, 168, 96)
    else:
        vgradient(arr, 0, 0, 64, 28, (24, 27, 26), (32, 34, 32))
        border_color, accent = (86, 66, 36), (124, 94, 46)
    border(arr, 0, 0, 64, 28, border_color)
    if state == "pressed":
        rect(arr, 1, 1, 62, 1, (12, 15, 15))
        rect(arr, 1, 1, 1, 26, (12, 15, 15))
        rect(arr, 1, 2, 62, 1, (24, 28, 27))
        rect(arr, 2, 1, 1, 26, (24, 28, 27))
        rect(arr, 1, 26, 62, 1, (72, 70, 60))
    else:
        rect(arr, 1, 1, 62, 1, (78, 82, 76))
        rect(arr, 1, 1, 1, 26, (64, 70, 66))
        rect(arr, 1, 26, 62, 1, (18, 21, 21))
    # small end brackets, a nod to the panel corners
    for bx in (4, 60):
        rect(arr, bx - 1, 9, 1, 10, accent, 170)
    return arr


def ui_slot() -> np.ndarray:
    arr = g.blank(40, 40, (0, 0, 0, 0))
    vgradient(arr, 0, 0, 40, 40, (24, 28, 27), (17, 20, 20))
    border(arr, 0, 0, 40, 40, (62, 70, 66))
    rect(arr, 1, 1, 38, 1, (14, 17, 17))
    rect(arr, 1, 1, 1, 38, (14, 17, 17))
    rect(arr, 1, 38, 38, 1, (74, 80, 74))
    rect(arr, 38, 1, 1, 38, (50, 56, 54))
    # faint crosshair so empty slots still read as slots
    rect(arr, 19, 8, 1, 6, (74, 80, 74), 90)
    rect(arr, 19, 26, 1, 6, (74, 80, 74), 90)
    rect(arr, 8, 19, 6, 1, (74, 80, 74), 90)
    rect(arr, 26, 19, 6, 1, (74, 80, 74), 90)
    return arr


def ui_divider() -> np.ndarray:
    arr = g.blank(32, 8, (0, 0, 0, 0))
    rect(arr, 0, 3, 32, 1, (96, 88, 66), 220)
    rect(arr, 0, 4, 32, 1, (28, 32, 31), 210)
    rect(arr, 0, 2, 32, 1, (16, 19, 19), 130)
    return arr


# --- icons ------------------------------------------------------------------

def icon_cassette() -> np.ndarray:
    arr = g.blank(24, 24, (0, 0, 0, 0))
    rect(arr, 3, 6, 18, 12, (52, 55, 54))
    rect(arr, 3, 6, 18, 1, (78, 82, 78))
    rect(arr, 3, 17, 18, 1, (30, 33, 33))
    border(arr, 3, 6, 18, 12, (22, 25, 25))
    # label
    rect(arr, 5, 8, 14, 5, (172, 164, 140))
    rect(arr, 5, 8, 14, 1, (196, 188, 164))
    rect(arr, 6, 10, 9, 1, (138, 130, 108))
    rect(arr, 6, 11, 6, 1, (138, 130, 108))
    rect(arr, 16, 9, 2, 3, (126, 44, 36))
    # tape window and reels
    rect(arr, 6, 14, 12, 3, (18, 21, 21))
    for cx in (9, 15):
        yy, xx = np.mgrid[0:24, 0:24]
        ring = np.abs(np.sqrt((xx - cx) ** 2 + (yy - 15) ** 2) - 1.6) < 0.9
        arr[ring, :3] = np.array([132, 128, 112], dtype=np.float32)
        arr[ring, 3] = 255
    rect(arr, 10, 19, 4, 1, (24, 27, 27))
    add_outline(arr)
    return arr


def icon_key() -> np.ndarray:
    arr = g.blank(24, 24, (0, 0, 0, 0))
    brass = (178, 146, 84)
    brass_l = (212, 184, 118)
    brass_d = (118, 92, 48)
    # bow
    yy, xx = np.mgrid[0:24, 0:24]
    dist = np.sqrt((xx - 8) ** 2 + (yy - 9) ** 2)
    ring = (dist <= 5.2) & (dist >= 2.6)
    arr[ring, :3] = np.array(brass, dtype=np.float32)
    arr[ring, 3] = 255
    inner_edge = (dist < 3.4) & (dist >= 2.6)
    arr[inner_edge, :3] = np.array(brass_d, dtype=np.float32)
    # shaft
    rect(arr, 12, 8, 9, 2, brass)
    rect(arr, 12, 8, 9, 1, brass_l)
    rect(arr, 12, 9, 9, 1, brass_d)
    # teeth
    rect(arr, 18, 10, 2, 4, brass)
    rect(arr, 18, 13, 2, 1, brass_d)
    rect(arr, 15, 10, 2, 3, brass)
    rect(arr, 15, 12, 2, 1, brass_d)
    # bow highlight
    hl = (np.abs(dist - 4.6) < 0.7) & (xx < 9) & (yy < 5)
    arr[hl, :3] = np.array(brass_l, dtype=np.float32)
    add_outline(arr)
    return arr


def icon_fuse() -> np.ndarray:
    arr = g.blank(24, 24, (0, 0, 0, 0))
    steel = (150, 154, 146)
    steel_d = (96, 102, 96)
    ceramic = (198, 190, 168)
    rect(arr, 9, 3, 6, 18, ceramic)
    rect(arr, 9, 3, 2, 18, (216, 208, 184))
    rect(arr, 14, 3, 1, 18, (168, 160, 138))
    # caps
    rect(arr, 8, 2, 8, 3, steel)
    rect(arr, 8, 2, 8, 1, (182, 186, 176))
    rect(arr, 8, 19, 8, 3, steel)
    rect(arr, 8, 21, 8, 1, steel_d)
    # filament band and rating mark
    rect(arr, 9, 9, 6, 2, (58, 60, 58))
    rect(arr, 10, 10, 4, 1, (206, 122, 58))
    rect(arr, 10, 13, 4, 1, (150, 60, 48))
    rect(arr, 11, 14, 2, 1, (150, 60, 48))
    add_outline(arr)
    return arr


def icon_note() -> np.ndarray:
    arr = g.blank(24, 24, (0, 0, 0, 0))
    rect(arr, 5, 3, 14, 18, PAPER)
    rect(arr, 5, 3, 14, 1, PAPER_L)
    rect(arr, 5, 20, 14, 1, PAPER_D)
    border(arr, 5, 3, 14, 18, PAPER_D)
    # folded corner
    rect(arr, 16, 3, 3, 1, PAPER_D)
    rect(arr, 18, 4, 1, 3, PAPER_D)
    rect(arr, 16, 4, 2, 2, (212, 204, 182))
    # text
    for index, width in enumerate((10, 8, 11, 7, 9)):
        rect(arr, 7, 7 + index * 2, width, 1, (128, 120, 100))
    # stamp
    rect(arr, 12, 16, 5, 3, (150, 44, 38), 220)
    rect(arr, 13, 17, 3, 1, (190, 74, 64), 220)
    add_outline(arr)
    return arr


def ui_note_sheet() -> np.ndarray:
    """Fixed-size sheet for the note overlay: creases, foxing, torn edge."""
    w, h = 520, 260
    arr = g.blank(w, h, (0, 0, 0, 0))
    vgradient(arr, 0, 0, w, h, PAPER_L, (172, 166, 150), 255)
    border(arr, 0, 0, w, h, (150, 142, 126))

    rng = np.random.default_rng(9101)
    # torn top edge: wider nicks with a darker lip underneath
    for x in range(w):
        if rng.random() < 0.34:
            depth = 1 + int(rng.integers(0, 3))
            rect(arr, x, 0, 1, depth, (148, 140, 124))
        if rng.random() < 0.16:
            rect(arr, x, 1, 1, 1, (168, 160, 144))
    for y in range(h):
        if rng.random() < 0.26:
            rect(arr, 0, y, 1, 1, (148, 140, 124))
        if rng.random() < 0.20:
            rect(arr, w - 1, y, 1, 1, (148, 140, 124))

    yy, xx = np.mgrid[0:h, 0:w]
    # paper fibres: sparse pixels, kept away from the central text block
    edge_zone = (xx < 40) | (xx >= w - 40) | (yy < 32) | (yy >= h - 32)
    fibre = rng.random((h, w)) < 0.035
    tint(arr, fibre & edge_zone, (168, 160, 144), 0.30)

    # one vertical fold crease reads as a sheet folded in half
    tint(arr, (xx == 171), (120, 112, 96), 0.09)
    tint(arr, (xx == 172), (250, 246, 232), 0.40)

    # foxing spots
    spots = [(64, 58, 5), (66, 61, 3), (438, 196, 6), (441, 199, 3),
             (246, 34, 3), (352, 224, 4), (96, 208, 3), (478, 88, 3)]
    for cx, cy, r in spots:
        mask = (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r
        tint(arr, mask, (128, 100, 66), 0.26)

    # coffee ring with a broken arc, plus a faint wash inside
    ring_r = 17
    dist = np.sqrt((xx - 414) ** 2 + (yy - 62) ** 2)
    angle = np.arctan2(yy - 62, xx - 414)
    ring = (np.abs(dist - ring_r) < 1.1) & ~((angle > 2.2) & (angle < 2.9))
    tint(arr, ring, (126, 92, 52), 0.30)
    tint(arr, dist < ring_r - 2, (150, 122, 82), 0.05)

    # punched hole with a worn, light rim
    hole = (xx - 26) ** 2 + (yy - 26) ** 2 <= 9
    hole_rim = ((xx - 26) ** 2 + (yy - 26) ** 2 <= 18) & ~hole
    tint(arr, hole_rim, (108, 100, 84), 0.32)
    arr[hole, 3] = 0

    # ink stamp: hollow frame with a diagonal slash
    stamp = np.zeros((h, w), dtype=bool)
    framebox = (xx >= 372) & (xx < 468) & (yy >= 202) & (yy < 234)
    framebox &= ~((xx >= 377) & (xx < 463) & (yy >= 207) & (yy < 229))
    stamp |= framebox
    stamp |= np.abs((xx - 420) + (yy - 218) * 2.2) < 2.4
    stamp &= (xx >= 374) & (xx < 466) & (yy >= 204) & (yy < 232)
    tint(arr, stamp, (132, 38, 32), 0.55)

    # one dried droplet near the stamp: the only red on the bare sheet
    drop = (xx - 348) ** 2 + (yy - 236) ** 2 <= 5
    drop |= (xx - 352) ** 2 + (yy - 240) ** 2 <= 2
    tint(arr, drop, (86, 22, 20), 0.55)
    return arr


# --- vignette ---------------------------------------------------------------

def ui_vignette() -> np.ndarray:
    yy, xx = np.mgrid[0:H, 0:W]
    nx = xx / (W - 1) * 2.0 - 1.0
    ny = yy / (H - 1) * 2.0 - 1.0
    dist = np.sqrt(nx ** 2 + (ny * 1.25) ** 2)
    dark = np.clip((dist - 0.42) / (1.05 - 0.42), 0.0, 1.0) ** 1.4 * 0.78
    scan = np.where(yy % 2 == 0, 0.012, 0.0)
    arr = np.zeros((H, W, 4), dtype=np.float32)
    arr[:, :, 3] = np.clip(dark + scan, 0.0, 1.0) * 255.0
    return arr


# --- logo -------------------------------------------------------------------

GLYPHS: dict[str, list[str]] = {
    "Э": ["11110", "00001", "00001", "01111", "00001", "00001", "11110"],
    "Т": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "А": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "Ж": ["10101", "10101", "01110", "00100", "01110", "10101", "10101"],
    "К": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "О": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "Р": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Г": ["11111", "10000", "10000", "10000", "10000", "10000", "10000"],
    "Н": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "Е": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    ",": ["..", "..", "..", "..", "..", "11", "1."],
}


def text_mask(line: str) -> np.ndarray:
    rows = 8
    columns: list[np.ndarray] = []
    for index, char in enumerate(line):
        if char == " ":
            columns.append(np.zeros((rows, 3), dtype=bool))
        else:
            glyph = GLYPHS[char]
            block = np.zeros((rows, len(glyph[0])), dtype=bool)
            offset = 1 if char == "," else 0
            block[offset:offset + 7] = np.array(
                [[c == "1" for c in row] for row in glyph], dtype=bool)
            columns.append(block)
        if index < len(line) - 1:
            columns.append(np.zeros((rows, 1), dtype=bool))
    return np.concatenate(columns, axis=1)


def dilate(mask: np.ndarray) -> np.ndarray:
    grown = mask.copy()
    grown[1:, :] |= mask[:-1, :]
    grown[:-1, :] |= mask[1:, :]
    grown[:, 1:] |= mask[:, :-1]
    grown[:, :-1] |= mask[:, 1:]
    return grown


def layer(mask: np.ndarray, color: tuple[int, int, int], alpha: int) -> Image.Image:
    arr = np.zeros((mask.shape[0], mask.shape[1], 4), dtype=np.uint8)
    arr[mask, 0] = color[0]
    arr[mask, 1] = color[1]
    arr[mask, 2] = color[2]
    arr[mask, 3] = alpha
    return Image.fromarray(arr, "RGBA")


def ui_logo() -> Image.Image:
    scale, gap = 3, 2
    lines = ["ЭТАЖ,", "КОТОРОГО НЕТ"]
    masks = [text_mask(line) for line in lines]
    line_widths = [m.shape[1] for m in masks]
    width = max(line_widths) * scale + 10
    height = (len(lines) * 8 + gap) * scale + 10

    base = np.zeros((height, width), dtype=bool)
    tops = [5, 5 + (8 + gap) * scale]
    for mask, top, line_width in zip(masks, tops, line_widths):
        big = np.kron(mask, np.ones((scale, scale), dtype=bool))
        left = (width - line_width * scale) // 2
        base[top:top + big.shape[0], left:left + big.shape[1]] = big

    # chunky one-pixel (at 1x) bevel: light on top, shade on bottom
    up = np.zeros_like(base)
    up[1:, :] = base[:-1, :]
    down = np.zeros_like(base)
    down[:-1, :] = base[1:, :]
    top_edge = base & ~up
    bottom_edge = base & ~down

    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    bleed = np.roll(np.roll(dilate(base), 2, axis=0), 1, axis=1)
    image.alpha_composite(layer(bleed, (74, 16, 16), 120))
    image.alpha_composite(layer(dilate(dilate(base)), (10, 12, 12), 255))
    image.alpha_composite(layer(base, BONE, 255))
    image.alpha_composite(layer(top_edge, (226, 220, 200), 255))
    image.alpha_composite(layer(bottom_edge, (146, 140, 120), 255))
    return image


# --- title art --------------------------------------------------------------

def load(rel: str) -> Image.Image:
    return Image.open(TEX / rel).convert("RGBA")


def label_plate(text: str, width: int, height: int) -> Image.Image:
    arr = g.blank(width, height, (0, 0, 0, 0))
    rect(arr, 0, 0, width, height, (29, 34, 34))
    border(arr, 0, 0, width, height, (63, 71, 67))
    rect(arr, 0, 0, width, 1, (98, 105, 98))
    rect(arr, 0, height - 1, width, 1, (18, 22, 22))
    plate = g.to_image(arr)
    draw = ImageDraw.Draw(plate)
    font = ImageFont.truetype(g.FONT_PATH, 7)
    draw.text((width / 2, height / 2 + 0.5), text, font=font,
              fill=(136, 142, 132, 255), anchor="mm")
    return plate


def number_plate(number: str) -> Image.Image:
    plate = Image.new("RGBA", (24, 16), (27, 13, 13, 255))
    draw = ImageDraw.Draw(plate)
    draw.rectangle((0, 0, 23, 0), fill=(99, 42, 38, 255))
    draw.rectangle((0, 15, 23, 15), fill=(16, 8, 8, 255))
    font = ImageFont.truetype(g.FONT_PATH, 10)
    draw.text((12, 8), number, font=font, fill=(206, 74, 62, 255), anchor="mm")
    return plate


def title_scene() -> Image.Image:
    import mock_props as mp

    scene = Image.new("RGBA", (W, H), (9, 12, 13, 255))
    floors = {name: load(f"floors/{name}.png") for name in (
        "floor_corridor_a", "floor_corridor_b", "floor_corridor_c",
        "floor_corridor_stain", "floor_corridor_wet",
    )}
    walls = {name: load(f"walls/{name}.png") for name in (
        "wall_cap", "wall_face_a", "wall_face_b", "wall_tile", "wall_pipe",
    )}

    rng = np.random.default_rng(4104)
    for y in range(64, H, 32):
        for x in range(0, W, 32):
            roll = rng.random()
            if roll < 0.05:
                tile = floors["floor_corridor_stain"]
            elif roll < 0.10:
                tile = floors["floor_corridor_wet"]
            elif roll < 0.24:
                tile = floors["floor_corridor_b"]
            elif roll < 0.36:
                tile = floors["floor_corridor_c"]
            else:
                tile = floors["floor_corridor_a"]
            mp.paste(scene, tile, x, y)

    for x in range(0, W, 32):
        mp.paste(scene, walls["wall_cap"], x, 0)
        face = walls["wall_face_a"]
        if 416 <= x < 576:
            face = walls["wall_face_b"]
        elif x >= 576:
            face = walls["wall_pipe"]
        mp.paste(scene, face, x, 32)

    # double door, ajar: the warm gap is the only light source on the floor
    warm = Image.new("RGBA", (8, 52), (232, 188, 122, 255))
    scene.alpha_composite(warm, (492, 6))
    door_frame = load("doors/door_double_frame.png").resize((128, 64), Image.NEAREST)
    left = load("doors/door_double_panel_left.png").resize((58, 52), Image.NEAREST)
    right = load("doors/door_double_panel_right.png").resize((58, 52), Image.NEAREST)
    mp.paste(scene, door_frame, 432, 0)
    mp.paste(scene, left, 435, 6)
    mp.paste(scene, right, 499, 6)

    mp.paste(scene, label_plate("ПАЛАТА 13", 56, 12), 358, 40)
    mp.paste(scene, number_plate("13"), 568, 40)
    mp.paste(scene, load("devices/prop_elevator_panel.png"), 600, 42)
    mp.paste(scene, load("decals/decal_wall_crack.png"), 314, 36)
    mp.paste(scene, load("decals/decal_mold.png"), 208, 38)
    mp.paste(scene, load("decals/decal_stain.png"), 256, 44)

    # blood runs from the gap toward the nurse's feet
    mp.paste(scene, load("decals/decal_blood_smear.png"), 470, 58)
    mp.paste(scene, load("decals/decal_blood_pool.png"), 508, 132)

    # the nurse waits just to the right of the gap, facing the camera
    nurse = Image.open(TEX / "characters/nurse_chase_sheet.png").convert("RGBA").crop((0, 0, 24, 38))
    nurse = nurse.resize((48, 76), Image.NEAREST)
    dim = nurse.copy()
    rgb_nurse = np.array(dim.convert("RGB"), dtype=np.float32) * 0.78
    dim = Image.fromarray(np.clip(rgb_nurse, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    dim.putalpha(nurse.getchannel("A"))
    scene.alpha_composite(dim, (512, 64))

    # a body bag on the floor fills the dark bottom-right corner
    mp.paste(scene, load("furniture/prop_body_bag.png"), 536, 268)
    mp.paste(scene, load("decals/decal_blood_pool.png"), 560, 292)

    # dead ceiling fixture on the far left, barely readable
    dead = g.blank(32, 6, (0, 0, 0, 0))
    rect(dead, 0, 0, 32, 6, (30, 34, 33))
    rect(dead, 0, 0, 32, 1, (48, 54, 51))
    rect(dead, 4, 3, 24, 2, (60, 65, 60))
    rect(dead, 26, 2, 2, 3, (74, 46, 36))
    mp.paste(scene, g.to_image(dead), 112, 12)

    rgb = np.array(scene.convert("RGB"), dtype=np.float32) / 255.0
    yy, xx = np.mgrid[0:H, 0:W]
    door_glow = np.clip(1.0 - np.sqrt((xx - 496) ** 2 + (yy - 92) ** 2) / 300.0, 0.0, 1.0) ** 1.15
    pool = np.clip(1.0 - np.sqrt((xx - 496) ** 2 + (yy - 142) ** 2) / 150.0, 0.0, 1.0) ** 2
    light = np.clip(0.27 + 0.86 * door_glow, 0.0, 1.16)
    rgb *= light[:, :, None]
    warm = np.array([1.0, 0.86, 0.64], dtype=np.float32)
    weight = (np.clip(door_glow * 0.46, 0.0, 0.56))[:, :, None]
    rgb = rgb * (1.0 - weight) + rgb * warm * weight
    # light escapes through the gap and spreads across the tiles
    gap = np.clip(1.0 - np.sqrt((xx - 496) ** 2 + (yy - 36) ** 2) / 54.0, 0.0, 1.0) ** 2
    rgb += np.array([1.0, 0.91, 0.74], dtype=np.float32) * (gap * 0.62)[:, :, None]
    rgb += warm * (pool * 0.30)[:, :, None]
    # red glow of the 13 sign
    sign = np.clip(1.0 - np.sqrt((xx - 580) ** 2 + (yy - 48) ** 2) / 44.0, 0.0, 1.0) ** 2
    rgb += np.array([0.62, 0.07, 0.05], dtype=np.float32) * (sign * 0.46)[:, :, None]
    # keep the menu side dark
    scrim = 0.22 + 0.78 * np.clip((xx - 8) / 300.0, 0.0, 1.0) ** 0.9
    rgb *= scrim[:, :, None]
    nx = np.abs(xx - W / 2) / (W / 2)
    ny = np.abs(yy - H / 2) / (H / 2)
    vig = np.clip(1.0 - (nx ** 2.2 + ny ** 2.2) * 0.46, 0.15, 1.0)
    rgb *= vig[:, :, None]
    rgb[:, :, 2] *= 1.07
    rgb[:, :, 0] *= 0.96
    return Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8), "RGB").convert("RGBA")


# --- manifest ---------------------------------------------------------------

def save_image(name: str, image: Image.Image, description: str,
               nine_patch: dict[str, int] | None = None,
               tileable: bool = False, quantized: bool = True,
               colors: int = 32) -> None:
    UI.mkdir(parents=True, exist_ok=True)
    final = g.quantize(image, colors=colors) if quantized else image.convert("RGBA")
    final.save(UI / f"{name}.png")
    entry = {
        "id": name,
        "file": f"assets/textures/ui/{name}.png",
        "size": list(final.size),
        "category": "ui",
        "tileable": tileable,
        "batch": 4,
        "description": description,
    }
    if nine_patch:
        entry["nine_patch"] = nine_patch
    MANIFEST.append(entry)


def write_manifest(entries: list[dict]) -> None:
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
    batches = sorted({entry.get("batch", 1) for entry in merged} | {4})
    path.write_text(
        json.dumps({"version": 1, "batches": batches, "assets": merged},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def build() -> None:
    margins = {"left": 12, "right": 12, "top": 12, "bottom": 12}
    save_image("ui_panel", g.to_image(ui_panel()),
               "Панель HUD: тёмный пластик, латунная линия, уголки и заклёпки",
               nine_patch=margins)
    save_image("ui_panel_alert", g.to_image(ui_panel_alert()),
               "Панель тревоги: ржаво-красная рамка для выбора и финалов",
               nine_patch=margins)
    save_image("ui_panel_paper", g.to_image(ui_panel_paper()),
               "Бумажная панель для записок: сгиб, потёртый край, пятно",
               nine_patch=margins)
    save_image("ui_button", g.to_image(ui_button("normal")),
               "Кнопка меню, обычное состояние",
               nine_patch={"left": 10, "right": 10, "top": 8, "bottom": 8})
    save_image("ui_button_hover", g.to_image(ui_button("hover")),
               "Кнопка меню, наведение: янтарная рамка",
               nine_patch={"left": 10, "right": 10, "top": 8, "bottom": 8})
    save_image("ui_button_pressed", g.to_image(ui_button("pressed")),
               "Кнопка меню, нажатие: утопленная рамка",
               nine_patch={"left": 10, "right": 10, "top": 8, "bottom": 8})
    save_image("ui_slot", g.to_image(ui_slot()),
               "Слот инвентаря 40x40: тёмное поле с прицелом",
               nine_patch={"left": 8, "right": 8, "top": 8, "bottom": 8})
    save_image("ui_divider", g.to_image(ui_divider()),
               "Разделитель: тонкая латунная линия с засечками", tileable=True)
    save_image("icon_cassette", g.to_image(icon_cassette()),
               "Иконка инвентаря: кассета", colors=24)
    save_image("icon_key", g.to_image(icon_key()),
               "Иконка инвентаря: служебный ключ", colors=24)
    save_image("icon_fuse", g.to_image(icon_fuse()),
               "Иконка инвентаря: предохранитель", colors=24)
    save_image("icon_note", g.to_image(icon_note()),
               "Иконка инвентаря: записка", colors=24)
    save_image("ui_note_sheet", g.to_image(ui_note_sheet()),
               "Лист записки 520x260: сгибы, пятна, кофейный круг, штамп",
               quantized=True, colors=48)
    save_image("ui_vignette", g.to_image(ui_vignette()),
               "Виньетка 640x360: затемнение по краям и сканлайны",
               quantized=False)
    save_image("ui_logo", ui_logo(),
               "Логотип «ЭТАЖ, КОТОРОГО НЕТ»: пиксельный шрифт 5x7, шкала 3x",
               quantized=False)
    save_image("ui_title_bg", title_scene(),
               "Титульный фон: коридор с дверью, лампой и фигурой в глубине",
               quantized=True, colors=64)

    write_manifest(MANIFEST)


if __name__ == "__main__":
    build()
    for entry in MANIFEST:
        print(f"{entry['id']} -> {entry['file']} ({entry['size'][0]}x{entry['size'][1]})")