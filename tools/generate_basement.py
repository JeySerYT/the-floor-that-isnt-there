#!/usr/bin/env python3
"""Generate batch 5: basement visuals for «Этаж, которого нет».

Archive and boiler floors, a shelf, a tank, the hall staircase and a rubble
pile. Uses the same palette helpers as the earlier batches, so the basement
matches the hospital above.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_textures as g

ROOT = g.ROOT
TEX = g.TEX
MANIFEST: list[dict] = []


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
        "batch": 5,
        "description": description,
    })


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
    batches = sorted({entry.get("batch", 1) for entry in merged} | {5})
    path.write_text(
        json.dumps({"version": 1, "batches": batches, "assets": merged},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def floor_archive() -> np.ndarray:
    arr = g.floor_tiles((78, 70, 56), 910, variation=4, damage="stain")
    for x, y, w, h in ((3, 7, 5, 2), (19, 22, 4, 2), (26, 5, 3, 1), (11, 15, 2, 1)):
        g.draw_rect(arr, x, y, w, h, (172, 162, 132), 210)
        g.draw_rect(arr, x, y + h, w, 1, (110, 102, 82), 160)
    g.add_grime(arr, 913, 0.2, 3)
    return arr


def floor_boiler() -> np.ndarray:
    arr = g.floor_tiles((58, 53, 46), 911, variation=5, damage="wet")
    g.add_grime(arr, 914, 0.28, 3)
    for _ in range(6):
        g.draw_line(arr, 4, 3, 27, 28, (112, 66, 38), 90)
        g.draw_line(arr, 27, 2, 5, 29, (88, 52, 30), 70)
    g.draw_rect(arr, 12, 9, 3, 2, (138, 84, 44), 200)
    g.draw_rect(arr, 21, 19, 4, 2, (124, 76, 40), 190)
    return arr


def prop_shelf() -> np.ndarray:
    arr = g.blank(64, 32)
    g.draw_rect(arr, 1, 1, 62, 30, (48, 54, 54))
    g.draw_rect(arr, 2, 2, 60, 28, (78, 84, 81))
    for row_y in (5, 18):
        g.draw_rect(arr, 3, row_y, 58, 9, (42, 48, 47))
        for index in range(6):
            x = 5 + index * 9
            height = 5 + index % 3
            g.draw_rect(arr, x, row_y + 9 - height, 7, height, (178, 168, 138))
            g.draw_rect(arr, x + 1, row_y + 10 - height, 5, 1, (118, 110, 88))
    g.draw_rect(arr, 0, 0, 64, 2, (104, 112, 107))
    g.draw_rect(arr, 0, 30, 64, 2, (34, 39, 39))
    g.add_grime(arr, 921, 0.18, 3)
    return arr


def prop_boiler_tank() -> np.ndarray:
    arr = g.blank(48, 64)
    g.draw_rect(arr, 6, 8, 36, 52, (68, 64, 56))
    g.draw_rect(arr, 8, 10, 32, 48, (96, 88, 74))
    g.draw_rect(arr, 10, 12, 6, 44, (122, 112, 94))
    g.draw_rect(arr, 30, 12, 8, 44, (72, 66, 54))
    g.draw_rect(arr, 6, 6, 36, 4, (52, 48, 42))
    g.draw_rect(arr, 6, 58, 36, 4, (46, 42, 37))
    g.draw_rect(arr, 20, 0, 8, 8, (82, 78, 68))
    g.draw_rect(arr, 22, 0, 4, 8, (54, 51, 45))
    g.draw_rect(arr, 0, 26, 6, 6, (90, 60, 38))
    g.draw_rect(arr, 42, 34, 6, 6, (90, 60, 38))
    for y in (20, 33, 46):
        g.draw_rect(arr, 9, y, 30, 1, (134, 76, 42), 180)
    g.add_grime(arr, 922, 0.24, 3)
    return arr


def prop_stairs() -> np.ndarray:
    arr = g.blank(64, 48)
    g.draw_rect(arr, 0, 0, 64, 48, (58, 63, 60))
    for index in range(6):
        y = 2 + index * 7
        tone = 86 - index * 9
        g.draw_rect(arr, 4, y, 56, 6, (tone, tone + 3, tone))
        g.draw_rect(arr, 4, y, 56, 1, (tone + 26, tone + 28, tone + 24))
        g.draw_rect(arr, 4, y + 6, 56, 1, (20, 23, 23))
    g.draw_rect(arr, 2, 0, 3, 48, (118, 126, 120))
    g.draw_rect(arr, 59, 0, 3, 48, (98, 106, 102))
    g.draw_rect(arr, 4, 40, 56, 8, (10, 12, 13))
    g.add_grime(arr, 923, 0.16, 3)
    return arr


def prop_collapse() -> np.ndarray:
    arr = g.blank(96, 48)
    rng = np.random.default_rng(924)
    for _ in range(26):
        x = int(rng.integers(2, 86))
        y = int(rng.integers(12, 42))
        w = int(rng.integers(4, 14))
        h = int(rng.integers(3, 9))
        tone = int(rng.integers(54, 96))
        g.draw_rect(arr, x, y, w, h, (tone, tone + 4, tone + 2))
        g.draw_rect(arr, x, y, w, 1, (tone + 22, tone + 25, tone + 22))
    for _ in range(4):
        x = int(rng.integers(6, 80))
        g.draw_line(arr, x, 8, x + 10, 40, (104, 70, 46), 210)
    g.add_grime(arr, 925, 0.2, 3)
    return arr


def build() -> None:
    save("floor_archive", floor_archive(), "floors", "Пол архива: пыльный кафель и бумаги", True)
    save("floor_boiler", floor_boiler(), "floors", "Пол котельной: ржавчина и сырость", True)
    save("prop_shelf", prop_shelf(), "furniture", "Стеллаж архива с папками")
    save("prop_boiler_tank", prop_boiler_tank(), "devices", "Ржавый бак котельной")
    save("prop_stairs", prop_stairs(), "furniture", "Лестница вниз с перилами")
    save("prop_collapse", prop_collapse(), "barriers", "Обрушение: бетон и арматура")
    write_manifest(MANIFEST)


if __name__ == "__main__":
    build()