"""Tests de comportement sans fenêtre ni périphérique audio nécessaires."""

import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pygame

from Notundertale.app import App
from Notundertale.assets import Assets
from Notundertale.audio import Audio
from Notundertale.config import ASSET_DIR
from Notundertale.difficulty import compute_difficulty
from Notundertale.game import Game
from Notundertale.player import Player
from Notundertale.input import InputState
from Notundertale.scores import load_scores, save_score
from Notundertale.sprites import HeartPowerUp, Meteor1, ShieldPowerUp
from Notundertale.timing import GameClock


class GameTests(unittest.TestCase):
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
        self.ticks = 100
        clock = GameClock(lambda: self.ticks)
        self.app = SimpleNamespace(screen=self.screen, assets=self.assets, clock=clock,
                                   now_ms=clock.now, selected_skin="default",
                                   speed_multiplier=1.0, audio=Mock(), inputs=Mock())
        self.keys = InputState()
        self.game = Game(self.app)
        self.player = self.game.player

    def advance(self, milliseconds):
        self.ticks += milliseconds

    def overlapping(self, group):
        sprite = pygame.sprite.Sprite()
        sprite.image = self.player.image.copy()
        sprite.mask = self.player.mask.copy()
        sprite.rect = self.player.rect.copy()
        self.game.add_sprite(sprite, group)
        return sprite

    def test_dash_starts_ready_and_recharges_at_five_seconds(self):
        self.assertEqual(self.player.dash_progress(), 1)
        self.assertTrue(self.player.start_dash(self.keys))
        self.assertFalse(self.player.start_dash(self.keys))
        self.assertEqual(self.player.dash_progress(), 0)
        self.advance(199)
        self.player.update(self.keys)
        self.assertTrue(self.player.dashing)
        self.advance(1)
        self.player.update(self.keys)
        self.assertFalse(self.player.dashing)
        self.advance(2300)
        self.assertEqual(self.player.dash_progress(), 0.5)
        self.advance(2499)
        self.assertFalse(self.player.can_dash())
        self.advance(1)
        self.assertTrue(self.player.can_dash())
        self.app.audio.play.assert_called_once_with("dash")

    def test_diagonal_dash_and_screen_bounds(self):
        self.keys.x = -1
        self.keys.y = -1
        self.player.start_dash(self.keys)
        self.assertAlmostEqual(self.player.dash_dir.length(), 1)
        for _ in range(100):
            self.player.update(self.keys)
        self.assertEqual(self.player.rect.topleft, (0, 0))

    def test_pause_freezes_score_dash_and_bonus_lifetime(self):
        bonus = HeartPowerUp(self.app)
        group = pygame.sprite.Group(bonus)
        self.player.start_dash(self.keys)
        self.advance(1200)
        self.app.clock.pause()
        remaining = self.player.dash_remaining_ms()
        self.advance(20_000)
        self.assertEqual(self.app.now_ms(), 1200)
        self.assertEqual(self.player.dash_remaining_ms(), remaining)
        bonus.update()
        self.assertIn(bonus, group)
        self.app.clock.resume()
        self.game.update(self.keys)
        self.assertEqual(self.game.score, 1200)
        self.advance(3800)
        bonus.update()
        self.assertNotIn(bonus, group)
        self.assertTrue(self.player.can_dash())

    def test_one_hit_when_meteor_and_laser_overlap(self):
        self.overlapping(self.game.projectiles)
        self.overlapping(self.game.lasers)
        self.game.handle_collisions(0)
        self.assertEqual(self.player.health, 2)
        self.game.handle_collisions(0)
        self.assertEqual(self.player.health, 2)
        self.app.audio.play.assert_called_once_with("hit")

    def test_dash_and_shield_prevent_damage_and_hit_sound(self):
        self.overlapping(self.game.projectiles)
        self.player.start_dash(self.keys)
        self.app.audio.reset_mock()
        self.game.handle_collisions(0)
        self.assertEqual(self.player.health, 3)
        self.advance(200)
        self.player.update(self.keys)
        self.game.shield_until = 3000
        self.overlapping(self.game.projectiles)
        self.game.handle_collisions(200)
        self.app.audio.play.assert_not_called()
        self.advance(2800)
        self.game.handle_collisions(3000)
        self.app.audio.play.assert_called_once_with("hit")

    def test_fatal_hit_plays_game_over_once_and_cannot_collect_heart(self):
        self.player.health = 1
        self.overlapping(self.game.projectiles)
        self.overlapping(self.game.lasers)
        self.overlapping(self.game.hearts)
        self.game.update(self.keys)
        self.assertEqual(self.player.health, 0)
        self.assertTrue(self.game.finished)
        self.assertEqual([call.args[0] for call in self.app.audio.play.call_args_list],
                         ["hit", "game_over"])
        self.game.update(self.keys)
        self.assertEqual(self.app.audio.play.call_count, 2)

    def test_both_pickup_types_play_sound_once(self):
        self.player.health = 2
        self.overlapping(self.game.shields)
        self.overlapping(self.game.hearts)
        self.game.handle_collisions(0)
        self.assertEqual(self.player.health, 3)
        self.assertEqual(self.game.shield_until, 3000)
        self.assertEqual(self.app.audio.play.call_count, 2)
        self.assertTrue(all(call.args == ("power_up",)
                            for call in self.app.audio.play.call_args_list))
        self.game.handle_collisions(0)
        self.assertEqual(self.app.audio.play.call_count, 2)

    def test_heart_at_full_health_is_collected(self):
        self.overlapping(self.game.hearts)
        self.game.handle_collisions(0)
        self.assertEqual(self.player.health, 3)
        self.assertFalse(self.game.hearts)
        self.app.audio.play.assert_called_once_with("power_up")

    def test_new_game_resets_score_difficulty_timers_and_dash(self):
        self.advance(150_000)
        self.game.update(self.keys)
        self.assertGreater(self.app.speed_multiplier, 1)
        new_game = Game(self.app)
        self.assertEqual(new_game.score, 0)
        self.assertEqual(self.app.speed_multiplier, 1)
        self.assertEqual(self.app.now_ms(), 0)
        self.assertEqual(new_game.next_laser, 30_000)
        self.assertTrue(new_game.player.can_dash())
        self.assertFalse(new_game.lasers)

    def test_laser_warning_then_laser_and_bonus_schedule(self):
        self.game.spawn_due(299)
        self.assertFalse(self.game.projectiles)
        self.game.spawn_due(300)
        self.assertEqual(len(self.game.projectiles), 1)
        self.game.spawn_due(15_000)
        self.assertEqual(len(self.game.shields), 1)
        self.assertFalse(self.game.hearts)
        self.game.spawn_due(28_000)
        self.assertEqual(len(self.game.warnings), 1)
        warning_x = self.game.laser_x
        self.game.spawn_due(30_000)
        self.assertFalse(self.game.warnings)
        self.assertEqual(next(iter(self.game.lasers)).rect.x, warning_x)
        self.game.spawn_due(40_000)
        self.assertEqual(len(self.game.hearts), 1)

    def test_assets_load_from_another_working_directory(self):
        original = Path.cwd()
        with tempfile.TemporaryDirectory() as folder:
            try:
                os.chdir(folder)
                assets = Assets((640, 480))
                self.assertEqual(assets.background.get_size(), (640, 480))
            finally:
                os.chdir(original)

    def test_powerup_alpha_does_not_change_other_sprites(self):
        first, second = ShieldPowerUp(self.app), ShieldPowerUp(self.app)
        first.image.set_alpha(50)
        self.assertEqual(second.image.get_alpha(), 255)
        self.assertEqual(self.app.assets.shield.get_alpha(), 255)

    def test_original_difficulty_cap_and_projectile_speeds(self):
        self.assertEqual(compute_difficulty(0), (0, 1.0, 300))
        self.assertEqual(compute_difficulty(20_000), (1, 1.1, 270))
        self.assertEqual(compute_difficulty(100_000), compute_difficulty(999_999))
        self.app.speed_multiplier = 1.5
        self.assertEqual(Meteor1(self.app).speed, 16.5)

    def test_quit_event_leaves_game(self):
        pygame.event.clear()
        pygame.event.post(pygame.event.Event(pygame.QUIT))
        self.assertEqual(self.game.run(), "quit")

    def test_game_pauses_on_disconnect_before_advancing(self):
        pygame.event.clear()
        self.app.inputs.release_actions.return_value = None
        self.app.inputs.sample.return_value = InputState(pause=False)
        def disconnected_sample():
            self.app.inputs.disconnected = True
            return InputState()
        self.app.inputs.sample.side_effect = disconnected_sample
        with patch("Notundertale.game.show_pause_menu", return_value="quit") as menu:
            with patch.object(self.game, "update") as update:
                self.assertEqual(self.game.run(), "quit")
        self.assertEqual(menu.call_args.args[2], "Manette déconnectée")
        update.assert_not_called()
        self.assertIsNone(self.app.clock._paused_at)

    def test_restart_reenters_game_without_main_menu(self):
        with patch("Notundertale.app.show_main_menu", side_effect=["infinite", "quit"]) as menu:
            with patch("Notundertale.app.Game") as game_class:
                game_class.return_value.run.side_effect = ["restart", "menu"]
                App.run(self.app)
        self.assertEqual(game_class.call_count, 2)
        self.assertEqual(menu.call_count, 2)


