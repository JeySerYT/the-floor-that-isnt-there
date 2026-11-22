#!/usr/bin/env python3
"""Generate batch 2 of the texture pack: props, furniture, devices and items.

Reuses the drawing helpers and palette from generate_textures.py so batch 2
matches batch 1 exactly (same quantization, same grime language).
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_textures as g

ROOT = g.ROOT
TEX = g.TEX
PREVIEW = g.PREVIEW
FONT_PATH = g.FONT_PATH

# --- palette additions ------------------------------------------------------

OUTLINE = (25, 30, 31)
STEEL = (122, 130, 127)
STEEL_L = (158, 166, 159)
STEEL_D = (76, 84, 83)
STEEL_XD = (46, 53, 53)
PAINT = (94, 106, 101)
PAINT_L = (122, 134, 127)
PAINT_D = (64, 74, 71)
WOOD = (82, 70, 52)
WOOD_L = (108, 94, 70)
WOOD_D = (54, 46, 35)
WOOD_XD = (38, 32, 25)
FABRIC = (166, 164, 145)
FABRIC_L = (196, 193, 172)
FABRIC_D = (122, 121, 106)
SHEET = (178, 180, 165)
SHEET_D = (133, 136, 123)
BLANKET = (98, 111, 99)
BLANKET_L = (121, 134, 119)
BLANKET_D = (70, 80, 72)
RUBBER = (37, 40, 40)
RUBBER_L = (57, 61, 60)
RUBBER_D = (24, 27, 27)
PAPER = (198, 190, 164)
PAPER_D = (156, 148, 124)
PAPER_XD = (112, 106, 89)
BRASS = (146, 115, 58)
BRASS_L = (192, 162, 92)
BRASS_D = (98, 75, 36)
AMBER = (186, 143, 66)
WARN = (158, 132, 58)
WARN_D = (92, 76, 34)
RED = (126, 36, 31)
TEAL_GLASS = (46, 70, 73)

MANIFEST: list[dict] = []


# --- local helpers ----------------------------------------------------------

def fill_ellipse(arr: np.ndarray, cx: float, cy: float, rx: float, ry: float,
                 color: tuple[int, int, int], alpha: int = 255) -> None:
    h, w = arr.shape[:2]
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).ellipse(
        [cx - rx, cy - ry, cx + rx, cy + ry], fill=255
    )
    region = np.array(mask) > 0
    arr[region, :3] = color
    arr[region, 3] = alpha


def ring(arr: np.ndarray, cx: float, cy: float, rx: float, ry: float,
         color: tuple[int, int, int], alpha: int = 255) -> None:
    h, w = arr.shape[:2]
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], outline=255, width=1)
    region = np.array(mask) > 0
    arr[region, :3] = color
    arr[region, 3] = alpha


def outline(arr: np.ndarray, x: int, y: int, w: int, h: int,
            color: tuple[int, int, int] = OUTLINE) -> None:
    g.draw_line(arr, x, y, x + w - 1, y, color)
    g.draw_line(arr, x, y, x, y + h - 1, color)
    g.draw_line(arr, x, y + h - 1, x + w - 1, y + h - 1, color)
    g.draw_line(arr, x + w - 1, y, x + w - 1, y + h - 1, color)


def bevel(arr: np.ndarray, x: int, y: int, w: int, h: int,
          light: tuple[int, int, int], dark: tuple[int, int, int]) -> None:
    g.draw_line(arr, x, y, x + w - 2, y, light, 220)
    g.draw_line(arr, x, y, x, y + h - 2, light, 150)
    g.draw_line(arr, x + 1, y + h - 1, x + w - 1, y + h - 1, dark, 230)
    g.draw_line(arr, x + w - 1, y + 1, x + w - 1, y + h - 1, dark, 200)


def panel(arr: np.ndarray, x: int, y: int, w: int, h: int,
          face: tuple[int, int, int], light: tuple[int, int, int],
          dark: tuple[int, int, int], outline_color: tuple[int, int, int] = OUTLINE) -> None:
    g.draw_rect(arr, x, y, w, h, face)
    bevel(arr, x, y, w, h, light, dark)
    outline(arr, x, y, w, h, outline_color)


def cut_corners(arr: np.ndarray, x: int, y: int, w: int, h: int, size: int = 1) -> None:
    for dx in range(size):
        for dy in range(size):
            arr[y + dy, x + dx, 3] = 0
            arr[y + dy, x + w - 1 - dx, 3] = 0
            arr[y + h - 1 - dy, x + dx, 3] = 0
            arr[y + h - 1 - dy, x + w - 1 - dx, 3] = 0


def cast_shadow(arr: np.ndarray, x: int, y: int, w: int, h: int, alpha: int = 55) -> None:
    g.draw_rect(arr, x + 2, y + 3, w - 2, h - 2, (0, 0, 0), alpha)


def grime(arr: np.ndarray, seed: int, strength: float = 0.1) -> None:
    g.add_grime(arr, seed, strength, 3)


def bolts(arr: np.ndarray, x: int, y: int, count: int, step: int = 6) -> None:
    for index in range(count):
        bx = x + index * step
        g.draw_rect(arr, bx, y, 1, 1, STEEL_L, 190)
        g.draw_rect(arr, bx, y, 1, 1, STEEL_XD, 90)


# --- furniture --------------------------------------------------------------

def reception_desk(seed: int) -> np.ndarray:
    arr = g.blank(96, 48, (0, 0, 0, 0))
    cast_shadow(arr, 1, 4, 94, 42, 60)
    panel(arr, 1, 4, 94, 40, WOOD_D, WOOD_L, WOOD_XD)
    g.draw_rect(arr, 4, 7, 88, 27, WOOD)
    for y in range(9, 33, 5):
        g.draw_line(arr, 4, y, 91, y, (86, 66, 46), 70)
        g.draw_line(arr, 5, y + 1, 90, y + 1, WOOD_L, 45)
    # front lip of the counter
    g.draw_rect(arr, 4, 35, 88, 7, (50, 38, 28))
    g.draw_line(arr, 4, 35, 91, 35, WOOD_L, 160)
    g.draw_line(arr, 4, 41, 91, 41, (34, 25, 19), 220)

    # open reception ledger
    g.draw_rect(arr, 7, 9, 27, 19, (0, 0, 0), 60)
    g.draw_rect(arr, 6, 8, 27, 19, PAPER_XD)
    g.draw_rect(arr, 7, 9, 25, 17, PAPER)
    g.draw_line(arr, 19, 9, 19, 25, PAPER_XD, 220)
    for y in range(12, 24, 3):
        g.draw_line(arr, 9, y, 17, y, PAPER_XD, 170)
        g.draw_line(arr, 21, y, 30, y, PAPER_XD, 150)
    g.draw_rect(arr, 22, 20, 4, 4, RED, 170)

    # pen
    g.draw_rect(arr, 35, 23, 8, 1, (42, 48, 50))
    g.draw_rect(arr, 35, 23, 2, 1, STEEL_L, 200)

    # CRT monitor, seen from above
    g.draw_rect(arr, 61, 7, 27, 23, (0, 0, 0), 70)
    panel(arr, 60, 6, 26, 22, (52, 58, 58), STEEL_D, STEEL_XD)
    g.draw_rect(arr, 63, 9, 20, 13, (34, 42, 44))
    g.draw_rect(arr, 64, 10, 18, 11, TEAL_GLASS)
    for y in range(11, 21, 2):
        g.draw_line(arr, 64, y, 81, y, (56, 86, 86), 120)
    g.draw_line(arr, 64, 10, 70, 10, (96, 132, 128), 120)
    g.draw_rect(arr, 68, 23, 9, 2, (72, 78, 76))
    g.draw_rect(arr, 71, 24, 3, 2, AMBER, 170)

    # telephone
    panel(arr, 43, 10, 12, 9, (48, 50, 48), STEEL_D, STEEL_XD)
    g.draw_rect(arr, 45, 12, 8, 4, (30, 32, 32))
    g.draw_rect(arr, 45, 11, 3, 2, STEEL, 200)
    g.draw_rect(arr, 50, 11, 3, 2, STEEL, 200)

    # loose papers and a mug ring
    g.draw_rect(arr, 36, 27, 15, 8, PAPER_XD, 200)
    g.draw_rect(arr, 37, 26, 13, 8, PAPER, 245)
    g.draw_line(arr, 39, 29, 48, 29, PAPER_XD, 160)
    g.draw_line(arr, 39, 31, 46, 31, PAPER_XD, 140)
    ring(arr, 80, 30, 4, 3, (62, 48, 35), 120)

    # wear: chipped corners, scuffs, dust
    g.draw_rect(arr, 2, 40, 2, 2, WOOD_XD)
    g.draw_rect(arr, 90, 5, 2, 1, WOOD_L, 120)
    g.scratches(arr, seed + 1, 4, 4, light=False)
    g.clusters(arr, seed + 2, 7, dark=True, amount=10, size=2)
    grime(arr, seed + 3, 0.08)
    return arr


def filing_cabinet(seed: int) -> np.ndarray:
    arr = g.blank(32, 32, (0, 0, 0, 0))
    cast_shadow(arr, 2, 2, 29, 29, 60)
    panel(arr, 2, 2, 28, 28, PAINT, PAINT_L, PAINT_D)
    for index, y in enumerate((6, 13, 20)):
        g.draw_rect(arr, 4, y, 24, 6, (84, 95, 90))
        g.draw_line(arr, 4, y, 27, y, PAINT_D, 200)
        g.draw_line(arr, 4, y + 1, 27, y + 1, PAINT_L, 90)
        g.draw_rect(arr, 12, y + 2, 8, 2, STEEL_L, 210)
        g.draw_rect(arr, 12, y + 4, 8, 1, STEEL_XD, 180)
        g.draw_rect(arr, 6, y + 1, 5, 3, PAPER_D, 210)
        g.draw_line(arr, 7, y + 2, 9, y + 2, PAPER_XD, 200)
    g.draw_rect(arr, 4, 25, 24, 3, (78, 88, 84))
    g.draw_line(arr, 4, 26, 27, 26, PAINT_D, 160)
    # rust creeping from the bottom edge
    g.draw_rect(arr, 24, 26, 3, 2, g.RUST_DARK, 200)
    g.drip(arr, 25, 27, 3, g.RUST, 1, 90)
    g.draw_rect(arr, 4, 27, 2, 1, g.RUST_DARK, 150)
    g.scratches(arr, seed + 1, 3, 3, light=False)
    g.clusters(arr, seed + 2, 5, amount=8, size=1)
    return arr


def waiting_bench(seed: int) -> np.ndarray:
    arr = g.blank(64, 24, (0, 0, 0, 0))
    cast_shadow(arr, 1, 3, 62, 19, 55)
    panel(arr, 1, 3, 62, 18, WOOD_D, WOOD_L, WOOD_XD)
    for index, y in enumerate((4, 9, 14)):
        tone = WOOD if index != 1 else (88, 68, 47)
        g.draw_rect(arr, 4, y, 56, 4, tone)
        g.draw_line(arr, 4, y, 59, y, WOOD_L, 160)
        g.draw_line(arr, 4, y + 3, 59, y + 3, WOOD_XD, 200)
        g.draw_line(arr, 4, y + 4, 59, y + 4, (30, 22, 17), 150)
    for x in (2, 57):
        g.draw_rect(arr, x, 3, 5, 18, (54, 60, 59))
        g.draw_line(arr, x, 3, x + 4, 3, STEEL_D, 160)
        g.draw_rect(arr, x + 2, 6, 1, 1, STEEL_L, 180)
        g.draw_rect(arr, x + 2, 18, 1, 1, STEEL_L, 180)
    g.scratches(arr, seed + 1, 4, 5, light=False)
    g.scratches(arr, seed + 2, 2, 3)
    g.clusters(arr, seed + 3, 6, amount=9, size=1)
    return arr


def chair(seed: int) -> np.ndarray:
    arr = g.blank(20, 24, (0, 0, 0, 0))
    cast_shadow(arr, 2, 2, 17, 20, 55)
    # legs
    for x in (3, 14):
        g.draw_rect(arr, x, 18, 3, 4, STEEL_XD)
        g.draw_rect(arr, x, 18, 1, 3, STEEL_D, 170)
    # seat
    panel(arr, 3, 7, 14, 12, (104, 116, 108), (138, 149, 139), (68, 78, 73))
    g.draw_rect(arr, 5, 9, 10, 8, (110, 122, 113))
    g.draw_line(arr, 5, 9, 14, 9, (146, 157, 145), 120)
    # backrest
    panel(arr, 3, 2, 14, 5, (86, 98, 92), (120, 132, 123), (58, 67, 63))
    g.draw_line(arr, 5, 3, 5, 6, (52, 60, 57), 170)
    g.draw_line(arr, 9, 3, 9, 6, (52, 60, 57), 150)
    g.draw_line(arr, 13, 3, 13, 6, (52, 60, 57), 150)
    # armrests
    g.draw_rect(arr, 1, 8, 2, 9, STEEL_D)
    g.draw_rect(arr, 17, 8, 2, 9, STEEL_D)
    g.draw_line(arr, 1, 8, 2, 8, STEEL_L, 160)
    g.draw_line(arr, 17, 8, 18, 8, STEEL_L, 160)
    g.scratches(arr, seed + 1, 2, 3, light=False)
    g.clusters(arr, seed + 2, 4, amount=8, size=1)
    return arr


def hospital_bed(seed: int) -> np.ndarray:
    arr = g.blank(96, 48, (0, 0, 0, 0))
    cast_shadow(arr, 1, 4, 94, 42, 60)
    # frame
    panel(arr, 1, 4, 94, 40, STEEL_D, STEEL, STEEL_XD)
    # mattress
    g.draw_rect(arr, 5, 8, 86, 32, FABRIC_D)
    g.draw_rect(arr, 5, 8, 86, 30, FABRIC)
    g.draw_line(arr, 6, 9, 89, 9, FABRIC_L, 140)
    # pillow
    g.draw_rect(arr, 7, 12, 22, 25, SHEET_D, 160)
    g.draw_rect(arr, 7, 11, 22, 26, SHEET)
    g.draw_line(arr, 7, 11, 28, 11, (216, 214, 196), 170)
    g.draw_line(arr, 28, 12, 28, 36, SHEET_D, 200)
    g.draw_line(arr, 10, 15, 18, 33, (160, 162, 148), 70)
    # blanket
    g.draw_rect(arr, 45, 8, 46, 32, BLANKET)
    g.draw_line(arr, 45, 8, 90, 8, BLANKET_L, 190)
    g.draw_line(arr, 45, 8, 45, 39, BLANKET_D, 190)
    for x in (54, 68, 82):
        g.draw_line(arr, x, 10, x - 2, 38, BLANKET_D, 70)
    g.draw_line(arr, 47, 15, 89, 14, BLANKET_L, 60)
    g.draw_line(arr, 47, 30, 89, 31, BLANKET_D, 90)
    # folded sheet edge over the blanket
    g.draw_rect(arr, 42, 8, 6, 32, SHEET)
    g.draw_line(arr, 42, 8, 47, 8, (218, 216, 198), 160)
    g.draw_line(arr, 47, 9, 47, 39, SHEET_D, 200)
    # rails along both long sides
    for y in (5, 43):
        g.draw_rect(arr, 9, y, 76, 2, STEEL)
        g.draw_line(arr, 9, y, 84, y, STEEL_L, 190)
        g.draw_line(arr, 9, y + 1, 84, y + 1, STEEL_XD, 170)
        for x in (13, 46, 79):
            g.draw_rect(arr, x, y - 1, 2, 4, STEEL_D)
            g.draw_rect(arr, x, y - 1, 2, 1, STEEL_L, 120)
    # headboard and footboard
    g.draw_rect(arr, 1, 7, 4, 34, STEEL)
    g.draw_line(arr, 1, 7, 1, 40, STEEL_L, 190)
    g.draw_line(arr, 4, 7, 4, 40, STEEL_XD, 200)
    g.draw_rect(arr, 2, 11, 2, 2, STEEL_XD, 160)
    g.draw_rect(arr, 2, 34, 2, 2, STEEL_XD, 160)
    g.draw_rect(arr, 92, 9, 3, 30, STEEL_D)
    g.draw_line(arr, 92, 9, 92, 38, STEEL, 160)
    # wheels
    for x in (4, 88):
        g.draw_rect(arr, x, 42, 4, 3, STEEL_XD)
        g.draw_rect(arr, x + 1, 43, 2, 1, STEEL_D, 180)
    # wear and a faint old stain
    g.draw_rect(arr, 60, 20, 7, 4, (76, 84, 76), 110)
    g.draw_rect(arr, 63, 21, 4, 2, (68, 76, 69), 120)
    g.scratches(arr, seed + 1, 3, 4, light=False)
    grime(arr, seed + 2, 0.06)
    return arr


def metal_cabinet(seed: int) -> np.ndarray:
    arr = g.blank(32, 40, (0, 0, 0, 0))
    cast_shadow(arr, 2, 2, 29, 37, 55)
    panel(arr, 2, 2, 28, 36, PAINT, PAINT_L, PAINT_D)
    g.draw_rect(arr, 4, 4, 24, 32, (86, 98, 93))
    g.draw_line(arr, 15, 4, 15, 35, PAINT_D, 220)
    g.draw_line(arr, 16, 4, 16, 35, PAINT_L, 90)
    # two doors with handles
    for x0, x1 in ((5, 14), (17, 26)):
        g.draw_rect(arr, x0, 6, x1 - x0 + 1, 18, (94, 106, 101))
        g.draw_line(arr, x0, 6, x1, 6, PAINT_L, 110)
        g.draw_line(arr, x0, 23, x1, 23, PAINT_D, 180)
        g.draw_rect(arr, x1 - 3, 14, 2, 4, STEEL_L, 220)
        g.draw_rect(arr, x1 - 3, 17, 2, 1, STEEL_XD, 190)
    # small label plate and vent slots
    g.draw_rect(arr, 8, 27, 16, 5, PAPER_D, 220)
    g.draw_line(arr, 9, 29, 22, 29, PAPER_XD, 180)
    g.draw_line(arr, 9, 30, 18, 30, PAPER_XD, 150)
    for y in (34, 36):
        g.draw_line(arr, 6, y, 25, y, PAINT_D, 150)
    g.draw_rect(arr, 24, 34, 3, 3, g.RUST_DARK, 160)
    g.scratches(arr, seed + 1, 3, 4, light=False)
    return arr


def morgue_table(seed: int) -> np.ndarray:
    arr = g.blank(96, 32, (0, 0, 0, 0))
    cast_shadow(arr, 1, 3, 94, 27, 60)
    # legs
    for x in (5, 88):
        g.draw_rect(arr, x, 25, 3, 5, STEEL_XD)
        g.draw_rect(arr, x, 25, 1, 4, STEEL_D, 150)
    panel(arr, 1, 3, 94, 24, STEEL_D, STEEL, STEEL_XD)
    g.draw_rect(arr, 4, 6, 88, 18, STEEL)
    g.draw_line(arr, 5, 7, 90, 7, STEEL_L, 150)
    g.draw_line(arr, 5, 23, 90, 23, STEEL_XD, 190)
    # drainage grooves with a slight run-off to the right
    for y in (11, 16, 21):
        g.draw_line(arr, 6, y, 88, y - 1, STEEL_D, 170)
        g.draw_line(arr, 6, y + 1, 88, y, STEEL_L, 60)
    # drain at the low end
    fill_ellipse(arr, 88, 16, 4, 4, STEEL_XD)
    fill_ellipse(arr, 88, 16, 2.5, 2.5, (28, 34, 35))
    ring(arr, 88, 16, 4.5, 4.5, STEEL_L, 120)
    # old blood residue in the grooves
    for x0, x1, y in ((10, 23, 11), (30, 37, 16), (52, 61, 11)):
        for x in range(x0, x1):
            if (x * 7 + y) % 5 != 0:
                arr[y, x, :3] = (48, 11, 12)
                arr[y, x, 3] = 200
    g.draw_rect(arr, 16, 10, 3, 1, (58, 15, 16), 170)
    g.draw_rect(arr, 44, 16, 2, 1, (58, 15, 16), 160)
    g.draw_rect(arr, 66, 21, 4, 1, (54, 13, 14), 150)
    # water droplets
    for x, y in ((44, 9), (58, 18), (72, 10), (80, 21)):
        g.draw_rect(arr, x, y, 1, 1, (188, 198, 193), 140)
    g.scratches(arr, seed + 1, 4, 5)
    g.clusters(arr, seed + 2, 7, amount=8, size=1)
    return arr


def body_bag(seed: int) -> np.ndarray:
    arr = g.blank(64, 24, (0, 0, 0, 0))
    cast_shadow(arr, 1, 3, 62, 19, 55)
    # rounded rubber bag
    g.draw_rect(arr, 3, 4, 56, 16, RUBBER)
    g.draw_rect(arr, 2, 6, 60, 12, RUBBER)
    cut_corners(arr, 2, 3, 60, 18, 2)
    outline(arr, 2, 3, 60, 18, (18, 21, 21))
    g.draw_line(arr, 4, 4, 59, 4, RUBBER_L, 130)
    g.draw_line(arr, 3, 19, 60, 19, RUBBER_D, 200)
    # subtle body silhouette, no detail
    g.draw_rect(arr, 16, 6, 24, 9, (44, 48, 48), 110)
    g.draw_line(arr, 16, 6, 39, 6, (54, 59, 58), 90)
    g.draw_line(arr, 16, 14, 39, 14, (30, 33, 33), 120)
    # folds at both ends
    for x in (8, 52):
        g.draw_line(arr, x, 5, x + 2, 18, RUBBER_D, 160)
        g.draw_line(arr, x + 2, 6, x + 4, 17, (50, 54, 54), 80)
    # zipper along the middle
    for x in range(5, 59, 2):
        g.draw_rect(arr, x, 12, 1, 1, (104, 108, 103), 200)
        g.draw_rect(arr, x + 1, 13, 1, 1, (60, 64, 62), 160)
    g.draw_rect(arr, 39, 11, 3, 5, STEEL_L, 230)
    g.draw_rect(arr, 40, 13, 1, 2, STEEL_XD, 200)
    # toe tag
    g.draw_line(arr, 50, 14, 52, 18, (150, 146, 128), 180)
    g.draw_rect(arr, 51, 17, 8, 5, PAPER)
    g.draw_rect(arr, 51, 17, 8, 1, (216, 210, 188), 160)
    g.draw_line(arr, 52, 19, 57, 19, PAPER_XD, 160)
    g.draw_line(arr, 52, 20, 55, 20, PAPER_XD, 140)
    g.draw_rect(arr, 52, 19, 1, 1, RED, 190)
    g.scratches(arr, seed + 1, 3, 4, light=False)
    return arr


def sink(seed: int) -> np.ndarray:
    arr = g.blank(32, 32, (0, 0, 0, 0))
    cast_shadow(arr, 2, 5, 28, 24, 55)
    panel(arr, 3, 7, 26, 22, STEEL, STEEL_L, STEEL_XD)
    fill_ellipse(arr, 16, 18, 9.5, 7.5, STEEL_D)
    fill_ellipse(arr, 16, 18, 8.5, 6.5, (58, 66, 65))
    fill_ellipse(arr, 16, 19, 7.0, 5.0, (44, 51, 51))
    # standing water and grime ring
    fill_ellipse(arr, 16, 20, 5.0, 3.0, (54, 62, 60), 190)
    ring(arr, 16, 18, 8.0, 6.0, (92, 100, 95), 130)
    g.draw_rect(arr, 15, 18, 2, 2, STEEL_XD)
    g.draw_rect(arr, 15, 18, 1, 1, (22, 27, 28))
    # faucet
    g.draw_rect(arr, 13, 3, 6, 5, STEEL_D)
    g.draw_rect(arr, 14, 3, 4, 2, STEEL)
    g.draw_rect(arr, 15, 5, 2, 3, STEEL_L, 220)
    g.draw_rect(arr, 9, 4, 3, 2, STEEL_D)
    g.draw_rect(arr, 20, 4, 3, 2, STEEL_D)
    g.draw_line(arr, 9, 4, 11, 4, STEEL_L, 140)
    g.draw_line(arr, 20, 4, 22, 4, STEEL_L, 140)
    g.draw_rect(arr, 14, 6, 4, 1, g.RUST_DARK, 150)
    g.drip(arr, 17, 8, 4, g.RUST, 1, 70)
    g.draw_rect(arr, 6, 26, 3, 2, g.RUST_DARK, 160)
    g.scratches(arr, seed + 1, 3, 3)
    return arr


# --- devices ----------------------------------------------------------------

def fusebox(seed: int) -> np.ndarray:
    arr = g.blank(32, 32, (0, 0, 0, 0))
    # conduits running into the ceiling edge
    for x in (6, 14, 22):
        g.draw_rect(arr, x, 0, 3, 5, STEEL_D)
        g.draw_rect(arr, x + 1, 0, 1, 4, STEEL, 200)
    cast_shadow(arr, 3, 3, 27, 27, 60)
    panel(arr, 3, 3, 26, 26, (86, 96, 91), PAINT_L, PAINT_D)
    g.draw_rect(arr, 5, 5, 22, 22, (78, 88, 84))
    g.draw_line(arr, 5, 5, 26, 5, (54, 63, 60), 200)
    # small gauge and breaker rows
    fill_ellipse(arr, 10, 11, 3.5, 3.5, (34, 40, 41))
    ring(arr, 10, 11, 3.5, 3.5, STEEL_L, 110)
    g.draw_line(arr, 10, 11, 12, 9, (170, 54, 40), 220)
    for y in (10, 14, 18):
        g.draw_rect(arr, 15, y, 9, 2, (44, 50, 50))
        g.draw_rect(arr, 15, y, 5, 2, (110, 118, 111), 200)
        g.draw_rect(arr, 15, y + 1, 9, 1, (26, 31, 32), 180)
    # warning label with diagonal stripes
    g.draw_rect(arr, 5, 20, 15, 9, WARN)
    outline(arr, 5, 20, 15, 9, (44, 38, 20))
    for offset in range(-8, 16, 5):
        g.draw_line(arr, 6 + offset, 28, 13 + offset, 20, (44, 38, 20), 170)
    g.draw_line(arr, 6, 21, 18, 21, (196, 168, 86), 90)
    g.draw_rect(arr, 21, 22, 3, 6, STEEL_L)
    g.draw_rect(arr, 21, 24, 3, 2, STEEL_XD)
    # rust dribbles
    g.draw_rect(arr, 26, 24, 2, 2, g.RUST_DARK, 180)
    g.drip(arr, 26, 26, 3, g.RUST, 1, 80)
    g.scratches(arr, seed + 1, 3, 3, light=False)
    return arr


def generator(seed: int) -> np.ndarray:
    arr = g.blank(32, 40, (0, 0, 0, 0))
    cast_shadow(arr, 2, 5, 29, 33, 60)
    # exhaust stack
    g.draw_rect(arr, 5, 1, 5, 7, STEEL_D)
    g.draw_rect(arr, 6, 1, 3, 6, STEEL)
    g.draw_rect(arr, 5, 1, 5, 2, STEEL_XD)
    g.draw_rect(arr, 6, 1, 2, 1, (170, 178, 172), 140)
    panel(arr, 2, 5, 28, 31, (76, 89, 78), (104, 118, 102), (52, 62, 54))
    # vent grille
    g.draw_rect(arr, 5, 10, 11, 17, (58, 69, 60))
    for y in range(12, 26, 3):
        g.draw_line(arr, 6, y, 14, y, (38, 46, 41), 210)
        g.draw_line(arr, 6, y + 1, 14, y + 1, (96, 109, 95), 90)
    # control panel
    g.draw_rect(arr, 18, 9, 10, 18, (52, 60, 58))
    outline(arr, 18, 9, 10, 18, (33, 39, 39))
    fill_ellipse(arr, 22, 13, 2.5, 2.5, (34, 40, 40))
    ring(arr, 22, 13, 2.5, 2.5, STEEL_L, 130)
    g.draw_line(arr, 22, 13, 24, 12, (176, 60, 44), 220)
    fill_ellipse(arr, 22, 19, 2.0, 2.0, (30, 36, 36))
    g.draw_rect(arr, 21, 18, 2, 1, (108, 160, 130), 200)
    g.draw_rect(arr, 20, 23, 6, 2, (134, 52, 40))
    g.draw_line(arr, 20, 23, 25, 23, (184, 84, 64), 160)
    # fuel cap and warning stripe
    fill_ellipse(arr, 10, 30, 2.5, 2.0, STEEL_D)
    ring(arr, 10, 30, 2.5, 2.0, STEEL_L, 100)
    g.draw_rect(arr, 3, 32, 26, 3, WARN)
    for x in range(3, 29, 4):
        g.draw_rect(arr, x, 32, 2, 3, (42, 36, 22))
    g.draw_line(arr, 3, 32, 28, 32, (196, 168, 86), 110)
    # casters and oil stain
    for x in (4, 23):
        g.draw_rect(arr, x, 37, 4, 3, STEEL_XD)
        g.draw_rect(arr, x + 1, 38, 2, 1, STEEL_D, 150)
    g.draw_rect(arr, 12, 37, 7, 1, (24, 27, 24), 120)
    g.draw_rect(arr, 21, 36, 3, 1, (24, 27, 24), 100)
    g.scratches(arr, seed + 1, 4, 4, light=False)
    return arr


def iv_stand(seed: int) -> np.ndarray:
    arr = g.blank(16, 44, (0, 0, 0, 0))
    cast_shadow(arr, 2, 33, 13, 8, 55)
    # base with casters
    fill_ellipse(arr, 8, 38, 6, 3.5, STEEL_D)
    ring(arr, 8, 38, 6, 3.5, STEEL_L, 110)
    for x in (3, 12):
        g.draw_rect(arr, x, 40, 2, 2, STEEL_XD)
    # pole
    g.draw_rect(arr, 7, 10, 2, 29, STEEL)
    g.draw_line(arr, 7, 10, 7, 38, STEEL_L, 180)
    g.draw_line(arr, 8, 10, 8, 38, STEEL_XD, 150)
    # bag
    g.draw_rect(arr, 4, 2, 9, 14, (0, 0, 0), 50)
    g.draw_rect(arr, 4, 2, 9, 14, (128, 138, 130))
    g.draw_rect(arr, 4, 2, 9, 14, (128, 138, 130))
    outline(arr, 4, 2, 9, 14, (58, 64, 62))
    g.draw_rect(arr, 5, 9, 7, 6, (96, 116, 106))
    g.draw_line(arr, 5, 9, 11, 9, (118, 140, 128), 160)
    g.draw_line(arr, 5, 3, 11, 3, (158, 168, 159), 160)
    g.draw_rect(arr, 6, 1, 5, 1, STEEL_L, 200)
    # medical label with a red cross, so the stand reads at a glance
    g.draw_rect(arr, 6, 4, 5, 5, PAPER, 235)
    g.draw_rect(arr, 6, 4, 5, 1, (214, 208, 186), 170)
    g.draw_rect(arr, 8, 5, 1, 3, RED, 235)
    g.draw_rect(arr, 7, 6, 3, 1, RED, 235)
    g.draw_line(arr, 8, 16, 12, 24, (74, 88, 82), 160)
    g.draw_line(arr, 12, 24, 12, 34, (74, 88, 82), 140)
    ring(arr, 12, 30, 1.5, 1.5, STEEL_L, 160)
    g.scratches(arr, seed + 1, 2, 3, light=False)
    return arr


def wheelchair(seed: int) -> np.ndarray:
    arr = g.blank(32, 32, (0, 0, 0, 0))
    cast_shadow(arr, 1, 3, 30, 27, 55)
    # large rear wheels: vertical ellipses seen from above
    for cx in (5, 27):
        fill_ellipse(arr, cx, 16, 4.0, 9.0, (26, 29, 29))
        fill_ellipse(arr, cx, 16, 2.6, 7.2, (62, 67, 64))
        fill_ellipse(arr, cx, 16, 1.4, 4.0, (34, 38, 38))
        ring(arr, cx, 16, 4.0, 9.0, (104, 110, 103), 130)
        ring(arr, cx, 16, 2.6, 7.2, (40, 45, 44), 180)
        g.draw_line(arr, cx, 7, cx, 25, (86, 92, 88), 90)
        g.draw_line(arr, cx - 2, 9, cx + 2, 23, (80, 86, 82), 60)
    # seat and backrest
    panel(arr, 7, 9, 18, 15, (62, 70, 67), (92, 101, 96), (44, 51, 49))
    g.draw_rect(arr, 9, 11, 14, 11, (52, 60, 58))
    for y in (14, 18):
        g.draw_line(arr, 9, y, 22, y, (42, 49, 47), 160)
    panel(arr, 9, 4, 14, 5, (78, 88, 83), (110, 120, 113), (48, 56, 53))
    g.draw_line(arr, 12, 5, 12, 8, (46, 53, 51), 160)
    g.draw_line(arr, 19, 5, 19, 8, (46, 53, 51), 160)
    # push handles
    g.draw_rect(arr, 10, 1, 3, 3, STEEL_D)
    g.draw_rect(arr, 19, 1, 3, 3, STEEL_D)
    g.draw_line(arr, 10, 1, 12, 1, STEEL_L, 130)
    g.draw_line(arr, 19, 1, 21, 1, STEEL_L, 130)
    # armrests
    g.draw_rect(arr, 7, 12, 2, 9, STEEL_L)
    g.draw_rect(arr, 23, 12, 2, 9, STEEL_D)
    # footrests
    g.draw_rect(arr, 11, 25, 4, 5, STEEL_D)
    g.draw_rect(arr, 17, 25, 4, 5, STEEL_D)
    g.draw_line(arr, 11, 25, 14, 25, STEEL_L, 130)
    g.draw_line(arr, 17, 25, 20, 25, STEEL_L, 130)
    g.draw_line(arr, 12, 27, 13, 29, STEEL_XD, 160)
    g.draw_line(arr, 18, 27, 19, 29, STEEL_XD, 160)
    g.scratches(arr, seed + 1, 3, 4, light=False)
    g.clusters(arr, seed + 2, 4, amount=7, size=1)
    return arr


def elevator_panel(seed: int) -> np.ndarray:
    arr = g.blank(16, 24, (0, 0, 0, 0))
    panel(arr, 2, 1, 12, 22, STEEL_D, STEEL_L, STEEL_XD)
    g.draw_rect(arr, 4, 3, 8, 18, (78, 86, 85))
    g.draw_line(arr, 4, 3, 11, 3, (60, 68, 67), 190)
    # buttons with lit rims
    for cy, lit in ((7, True), (13, False)):
        fill_ellipse(arr, 8, cy, 2.5, 2.5, (34, 40, 40))
        ring(arr, 8, cy, 2.5, 2.5, STEEL_L, 130)
        color = (196, 64, 46) if lit else (128, 134, 128)
        fill_ellipse(arr, 8, cy, 1.5, 1.5, color)
        if lit:
            g.draw_rect(arr, 7, cy - 3, 2, 1, STEEL_L, 140)
    g.draw_rect(arr, 8, 15, 2, 1, STEEL_L, 120)
    # indicator and screws
    g.draw_rect(arr, 6, 18, 4, 2, (52, 30, 24))
    g.draw_rect(arr, 7, 18, 2, 1, (184, 74, 52), 200)
    for x, y in ((3, 2), (12, 2), (3, 20), (12, 20)):
        g.draw_rect(arr, x, y, 1, 1, STEEL_L, 170)
    g.scratches(arr, seed + 1, 2, 3, light=False)
    return arr


# --- barriers ---------------------------------------------------------------

def boarded_door(seed: int) -> np.ndarray:
    arr = g.blank(64, 32, (0, 0, 0, 0))
    # door body
    panel(arr, 1, 1, 62, 30, (54, 50, 44), (92, 86, 72), (30, 28, 25))
    g.draw_rect(arr, 4, 4, 56, 24, (66, 60, 51))
    for x in (20, 43):
        g.draw_line(arr, x, 4, x, 27, (38, 34, 29), 190)
    g.draw_line(arr, 4, 4, 59, 4, (92, 86, 72), 120)
    # planks nailed across
    for index, (y, tone) in enumerate(((7, WOOD), (14, (86, 66, 45)), (21, WOOD))):
        g.draw_rect(arr, 2, y, 60, 5, tone)
        g.draw_line(arr, 2, y, 61, y, WOOD_L, 180)
        g.draw_line(arr, 2, y + 4, 61, y + 4, WOOD_XD, 220)
        g.draw_line(arr, 2, y + 1, 61, y + 1 + index % 2, (70, 53, 36), 110)
        for x in (6, 22, 40, 56):
            g.draw_rect(arr, x, y + 1, 2, 2, STEEL_L, 200)
            g.draw_rect(arr, x + 1, y + 2, 1, 1, STEEL_XD, 190)
    # nails shadow and splintered ends
    for y in (7, 14, 21):
        g.draw_rect(arr, 1, y, 1, 5, WOOD_XD, 200)
        g.draw_rect(arr, 61, y + 1, 1, 3, WOOD_XD, 180)
    # warning note
    g.draw_rect(arr, 24, 15, 15, 9, PAPER)
    outline(arr, 24, 15, 15, 9, PAPER_XD)
    g.draw_line(arr, 26, 17, 37, 17, PAPER_XD, 180)
    g.draw_line(arr, 26, 19, 34, 19, PAPER_XD, 160)
    g.draw_rect(arr, 26, 20, 5, 2, RED, 170)
    g.draw_rect(arr, 24, 15, 15, 1, (222, 214, 190), 130)
    g.scratches(arr, seed + 1, 4, 4, light=False)
    g.clusters(arr, seed + 2, 5, amount=8, size=1)
    return arr


def observation_window(seed: int) -> np.ndarray:
    arr = g.blank(64, 32, (0, 0, 0, 0))
    panel(arr, 1, 3, 62, 26, (52, 56, 55), STEEL_D, STEEL_XD)
    g.draw_rect(arr, 5, 6, 54, 20, (26, 32, 34))
    g.draw_rect(arr, 6, 7, 52, 18, TEAL_GLASS)
    # reflections
    g.draw_line(arr, 8, 22, 22, 9, (74, 106, 108), 80)
    g.draw_line(arr, 11, 23, 25, 10, (66, 96, 99), 60)
    g.draw_line(arr, 30, 21, 44, 9, (64, 92, 95), 55)
    # wire mesh
    for x in range(10, 60, 9):
        g.draw_line(arr, x, 7, x, 24, (34, 43, 45), 160)
    g.draw_line(arr, 6, 15, 57, 15, (34, 43, 45), 160)
    g.draw_line(arr, 6, 16, 57, 16, (58, 74, 76), 70)
    # crack and a smudged handprint
    g.draw_line(arr, 14, 24, 19, 18, (18, 24, 25), 200)
    g.draw_line(arr, 19, 18, 18, 13, (22, 28, 29), 180)
    g.draw_line(arr, 19, 18, 24, 15, (22, 28, 29), 160)
    g.draw_rect(arr, 42, 10, 3, 5, (70, 96, 96), 80)
    g.draw_rect(arr, 44, 12, 3, 3, (70, 96, 96), 60)
    # frame rivets and grime
    for x in range(4, 62, 12):
        g.draw_rect(arr, x, 3, 1, 1, STEEL_L, 130)
        g.draw_rect(arr, x, 28, 1, 1, STEEL_L, 110)
    g.draw_rect(arr, 2, 26, 60, 2, (36, 42, 42), 120)
    g.scratches(arr, seed + 1, 3, 4, light=False)
    return arr


# --- items ------------------------------------------------------------------

def cassette(seed: int) -> np.ndarray:
    arr = g.blank(16, 16, (0, 0, 0, 0))
    g.draw_rect(arr, 1, 3, 14, 11, (0, 0, 0), 60)
    panel(arr, 1, 2, 14, 11, (40, 42, 42), (72, 75, 73), (22, 24, 24))
    # reel windows
    for x in (3, 9):
        fill_ellipse(arr, x + 2, 7, 2.5, 2.5, (24, 27, 27))
        ring(arr, x + 2, 7, 2.5, 2.5, (118, 120, 112), 160)
        fill_ellipse(arr, x + 2, 7, 0.8, 0.8, (84, 86, 80))
    # label strip
    g.draw_rect(arr, 5, 3, 6, 6, PAPER, 235)
    g.draw_line(arr, 6, 5, 9, 5, PAPER_XD, 150)
    g.draw_line(arr, 6, 7, 8, 7, PAPER_XD, 130)
    # screws and bottom seam
    g.draw_rect(arr, 2, 11, 1, 1, STEEL_L, 180)
    g.draw_rect(arr, 13, 11, 1, 1, STEEL_L, 180)
    g.draw_line(arr, 2, 12, 13, 12, (26, 29, 29), 200)
    g.scratches(arr, seed + 1, 1, 2)
    return arr


def key_item(seed: int) -> np.ndarray:
    arr = g.blank(16, 16, (0, 0, 0, 0))
    # bow with a hole
    fill_ellipse(arr, 5, 5, 4.0, 4.0, BRASS_D)
    fill_ellipse(arr, 5, 5, 3.0, 3.0, BRASS)
    fill_ellipse(arr, 5, 5, 1.4, 1.4, (0, 0, 0), 0)
    ring(arr, 5, 5, 4.0, 4.0, BRASS_L, 150)
    # shaft
    g.draw_line(arr, 7, 7, 13, 13, BRASS_D, 255)
    g.draw_line(arr, 7, 8, 12, 13, BRASS, 255)
    g.draw_line(arr, 7, 7, 12, 12, BRASS_L, 160)
    # teeth
    g.draw_rect(arr, 11, 12, 2, 3, BRASS)
    g.draw_rect(arr, 13, 10, 2, 3, BRASS)
    g.draw_rect(arr, 13, 12, 1, 1, BRASS_D)
    # outline-ish dark edges
    g.draw_line(arr, 8, 8, 14, 14, (72, 54, 25), 120)
    g.scratches(arr, seed + 1, 1, 2, light=False)
    return arr


def fuse_item(seed: int) -> np.ndarray:
    arr = g.blank(16, 16, (0, 0, 0, 0))
    g.draw_rect(arr, 6, 3, 4, 10, (0, 0, 0), 50)
    panel(arr, 6, 2, 4, 12, (182, 176, 152), (214, 208, 182), (128, 123, 104))
    # metal caps
    g.draw_rect(arr, 5, 2, 6, 3, STEEL)
    g.draw_rect(arr, 5, 11, 6, 3, STEEL)
    g.draw_rect(arr, 5, 2, 6, 1, STEEL_L, 200)
    g.draw_rect(arr, 5, 11, 6, 1, STEEL_L, 170)
    g.draw_rect(arr, 6, 4, 4, 1, (150, 143, 120), 180)
    g.draw_rect(arr, 6, 9, 4, 1, (150, 143, 120), 180)
    # rating band
    g.draw_rect(arr, 6, 6, 4, 2, (128, 62, 44), 220)
    g.draw_line(arr, 6, 7, 9, 7, (178, 96, 68), 150)
    # wire stubs
    g.draw_line(arr, 8, 0, 8, 2, STEEL_L, 220)
    g.draw_line(arr, 8, 14, 8, 15, STEEL_L, 220)
    g.scratches(arr, seed + 1, 1, 2, light=False)
    return arr


def note_item(seed: int) -> np.ndarray:
    arr = g.blank(16, 16, (0, 0, 0, 0))
    g.draw_rect(arr, 4, 3, 10, 12, (0, 0, 0), 55)
    g.draw_rect(arr, 3, 2, 10, 12, PAPER_D)
    g.draw_rect(arr, 3, 2, 10, 12, PAPER)
    outline(arr, 3, 2, 10, 12, PAPER_XD)
    # folded corner
    fill_triangle = g.fill_polygon
    fill_triangle(arr, [(9, 2), (12, 2), (12, 5)], PAPER_D, 235)
    for step in range(4):
        g.draw_line(arr, 9 + step, 2, 12, 5 - step, PAPER_D, 220)
    g.draw_rect(arr, 10, 2, 3, 2, (176, 170, 146), 200)
    # text lines
    for y in range(5, 11, 2):
        g.draw_line(arr, 5, y, 11, y, (116, 110, 92), 190)
    g.draw_line(arr, 5, 10, 8, 10, (116, 110, 92), 170)
    # red stamp
    g.draw_rect(arr, 8, 9, 4, 3, (128, 52, 44), 170)
    g.draw_line(arr, 9, 10, 10, 10, (82, 30, 26), 200)
    # shadow at the bottom edge and a pin
    g.draw_line(arr, 4, 13, 12, 13, PAPER_XD, 160)
    g.draw_rect(arr, 7, 1, 1, 1, STEEL_L, 180)
    return arr


# --- preview ----------------------------------------------------------------

def make_preview() -> None:
    PREVIEW.mkdir(parents=True, exist_ok=True)
    font = ImageFont.truetype(FONT_PATH, 13)
    font_small = ImageFont.truetype(FONT_PATH, 11)
    title_font = ImageFont.truetype(FONT_PATH, 26)
    zoom = 4
    padding = 16
    gap = 14
    bg = (14, 17, 18)

    sections: dict[str, list[dict]] = {}
    for entry in MANIFEST:
        sections.setdefault(entry["category"], []).append(entry)

    order = ["furniture", "devices", "items", "barriers"]
    titles = {
        "furniture": "МЕБЕЛЬ  ·  FURNITURE",
        "devices": "ПРИБОРЫ  ·  DEVICES",
        "items": "ПРЕДМЕТЫ  ·  ITEMS",
        "barriers": "ЗАГРАЖДЕНИЯ  ·  BARRIERS",
    }

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
        section_gap = 44 if category == "items" else gap
        for entry in entries:
            w, h = entry["size"]
            dw, dh = w * zoom, h * zoom
            if x + dw + padding > padding + max_width:
                x = padding
                y += row_height + 34
                row_height = 0
            placed.append((entry, x, y, dw, dh))
            x += dw + section_gap
            row_height = max(row_height, dh)
        y += row_height + 84
        layout.append((category, placed))

    total_height = y + padding
    sheet = Image.new("RGB", (width, total_height), bg)
    draw = ImageDraw.Draw(sheet)
    draw.text((padding, 14), "ЭТАЖ, КОТОРОГО НЕТ — texture pack / batch 2",
              font=title_font, fill=(220, 216, 203))
    draw.text((padding, 45),
              "props, furniture, devices and items · 4x preview · matches batch 1 palette",
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

    sheet.save(PREVIEW / "batch2_props.png")
    print(f"preview -> {PREVIEW / 'batch2_props.png'} ({sheet.size[0]}x{sheet.size[1]})")


# --- build ------------------------------------------------------------------

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
    batches = sorted({entry.get("batch", 1) for entry in merged} | {2})
    path.write_text(
        json.dumps({"version": 1, "batches": batches, "assets": merged},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def save(name: str, arr: np.ndarray, category: str, description: str,
         tileable: bool = False) -> None:
    folder = TEX / category
    folder.mkdir(parents=True, exist_ok=True)
    image = g.quantize(g.to_image(arr), colors=32)
    image.save(folder / f"{name}.png")
    MANIFEST.append({
        "id": name,
        "file": f"assets/textures/{category}/{name}.png",
        "size": list(image.size),
        "category": category,
        "tileable": tileable,
        "batch": 2,
        "description": description,
    })


def build() -> None:
    furniture = [
        ("prop_reception_desk", reception_desk(501), "Стойка приёмного покоя с журналом и монитором"),
        ("prop_filing_cabinet", filing_cabinet(502), "Картотека на три ящика"),
        ("prop_waiting_bench", waiting_bench(503), "Деревянная скамья ожидания"),
        ("prop_chair", chair(504), "Стул с металлическими ножками"),
        ("prop_hospital_bed", hospital_bed(505), "Койка с подушкой, одеялом и поручнями"),
        ("prop_metal_cabinet", metal_cabinet(506), "Медицинский шкаф с двумя дверцами"),
        ("prop_morgue_table", morgue_table(507), "Стол морга с желобами и сливом"),
        ("prop_body_bag", body_bag(508), "Мешок для тела с молнией и биркой"),
        ("prop_sink", sink(509), "Раковина с краном и ржавчиной"),
    ]
    for name, arr, description in furniture:
        save(name, arr, "furniture", description)

    devices = [
        ("prop_fusebox", fusebox(601), "Электрощит с предохранителями и предупреждением"),
        ("prop_generator", generator(602), "Генератор с патрубком и щитком"),
        ("prop_iv_stand", iv_stand(603), "Штатив капельницы с пакетом"),
        ("prop_wheelchair", wheelchair(604), "Кресло-каталка, вид сверху"),
        ("prop_elevator_panel", elevator_panel(605), "Панель вызова лифта с кнопками"),
    ]
    for name, arr, description in devices:
        save(name, arr, "devices", description)

    barriers = [
        ("prop_boarded_door", boarded_door(701), "Забитая дверь с предупреждением"),
        ("prop_observation_window", observation_window(702), "Смотровое стекло с сеткой и трещиной"),
    ]
    for name, arr, description in barriers:
        save(name, arr, "barriers", description)

    items = [
        ("item_cassette", cassette(801), "Аудиокассета с записью"),
        ("item_key", key_item(802), "Служебный ключ"),
        ("item_fuse", fuse_item(803), "Керамический предохранитель"),
        ("item_note", note_item(804), "Записка с красным штампом"),
    ]
    for name, arr, description in items:
        save(name, arr, "items", description)

    write_manifest(MANIFEST)
    make_preview()


if __name__ == "__main__":
    build()