"""Démarrage de Pygame et navigation entre les écrans."""

import argparse

import pygame

from .assets import Assets
from .audio import Audio
from .game import Game
from .input import InputManager
from .menus import show_coming_soon_screen, show_main_menu
from .timing import GameClock
from .skins import DEFAULT_SKIN


class App:
    def __init__(self, windowed=False):
        # Initialiser l'affichage séparément permet de jouer même sans audio.
        pygame.display.init()
        pygame.font.init()
        pygame.key.set_repeat(350, 130)
        if windowed:
            self.screen = pygame.display.set_mode((1280, 720))
        else:
            info = pygame.display.Info()
            self.screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
        pygame.display.set_caption("NotUndertale")
        self.assets = Assets(self.screen.get_size())
        self.audio = Audio()
        self.clock = GameClock()
        self.selected_skin = DEFAULT_SKIN
        self.speed_multiplier = 1.0
        self.inputs = InputManager()

    def now_ms(self):
        return self.clock.now()

    def run(self):
        while True:
            mode = show_main_menu(self)
            if mode == "quit":
                return
            if mode == "story":
                if show_coming_soon_screen(self) == "quit":
                    return
            elif mode == "infinite":
                action = "restart"
                while action == "restart":
                    action = Game(self).run()
                if action == "quit":
                    return


def main():
    parser = argparse.ArgumentParser(description="NotUndertale")
    parser.add_argument("--windowed", action="store_true", help="Jouer en fenêtre (1280 × 720)")
    args = parser.parse_args()
    try:
        App(windowed=args.windowed).run()
    finally:
        pygame.quit()
