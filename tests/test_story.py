"""Parcours jouable, physique, combats et isolation des commandes Histoire."""

import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

from collections import defaultdict
import tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import pygame

from Notundertale.app import App
from Notundertale.assets import Assets
from Notundertale.controls import Binding, ControlSettings, STORY_KEYS
from Notundertale.controls_menu import show_controls_menu
from Notundertale.input import InputManager, InputState
from Notundertale.story.game import StoryGame, show_story_result
from Notundertale.story.player import StoryPlayer
from Notundertale.story.rooms import FLOOR_Y, make_rooms
from Notundertale.timing import GameClock
from test_controls import FakePad


class StoryTests(unittest.TestCase):
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
        self.settings = ControlSettings(Path(self.folder.name) / "controls.json")
        with patch("pygame.joystick.get_count", return_value=0):
            self.inputs = InputManager(self.settings)
        clock = GameClock()
        self.app = SimpleNamespace(screen=self.screen, assets=self.assets, clock=clock,
                                   inputs=self.inputs, audio=Mock(), selected_skin="remanent")
        self.game = StoryGame(self.app, seed=23)
        pygame.event.clear()

    def play(self, seconds, state=None, fps=60):
        for _ in range(round(seconds * fps)):
            self.game.update(state or InputState(), 1 / fps)

    def wake(self):
        self.play(2.5)
        self.assertEqual(self.game.phase, "playing")

    def press_interact(self):
        self.game.update(InputState(), 1 / 60)
        self.game.update(InputState(interact=True), 1 / 60)

    def test_wake_then_walk_jump_land_and_no_auto_jump(self):
        self.wake()
        player = self.game.player
        self.play(0.2, InputState(x=1))
        self.assertAlmostEqual(player.pos.x, 296, delta=1)
        self.play(0.3, InputState(jump=True))
        self.assertLess(player.rect.bottom, FLOOR_Y - 90)
        self.play(1, InputState(jump=True))
        self.assertEqual(player.rect.bottom, FLOOR_Y)
        self.assertTrue(player.grounded)
        self.play(0.3, InputState(jump=True))
        self.assertEqual(player.rect.bottom, FLOOR_Y)

    def test_jump_lands_on_platform_and_dash_cannot_cross_wall(self):
        self.wake()
        player = self.game.player
        player.place(720, FLOOR_Y)
        self.play(0.46, InputState(x=1, jump=True))
        self.play(0.5)
        self.assertEqual(player.rect.bottom, 484)
        self.assertTrue(player.grounded)
        player.place(780, FLOOR_Y)
        self.play(0.02, InputState(jump=True))
        self.assertGreaterEqual(player.rect.top, 508)
        player.place(1760, FLOOR_Y)
        self.play(0.2, InputState(x=1, dash=True))
        self.assertLessEqual(player.rect.right, self.game.room.width)

    def test_dash_protects_recharges_and_requires_new_press(self):
        self.wake()
        self.play(0.05, InputState(dash=True))
        player = self.game.player
        self.assertFalse(player.hurt())
        self.play(1.4, InputState(dash=True))
        self.assertEqual(player.cooldown, 0)
        self.assertEqual(self.app.audio.play.call_args_list.count(unittest.mock.call("dash")), 1)
        self.assertTrue(player.hurt())
        self.assertFalse(player.hurt())
        self.play(1.1)
        self.play(0.05, InputState(dash=True))
        self.assertGreater(player.cooldown, 0)

    def test_movement_is_stable_at_30_60_and_144_fps(self):
        positions = []
        for fps in (30, 60, 144):
            self.game.player = StoryPlayer()
            self.game.phase = "playing"
            self.game._held.clear()
            self.play(0.5, InputState(x=1, jump=True), fps)
            positions.append(self.game.player.pos.copy())
        for pos in positions[1:]:
            self.assertAlmostEqual(pos.x, positions[0].x, delta=1)
            self.assertAlmostEqual(pos.y, positions[0].y, delta=3)

    def test_complete_route_pickup_combat_return_and_finish(self):
        self.wake()
        route = list(self.game.rooms)
        self.play(1.2, InputState(x=1))
        self.press_interact()
        self.assertTrue(self.game.player.has_weapon)
        self.assertFalse(self.game.room.weapon_available)
        self.assertEqual(len(self.game.weapon.slots), 1)
        self.play(3.9, InputState(x=1))
        self.press_interact()
        self.assertEqual(self.game.current_room, route[1])
        self.assertEqual(self.game.visited, {"cockpit", route[1]})
        second_pickup = self.game.room.loot[0]
        self.game.player.place(second_pickup.x - 22, FLOOR_Y)
        self.press_interact()
        self.assertEqual(set(self.game.weapon.slots), {"rifle", "raygun"})
        self.assertTrue(second_pickup.collected)
        enemy = self.game.room.enemies[0]
        self.game.player.place(enemy.rect.x - 240, FLOOR_Y)
        self.play(1.1, InputState(shoot=True))
        self.assertEqual(enemy.health, 0)
        self.assertTrue(enemy.rewarded)
        self.assertGreaterEqual(self.game.progression.kills, 1)
        self.assertFalse(self.game.cleared)
        self.assertEqual(self.game.player.health, self.game.player.max_health)
        self.assertIn(unittest.mock.call("ray"), self.app.audio.play.call_args_list)
        back_door = next(door for door in self.game.room.doors if door.target == "cockpit")
        self.game.player.place(back_door.x - 22, FLOOR_Y)
        self.press_interact()
        self.assertEqual(self.game.current_room, "cockpit")
        self.assertFalse(self.game.room.weapon_available)
        self.game.player.place(self.game.room.doors[0].x - 22, FLOOR_Y)
        self.press_interact()
        self.assertEqual(self.game.current_room, route[1])
        self.assertEqual(enemy.health, 0)
        self.assertTrue(self.game.room.loot[0].collected)
        # Le combat ci-dessus utilise les vrais tirs. Pour vérifier les portes et
        # le verrou du sas sans simuler tous les combats, sécuriser chaque salle.
        for index, name in enumerate(route[1:], start=1):
            self.assertEqual(self.game.current_room, name)
            if self.game.room.is_exit:
                self.game.player.place(self.game.room.width - 152, FLOOR_Y)
                self.press_interact()
                self.assertEqual(self.game.phase, "playing")
                self.assertFalse(self.game.cleared)
            for creature in self.game.room.enemies:
                creature.health = 0
            self.play(0.02)
            if not self.game.room.is_exit:
                next_door = next(door for door in self.game.room.doors if door.target == route[index + 1])
                self.game.player.place(next_door.x - 22, FLOOR_Y)
                self.press_interact()
        self.assertTrue(self.game.cleared)
        self.assertEqual(self.game.visited, set(route))
        self.game.player.place(self.game.room.width - 152, FLOOR_Y)
        self.press_interact()
        self.assertEqual(self.game.phase, "complete")
        self.assertFalse(self.game.weapon.rays)

    def test_unarmed_door_and_uncleared_terminal_do_not_finish(self):
        self.wake()
        self.game.player.place(self.game.room.doors[0].x - 22, FLOOR_Y)
        self.press_interact()
        self.assertEqual(self.game.current_room, "cockpit")
        self.game.current_room = next(name for name, room in self.game.rooms.items() if room.is_exit)
        self.game.player.place(self.game.room.width - 152, FLOOR_Y)
        self.press_interact()
        self.assertEqual(self.game.phase, "playing")

    def test_walls_stop_rays_before_enemy(self):
        self.wake()
        self.game.current_room = list(self.game.rooms)[1]
        enemy = self.game.room.enemies[0]
        self.game.room.enemies = [enemy]
        enemy.place(580, 484)
        self.game.player.place(380, 484)
        self.game.player.has_weapon = True
        self.game.weapon.equip("raygun")
        self.game.room.platforms = ((460, 484, 180, 24), (480, 350, 20, 134))
        impacts = []
        for _ in range(22):
            self.game.update(InputState(shoot=True), 1 / 120)
            impacts.extend(self.game.weapon.impacts)
        self.assertEqual(enemy.health, enemy.max_health)
        self.assertIn(unittest.mock.call("ray"), self.app.audio.play.call_args_list)
        # Le canon plus long touche le mur plus tôt ; l'éclair peut déjà avoir
        # disparu à la fin des 0,18 s, mais l'impact doit avoir eu lieu sur le mur.
        self.assertTrue(impacts)
        self.assertTrue(all(x == 480 for x, _, _ in impacts))

    def test_alien_warns_then_attacks_and_fatal_hit_only_once(self):
        self.wake()
        self.game.current_room = list(self.game.rooms)[1]
        enemy = self.game.room.enemies[0]
        self.game.room.enemies = [enemy]
        self.game.player.place(enemy.rect.x - 110, FLOOR_Y)
        self.play(0.25)
        self.assertEqual(enemy.phase, "warn")
        self.assertEqual(self.game.player.health, self.game.player.max_health)
        self.game.player.health = 1
        self.play(0.5)
        self.assertEqual(self.game.phase, "dead")
        self.play(2)
        self.assertEqual(self.app.audio.play.call_args_list.count(unittest.mock.call("game_over")), 1)

    def test_restart_has_fresh_world_equipment_and_health(self):
        first_fight = list(self.game.rooms)[1]
        self.game.rooms[first_fight].enemies[0].health = 0
        self.game.rooms["cockpit"].loot[0].collected = True
        self.game.player.health = 1
        self.game.player.has_weapon = True
        self.game.weapon.equip("rifle")
        self.game.weapon.equip("raygun")
        self.game.progression.add_xp(700)
        self.game.progression.heal_charges = 0
        self.game.progression.kills = 12
        fresh = StoryGame(self.app)
        self.assertNotEqual(fresh.seed, self.game.seed)
        self.assertEqual(fresh.player.health, 100)
        self.assertEqual(fresh.player.max_health, 100)
        self.assertFalse(fresh.player.has_weapon)
        self.assertFalse(fresh.weapon.slots)
        self.assertEqual(fresh.progression.level, 1)
        self.assertEqual(fresh.progression.xp, 0)
        self.assertEqual(fresh.progression.total_xp, 0)
        self.assertEqual(fresh.progression.kills, 0)
        self.assertEqual(fresh.progression.heal_charges, 1)
        self.assertTrue(fresh.rooms["cockpit"].weapon_available)
        self.assertTrue(all(enemy.health == enemy.max_health for room in fresh.rooms.values() for enemy in room.enemies))
        self.assertFalse(fresh.cleared)
        self.assertEqual(fresh.visited, {"cockpit"})
        self.assertEqual(fresh.phase, "awakening")

    def test_story_xbox_and_rebindings_are_independent_and_saved(self):
        pad = FakePad()
        self.inputs.pads, self.inputs.active_id = {pad.id: pad}, pad.id
        pad.buttons[0] = pad.buttons[1] = pad.buttons[2] = pad.buttons[3] = True
        pad.axes[5] = 32767
        state = self.inputs.sample(defaultdict(bool))
        self.assertTrue(state.jump and state.dash and state.shoot and state.interact)
        story = self.inputs.settings
        story.bind_key("jump", pygame.K_z)
        story.bind_pad(pad.profile_name, True, "shoot", Binding("button", 9))
        loaded = ControlSettings(story.path, "story")
        self.assertEqual(loaded.keyboard["jump"], pygame.K_z)
        self.assertEqual(loaded.profile(pad.profile_name)["shoot"], [Binding("button", 9)])
        self.inputs.set_mode("infinite")
        self.assertIs(self.inputs.settings, self.settings)
        self.assertEqual(self.settings.keyboard["up"], pygame.K_UP)
        self.assertEqual(self.settings.profile(pad.profile_name)["dash"], [Binding("button", 0)])
        self.assertFalse(self.settings.path.exists())

    def test_menu_exit_blocks_held_jump_shoot_and_interact(self):
        keys = defaultdict(bool, {STORY_KEYS[action]: True for action in ("jump", "shoot", "interact")})
        with patch("pygame.key.get_pressed", return_value=keys):
            self.inputs.release_actions()
        state = self.inputs.sample(keys)
        self.assertFalse(state.jump or state.shoot or state.interact)
        self.inputs.sample(defaultdict(bool))
        with patch("pygame.mouse.get_pressed", return_value=(True, False, False)):
            state = self.inputs.sample(keys)
        self.assertTrue(state.jump and state.shoot and state.interact)

    def test_mouse_shoot_rebind_save_and_menu_click_suppression(self):
        keys = defaultdict(bool)
        with patch("pygame.mouse.get_pressed", return_value=(True, False, False)):
            self.assertTrue(self.inputs.sample(keys).shoot)
            self.inputs.release_actions()
            self.assertFalse(self.inputs.sample(keys).shoot)
        self.inputs.sample(keys)
        self.inputs.settings.bind_key("shoot", -3)
        saved = ControlSettings(self.inputs.settings.path, "story")
        self.assertEqual(saved.keyboard["shoot"], -3)
        with patch("pygame.mouse.get_pressed", return_value=(True, False, False)):
            self.assertFalse(self.inputs.sample(keys).shoot)
        with patch("pygame.mouse.get_pressed", return_value=(False, False, True)):
            self.assertTrue(self.inputs.sample(keys).shoot)

    def test_previous_defaults_migrate_without_changing_movement(self):
        import json
        settings = self.inputs.settings
        settings.keyboard["shoot"] = pygame.K_f
        settings.keyboard["left"] = pygame.K_q
        profile = settings.profile("sdl:old")
        profile.update(dash=[Binding("button", 1)], shoot=[Binding("axis", 5, 1)],
                       interact=[Binding("button", 2)])
        settings.save()
        data = json.loads(settings.path.read_text(encoding="utf-8"))
        data["version"] = 1
        settings.path.write_text(json.dumps(data), encoding="utf-8")
        loaded = ControlSettings(settings.path, "story")
        self.assertEqual(loaded.keyboard["shoot"], -1)
        self.assertEqual(loaded.keyboard["left"], pygame.K_q)
        self.assertEqual(loaded.profile("sdl:old")["shoot"], [Binding("button", 1)])
        self.assertEqual(loaded.profile("sdl:old")["dash"], [Binding("button", 2)])
        self.assertEqual(loaded.profile("sdl:old")["interact"], [Binding("button", 3)])

    def test_controls_switch_page_edit_story_and_restore_infinite(self):
        self.inputs.set_mode("infinite")
        with patch("pygame.event.get", side_effect=[
            [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_TAB)],
            [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN),
             pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN),
             pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)],
            [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_z)],
            [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)]
        ]):
            self.assertEqual(show_controls_menu(self.app), "back")
        self.assertEqual(self.inputs.settings.mode, "infinite")
        self.inputs.set_mode("story")
        self.assertEqual(self.inputs.settings.keyboard["jump"], pygame.K_z)

    def test_quit_restores_previous_mode(self):
        pygame.event.post(pygame.event.Event(pygame.QUIT))
        self.assertEqual(self.game.run(), "quit")
        self.assertEqual(self.inputs.settings.mode, "infinite")

    def test_disconnect_pauses_before_simulation(self):
        self.inputs.last_device = "pad"
        pad = FakePad()
        self.inputs.pads, self.inputs.active_id = {pad.id: pad}, pad.id
        pygame.event.post(pygame.event.Event(pygame.JOYDEVICEREMOVED, instance_id=pad.id))
        with patch("Notundertale.story.game.show_pause_menu", return_value="menu") as pause:
            self.assertEqual(self.game.run(), "menu")
        self.assertEqual(pause.call_args.args[2], "Manette déconnectée")
        self.assertEqual(self.game.elapsed, 0)
        self.assertIsNone(self.app.clock._paused_at)
        self.assertEqual(self.inputs.settings.mode, "infinite")

    def test_main_menu_routes_story_restart_to_story_only(self):
        with patch("Notundertale.app.show_main_menu", side_effect=["story", "quit"]):
            with patch("Notundertale.app.StoryGame") as story, patch("Notundertale.app.Game") as infinite:
                story.return_value.run.side_effect = ["restart", "menu"]
                App.run(self.app)
        self.assertEqual(story.call_count, 2)
        infinite.assert_not_called()

    def test_resume_discards_pause_duration_and_keeps_jump_blocked(self):
        self.wake()
        self.game.player.cooldown = 0.8
        elapsed = self.game.elapsed
        fake_clock = Mock()
        fake_clock.tick.side_effect = [16, 20_000, 16, 16]
        with patch("Notundertale.story.game.pygame.time.Clock", return_value=fake_clock), \
             patch("pygame.event.get", side_effect=[[], [], [pygame.event.Event(pygame.QUIT)]]), \
             patch.object(self.inputs, "sample", side_effect=[InputState(pause=True), InputState()]), \
             patch("Notundertale.story.game.show_pause_menu", return_value="resume"):
            self.assertEqual(self.game.run(), "quit")
        self.assertAlmostEqual(self.game.elapsed - elapsed, 0.016)
        self.assertAlmostEqual(self.game.player.cooldown, 0.784)

    def test_controller_changes_story_binding_in_controls_menu(self):
        pad = FakePad()
        self.inputs.pads, self.inputs.active_id = {pad.id: pad}, pad.id
        def button(index):
            return pygame.event.Event(pygame.CONTROLLERBUTTONDOWN, instance_id=pad.id, button=index)
        with patch("pygame.event.get", side_effect=[
            [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT)],
            [button(0)], [button(9)], [button(1)]
        ]):
            self.assertEqual(show_controls_menu(self.app), "back")
        self.assertEqual(self.inputs.settings.mode, "story")
        self.assertEqual(self.inputs.settings.profile(pad.profile_name)["left"], [Binding("button", 9)])

    def test_result_menu_can_restart_with_controller(self):
        pad = FakePad()
        self.inputs.pads, self.inputs.active_id = {pad.id: pad}, pad.id
        pygame.event.post(pygame.event.Event(pygame.CONTROLLERBUTTONDOWN, instance_id=pad.id, button=0))
        self.assertEqual(show_story_result(self.app, True), "restart")

    def test_draw_all_characters_rooms_and_scaled_viewports(self):
        for size in ((1280, 720), (1920, 1080), (1024, 768)):
            for skin in self.assets.skins:
                app = SimpleNamespace(**vars(self.app))
                app.screen = pygame.Surface(size)
                app.selected_skin = skin
                game = StoryGame(app)
                for room in game.rooms:
                    game.current_room = room
                    game.phase = "playing"
                    game.draw()
                    self.assertEqual(game.canvas.surface.get_size(), (1280, 720))
                    self.assertLessEqual(game.canvas.viewport.right, size[0])


if __name__ == "__main__":
    unittest.main()
