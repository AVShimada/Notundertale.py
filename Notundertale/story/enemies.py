"""Premier alien : approche, avertissement, bond offensif et récupération."""

from .physics import Body, GRAVITY, move_body


class Alien(Body):
    def __init__(self, x, y, tier=1):
        super().__init__(x, y, 54, 44)
        self.tier = max(1, int(tier))
        self.max_health = 30 + 10 * (self.tier - 1)
        self.health = self.max_health
        self.xp_reward = 10 + 5 * (self.tier - 1)
        self.contact_damage = 20 + 4 * (self.tier - 1)
        self.rewarded = False
        self.facing = -1
        self.phase = "hunt"
        self.timer = 0.0
        self.flash = 0.0

    def update(self, dt, player, room):
        if self.health <= 0:
            return
        self.flash = max(0, self.flash - dt)
        self.timer = max(0, self.timer - dt)
        distance = player.rect.centerx - self.rect.centerx
        vx = 0
        if self.phase == "hunt":
            self.facing = 1 if distance > 0 else -1
            if abs(distance) < 150 and abs(player.rect.bottom - self.rect.bottom) < 100:
                self.phase, self.timer = "warn", 0.42
            elif abs(distance) < 680:
                vx = self.facing * 110
                # Franchir les petits obstacles au sol, sans poursuivre dans le vide.
                ahead = self.rect.move(self.facing * 14, 0)
                if self.grounded and any(ahead.colliderect(s) for s in room.solids):
                    self.vy = -480
        elif self.phase == "warn" and self.timer == 0:
            self.phase, self.timer = "attack", 0.30
            self.vy = -180
        elif self.phase == "attack":
            vx = self.facing * 410
            if self.timer == 0:
                self.phase, self.timer = "recover", 0.85
        elif self.phase == "recover" and self.timer == 0:
            self.phase = "hunt"
        self.vy += GRAVITY * dt
        move_body(self, vx, dt, room.solids, room.width)

    def hit(self, damage=10):
        """Renvoyer True uniquement au passage de vivant à mort."""
        if self.health <= 0 or damage <= 0:
            return False
        self.health = max(0, self.health - damage)
        self.flash = 0.12
        return self.health == 0
