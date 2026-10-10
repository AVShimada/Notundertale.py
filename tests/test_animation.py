"""Animations en situation : état, temps, collision et partage des images."""

import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import pygame

from Notundertale.assets import Assets
from Notundertale.controls import ControlSettings
from Notundertale.input import InputManager, InputState
from Notundertale.player import Player
from Notundertale.story.game import StoryGame
from Notundertale.timing import GameClock

NAMES = ("remanent", "scaphandre", "colonie", "deriveur")


class AnimationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.display.init()
        pygame.font.init()
        cls.screen = pygame.display.set_mode((1280, 720))
        cls.assets = Assets(cls.screen.get_size())

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        with patch("pygame.joystick.get_count", return_value=0):
            inputs = InputManager(ControlSettings(Path(self.folder.name) / "controls.json"))
        self.ticks = 0
        clock = GameClock(lambda: self.ticks)
        self.app = SimpleNamespace(screen=self.screen, assets=self.assets, inputs=inputs,
                                   clock=clock, now_ms=clock.now, selected_skin="remanent", audio=Mock())

    def test_frames_are_distinct_full_transparent_cells(self):
        for name in NAMES:
            frames = self.assets.animation_frames[name]
            self.assertEqual(len(frames), 8)
            self.assertEqual(len({pygame.image.tostring(f, "RGBA") for f in frames[:6]}), 6)
            for frame in frames:
                self.assertEqual(frame.get_size(), (100, 100))
                self.assertEqual(frame.get_at((0, 0)).a, 0)
                bounds = frame.get_bounding_rect(min_alpha=128)
                self.assertGreater(bounds.width, 30)
                self.assertGreater(bounds.height, 60)
                self.assertEqual(bounds.bottom, 97)
                self.assertGreater(bounds.left, 0)
                self.assertLess(bounds.right, 100)

    def test_walk_cycles_stop_returns_to_idle_and_states_have_priority(self):
        for name in NAMES:
            animation = self.assets.character_animation(name)
            indices = set()
            for _ in range(12):
                animation.update(0.1, 28)
                indices.add(animation.frame_index)
            self.assertEqual(indices, set(range(6)))
            animation.update(0.1)
            self.assertEqual(animation.state, "idle")
            self.assertIs(animation.image(), self.assets.skins[name])
            animation.update(0.1, 28, airborne=True)
            self.assertEqual(animation.state, "air")
            animation.update(0.1, 70, airborne=True, dashing=True)
            self.assertEqual(animation.state, "dash")

    def test_walking_cadence_is_independent_of_frame_rate(self):
        phases = []
        for fps in (30, 60, 144):
            animation = self.assets.character_animation("remanent")
            for _ in range(fps):
                animation.update(1 / fps, 280 / fps)
            phases.append(animation.phase)
        self.assertAlmostEqual(phases[0], phases[1])
        self.assertAlmostEqual(phases[0], phases[2])

    def test_infinite_uses_animated_mask_both_directions(self):
        for name in NAMES:
            self.app.selected_skin = name
            player = Player(self.app)
            for direction in (-1, 1):
                self.ticks += 100
                player.update(InputState(x=direction))
                expected = player.animation.image(direction < 0)
                self.assertEqual(pygame.image.tostring(player.image, "RGBA"), pygame.image.tostring(expected, "RGBA"))
                self.assertEqual(player.mask.count(), pygame.mask.from_surface(expected).count())
                sprite = pygame.sprite.Sprite()
                sprite.image = pygame.Surface((1, 1), pygame.SRCALPHA)
                sprite.image.fill("white")
                sprite.mask = pygame.mask.from_surface(sprite.image)
                opaque = next((x, y) for y in range(100) for x in range(100) if player.mask.get_at((x, y)))
                sprite.rect = pygame.Rect(player.rect.x + opaque[0], player.rect.y + opaque[1], 1, 1)
                self.assertIsNotNone(pygame.sprite.collide_mask(player, sprite))
                sprite.rect.topleft = player.rect.topleft
                self.assertIsNone(pygame.sprite.collide_mask(player, sprite))

    def test_dash_alpha_does_not_modify_shared_pose_or_other_player(self):
        first, second = Player(self.app), Player(self.app)
        first.update(InputState(x=1, dash=True))
        self.assertEqual(first.animation.state, "dash")
        self.assertEqual(first.image.get_alpha(), 180)
        self.assertEqual(second.animation.state, "idle")
        self.assertEqual(second.image.get_alpha(), 255)
        self.assertTrue(all(f.get_alpha() == 255 for f in self.assets.animation_frames["remanent"]))

    def test_story_moves_jumps_dashes_and_stops_at_wall(self):
        game = StoryGame(self.app)
        game.phase = "playing"
        player = game.player
        for _ in range(20):
            game.update(InputState(x=1), 1 / 60)
        self.assertEqual(player.animation.state, "walk")
        self.assertNotEqual(player.animation.frame_index, 0)
        game.update(InputState(jump=True), 1 / 60)
        self.assertEqual(player.animation.state, "air")
        game.update(InputState(dash=True), 1 / 60)
        self.assertEqual(player.animation.state, "dash")
        player.place(game.room.width - player.rect.width, 600)
        player.dash_left = 0
        game.update(InputState(x=1), 1 / 60)
        self.assertEqual(player.animation.state, "idle")
        self.assertEqual(player.rect.size, (44, 86))

    def test_story_rendering_does_not_advance_pose_during_pause(self):
        game = StoryGame(self.app)
        game.phase = "playing"
        game.update(InputState(x=1), 0.1)
        pose = (game.player.animation.state, game.player.animation.phase)
        self.app.clock.pause()
        self.ticks += 20_000
        for _ in range(4):
            game.draw()
        self.assertEqual((game.player.animation.state, game.player.animation.phase), pose)

    def test_infinite_animation_ignores_time_spent_in_pause(self):
        player = Player(self.app)
        self.ticks = 100
        player.update(InputState(x=1))
        phase = player.animation.phase
        self.app.clock.pause()
        self.ticks += 30_000
        self.app.clock.resume()
        player.update(InputState(x=1))
        self.assertEqual(player.animation.phase, phase)

    def test_classic_skins_remain_valid_without_sheets(self):
        for name in ("default", "skin2"):
            animation = self.assets.character_animation(name)
            for kwargs in ({"distance": 28}, {"airborne": True}, {"dashing": True}):
                animation.update(0.1, **kwargs)
                self.assertIs(animation.image(), self.assets.skins[name])


if __name__ == "__main__":
    unittest.main()
