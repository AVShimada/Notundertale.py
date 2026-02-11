from __future__ import annotations
import random
import pygame


class WarningLight(pygame.sprite.Sprite):
    """
    Un warning (ligne semi-transparente) qui annonce où le laser va frapper.
    orient = "v" (vertical) ou "h" (horizontal)
    """
    def __init__(self, orient: str, pos: int, screen_w: int, screen_h: int, duration_ms: int = 1000):
        super().__init__()
        self.orient = orient
        self.pos = pos
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.spawn_time = pygame.time.get_ticks()
        self.duration_ms = duration_ms

        thickness = 10
        if orient == "v":
            self.image = pygame.Surface((thickness, screen_h), pygame.SRCALPHA)
            self.image.fill((255, 255, 255, 90))
            self.rect = self.image.get_rect(midtop=(pos, 0))
        else:
            self.image = pygame.Surface((screen_w, thickness), pygame.SRCALPHA)
            self.image.fill((255, 255, 255, 90))
            self.rect = self.image.get_rect(midleft=(0, pos))

    def update(self) -> None:
        now = pygame.time.get_ticks()
        age = now - self.spawn_time

        if age >= self.duration_ms - 250:
            self.image.set_alpha(50 if (now // 80) % 2 == 0 else 140)
        else:
            self.image.set_alpha(140)

        if age >= self.duration_ms:
            self.kill()


class LaserBeam(pygame.sprite.Sprite):
    """Laser actif (dangereux)."""
    def __init__(self, orient: str, pos: int, screen_w: int, screen_h: int, duration_ms: int = 800):
        super().__init__()
        self.orient = orient
        self.pos = pos
        self.spawn_time = pygame.time.get_ticks()
        self.duration_ms = duration_ms

        thickness = 100
        if orient == "v":
            self.image = pygame.Surface((thickness, screen_h), pygame.SRCALPHA)
            self.image.fill((255, 255, 255, 220))
            self.rect = self.image.get_rect(midtop=(pos, 0))
        else:
            self.image = pygame.Surface((screen_w, thickness), pygame.SRCALPHA)
            self.image.fill((255, 255, 255, 220))
            self.rect = self.image.get_rect(midleft=(0, pos))

        self.mask = pygame.mask.from_surface(self.image)

    def update(self) -> None:
        if pygame.time.get_ticks() - self.spawn_time >= self.duration_ms:
            self.kill()


def random_laser_params(screen_w: int, screen_h: int) -> tuple[str, int]:
    orient = random.choice(["v", "h"])
    if orient == "v":
        pos = random.randint(80, max(81, screen_w - 80))
    else:
        pos = random.randint(80, max(81, screen_h - 80))
    return orient, pos
