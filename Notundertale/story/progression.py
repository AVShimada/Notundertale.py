"""Progression d'une seule expédition ; aucune amélioration ne survit à la mort."""

from dataclasses import dataclass
from math import ceil


BASE_XP = 100
XP_GROWTH = 1.35
BASE_HEALTH = 100
HEALTH_PER_LEVEL = 20
DAMAGE_PER_LEVEL = 0.12
BOSS_XP = 250
HEAL_KILLS_REQUIRED = 5
HEAL_FRACTION = 0.40
SECOND_HEAL_LEVEL = 5


@dataclass
class Progression:
    level: int = 1
    xp: int = 0
    total_xp: int = 0
    kills: int = 0
    heal_charges: int = 1
    heal_kills: int = 0

    @property
    def xp_required(self):
        """Coût du prochain niveau, arrondi au multiple de cinq supérieur."""
        return ceil(BASE_XP * XP_GROWTH ** (self.level - 1) / 5) * 5

    @property
    def max_health(self):
        return BASE_HEALTH + HEALTH_PER_LEVEL * (self.level - 1)

    @property
    def damage_multiplier(self):
        return 1 + DAMAGE_PER_LEVEL * (self.level - 1)

    @property
    def heal_capacity(self):
        return 2 if self.level >= SECOND_HEAL_LEVEL else 1

    def add_xp(self, amount):
        """Absorber un butin et garder l'excédent, même après plusieurs niveaux."""
        if not isinstance(amount, int) or amount < 0:
            raise ValueError("La quantité d'expérience doit être un entier positif ou nul.")
        self.xp += amount
        self.total_xp += amount
        old_capacity = self.heal_capacity
        gained = 0
        while self.xp >= self.xp_required:
            self.xp -= self.xp_required
            self.level += 1
            gained += 1
        # La nouvelle place débloquée arrive chargée ; les charges utilisées
        # avant la montée de niveau doivent toujours être regagnées au combat.
        self.heal_charges += self.heal_capacity - old_capacity
        return gained

    def record_kill(self, is_boss=False):
        """Cinq ennemis ou un boss rechargent une seule dose manquante."""
        self.kills += 1
        if self.heal_charges >= self.heal_capacity:
            self.heal_kills = 0
            return False
        self.heal_kills += 1
        if is_boss or self.heal_kills >= HEAL_KILLS_REQUIRED:
            self.heal_charges += 1
            self.heal_kills = 0
            return True
        return False

    def use_heal(self, player):
        if self.heal_charges <= 0 or not 0 < player.health < self.max_health:
            return False
        player.health = min(self.max_health, player.health + round(self.max_health * HEAL_FRACTION))
        self.heal_charges -= 1
        # Une recharge partielle déjà gagnée continue si une deuxième dose
        # est consommée : les deux doses sont remplies l'une après l'autre.
        return True
