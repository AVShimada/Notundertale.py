"""Une épave différente par partie, dont les salles gardent leur état à la visite."""

from dataclasses import dataclass, field
import random

import pygame

FLOOR_Y = 600
WEAPON_IDS = ("rifle", "raygun")
ROOM_LABELS = {
    "cockpit": "Cockpit",
    "service": "Coursive",
    "cargo": "Soute",
    "medbay": "Infirmerie",
    "reactor": "Réacteur",
    "laboratory": "Laboratoire",
    "hangar": "Hangar",
}


@dataclass(frozen=True)
class Door:
    x: int
    target: str
    arrival_x: int
    label: str


@dataclass
class WeaponPickup:
    x: int
    weapon_id: str
    collected: bool = False


@dataclass
class Room:
    name: str
    title: str
    width: int
    platforms: tuple
    doors: tuple
    enemies: list = field(default_factory=list)
    loot: list = field(default_factory=list)
    decor_seed: int = 0
    theme: str = "service"
    tier: int = 1
    is_exit: bool = False
    xp_drops: list = field(default_factory=list)

    @property
    def solids(self):
        return [pygame.Rect(0, FLOOR_Y, self.width, 120),
                *(pygame.Rect(*platform) for platform in self.platforms)]


    @property
    def weapon_available(self):
        """Compatibilité du prototype, sans second état à synchroniser."""
        return any(not pickup.collected for pickup in self.loot)

    @weapon_available.setter
    def weapon_available(self, available):
        for pickup in self.loot:
            pickup.collected = not available


def _platforms(rng, width):
    """Variantes de passerelles facultatives au-dessus d'un trajet au sol continu."""
    result = []
    for start in range(460, width - 400, 520):
        x = start + rng.randrange(-8, 9) * 4
        length = rng.choice((160, 180, 200, 220))
        layout = rng.randrange(3)
        result.append((x, 484, length, 24))
        if layout == 1:
            result.append((x + 156, 388, 160, 24))
        elif layout == 2:
            result.append((x - 64, 388, 180, 24))
    return tuple(result)


def _enemies(rng, width, tier):
    from .enemies import Alien

    count = rng.randint(7, 8)
    # Des emplacements séparés évitent un groupe superposé au premier tir.
    # Les deux portes restent dégagées, y compris lors d'un retour en arrière.
    left, right = 480, width - 480
    spacing = (right - left) / (count - 1)
    return [Alien(round((left + i * spacing) / 4) * 4 + rng.randrange(-5, 6) * 4,
                  FLOOR_Y - 44, tier=tier)
            for i in range(count)]


def make_rooms(seed=None):
    """Génère une route bidirectionnelle reproductible sans toucher au hasard global.

    L'ordre du dictionnaire est l'ordre de traversée, du cockpit sûr jusqu'au sas.
    Chaque appel crée aussi de nouveaux ennemis, butins et réserves d'expérience.
    """
    rng = random.Random(seed)
    route = ["service", "cargo", "medbay", "reactor", "laboratory", "hangar"]
    rng.shuffle(route)
    route.insert(0, "cockpit")
    widths = {name: (1800 if name == "cockpit" else rng.randrange(650, 801) * 4)
              for name in route}
    first_weapon = rng.choice(WEAPON_IDS)
    second_weapon = next(weapon for weapon in WEAPON_IDS if weapon != first_weapon)
    rooms = {}
    for index, name in enumerate(route):
        width = widths[name]
        tier = max(1, index - 1)
        doors = []
        if index:
            previous = route[index - 1]
            doors.append(Door(80, previous, widths[previous] - 200, ROOM_LABELS[previous]))
        if index + 1 < len(route):
            following = route[index + 1]
            doors.append(Door(width - 100, following, 140, ROOM_LABELS[following]))
        if index == 0:
            platforms = ((820, 484, 180, 24), (1132, 388, 180, 24))
            enemies = []
            loot = [WeaponPickup(610, first_weapon)]
        else:
            platforms = _platforms(rng, width)
            enemies = _enemies(rng, width, tier)
            # Les deux types sont accessibles dès le début, quel que soit le tirage.
            loot = [WeaponPickup(rng.randrange(68, 91) * 4, second_weapon)] if index == 1 else [
                WeaponPickup(rng.randrange(125, (width - 400) // 4) * 4,
                             rng.choice(WEAPON_IDS))]
        rooms[name] = Room(
            name=name, title=f"{index + 1:02d} / {ROOM_LABELS[name].upper()}",
            width=width, platforms=platforms, doors=tuple(doors), enemies=enemies,
            loot=loot, decor_seed=rng.randrange(2 ** 32), theme=name, tier=tier,
            is_exit=index == len(route) - 1,
        )
    return rooms
