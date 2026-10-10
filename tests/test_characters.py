"""Les personnages 100 × 100 sont sélectionnables et leurs collisions suivent le sprite."""
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import pygame

from Notundertale.assets import Assets
from Notundertale.config import ASSET_DIR
from Notundertale.controls import ControlSettings
from Notundertale.game import Game
from Notundertale.input import InputManager, InputState
from Notundertale.menus import show_main_menu
from Notundertale.skins import PLAYER_SPRITE_SIZE, SKINS
from Notundertale.timing import GameClock

MINI_NAMES = ("remanent", "scaphandre", "colonie", "deriveur")


class MiniCharacterTests(unittest.TestCase):
    def setUp(self):
        pygame.display.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((1280, 720))
        self.assets = Assets(self.screen.get_size())
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        with patch("pygame.joystick.get_count", return_value=0):
            inputs = InputManager(ControlSettings(Path(self.folder.name) / "controls.json"))
        clock = GameClock(lambda: 0)
        self.app = SimpleNamespace(screen=self.screen, assets=self.assets, clock=clock,
                                   now_ms=clock.now, selected_skin="remanent",
                                   audio=Mock(), inputs=inputs, speed_multiplier=1.0)

    def tearDown(self):
        pygame.quit()

    def game_with(self, name):
        self.app.selected_skin = name
        return Game(self.app)

    def test_delivered_sprites_are_native_size_transparent_and_distinct(self):
        pixels = set()
        for name in MINI_NAMES:
            with self.subTest(name=name):
                image = pygame.image.load(str(ASSET_DIR / SKINS[name].filename))
                self.assertEqual(image.get_size(), PLAYER_SPRITE_SIZE)
                self.assertEqual(image.get_at((0, 0)).a, 0)
                mask = pygame.mask.from_surface(image)
                self.assertGreater(mask.count(), 1000)
                self.assertLess(mask.count(), 100 * 100 * 0.8)
                pixels.add(pygame.image.tostring(image, "RGBA"))
                player = self.game_with(name).player
                self.assertEqual(pygame.image.tostring(player.image, "RGBA"),
                                 pygame.image.tostring(image, "RGBA"))
                self.assertEqual(player.rect.size, (100, 100))
                self.assertEqual(player.image.get_bounding_rect(min_alpha=128).height,
                                 self.assets.skins["skin2"].get_bounding_rect(min_alpha=128).height)
        self.assertEqual(len(pixels), 4)

    def test_transparent_margin_misses_but_visible_body_takes_damage_both_directions(self):
        for name in MINI_NAMES:
            for direction in (-1, 1):
                with self.subTest(name=name, direction=direction):
                    game = self.game_with(name)
                    player = game.player
                    player.update(InputState(x=direction))
                    bullet = pygame.sprite.Sprite()
                    bullet.image = pygame.Surface((1, 1), pygame.SRCALPHA)
                    bullet.image.fill("white")
                    bullet.mask = pygame.mask.from_surface(bullet.image)
                    bullet.rect = bullet.image.get_rect(topleft=player.rect.topleft)
                    game.add_sprite(bullet, game.projectiles)
                    game.handle_collisions(0)
                    self.assertEqual(player.health, 3)
                    point = next((x, y) for y in range(player.rect.height) for x in range(player.rect.width)
                                 if player.mask.get_at((x, y)))
                    bullet.rect.topleft = (player.rect.x + point[0], player.rect.y + point[1])
                    game.handle_collisions(0)
                    self.assertEqual(player.health, 2)
                    self.assertFalse(game.projectiles)

    def test_miniature_dash_stays_on_screen_and_restart_keeps_the_skin(self):
        for name in MINI_NAMES:
            with self.subTest(name=name):
                game = self.game_with(name)
                game.player.rect.topleft = (1, 1)
                game.player.update(InputState(x=-1, y=-1, dash=True))
                self.assertEqual(game.player.rect.topleft, (0, 0))
                self.assertTrue(game.player.dashing)
                self.assertEqual(game.player.image.get_size(), (100, 100))
                restarted = Game(self.app)
                self.assertEqual(restarted.player.image.get_size(), (100, 100))
                self.assertEqual(restarted.player.image.get_alpha(), 255)
                self.assertTrue(restarted.player.can_dash())

    def test_all_six_cards_launch_the_selected_skin_at_scaled_resolutions(self):
        for size in ((1280, 720), (1920, 1080), (1024, 768)):
            self.app.screen = pygame.display.set_mode(size)
            scale = min(size[0] / 1280, size[1] / 720)
            for i, name in enumerate(SKINS):
                with self.subTest(size=size, name=name):
                    logical = (854 + i % 3 * 136, 360 + i // 3 * 128)
                    position = (round((size[0] - 1280 * scale) / 2 + logical[0] * scale),
                                round((size[1] - 720 * scale) / 2 + logical[1] * scale))
                    events = [[pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=position)],
                              [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)],
                              [pygame.event.Event(pygame.QUIT)]]
                    with patch("pygame.event.get", side_effect=events):
                        self.assertEqual(show_main_menu(self.app), "infinite")
                    self.assertEqual(self.app.selected_skin, name)
                    self.assertEqual(Game(self.app).player.rect.size, SKINS[name].size)

    def test_direction_selection_wraps_through_both_rows(self):
        names = list(SKINS)
        for key, expected in ((pygame.K_RIGHT, names[1:]+names[:1]),
                              (pygame.K_LEFT, list(reversed(names)))):
            for name in expected:
                events = [[pygame.event.Event(pygame.KEYDOWN, key=key)],
                          [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)],
                          [pygame.event.Event(pygame.QUIT)]]
                with patch("pygame.event.get", side_effect=events):
                    self.assertEqual(show_main_menu(self.app), "infinite")
                self.assertEqual(self.app.selected_skin, name)


if __name__ == "__main__":
    unittest.main()
