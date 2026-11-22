#!/usr/bin/env python3
"""Compose a gameplay mock with the batch 3 character sprites at scale."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mock_props as mp

ROOT = Path(__file__).resolve().parent.parent
TEX = ROOT / "assets" / "textures"
OUT = ROOT / "assets" / "previews" / "batch3_mock.png"


def sprite(name: str, row: int, column: int, fw: int, fh: int) -> Image.Image:
    sheet = Image.open(TEX / "characters" / f"{name}.png").convert("RGBA")
    return sheet.crop((column * fw, row * fh, (column + 1) * fw, (row + 1) * fh))


def add_red_glow(image: Image.Image, cx: int, cy: int, radius: int,
                 strength: float = 0.35) -> Image.Image:
    arr = np.array(image.convert("RGB"), dtype=np.float32) / 255.0
    h, w = arr.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    glow = np.clip(1.0 - dist / radius, 0.0, 1.0) ** 2 * strength
    arr[:, :, 0] += glow * 0.46
    arr[:, :, 1] += glow * 0.05
    arr[:, :, 2] += glow * 0.03
    return Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8), "RGB")


def build() -> Image.Image:
    scene = mp.build_scene()

    # Mark faces right, holding the flashlight; the nurse walks in from the right.
    player = sprite("player_sheet", 2, 0, 20, 32)
    scene.alpha_composite(player, (230, 198))
    nurse = sprite("nurse_chase_sheet", 1, 2, 24, 38)
    scene.alpha_composite(nurse, (468, 192))  # feet share Mark's ground line

    mp.add_flashlight_cone(scene, (248, 220))
    image = mp.apply_lighting(scene, (240, 214))
    image = add_red_glow(image, 480 * 2, 211 * 2, 120, 0.32)
    return image


if __name__ == "__main__":
    image = build()
    image.save(OUT)
    print(f"mock -> {OUT} ({image.size[0]}x{image.size[1]})")