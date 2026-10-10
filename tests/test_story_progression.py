"""Parcours Histoire : le combat, les restes et les soins partagent une seule partie."""

import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import Mock, call, patch

import pygame

from Notundertale.assets import Assets
from Notundertale.controls import ControlSettings
from Notundertale.input import InputManager, InputState
from Notundertale.story.enemies import Alien
from Notundertale.story.experience import ExperienceDrop
from Notundertale.story.game import StoryGame
from Notundertale.story.rooms import FLOOR_Y
from Notundertale.timing import GameClock


class StoryProgressionTests(unittest.TestCase):
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
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        settings = ControlSettings(Path(folder.name) / "controls.json")
        with patch("pygame.joystick.get_count", return_value=0):
            inputs = InputManager(settings)
        self.app = SimpleNamespace(screen=self.screen, assets=self.assets, inputs=inputs,
                                   clock=GameClock(), audio=Mock(), selected_skin="remanent")
        # Le rendu est testé ailleurs ; garder ici les vrais assets, entrées,
        # salles, collisions et animations sans construire sept fonds par cas.
        renderer = patch("Notundertale.story.game.StoryRenderer")
        renderer.start()
        self.addCleanup(renderer.stop)
        self.game = StoryGame(self.app, seed=60727)
        self.game.phase = "playing"

    def play(self, duration, state=None):
        for _ in range(round(duration * 120)):
            self.game.update(state or InputState(), 1 / 120)

    def equip(self, weapon_id):
        self.game.weapon.equip(weapon_id)
        self.game.player.has_weapon = True

    def add_drop(self, value, position=None):
        drop = ExperienceDrop(pygame.Vector2(position or self.game.player.rect.center), value)
        self.game.room.xp_drops.append(drop)
        return drop

    def test_shooting_leaves_one_drop_without_awarding_xp_until_approach(self):
        game = self.game
        self.equip("raygun")
        game.player.place(200, FLOOR_Y)
        enemy = Alien(550, FLOOR_Y - 44)
        game.room.enemies = [enemy]
        self.play(.5, InputState(shoot=True))
        self.assertEqual(enemy.health, 0)
        self.assertTrue(enemy.rewarded)
        self.assertEqual((game.progression.kills, game.progression.total_xp), (1, 0))
        self.assertEqual(len(game.room.xp_drops), 1)
        drop = game.room.xp_drops[0]
        self.assertEqual(drop.value, 10)
        self.play(.5, InputState(shoot=True))
        self.assertEqual((len(game.room.xp_drops), game.progression.kills), (1, 1))
        self.assertFalse(drop.attracted)
        game.player.place(round(drop.pos.x) - 22, FLOOR_Y)
        self.play(.2)
        self.assertTrue(drop.collected)
        self.assertEqual((game.progression.xp, game.progression.total_xp), (10, 10))
        self.assertFalse(game.room.xp_drops)
        self.play(.2)
        self.assertEqual(game.progression.total_xp, 10)

    def test_multiple_absorptions_level_up_without_freezing_player_or_enemy(self):
        game = self.game
        game.player.health = 60
        enemy = Alien(650, FLOOR_Y - 44)
        game.room.enemies = [enemy]
        self.add_drop(100)
        self.add_drop(250)
        player_x, enemy_x = game.player.pos.x, enemy.pos.x
        game.update(InputState(x=1), .05)
        self.assertEqual((game.progression.level, game.progression.xp), (3, 115))
        self.assertEqual((game.player.max_health, game.player.health), (140, 100))
        self.assertAlmostEqual(game.player.damage_multiplier, 1.24)
        self.assertGreater(game.level_flash, 0)
        self.assertEqual(game.phase, "playing")
        self.assertGreater(game.player.pos.x, player_x)
        self.assertLess(enemy.pos.x, enemy_x)
        self.assertFalse(game.room.xp_drops)
        self.assertIn(call("power_up"), self.app.audio.play.call_args_list)
        game.update(InputState(x=1), .05)
        self.assertGreater(game.player.pos.x, player_x + 14)

    def test_five_kills_recharge_before_any_experience_is_collected(self):
        game = self.game
        game.player.health = 20
        game.update(InputState(heal=True), 1 / 120)
        self.assertEqual((game.player.health, game.progression.heal_charges), (60, 0))
        enemies = [Alien(1100 + index * 60, FLOOR_Y - 44) for index in range(5)]
        game.room.enemies = enemies
        for index, enemy in enumerate(enemies):
            enemy.health = 0
            game.update(InputState(), 1 / 120)
            self.assertEqual(game.progression.kills, index + 1)
            self.assertEqual(game.progression.heal_charges, int(index == 4))
        self.assertEqual((game.progression.heal_kills, game.progression.total_xp), (0, 0))
        self.assertEqual(len(game.room.xp_drops), 5)
        self.play(.1)
        self.assertEqual((game.progression.kills, game.progression.heal_charges), (5, 1))

    def test_boss_death_restores_only_one_charge_and_drops_250_xp_once(self):
        game = self.game
        game.progression.level = 5
        game.progression.heal_charges = 0
        game.progression.heal_kills = 3
        boss = Alien(1200, FLOOR_Y - 44)
        boss.is_boss = True
        boss.health = 0
        game.room.enemies = [boss]
        self.play(.05)
        self.assertEqual((game.progression.heal_charges, game.progression.heal_kills), (1, 0))
        self.assertEqual((game.progression.kills, game.progression.total_xp), (1, 0))
        self.assertEqual([drop.value for drop in game.room.xp_drops], [250])

    def test_level_five_grants_second_charge_and_held_heal_uses_only_one(self):
        game = self.game
        game.progression.level = 4
        game.progression.xp = 249
        game.progression.total_xp = 669
        game.player.health = 140
        self.add_drop(1)
        game.update(InputState(), 1 / 120)
        self.assertEqual((game.progression.level, game.progression.heal_capacity,
                          game.progression.heal_charges), (5, 2, 2))
        self.assertEqual((game.player.health, game.player.max_health), (160, 180))
        game.update(InputState(heal=True), 1 / 120)
        self.assertEqual((game.player.health, game.progression.heal_charges), (180, 1))
        game.player.health = 20
        self.play(.25, InputState(heal=True))
        self.assertEqual((game.player.health, game.progression.heal_charges), (20, 1))
        game.update(InputState(), 1 / 120)
        game.update(InputState(heal=True), 1 / 120)
        self.assertEqual((game.player.health, game.progression.heal_charges), (92, 0))

    def test_direct_slots_while_firing_cannot_reset_raygun_cooldown(self):
        game = self.game
        self.equip("rifle")
        self.equip("raygun")
        game.update(InputState(shoot=True), 1 / 120)
        game.update(InputState(shoot=True, weapon_1=True), 1 / 120)
        self.assertEqual(game.weapon.current, "rifle")
        game.update(InputState(shoot=True, weapon_2=True), 1 / 120)
        self.assertEqual(game.weapon.current, "raygun")
        self.assertEqual(self.app.audio.play.call_args_list.count(call("ray")), 2)
        self.assertGreater(game.weapon.cooldown, .5)
        # Re-sélectionner une arme déjà active ne doit pas annoncer un slot vide.
        game.update(InputState(), 1 / 120)
        game.update(InputState(weapon_2=True), 1 / 120)
        self.assertNotIn("vide", game.notice_text.lower())
        game.weapon.slots.pop()
        game.weapon.selected = 0
        game.update(InputState(), 1 / 120)
        game.update(InputState(weapon_2=True), 1 / 120)
        self.assertEqual(game.weapon.current, "rifle")
        self.assertIn("vide", game.notice_text.lower())

    def test_deaths_and_uncollected_drops_survive_room_round_trip(self):
        game = self.game
        self.equip("rifle")
        door = game.room.doors[0]
        game.player.place(door.x - 22, FLOOR_Y)
        game.interact()
        combat_name = game.current_room
        combat_room = game.room
        enemy = combat_room.enemies[0]
        enemy.health = 0
        game.update(InputState(), 1 / 120)
        drop = combat_room.xp_drops[0]
        self.assertEqual(game.progression.kills, 1)
        back = next(door for door in combat_room.doors if door.target == "cockpit")
        game.player.place(back.x - 22, FLOOR_Y)
        game.interact()
        self.assertEqual(game.current_room, "cockpit")
        forward = next(door for door in game.room.doors if door.target == combat_name)
        game.player.place(forward.x - 22, FLOOR_Y)
        game.interact()
        game.update(InputState(), 1 / 120)
        self.assertIs(game.room, combat_room)
        self.assertIs(game.room.xp_drops[0], drop)
        self.assertTrue(enemy.rewarded)
        self.assertEqual((game.progression.kills, game.progression.total_xp), (1, 0))

    def test_death_stops_absorption_and_restart_resets_run_with_new_seed(self):
        game = self.game
        self.equip("raygun")
        game.progression.level = 5
        game.progression.xp = 12
        game.progression.heal_charges = 0
        game.progression.heal_kills = 4
        game.player.health = 1
        enemy = Alien(game.player.rect.x, FLOOR_Y - 44)
        enemy.phase, enemy.timer = "attack", 1.0
        game.room.enemies = [enemy]
        drop = self.add_drop(250)
        game.update(InputState(), 1 / 120)
        self.assertEqual((game.phase, game.player.health), ("dead", 0))
        self.assertFalse(drop.collected)
        self.play(.5, InputState(heal=True, shoot=True, x=1))
        self.assertEqual(game.progression.xp, 12)
        self.assertEqual(self.app.audio.play.call_args_list.count(call("game_over")), 1)
        random_source = Mock(side_effect=[game.seed, game.seed + 1])
        with patch("Notundertale.story.game.random.SystemRandom",
                   return_value=SimpleNamespace(getrandbits=random_source)):
            fresh = StoryGame(self.app)
        self.assertEqual(fresh.seed, game.seed + 1)
        self.assertEqual(random_source.call_count, 2)
        self.assertEqual((fresh.progression.level, fresh.progression.xp,
                          fresh.progression.heal_charges, fresh.progression.heal_kills), (1, 0, 1, 0))
        self.assertEqual(fresh.player.health, 100)
        self.assertFalse(fresh.player.has_weapon or fresh.weapon.slots)
        self.assertEqual(fresh.phase, "awakening")
        self.assertEqual(fresh.visited, {"cockpit"})
        self.assertTrue(all(not room.xp_drops for room in fresh.rooms.values()))
        self.assertTrue(all(enemy.health == enemy.max_health and not enemy.rewarded
                            for room in fresh.rooms.values() for enemy in room.enemies))
        self.assertNotEqual([room.decor_seed for room in game.rooms.values()],
                            [room.decor_seed for room in fresh.rooms.values()])


if __name__ == "__main__":
    unittest.main()
