"""Commandes de combat Histoire et migration des préférences existantes."""

import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

from collections import defaultdict
from dataclasses import asdict
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import pygame

from Notundertale.controls import (Binding, ControlSettings, LEGACY_STORY_ACTIONS,
                                  STORY_ACTIONS, STORY_KEYS, default_pad)
from Notundertale.controls_menu import show_controls_menu
from Notundertale.input import InputManager
from test_controls import FakePad


class StoryCombatControlsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.display.init()
        pygame.font.init()
        cls.screen = pygame.display.set_mode((1280, 720))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / "controls_story.json"
        self.settings = ControlSettings(self.path, "story")
        with patch("pygame.joystick.get_count", return_value=0):
            self.inputs = InputManager(self.settings)
        self.pad = FakePad()
        self.inputs.pads = {self.pad.id: self.pad}
        self.inputs.active_id = self.pad.id
        self.keys = defaultdict(bool)
        pygame.event.clear()

    def write_legacy(self, version, keyboard, profile, name="sdl:7"):
        data = {"version": version, "keyboard": keyboard, "deadzone": 0.35,
                "profiles": {name: {action: [asdict(item) for item in items]
                                    for action, items in profile.items()}}}
        self.path.write_text(json.dumps(data), encoding="utf-8")

    def test_xbox_slot_selection_heal_and_existing_face_buttons(self):
        for action, button in (("weapon_1", 10), ("heal", 9), ("jump", 0),
                               ("dash", 2), ("shoot", 1), ("interact", 3)):
            with self.subTest(action=action):
                self.pad.buttons.clear()
                self.pad.buttons[button] = True
                state = self.inputs.sample(self.keys)
                self.assertTrue(getattr(state, action))
                for other in ("weapon_1", "weapon_2", "heal", "jump", "dash", "shoot", "interact"):
                    if other != action:
                        self.assertFalse(getattr(state, other))
        self.pad.buttons.clear()
        self.pad.axes[5] = 32767
        self.assertTrue(self.inputs.sample(self.keys).weapon_2)
        self.inputs.last_device = "pad"
        self.assertEqual(self.inputs.action_label("weapon_1"), "R1 / RB")
        self.assertEqual(self.inputs.action_label("weapon_2"), "R2 / RT")
        self.assertEqual(self.inputs.action_label("heal"), "L1 / LB")

    def test_keyboard_mouse_and_raw_pad_can_use_all_new_actions(self):
        self.keys.update({pygame.K_1: True, pygame.K_2: True, pygame.K_r: True})
        with patch("pygame.mouse.get_pressed", return_value=(True, False, False)):
            state = self.inputs.sample(self.keys)
        self.assertTrue(state.weapon_1 and state.weapon_2 and state.heal and state.shoot)
        self.keys.clear()
        self.pad = FakePad(standard=False)
        self.inputs.pads[7] = self.pad
        self.pad.buttons[5] = self.pad.buttons[4] = True
        self.pad.axes[5] = 1
        state = self.inputs.sample(self.keys)
        self.assertTrue(state.weapon_1 and state.weapon_2 and state.heal)

    def test_new_actions_wait_for_release_after_closing_menu(self):
        self.pad.buttons[10] = self.pad.buttons[9] = True
        self.pad.axes[5] = 32767
        with patch("pygame.key.get_pressed", return_value=self.keys):
            self.inputs.release_actions()
        for _ in range(2):
            state = self.inputs.sample(self.keys)
            self.assertFalse(state.weapon_1 or state.weapon_2 or state.heal)
        self.pad.buttons.clear()
        self.pad.axes.clear()
        self.inputs.sample(self.keys)
        self.pad.buttons[10] = self.pad.buttons[9] = True
        self.pad.axes[5] = 32767
        state = self.inputs.sample(self.keys)
        self.assertTrue(state.weapon_1 and state.weapon_2 and state.heal)

    def test_v2_migration_keeps_all_custom_bindings_and_avoids_conflicts(self):
        for standard, name in ((True, "sdl:7"), (False, "raw:7")):
            with self.subTest(name=name):
                keyboard = {action: STORY_KEYS[action] for action in LEGACY_STORY_ACTIONS}
                keyboard.update(jump=pygame.K_1, dash=pygame.K_2, interact=pygame.K_r)
                defaults = default_pad(standard, "story")
                profile = {action: defaults[action] for action in LEGACY_STORY_ACTIONS}
                profile.update(jump=defaults["weapon_1"], shoot=defaults["weapon_2"],
                               interact=defaults["heal"])
                self.write_legacy(2, keyboard, profile, name)
                loaded = ControlSettings(self.path, "story")
                self.assertEqual(loaded.message, "")
                self.assertEqual(loaded.deadzone, 0.35)
                for action in LEGACY_STORY_ACTIONS:
                    self.assertEqual(loaded.keyboard[action], keyboard[action])
                    self.assertEqual(loaded.profiles[name][action], profile[action])
                self.assertEqual(set(loaded.keyboard), set(STORY_ACTIONS))
                self.assertEqual(len(set(loaded.keyboard.values())), 10)
                bindings = [item for items in loaded.profiles[name].values() for item in items]
                self.assertEqual(len(bindings), len(set(bindings)))
                self.assertTrue(loaded.save())
                self.assertEqual(json.loads(self.path.read_text())["version"], 3)
                self.assertEqual(ControlSettings(self.path, "story").profiles, loaded.profiles)

    def test_v1_default_upgrade_frees_rt_before_adding_second_weapon(self):
        keyboard = {action: STORY_KEYS[action] for action in LEGACY_STORY_ACTIONS}
        keyboard["shoot"] = pygame.K_f
        defaults = default_pad(True, "story")
        profile = {action: defaults[action] for action in LEGACY_STORY_ACTIONS}
        profile.update(dash=[Binding("button", 1)], shoot=[Binding("axis", 5, 1)],
                       interact=[Binding("button", 2)])
        self.write_legacy(1, keyboard, profile)
        loaded = ControlSettings(self.path, "story")
        self.assertEqual(loaded.message, "")
        self.assertEqual(loaded.keyboard, STORY_KEYS)
        self.assertEqual(loaded.profiles["sdl:7"], defaults)

    def test_v1_upgrade_keeps_existing_mouse_and_y_custom_assignments(self):
        keyboard = {action: STORY_KEYS[action] for action in LEGACY_STORY_ACTIONS}
        keyboard.update(shoot=pygame.K_f, jump=-1)
        defaults = default_pad(True, "story")
        profile = {action: defaults[action] for action in LEGACY_STORY_ACTIONS}
        profile.update(dash=[Binding("button", 1)], shoot=[Binding("axis", 5, 1)],
                       interact=[Binding("button", 2)], jump=[Binding("button", 3)])
        self.write_legacy(1, keyboard, profile)
        loaded = ControlSettings(self.path, "story")
        self.assertEqual(loaded.message, "")
        for action in LEGACY_STORY_ACTIONS:
            self.assertEqual(loaded.keyboard[action], keyboard[action])
            self.assertEqual(loaded.profiles["sdl:7"][action], profile[action])
        self.assertNotEqual(loaded.profiles["sdl:7"]["weapon_2"], profile["shoot"])

    def test_new_actions_rebind_mouse_keyboard_and_controller_with_saved_swaps(self):
        self.settings.bind_key("weapon_1", -3)
        self.settings.bind_key("heal", pygame.K_2)
        self.settings.bind_pad("sdl:7", True, "weapon_2", Binding("button", 9))
        loaded = ControlSettings(self.path, "story")
        self.assertEqual(loaded.keyboard["weapon_1"], -3)
        self.assertEqual(loaded.keyboard["heal"], pygame.K_2)
        self.assertEqual(loaded.keyboard["weapon_2"], pygame.K_r)
        self.assertEqual(loaded.profiles["sdl:7"]["weapon_2"], [Binding("button", 9)])
        self.assertEqual(loaded.profiles["sdl:7"]["heal"], [Binding("axis", 5, 1)])

    def test_story_controls_last_row_is_visible_and_rebindable(self):
        app = SimpleNamespace(screen=self.screen, inputs=self.inputs)
        events = [[pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(415, 480))],
                  [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_h)],
                  [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)],
                  [pygame.event.Event(pygame.QUIT)]]
        with patch("pygame.event.get", side_effect=events):
            self.assertEqual(show_controls_menu(app), "back")
        self.assertEqual(ControlSettings(self.path, "story").keyboard["heal"], pygame.K_h)

    def test_infinite_settings_and_new_action_states_are_unchanged(self):
        infinite = ControlSettings(Path(self.folder.name) / "controls.json")
        with patch("pygame.joystick.get_count", return_value=0):
            inputs = InputManager(infinite)
        self.keys.update({pygame.K_1: True, pygame.K_2: True, pygame.K_r: True})
        state = inputs.sample(self.keys)
        self.assertFalse(state.weapon_1 or state.weapon_2 or state.heal)
        self.assertEqual(default_pad(True)["dash"], [Binding("button", 0)])
        infinite.save()
        self.assertEqual(json.loads(infinite.path.read_text())["version"], 2)


if __name__ == "__main__":
    unittest.main()
