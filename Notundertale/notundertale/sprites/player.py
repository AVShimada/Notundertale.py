from __future__ import annotations
import pygame

DASH_DURATION_MS = 200
DASH_COOLDOWN_MS = 5000
DASH_SPEED_MULT = 3.0

class Player(pygame.sprite.Sprite):
    def __init__(self, image: pygame.Surface, pos: tuple[int, int]):
        super().__init__()
        self.original_image = pygame.transform.scale(image.convert_alpha(), (100, 100))
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect(center=pos)
        self.mask = pygame.mask.from_surface(self.image)

        self.base_speed = 10
        self.health = 3

        # invu après hit
        self.invulnerable = False
        self.invulnerable_start_time = 0
        self.invulnerable_duration_s = 1.0

        # dash
        self.dashing = False
        self.dash_start_time = 0
        self.last_dash_time = -10_000_000
        self.dash_dir = pygame.Vector2(0, 0)

    def can_dash(self) -> bool:
        now = pygame.time.get_ticks()
        return (now - self.last_dash_time) >= DASH_COOLDOWN_MS and not self.dashing

    def start_dash(self, keys: pygame.key.ScancodeWrapper) -> None:
        dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
        dy = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])

        v = pygame.Vector2(dx, dy)
        if v.length_squared() == 0:
            v = pygame.Vector2(1, 0)
        else:
            v = v.normalize()

        self.dashing = True
        self.dash_start_time = pygame.time.get_ticks()
        self.last_dash_time = self.dash_start_time
        self.dash_dir = v

    def is_invincible(self) -> bool:
        return self.dashing or self.invulnerable

    def decrease_health(self) -> bool:
        """True si un dégât est appliqué (utile pour hit feedback)."""
        if self.is_invincible():
            return False

        self.health -= 1
        if self.health <= 0:
            self.kill()
            return True

        self.invulnerable = True
        self.invulnerable_start_time = pygame.time.get_ticks()
        return True

    def update(self, keys: pygame.key.ScancodeWrapper, bounds: pygame.Rect) -> None:
        now = pygame.time.get_ticks()

        # invu après hit (clignote)
        if self.invulnerable and not self.dashing:
            if (now - self.invulnerable_start_time) / 1000 > self.invulnerable_duration_s:
                self.invulnerable = False
                self.image = self.original_image.copy()
                self.image.set_alpha(255)
            else:
                alpha = 255 * (1 - ((now - self.invulnerable_start_time) % 200) / 100)
                self.image.set_alpha(alpha)

        # dash
        if self.dashing:
            if (now - self.dash_start_time) >= DASH_DURATION_MS:
                self.dashing = False
            else:
                self.image.set_alpha(180)

        # déclenchement dash
        if (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) and self.can_dash():
            self.start_dash(keys)

        # move
        if self.dashing:
            dash_speed = self.base_speed * DASH_SPEED_MULT
            self.rect.x += int(self.dash_dir.x * dash_speed)
            self.rect.y += int(self.dash_dir.y * dash_speed)
        else:
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.rect.x -= self.base_speed
                self.image = pygame.transform.flip(self.original_image, True, False)
                self.mask = pygame.mask.from_surface(self.image)
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.rect.x += self.base_speed
                self.image = self.original_image
                self.mask = pygame.mask.from_surface(self.image)
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                self.rect.y -= self.base_speed
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                self.rect.y += self.base_speed

        self.rect.clamp_ip(bounds)

        if not self.invulnerable and not self.dashing:
            self.image.set_alpha(255)
