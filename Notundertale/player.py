"""Déplacement, dash et points de vie du joueur."""

import pygame

from .config import DASH_COOLDOWN_MS, DASH_DURATION_MS, DASH_SPEED_MULT


class Player(pygame.sprite.Sprite):
    def __init__(self, app):
        super().__init__()
        self.app = app
        # Les assets ont déjà la bonne taille de jeu et conservent leurs proportions.
        self.original_image = app.assets.skins[app.selected_skin].copy()
        self.animation = app.assets.character_animation(app.selected_skin)
        self._animation_time = app.now_ms()
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect(center=app.screen.get_rect().center)
        self.mask = pygame.mask.from_surface(self.image)
        self.base_speed = 10
        self.health = 3
        self.invulnerable = False
        self.invulnerable_start_time = 0
        self.invulnerable_duration_ms = 1000
        self.dashing = False
        self.dash_start_time = 0
        self.last_dash_time = -DASH_COOLDOWN_MS
        self.dash_dir = pygame.Vector2()
        self.facing_left = False
        self._fraction = pygame.Vector2()

    def dash_remaining_ms(self):
        return max(0, DASH_COOLDOWN_MS - (self.app.now_ms() - self.last_dash_time))

    def dash_progress(self):
        return 1.0 - min(DASH_COOLDOWN_MS, self.dash_remaining_ms()) / DASH_COOLDOWN_MS

    def can_dash(self):
        return self.health > 0 and not self.dashing and self.dash_remaining_ms() == 0

    def start_dash(self, inputs):
        if not self.can_dash():
            return False
        direction = pygame.Vector2(inputs.x, inputs.y)
        self.dash_dir = direction.normalize() if direction.length_squared() else pygame.Vector2(1, 0)
        self.dashing = True
        self.dash_start_time = self.app.now_ms()
        self.last_dash_time = self.dash_start_time
        self.app.audio.play("dash")
        return True

    def is_invincible(self):
        return self.dashing or self.invulnerable

    def update(self, inputs):
        now = self.app.now_ms()
        animation_dt = max(0, min(0.1, (now - self._animation_time) / 1000))
        self._animation_time = now
        previous_position = pygame.Vector2(self.rect.topleft)
        if self.invulnerable and now - self.invulnerable_start_time >= self.invulnerable_duration_ms:
            self.invulnerable = False
        if self.dashing and now - self.dash_start_time >= DASH_DURATION_MS:
            self.dashing = False
        if inputs.dash:
            self.start_dash(inputs)

        if self.dashing:
            movement = self.dash_dir * self.base_speed * DASH_SPEED_MULT
            if self.dash_dir.x:
                self.facing_left = self.dash_dir.x < 0
        else:
            direction = pygame.Vector2(inputs.x, inputs.y)
            movement = direction * self.base_speed
            if direction.x:
                self.facing_left = direction.x < 0
        movement += self._fraction
        step = pygame.Vector2(int(movement.x), int(movement.y))
        self._fraction = movement - step
        self.rect.move_ip(int(step.x), int(step.y))
        self.rect.clamp_ip(self.app.screen.get_rect())

        distance = previous_position.distance_to(self.rect.topleft)
        self.animation.update(animation_dt, distance, dashing=self.dashing)
        # Copier la pose avant de modifier l'alpha pour ne pas altérer les assets partagés.
        self.image = self.animation.image(self.facing_left).copy()
        self.mask = pygame.mask.from_surface(self.image)
        if self.dashing:
            self.image.set_alpha(180)
        elif self.invulnerable:
            self.image.set_alpha(70 if (now - self.invulnerable_start_time) // 100 % 2 == 0 else 255)

    def decrease_health(self):
        """Retourne True seulement quand une vie a effectivement été perdue."""
        if self.health <= 0 or self.is_invincible():
            return False
        self.health -= 1
        if self.health == 0:
            self.kill()
        else:
            self.invulnerable = True
            self.invulnerable_start_time = self.app.now_ms()
        return True
