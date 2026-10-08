"""Catalogue des apparences et dimensions utilisées pendant une partie."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Skin:
    label: str
    filename: str
    size: tuple[int, int]


MINI_SPRITE_SIZE = (32, 48)
DEFAULT_SKIN = "remanent"
SKINS = {
    "remanent": Skin("Le Rémanent", "characters/remanent.png", MINI_SPRITE_SIZE),
    "scaphandre": Skin("Le Scaphandre", "characters/scaphandre.png", MINI_SPRITE_SIZE),
    "colonie": Skin("La Colonie", "characters/colonie.png", MINI_SPRITE_SIZE),
    "deriveur": Skin("Le Dériveur", "characters/deriveur.png", MINI_SPRITE_SIZE),
    "default": Skin("Classique", "player.png", (100, 100)),
    "skin2": Skin("Classique II", "player_skin2.png", (100, 100)),
}


def skin_label(name):
    return SKINS[name].label


def skin_preview(image, bounds=(96, 96)):
    """Agrandir sans lisser ni déformer ; pixels entiers pour les miniatures."""
    import pygame

    ratio = min(bounds[0] / image.get_width(), bounds[1] / image.get_height())
    if ratio >= 1:
        ratio = int(ratio)
    size = (max(1, round(image.get_width() * ratio)),
            max(1, round(image.get_height() * ratio)))
    return pygame.transform.scale(image, size)