class PersistenceAndAudioTests(unittest.TestCase):
    def test_scores_sort_limit_and_existing_format(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "scores.json"
            path.write_text(json.dumps({"scores": [
                {"score": "8", "date": "2020-01-01", "skin": "skin1"},
                {"score": "bad"}, None]}), encoding="utf-8")
            for value in range(12):
                self.assertTrue(save_score(value, "default", path))
            scores = load_scores(path)
            self.assertEqual(len(scores), 10)
            self.assertEqual(scores[0]["score"], 11)
            tied = [entry for entry in scores if entry["score"] == 8]
            self.assertEqual(tied[0]["date"], "2020-01-01")

    def test_corrupt_score_file_does_not_crash(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "scores.json"
            for content in ("{broken", "null", '{"scores": 4}'):
                path.write_text(content, encoding="utf-8")
                self.assertEqual(load_scores(path), [])
                self.assertTrue(save_score(42, "default", path))

    def test_missing_audio_device_is_optional(self):
        with patch("pygame.mixer.get_init", return_value=None):
            with patch("pygame.mixer.init", side_effect=pygame.error("No audio device")):
                with self.assertLogs("Notundertale.audio", level="WARNING"):
                    audio = Audio()
        self.assertFalse(audio.available)
        audio.play("dash")
        audio.play_music()
        audio.stop_music()
        audio.set_volume(0.4)

    def test_sound_files_decode_and_master_volume_mutes_them(self):
        pygame.mixer.init()
        try:
            audio = Audio()
            self.assertEqual(set(audio.sounds), {"hit", "dash", "power_up", "game_over"})
            for sound in audio.sounds.values():
                self.assertGreater(sound.get_length(), 0.05)
            audio.set_volume(0)
            self.assertEqual(pygame.mixer.music.get_volume(), 0)
            self.assertTrue(all(sound.get_volume() == 0 for sound in audio.sounds.values()))
            audio.set_volume(5)
            self.assertEqual(audio.volume, 1)
        finally:
            pygame.mixer.quit()

    def test_missing_sound_files_are_optional(self):
        pygame.mixer.init()
        try:
            with tempfile.TemporaryDirectory() as folder:
                with self.assertLogs("Notundertale.audio", level="WARNING"):
                    audio = Audio(Path(folder))
                audio.play("hit")
                self.assertEqual(audio.sounds, {})
        finally:
            pygame.mixer.quit()

    def test_importing_game_does_not_open_a_window(self):
        result = subprocess.run([sys.executable, "-c",
            "import pygame; import Notundertale.app; import Notundertale.notundertalev1006; "
            "assert not pygame.display.get_init(); assert not pygame.mixer.get_init()"],
            cwd=ASSET_DIR.parent, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
