from __future__ import annotations
import random
import pygame

POWERUP_LIFETIME_MS = 5000
POWERUP_BLINK_MS = 1000
POWERUP_BLINK_PERIOD_MS = 150

class TimedPowerUp(pygame.sprite.Sprite):
    """Disparaît à 5s, clignote la dernière seconde."""
    def __init__(self):
        super().__init__()
        self.spawn_time = pygame.time.get_ticks()

    def _handle_lifetime(self):
        now = pygame.time.get_ticks()
        age = now - self.spawn_time

        if age >= POWERUP_LIFETIME_MS:
            self.kill()
            return

        if age >= (POWERUP_LIFETIME_MS - POWERUP_BLINK_MS):
            self.image.set_alpha(50 if (now // POWERUP_BLINK_PERIOD_MS) % 2 == 0 else 255)
        else:
            self.image.set_alpha(255)

class ShieldPowerUp(TimedPowerUp):
    kind = "shield"
    def __init__(self, image: pygame.Surface, screen_w: int, screen_h: int):
        super().__init__()
        self.image = image.convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, max(0, screen_w - self.rect.width))
        self.rect.y = random.randint(0, max(0, screen_h - self.rect.height))
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        self._handle_lifetime()

class HeartPowerUp(TimedPowerUp):
    kind = "heart"
    def __init__(self, image: pygame.Surface, screen_w: int, screen_h: int):
        super().__init__()
        self.image = image.convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, max(0, screen_w - self.rect.width))
        self.rect.y = random.randint(0, max(0, screen_h - self.rect.height))
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        self._handle_lifetime()
