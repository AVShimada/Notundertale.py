"""Progression de la difficulté et choix des variantes de météores."""

import random

from .config import (DIFF_CAP, DIFF_STEP, SPEED_INC_PER_STEP,
                     BASE_PROJECTILE_INTERVAL, SPAWN_INC_PER_STEP,
                     MIN_PROJECTILE_INTERVAL)
from .sprites import Meteor1, Meteor2, Meteor3, BigSlowMeteor, ZigZagMeteor


def get_difficulty_level(score_value: int) -> int:
    capped = min(score_value, DIFF_CAP)
    return capped // DIFF_STEP


def compute_difficulty(score_value: int):
    level = get_difficulty_level(score_value)
    speed_mult = 1.0 + level * SPEED_INC_PER_STEP
    interval = int(BASE_PROJECTILE_INTERVAL * ((1.0 - SPAWN_INC_PER_STEP) ** level))
    interval = max(MIN_PROJECTILE_INTERVAL, interval)
    return level, speed_mult, interval


def lerp(a, b, t):
    return a + (b - a) * max(0.0, min(1.0, t))


def choose_projectile_class(score_value: int):
    """
    - Base meteors au début
    - BigSlowMeteor apparaît progressivement à partir de 100k (0% -> 30% jusqu'à 150k)
    - ZigZagMeteor apparaît progressivement à partir de 150k (0% -> 25% jusqu'à 200k)
    """
    base_classes = [Meteor1, Meteor2, Meteor3]

    if score_value < 100000:
        p_big = 0.0
    else:
        t = (score_value - 100000) / 50000.0
        p_big = lerp(0.0, 0.30, t)

    if score_value < 150000:
        p_zig = 0.0
    else:
        t = (score_value - 150000) / 50000.0
        p_zig = lerp(0.0, 0.25, t)

    r = random.random()
    if r < p_zig:
        return ZigZagMeteor
    elif r < p_zig + p_big:
        return BigSlowMeteor
    else:
        return random.choice(base_classes)
