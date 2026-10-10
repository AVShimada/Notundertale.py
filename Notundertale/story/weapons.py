"""Deux armes Histoire, tirs bloqués par le décor et cadences indépendantes."""

from dataclasses import dataclass

import pygame

from .weapon_pose import muzzle_position, RECOIL_PIXELS


@dataclass(frozen=True)
class WeaponSpec:
    label: str
    damage: int
    cooldown: float
    speed: int
    color: tuple[int, int, int]


WEAPONS = {
    "rifle": WeaponSpec("Fusil à impulsions", 9, 0.10, 1100, (245, 199, 94)),
    "raygun": WeaponSpec("Raygun lourd", 30, 0.55, 800, (88, 225, 235)),
}


@dataclass
class Ray:
    x: float
    y: float
    direction: int
    remaining: float = 1.1
    damage: int = 30
    speed: int = 800
    color: tuple[int, int, int] = (88, 225, 235)
    weapon_id: str = "raygun"
    origin_x: float | None = None

    @property
    def rect(self):
        height = 4 if self.weapon_id == "rifle" else 8
        return pygame.Rect(round(self.x) - 10, round(self.y) - height // 2, 20, height)


class Armory:
    FLASH_DURATION = 0.08

    def __init__(self):
        self.slots = []
        self.selected = 0
        self.cooldowns = {weapon_id: 0.0 for weapon_id in WEAPONS}
        self.rays = []
        self.impacts = []
        self.shot_flash = 0.0
        self.last_shot_weapon = None

    @property
    def current(self):
        return self.slots[self.selected] if self.slots else None

    @property
    def spec(self):
        return WEAPONS.get(self.current)

    @property
    def cooldown(self):
        return self.cooldowns.get(self.current, 0.0)

    def equip(self, weapon_id):
        """Prendre une arme ; le retour indique l'arme à redéposer dans la salle.

        Un doublon sélectionne l'arme déjà portée et n'ajoute jamais de troisième
        place. Changer ou reprendre une arme ne réinitialise pas sa cadence.
        """
        if weapon_id not in WEAPONS:
            raise ValueError(f"Arme inconnue : {weapon_id}")
        if weapon_id in self.slots:
            self.selected = self.slots.index(weapon_id)
            return None
        if len(self.slots) < 2:
            self.slots.append(weapon_id)
            self.selected = len(self.slots) - 1
            return None
        displaced = self.current
        self.slots[self.selected] = weapon_id
        return displaced

    def select(self, index):
        """Sélection directe : RB = index 0, RT = index 1."""
        if not 0 <= index < len(self.slots) or index == self.selected:
            return False
        self.selected = index
        return True

    def cycle(self, direction=1):
        if self.slots:
            self.selected = (self.selected + direction) % len(self.slots)
        return self.current

    def update(self, dt, firing, player, room):
        dt = max(0.0, dt)
        self.shot_flash = max(0, self.shot_flash - dt)
        for weapon_id in self.cooldowns:
            self.cooldowns[weapon_id] = max(0, self.cooldowns[weapon_id] - dt)
        fired = bool(firing and self.current and self.cooldown <= 1e-9 and player.health > 0)
        if fired:
            spec = self.spec
            # Les dégâts appartiennent au projectile : une montée de niveau ou
            # un changement d'arme pendant son vol ne modifie pas un tir parti.
            damage = max(1, round(spec.damage * getattr(player, "damage_multiplier", 1.0)))
            muzzle_x, muzzle_y = muzzle_position(player, RECOIL_PIXELS.get(self.current, 2))
            self.rays.append(Ray(muzzle_x, muzzle_y, player.facing,
                                 damage=damage, speed=spec.speed, color=spec.color,
                                 weapon_id=self.current,
                                 origin_x=player.rect.centerx + player.facing * 22))
            self.cooldowns[self.current] = spec.cooldown
            self.last_shot_weapon = self.current
            self.shot_flash = self.FLASH_DURATION
        self.impacts = [(x, y, life - dt) for x, y, life in self.impacts if life > dt]
        for ray in self.rays[:]:
            old = ray.rect
            if ray.origin_x is not None:
                # Vérifier aussi l'espace sous le canon au départ : un mur ou
                # une cible collée à l'hôte ne doit jamais être traversé.
                old.centerx = round(ray.origin_x)
                ray.origin_x = None
            ray.x += ray.direction * ray.speed * dt
            ray.remaining -= dt
            sweep = old.union(ray.rect)
            # Un tir résout seulement le premier obstacle croisé. Les morts ne
            # bloquent pas les suivants et ne peuvent pas recevoir deux butins.
            candidates = [(s, None) for s in room.solids if sweep.colliderect(s)]
            candidates += [(e.rect, e) for e in room.enemies
                           if e.health > 0 and sweep.colliderect(e.rect)]
            if candidates:
                rect, enemy = min(candidates, key=lambda item: item[0].left if ray.direction > 0 else -item[0].right)
                if enemy is not None:
                    enemy.hit(ray.damage)
                self.impacts.append((rect.left if ray.direction > 0 else rect.right, ray.y, 0.16))
            if candidates or ray.remaining <= 0 or not 0 <= ray.x <= room.width:
                self.rays.remove(ray)
        return fired


class RayGun(Armory):
    """Ancien point d'entrée, réservé aux outils de prévisualisation du prototype."""

    def update(self, dt, firing, player, room):
        if player.has_weapon and not self.slots:
            self.equip("raygun")
        return super().update(dt, firing and player.has_weapon, player, room)
