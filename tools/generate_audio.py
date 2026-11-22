#!/usr/bin/env python3
"""Generate the game's compact placeholder soundscape using only stdlib."""

from __future__ import annotations

import math
import random
import struct
import wave
from pathlib import Path

RATE = 22050
OUT = Path(__file__).resolve().parent.parent / "assets" / "audio"
random.seed(1313)


def envelope(t: float, duration: float, attack: float, decay: float) -> float:
    attack_gain = min(1.0, t / max(attack, 1e-6))
    decay_gain = math.exp(-max(0.0, t - attack) * decay)
    release = min(1.0, max(0.0, duration - t) / 0.05)
    return attack_gain * decay_gain * release


def write_wav(name: str, samples: list[float], rate: int = RATE) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    frames = bytearray()
    for value in samples:
        clipped = max(-0.98, min(0.98, value))
        frames += struct.pack("<h", int(clipped * 32767))
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(bytes(frames))
    print(f"wrote {path.relative_to(OUT.parent)} ({len(samples) / rate:.2f}s)")


def drone(duration: float, base: float, brightness: float, pulse: float) -> list[float]:
    count = int(RATE * duration)
    samples: list[float] = []
    for index in range(count):
        t = index / RATE
        slow = 0.72 + 0.28 * math.sin(2 * math.pi * t / duration * 2)
        beat = 0.86 + 0.14 * math.sin(2 * math.pi * 0.25 * t)
        tone = (
            0.44 * math.sin(2 * math.pi * base * t)
            + 0.18 * math.sin(2 * math.pi * base * 1.5 * t)
            + 0.12 * math.sin(2 * math.pi * base * 2.0 * t + 0.8)
            + brightness * 0.035 * math.sin(2 * math.pi * 740 * t + math.sin(t * 0.7))
        )
        samples.append(tone * slow * beat * pulse)
    return samples


def add_event(samples: list[float], at: float, event: list[float], gain: float = 1.0) -> None:
    offset = int(at * RATE)
    for index, value in enumerate(event):
        target = offset + index
        if 0 <= target < len(samples):
            samples[target] += value * gain


def low_noise(duration: float, decay: float, gain: float = 1.0) -> list[float]:
    count = int(RATE * duration)
    values: list[float] = []
    previous = 0.0
    for index in range(count):
        t = index / RATE
        current = random.uniform(-1.0, 1.0)
        previous = previous * 0.72 + current * 0.28
        values.append(previous * math.exp(-t * decay) * envelope(t, duration, 0.002, decay) * gain)
    return values


def build_ambient_menu() -> None:
    duration = 12.0
    samples = drone(duration, 55.0, 0.8, 0.36)
    for index in range(len(samples)):
        t = index / RATE
        samples[index] *= 0.82 + 0.18 * math.sin(2 * math.pi * t / duration * 6)
    write_wav("ambient_menu.wav", samples)


def build_ambient_hospital() -> None:
    duration = 16.0
    samples = drone(duration, 45.0, 1.3, 0.42)
    clank = low_noise(0.6, 8.0, 0.35)
    for index, value in enumerate(clank):
        t = index / RATE
        clank[index] = value + 0.06 * math.sin(2 * math.pi * (190 - t * 80) * t) * math.exp(-t * 7)
    add_event(samples, 6.2, clank, 0.55)
    add_event(samples, 13.4, clank, 0.28)
    write_wav("ambient_hospital.wav", samples)


def build_step() -> None:
    duration = 0.13
    samples = low_noise(duration, 28.0, 0.45)
    for index in range(len(samples)):
        t = index / RATE
        samples[index] += 0.12 * math.sin(2 * math.pi * 95 * t) * math.exp(-t * 30)
    write_wav("step.wav", samples)


def build_interact() -> None:
    duration = 0.11
    samples: list[float] = []
    for index in range(int(RATE * duration)):
        t = index / RATE
        click = 0.08 * math.sin(2 * math.pi * 1350 * t) * math.exp(-t * 55)
        body = 0.1 * math.sin(2 * math.pi * 420 * t) * math.exp(-t * 28)
        samples.append(click + body)
    write_wav("interact.wav", samples)


def build_pickup() -> None:
    duration = 0.34
    samples: list[float] = []
    for index in range(int(RATE * duration)):
        t = index / RATE
        first = 0.13 * math.sin(2 * math.pi * 620 * t) * math.exp(-t * 15)
        second_t = max(0.0, t - 0.12)
        second = 0.18 * math.sin(2 * math.pi * 930 * second_t) * math.exp(-second_t * 13) if t > 0.12 else 0.0
        samples.append(first + second)
    write_wav("pickup.wav", samples)


def build_power() -> None:
    duration = 1.35
    samples: list[float] = []
    for index in range(int(RATE * duration)):
        t = index / RATE
        thump = 0.22 * math.sin(2 * math.pi * 52 * t) * math.exp(-t * 4.4)
        electric = 0.045 * math.sin(2 * math.pi * 100 * t) * min(1.0, t * 6) * math.exp(-t * 0.8)
        crackle = random.uniform(-0.1, 0.1) * math.exp(-t * 9) if random.random() < 0.025 else 0.0
        samples.append(thump + electric + crackle)
    write_wav("power.wav", samples)


def build_stinger() -> None:
    duration = 1.1
    samples: list[float] = []
    for index in range(int(RATE * duration)):
        t = index / RATE
        sweep = 1500 - t * 600
        tone = (
            0.22 * math.sin(2 * math.pi * sweep * t)
            + 0.15 * math.sin(2 * math.pi * (sweep * 1.41) * t + 0.4)
            + 0.1 * math.sin(2 * math.pi * 87 * t)
        )
        noise = random.uniform(-1.0, 1.0) * 0.09
        values = (tone + noise) * envelope(t, duration, 0.008, 4.2)
        samples.append(max(-0.9, min(0.9, values)))
    write_wav("stinger.wav", samples)


def build_heartbeat() -> None:
    duration = 0.8
    samples: list[float] = []
    for index in range(int(RATE * duration)):
        t = index / RATE
        beat_one = 0.3 * math.sin(2 * math.pi * 54 * t) * math.exp(-t * 19)
        beat_two_t = max(0.0, t - 0.28)
        beat_two = 0.22 * math.sin(2 * math.pi * 47 * beat_two_t) * math.exp(-beat_two_t * 21) if t > 0.28 else 0.0
        samples.append(beat_one + beat_two)
    write_wav("heartbeat.wav", samples)


def main() -> None:
    build_ambient_menu()
    build_ambient_hospital()
    build_step()
    build_interact()
    build_pickup()
    build_power()
    build_stinger()
    build_heartbeat()


if __name__ == "__main__":
    main()