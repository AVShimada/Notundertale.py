from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class Difficulty:
    speed_mult: float
    spawn_delay_ms: int
    tier: int  # 0 = normal, 1 = ajoute zigzag, 2 = ajoute bigslow

def compute_difficulty(elapsed_s: float) -> Difficulty:
    """
    Progression simple et lisible :
    - la vitesse augmente
    - l'intervalle de spawn diminue
    - on débloque des "tiers" de projectiles
    """
    # Spawn: 950ms -> 320ms
    spawn = max(320, int(950 - elapsed_s * 8))

    # Vitesse: 1.0 -> 2.2
    speed_mult = min(2.2, 1.0 + elapsed_s / 70)

    # Tiers
    if elapsed_s < 25:
        tier = 0
    elif elapsed_s < 55:
        tier = 1
    else:
        tier = 2

    return Difficulty(speed_mult=speed_mult, spawn_delay_ms=spawn, tier=tier)
