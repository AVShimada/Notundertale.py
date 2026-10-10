"""Biomasse laissée au sol : approche, absorption et gain d'XP sans interrompre le jeu."""

from dataclasses import dataclass

import pygame


@dataclass
class ExperienceDrop:
    pos: pygame.Vector2
    value: int
    attracted: bool = False
    collected: bool = False
    age: float = 0.0

    def update(self, dt, player):
        if self.collected or player.health <= 0:
            return 0
        self.age += dt
        delta = pygame.Vector2(player.rect.center) - self.pos
        distance = delta.length()
        if distance < 110:
            self.attracted = True
        if not self.attracted:
            return 0
        if distance <= max(12, 420 * dt):
            self.collected = True
            return self.value
        self.pos += delta / distance * 420 * dt
        return 0
