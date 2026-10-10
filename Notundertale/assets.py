"""Chargement des images depuis le dossier du jeu, avec mise en cache."""

import pygame

from .config import ASSET_DIR
from .skins import SKINS
from .animation import CharacterAnimation


class Assets:
    def __init__(self, screen_size):
        self._images = {}
        self.skins = {
            name: self.image(skin.filename, skin.size)
            for name, skin in SKINS.items()
        }
        self.animation_frames = {}
        for name, skin in SKINS.items():
            if skin.animation_filename:
                sheet = self.image(skin.animation_filename)
                width, height = skin.size
                if sheet.get_size() != (width * 4, height * 2):
                    raise ValueError(f"Planche d'animation invalide : {skin.animation_filename}")
                self.animation_frames[name] = tuple(
                    sheet.subsurface((i % 4 * width, i // 4 * height, width, height)).copy()
                    for i in range(8))
        self.heart = self.image("heart.png", (50, 50))
        self.shield = self.image("shield.png", (75, 75))
        self.background = self.image("space_background.png", screen_size)

    def character_animation(self, name):
        # Chaque joueur possède son état ; seules les poses opaques sont partagées.
        return CharacterAnimation(self.skins[name], self.animation_frames.get(name, ()))

    def image(self, filename, size=None):
        key = (filename, size)
        if key not in self._images:
            if size is None:
                image = pygame.image.load(str(ASSET_DIR / filename)).convert_alpha()
            else:
                source = self.image(filename)
                image = source if source.get_size() == size else pygame.transform.scale(source, size)
            self._images[key] = image
        # Chaque sprite peut modifier son alpha sans modifier les autres.
        return self._images[key].copy()
