"""Les clics restent utilisables après adaptation des menus à l'écran."""

import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import pygame

from Notundertale.controls import ControlSettings
from Notundertale.controls_menu import show_controls_menu
from Notundertale.input import InputManager
from Notundertale.menus import show_main_menu


class ScaledMenuTests(unittest.TestCase):
    def setUp(self):
        pygame.display.init()
        pygame.font.init()
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.settings = ControlSettings(Path(self.folder.name) / "controls.json")
        with patch("pygame.joystick.get_count", return_value=0):
            self.inputs = InputManager(self.settings)

    def tearDown(self):
        pygame.quit()

    def app_at(self, size):
        image = pygame.Surface((32, 32))
        return SimpleNamespace(screen=pygame.display.set_mode(size), inputs=self.inputs,
                               assets=SimpleNamespace(skins={"default": image, "skin2": image}),
                               selected_skin="default")

    def click(self, size, logical_pos):
        scale = min(size[0] / 1280, size[1] / 720)
        x = (size[0] - 1280 * scale) / 2 + logical_pos[0] * scale
        y = (size[1] - 720 * scale) / 2 + logical_pos[1] * scale
        return pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(round(x), round(y)))

    def test_play_button_at_wide_and_letterboxed_resolutions(self):
        for size in ((1280,720), (1920,1080), (1024,768)):
            with self.subTest(size=size):
                app = self.app_at(size)
                with patch("pygame.event.get", side_effect=[
                    [self.click(size, (360,308))], [pygame.event.Event(pygame.QUIT)]]):
                    self.assertEqual(show_main_menu(app), "infinite")

    def test_mouse_skin_selection_matches_scaled_card(self):
        size = (1920,1080)
        app = self.app_at(size)
        with patch("pygame.event.get", side_effect=[
            [self.click(size, (1070,404))],
            [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)],
            [pygame.event.Event(pygame.QUIT)]]):
            self.assertEqual(show_main_menu(app), "infinite")
        self.assertEqual(app.selected_skin, "skin2")

    def test_scaled_settings_cell_still_rebinds_and_saves(self):
        size = (1024,768)
        app = self.app_at(size)
        with patch("pygame.event.get", side_effect=[
            [self.click(size, (415,197))],
            [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_z)],
            [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)],
            [pygame.event.Event(pygame.QUIT)]]):
            self.assertEqual(show_controls_menu(app), "back")
        self.assertEqual(ControlSettings(self.settings.path).keyboard["up"], pygame.K_z)


if __name__ == "__main__":
    unittest.main()
