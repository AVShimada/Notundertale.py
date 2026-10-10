"""Déplacement latéral, saut tolérant, dash et dégâts du personnage Histoire."""

from .physics import Body, GRAVITY, move_body
from .progression import Progression


class StoryPlayer(Body):
    SPEED = 280
    JUMP_SPEED = 760
    DASH_SPEED = 850
    DASH_DURATION = 0.16
    DASH_COOLDOWN = 1.2
    MAX_HEALTH = 100

    def __init__(self):
        super().__init__(240, 514, 44, 86)
        self.grounded = True
        self.progression = Progression()
        self.health = self.max_health
        self.facing = 1
        self.dash_left = 0.0
        self.cooldown = 0.0
        self.invulnerable = 0.0
        self.coyote = 0.0
        self.jump_buffer = 0.0
        self.has_weapon = False
        self.animation = None

    @property
    def max_health(self):
        return self.progression.max_health

    @property
    def damage_multiplier(self):
        return self.progression.damage_multiplier

    def update(self, state, dt, room, jump_pressed=False, dash_pressed=False):
        previous_x = self.pos.x
        self.cooldown = max(0, self.cooldown - dt)
        self.invulnerable = max(0, self.invulnerable - dt)
        self.dash_left = max(0, self.dash_left - dt)
        self.coyote = 0.09 if self.grounded else max(0, self.coyote - dt)
        self.jump_buffer = 0.12 if jump_pressed else max(0, self.jump_buffer - dt)
        if state.x and not self.dash_left:
            self.facing = 1 if state.x > 0 else -1
        dashed = dash_pressed and self.cooldown == 0
        if dashed:
            self.dash_left = self.DASH_DURATION
            self.cooldown = self.DASH_COOLDOWN
            self.vy = 0
        if self.jump_buffer and self.coyote and not self.dash_left:
            self.vy = -self.JUMP_SPEED
            self.jump_buffer = self.coyote = 0
            self.grounded = False
        if self.dash_left:
            vx = self.facing * self.DASH_SPEED
            self.vy = 0
        else:
            vx = max(-1, min(1, state.x)) * self.SPEED
            # Relâcher le saut tôt permet un saut plus court.
            self.vy += GRAVITY * dt * (1.8 if self.vy < 0 and not state.jump else 1)
        move_body(self, vx, dt, room.solids, room.width)
        if self.animation:
            self.animation.update(dt, abs(self.pos.x - previous_x),
                                  airborne=not self.grounded, dashing=self.dash_left > 0)
        return dashed

    def hurt(self, damage=20):
        if self.health <= 0 or self.invulnerable or self.dash_left:
            return False
        self.health = max(0, self.health - damage)
        self.invulnerable = 1.0
        return True
