"""Chargement des images depuis le dossier du jeu, avec mise en cache."""

import pygame

from .config import ASSET_DIR
from .skins import SKINS


class Assets:
    def __init__(self, screen_size):
        self._images = {}
        reference = SKINS["skin2"]
        reference_height = self.image(reference.filename, reference.size).get_bounding_rect(min_alpha=128).height
        self.skins = {
            name: (self.character(skin.filename, skin.size, reference_height)
                   if skin.match_reference_height else self.image(skin.filename, skin.size))
            for name, skin in SKINS.items()
        }
        self.heart = self.image("heart.png", (50, 50))
        self.shield = self.image("shield.png", (75, 75))
        self.background = self.image("space_background.png", screen_size)

    def character(self, filename, size, visible_height):
        """Même hauteur visible que le skin 2, proportions et alpha préservés."""
        source = self.image(filename)
        body = source.subsurface(source.get_bounding_rect(min_alpha=128))
        ratio = min(size[0] / body.get_width(), visible_height / body.get_height())
        dimensions = (max(1, round(body.get_width() * ratio)),
                      max(1, round(body.get_height() * ratio)))
        enlarged = pygame.transform.scale(body, dimensions)
        frame = pygame.Surface(size, pygame.SRCALPHA)
        frame.blit(enlarged, enlarged.get_rect(center=frame.get_rect().center))
        return frame

    def image(self, filename, size=None):
        key = (filename, size)
        if key not in self._images:
            if size is None:
                image = pygame.image.load(str(ASSET_DIR / filename)).convert_alpha()
            else:
                image = pygame.transform.scale(self.image(filename), size)
            self._images[key] = image
        # Chaque sprite peut modifier son alpha sans modifier les autres.
        return self._images[key].copy()
