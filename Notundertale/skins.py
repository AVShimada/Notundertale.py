"""Catalogue des apparences et dimensions utilisées pendant une partie."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Skin:
    label: str
    filename: str
    size: tuple[int, int]
    animation_filename: str | None = None


PLAYER_SPRITE_SIZE = (100, 100)
DEFAULT_SKIN = "remanent"
SKINS = {
    "remanent": Skin("Le Rémanent", "characters/remanent.png", PLAYER_SPRITE_SIZE, "characters/animations/remanent.png"),
    "scaphandre": Skin("Le Scaphandre", "characters/scaphandre.png", PLAYER_SPRITE_SIZE, "characters/animations/scaphandre.png"),
    "colonie": Skin("La Colonie", "characters/colonie.png", PLAYER_SPRITE_SIZE, "characters/animations/colonie.png"),
    "deriveur": Skin("Le Dériveur", "characters/deriveur.png", PLAYER_SPRITE_SIZE, "characters/animations/deriveur.png"),
    "default": Skin("Classique", "player.png", PLAYER_SPRITE_SIZE),
    "skin2": Skin("Classique II", "player_skin2.png", PLAYER_SPRITE_SIZE),
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
