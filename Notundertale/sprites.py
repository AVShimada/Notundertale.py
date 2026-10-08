"""Météores, lasers, avertissements et bonus du mode infini."""

import math
import random

import pygame

from .config import (WHITE, POWERUP_LIFETIME_MS, POWERUP_BLINK_MS,
                     POWERUP_BLINK_PERIOD_MS)


class WarningLight(pygame.sprite.Sprite):
    def __init__(self, app, x_position):
        super().__init__()
        self.app = app
        self.width = self.app.screen.get_width() // 8
        self.height = self.app.screen.get_height()
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.image.fill((255, 255, 255, 120))
        self.rect = self.image.get_rect()
        self.rect.x = x_position
        self.rect.y = 0

        self.fading = False
        self.fade_duration = 0.5
        self.start_time = self.app.now_ms()

    def update(self):
        current_time = self.app.now_ms()
        elapsed_time = (current_time - self.start_time) / 1000
        if elapsed_time >= 2 and not self.fading:
            self.fading = True
            self.fade_start_time = current_time

        if self.fading:
            fade_elapsed_time = (current_time - self.fade_start_time) / 1000
            alpha = max(0, 255 * (1 - fade_elapsed_time / self.fade_duration))
            self.image.set_alpha(alpha)
            if alpha <= 0:
                self.kill()


class Projectile(pygame.sprite.Sprite):
    def __init__(self, app, image_path, speed, size=(40, 40)):
        super().__init__()
        self.app = app
        self.image = self.app.assets.image(image_path)
        self.image = pygame.transform.scale(self.image, size)
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, max(0, self.app.screen.get_width() - self.rect.width))
        self.rect.y = 0

        self.speed = float(speed) * float(self.app.speed_multiplier)
        self.y = float(self.rect.y)

        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        self.y += self.speed
        self.rect.y = int(self.y)
        if self.rect.top > self.app.screen.get_height():
            self.kill()


class Meteor1(Projectile):
    def __init__(self, app):
        super().__init__(app, 'meteor1.png', speed=11, size=(40, 40))


class Meteor2(Projectile):
    def __init__(self, app):
        super().__init__(app, 'meteor2.png', speed=12, size=(40, 40))


class Meteor3(Projectile):
    def __init__(self, app):
        super().__init__(app, 'meteor3.png', speed=10, size=(40, 40))


class BigSlowMeteor(Projectile):
    def __init__(self, app):
        super().__init__(app, 'meteor3.png', speed=6, size=(90, 90))


class ZigZagMeteor(Projectile):
    def __init__(self, app):
        super().__init__(app, 'meteor2.png', speed=11, size=(45, 45))
        self.base_x = self.rect.x
        self.spawn_time = self.app.now_ms()
        self.amplitude = 140
        self.freq = 0.010

    def update(self):
        self.y += self.speed
        self.rect.y = int(self.y)

        t = self.app.now_ms() - self.spawn_time
        offset = int(math.sin(t * self.freq) * self.amplitude)
        self.rect.x = self.base_x + offset

        if self.rect.x < 0:
            self.rect.x = 0
        if self.rect.right > self.app.screen.get_width():
            self.rect.right = self.app.screen.get_width()

        if self.rect.top > self.app.screen.get_height():
            self.kill()


class Laser(pygame.sprite.Sprite):
    def __init__(self, app, x_position):
        super().__init__()
        self.app = app
        self.width = self.app.screen.get_width() // 8
        self.height = self.app.screen.get_height()
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.image.fill(WHITE)
        self.rect = self.image.get_rect()
        self.rect.x = x_position
        self.rect.y = 0
        self.mask = pygame.mask.from_surface(self.image)

        self.lifetime = 1.5
        self.fade_duration = 0.5
        self.start_time = self.app.now_ms()
        self.fading = False

    def update(self):
        current_time = self.app.now_ms()
        elapsed_time = (current_time - self.start_time) / 1000
        if elapsed_time >= self.lifetime and not self.fading:
            self.fading = True
            self.fade_start_time = current_time

        if self.fading:
            fade_elapsed_time = (current_time - self.fade_start_time) / 1000
            alpha = max(0, 255 * (1 - fade_elapsed_time / self.fade_duration))
            self.image.set_alpha(alpha)
            if alpha <= 0:
                self.kill()


class TimedPowerUp(pygame.sprite.Sprite):
    """Base pour power-ups temporisés: disparaît à 5s, clignote la dernière seconde."""
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.spawn_time = self.app.now_ms()

    def _handle_lifetime(self):
        now = self.app.now_ms()
        age = now - self.spawn_time

        if age >= POWERUP_LIFETIME_MS:
            self.kill()
            return

        if age >= (POWERUP_LIFETIME_MS - POWERUP_BLINK_MS):
            if (now // POWERUP_BLINK_PERIOD_MS) % 2 == 0:
                self.image.set_alpha(50)
            else:
                self.image.set_alpha(255)
        else:
            self.image.set_alpha(255)


class ShieldPowerUp(TimedPowerUp):
    def __init__(self, app):
        super().__init__(app)
        self.image = self.app.assets.image('shield.png')
        self.image = pygame.transform.scale(self.image, (75, 75))
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, self.app.screen.get_width() - self.rect.width)
        self.rect.y = random.randint(0, self.app.screen.get_height() - self.rect.height)
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        self._handle_lifetime()


class HeartPowerUp(TimedPowerUp):
    def __init__(self, app):
        super().__init__(app)
        self.image = self.app.assets.image('heart.png')
        self.image = pygame.transform.scale(self.image, (50, 50))
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, self.app.screen.get_width() - self.rect.width)
        self.rect.y = random.randint(0, self.app.screen.get_height() - self.rect.height)
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        self._handle_lifetime()
