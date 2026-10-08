"""Chargement des images depuis le dossier du jeu, avec mise en cache."""

import pygame

from .config import ASSET_DIR
from .skins import SKINS


class Assets:
    def __init__(self, screen_size):
        self._images = {}
        self.skins = {
            name: self.image(skin.filename, skin.size)
            for name, skin in SKINS.items()
        }
        self.heart = self.image("heart.png", (50, 50))
        self.shield = self.image("shield.png", (75, 75))
        self.background = self.image("space_background.png", screen_size)

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
