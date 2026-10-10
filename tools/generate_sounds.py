"""Régénère les effets chiptune, sans échantillons externes ni dépendances.

Utilisation depuis la racine : python tools/generate_sounds.py
"""

import random
import struct
import wave
from pathlib import Path

RATE = 44_100
OUTPUT = Path(__file__).resolve().parents[1] / "Notundertale" / "sounds"


def tone(start_hz, end_hz, duration, noise=0.0, amplitude=0.45):
    samples = []
    phase = 0.0
    count = int(RATE * duration)
    rng = random.Random(42)
    for index in range(count):
        t = index / RATE
        progress = index / max(1, count - 1)
        frequency = start_hz + (end_hz - start_hz) * progress
        phase += frequency / RATE
        # Onde carrée + triangle : timbre rétro adouci.
        square = 1.0 if phase % 1 < 0.5 else -1.0
        triangle = 1.0 - 4.0 * abs(phase % 1 - 0.5)
        signal = 0.45 * square + 0.55 * triangle
        signal = (1 - noise) * signal + noise * rng.uniform(-1, 1)
        envelope = min(1.0, t / 0.005) * min(1.0, (duration - t) / 0.035)
        envelope *= 1.0 - 0.35 * progress
        samples.append(int(32767 * amplitude * signal * envelope))
    return samples


def write_sound(filename, samples):
    with wave.open(str(OUTPUT / filename), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(RATE)
        output.writeframes(struct.pack(f"<{len(samples)}h", *samples))


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    write_sound("hit.wav", tone(200, 55, 0.17, noise=0.45))
    write_sound("dash.wav", tone(240, 1100, 0.14, noise=0.18, amplitude=0.30))
    write_sound("ray.wav", tone(1400, 160, 0.11, noise=0.04, amplitude=0.23))
    write_sound("power_up.wav", tone(523.25, 523.25, 0.08) +
                tone(659.25, 659.25, 0.08) + tone(1046.5, 1046.5, 0.18))
    write_sound("game_over.wav", tone(392, 392, 0.18) + tone(329.63, 329.63, 0.18) +
                tone(261.63, 261.63, 0.20) + tone(130.81, 65.4, 0.48))


if __name__ == "__main__":
    main()
