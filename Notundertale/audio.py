"""Musique et effets ; le jeu fonctionne aussi sans périphérique audio."""

import logging

import pygame

from .config import ASSET_DIR

logger = logging.getLogger(__name__)


class Audio:
    SOUND_FILES = {
        "hit": "hit.wav",
        "dash": "dash.wav",
        "power_up": "power_up.wav",
        "game_over": "game_over.wav",
    }

    def __init__(self, asset_dir=ASSET_DIR):
        self.asset_dir = asset_dir
        self.volume = 0.5
        self.sounds = {}
        self.available = pygame.mixer.get_init() is not None
        if not self.available:
            try:
                pygame.mixer.init()
                self.available = True
            except pygame.error as error:
                logger.warning("Audio indisponible, poursuite sans son : %s", error)
        if self.available:
            for name, filename in self.SOUND_FILES.items():
                try:
                    self.sounds[name] = pygame.mixer.Sound(str(asset_dir / "sounds" / filename))
                except (pygame.error, OSError) as error:
                    logger.warning("Effet %s indisponible : %s", filename, error)
            self.set_volume(self.volume)

    def play(self, name):
        sound = self.sounds.get(name)
        if sound is not None:
            sound.play()

    def set_volume(self, volume):
        self.volume = max(0.0, min(1.0, volume))
        if self.available:
            pygame.mixer.music.set_volume(self.volume)
            for sound in self.sounds.values():
                sound.set_volume(self.volume * 0.7)

    def play_music(self):
        if self.available:
            try:
                pygame.mixer.music.load(str(self.asset_dir / "background_music.mp3"))
                pygame.mixer.music.play(-1)
            except (pygame.error, OSError) as error:
                logger.warning("Musique indisponible : %s", error)

    def stop_music(self):
        if self.available:
            pygame.mixer.music.stop()
