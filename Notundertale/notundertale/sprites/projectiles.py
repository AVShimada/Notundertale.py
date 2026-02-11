from __future__ import annotations
import random
import math
import pygame

class BaseMeteor(pygame.sprite.Sprite):
    def __init__(self, image: pygame.Surface, screen_w: int, screen_h: int, speed: float, size: int):
        super().__init__()
        self.image = pygame.transform.scale(image.convert_alpha(), (size, size))
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, max(0, screen_w - self.rect.width))
        self.rect.y = -self.rect.height
        self.screen_h = screen_h
        self.speed = float(speed)
        self.y = float(self.rect.y)
        self.mask = pygame.mask.from_surface(self.image)

    def update(self) -> None:
        self.y += self.speed
        self.rect.y = int(self.y)
        if self.rect.top > self.screen_h:
            self.kill()

class Meteor(BaseMeteor):
    """Meteor classique"""
    def __init__(self, image: pygame.Surface, screen_w: int, screen_h: int, speed: float):
        size = random.randint(40, 65)
        super().__init__(image, screen_w, screen_h, speed=speed, size=size)

class ZigZagMeteor(BaseMeteor):
    """Meteor qui ondule horizontalement"""
    def __init__(self, image: pygame.Surface, screen_w: int, screen_h: int, speed: float):
        super().__init__(image, screen_w, screen_h, speed=speed, size=random.randint(42, 62))
        self.base_x = self.rect.x
        self.spawn_time = pygame.time.get_ticks()
        self.amp = random.randint(90, 160)
        self.freq = random.uniform(0.009, 0.014)
        self.screen_w = screen_w

    def update(self) -> None:
        super().update()
        t = pygame.time.get_ticks() - self.spawn_time
        offset = int(math.sin(t * self.freq) * self.amp)
        self.rect.x = max(0, min(self.base_x + offset, self.screen_w - self.rect.width))

class BigSlowMeteor(BaseMeteor):
    """Gros meteor lent = plus dangereux à esquiver"""
    def __init__(self, image: pygame.Surface, screen_w: int, screen_h: int, speed: float):
        size = random.randint(85, 115)
        super().__init__(image, screen_w, screen_h, speed=speed * 0.72, size=size)
