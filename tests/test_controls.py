"""Contrôles clavier/manette avec périphériques simulés et menus réels."""

import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

import json
import tempfile
import unittest
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pygame

from Notundertale.controls import Binding, ControlSettings, DEFAULT_KEYS, default_pad
from Notundertale.controls_menu import show_controls_menu
from Notundertale.input import BindingCapture, InputManager, MenuInput, Pad
from Notundertale.menus import show_main_menu, show_pause_menu, show_game_over_screen
from Notundertale.assets import Assets
from Notundertale.skins import SKINS


class FakePad(Pad):
    def __init__(self, standard=True, identity=7):
        self.id = identity
        self.name = "Xbox Controller" if standard else "Generic gamepad"
        self.standard = standard
        self.profile_name = ("sdl:" if standard else "raw:") + str(identity)
        self.buttons = defaultdict(bool)
        self.axes = defaultdict(float)
        self.hats = defaultdict(lambda: (0, 0))
        self.device = SimpleNamespace(get_axis=lambda index: self.axes[index],
                                      get_button=lambda index: self.buttons[index], quit=Mock())
        self.joystick = SimpleNamespace(get_numaxes=lambda: 6, get_numbuttons=lambda: 16,
                                        get_numhats=lambda: 1, get_hat=lambda index: self.hats[index], quit=Mock())


class ControlsTests(unittest.TestCase):
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
        self.path = Path(self.folder.name) / "controls.json"
        self.settings = ControlSettings(self.path)
        with patch("pygame.joystick.get_count", return_value=0):
            self.inputs = InputManager(self.settings)
        self.pad = FakePad()
        self.inputs.pads = {self.pad.id: self.pad}
        self.inputs.active_id = self.pad.id
        self.keys = defaultdict(bool)
        pygame.event.clear()

    def test_xbox_stick_dpad_buttons_and_pause_edge(self):
        self.pad.axes[0] = 32767
        self.pad.buttons[11] = True
        self.pad.buttons[0] = True
        self.pad.buttons[6] = True
        state = self.inputs.sample(self.keys)
        self.assertAlmostEqual(state.x, 1, places=3)
        self.assertEqual(state.y, -1)
        self.assertTrue(state.dash)
        self.assertTrue(state.pause)
        self.assertFalse(self.inputs.sample(self.keys).pause)
        self.pad.buttons[6] = False
        self.inputs.sample(self.keys)
        self.pad.buttons[6] = True
        self.assertTrue(self.inputs.sample(self.keys).pause)

    def test_deadzone_blocks_drift_and_preserves_partial_tilt(self):
        self.pad.axes[0] = 3276
        self.assertEqual(self.inputs.sample(self.keys).x, 0)
        self.pad.axes[0] = 19660
        self.assertAlmostEqual(self.inputs.sample(self.keys).x, 0.5, places=3)
        self.settings.deadzone = 0.5
        self.pad.axes[0] = 16383
        self.assertEqual(self.inputs.sample(self.keys).x, 0)

    def test_keyboard_rebinding_and_escape_fallback(self):
        self.settings.bind_key("left", pygame.K_q)
        self.settings.bind_key("dash", pygame.K_SPACE)
        self.settings.bind_key("pause", pygame.K_p)
        self.keys[pygame.K_q] = True
        self.keys[pygame.K_SPACE] = True
        self.keys[pygame.K_ESCAPE] = True
        state = self.inputs.sample(self.keys)
        self.assertEqual(state.x, -1)
        self.assertTrue(state.dash)
        self.assertTrue(state.pause)
        self.keys.clear()
        self.keys[pygame.K_LEFT] = True
        self.assertEqual(self.inputs.sample(self.keys).x, 0)

    def test_pad_trigger_rebinding_replaces_old_button(self):
        self.settings.bind_pad(self.pad.profile_name, True, "dash", Binding("axis", 5, 1))
        self.pad.buttons[0] = True
        self.assertFalse(self.inputs.sample(self.keys).dash)
        self.pad.axes[5] = 30000
        self.assertTrue(self.inputs.sample(self.keys).dash)
        self.inputs.last_device = "pad"
        self.assertEqual(self.inputs.dash_label(), "R2 / RT")

    def test_right_shift_can_be_reassigned_without_also_dashing(self):
        self.settings.bind_key("left", pygame.K_RSHIFT)
        self.keys[pygame.K_RSHIFT] = True
        state = self.inputs.sample(self.keys)
        self.assertEqual(state.x, -1)
        self.assertFalse(state.dash)

    def test_partial_stick_input_counts_as_using_the_controller(self):
        self.pad.axes[0] = 13000
        self.inputs.handle_event(pygame.event.Event(pygame.CONTROLLERAXISMOTION, instance_id=7, axis=0, value=13000))
        self.assertEqual(self.inputs.last_device, "pad")
        self.inputs.handle_event(pygame.event.Event(pygame.JOYDEVICEREMOVED, instance_id=7))
        self.assertTrue(self.inputs.disconnected)

    def test_rebinding_movement_replaces_stick_and_dpad(self):
        self.settings.bind_pad(self.pad.profile_name, True, "left", Binding("button", 2))
        self.pad.axes[0] = -32768
        self.pad.buttons[13] = True
        self.assertEqual(self.inputs.sample(self.keys).x, 0)
        self.pad.buttons[2] = True
        self.assertEqual(self.inputs.sample(self.keys).x, -1)

    def test_conflicts_swap_instead_of_disabling_an_action(self):
        self.settings.bind_key("up", pygame.K_DOWN)
        self.assertEqual(self.settings.keyboard["down"], pygame.K_UP)
        self.settings.bind_pad(self.pad.profile_name, True, "dash", Binding("button", 6))
        profile = self.settings.profile(self.pad.profile_name)
        self.assertEqual(profile["dash"], [Binding("button", 6)])
        self.assertEqual(profile["pause"], [Binding("button", 0)])
        self.assertEqual(ControlSettings(self.path).profiles, self.settings.profiles)

    def test_pause_swap_cannot_assign_escape_to_movement(self):
        self.assertFalse(self.settings.bind_key("pause", pygame.K_UP))
        self.assertEqual(self.settings.keyboard, DEFAULT_KEYS)

    def test_settings_round_trip_separate_models_and_reset(self):
        self.settings.bind_key("dash", pygame.K_SPACE)
        self.settings.bind_pad("sdl:first", True, "dash", Binding("button", 3))
        self.settings.bind_pad("raw:second", False, "dash", Binding("button", 5))
        self.settings.deadzone = 0.35
        self.settings.save()
        loaded = ControlSettings(self.path)
        self.assertEqual(loaded.keyboard["dash"], pygame.K_SPACE)
        self.assertEqual(loaded.deadzone, 0.35)
        self.assertEqual(loaded.profile("sdl:first")["dash"], [Binding("button", 3)])
        loaded.reset("sdl:first")
        self.assertEqual(loaded.keyboard, DEFAULT_KEYS)
        self.assertEqual(loaded.profile("sdl:first"), default_pad(True))
        self.assertEqual(loaded.profile("raw:second")["dash"], [Binding("button", 5)])

    def test_invalid_settings_fall_back_without_partial_changes(self):
        self.settings.save()
        valid = json.loads(self.path.read_text(encoding="utf-8"))
        for content in ("{bad", "null", json.dumps(dict(valid, deadzone=float("nan"))),
                        json.dumps(dict(valid, keyboard={"up": 42}))):
            self.path.write_text(content, encoding="utf-8")
            loaded = ControlSettings(self.path)
            self.assertEqual(loaded.keyboard, DEFAULT_KEYS)
            self.assertEqual(loaded.deadzone, 0.2)
            self.assertTrue(loaded.message)

    def test_failed_save_keeps_current_session_and_reports_it(self):
        with patch.object(Path, "write_text", side_effect=PermissionError):
            self.settings.bind_key("dash", pygame.K_SPACE)
        self.assertEqual(self.settings.keyboard["dash"], pygame.K_SPACE)
        self.assertIn("impossible", self.settings.message)

    def test_disconnect_pauses_only_when_pad_was_in_use(self):
        self.inputs.last_device = "pad"
        self.inputs.handle_event(pygame.event.Event(pygame.JOYDEVICEREMOVED, instance_id=7))
        self.assertTrue(self.inputs.disconnected)
        self.assertIsNone(self.inputs.pad)
        self.assertEqual(self.inputs.sample(self.keys).x, 0)
        self.pad.device.quit.assert_called_once()
        self.inputs.pads[7] = self.pad
        self.inputs.active_id = 7
        self.inputs.last_device = "keyboard"
        self.inputs.disconnected = False
        self.inputs.handle_event(pygame.event.Event(pygame.JOYDEVICEREMOVED, instance_id=7))
        self.assertFalse(self.inputs.disconnected)

    def test_hotplug_uses_instance_id_and_ignores_duplicates(self):
        joystick = SimpleNamespace(get_instance_id=lambda: 99)
        replacement = FakePad(identity=99)
        with patch("pygame.joystick.Joystick", return_value=joystick), patch("Notundertale.input.Pad", return_value=replacement) as constructor:
            self.inputs.handle_event(pygame.event.Event(pygame.JOYDEVICEADDED, device_index=2))
            self.inputs.handle_event(pygame.event.Event(pygame.JOYDEVICEADDED, device_index=2))
        self.assertIn(99, self.inputs.pads)
        self.assertEqual(constructor.call_count, 1)

    def test_menu_close_button_cannot_trigger_dash_until_released(self):
        self.pad.buttons[0] = True
        with patch("pygame.key.get_pressed", return_value=self.keys):
            self.inputs.release_actions()
        self.assertFalse(self.inputs.sample(self.keys).dash)
        self.pad.buttons[0] = False
        self.inputs.sample(self.keys)
        self.pad.buttons[0] = True
        self.assertTrue(self.inputs.sample(self.keys).dash)

    def test_raw_joystick_hat_and_button_fallback(self):
        self.pad = FakePad(standard=False)
        self.inputs.pads[7] = self.pad
        self.pad.hats[0] = (-1, 1)
        self.pad.buttons[0] = True
        state = self.inputs.sample(self.keys)
        self.assertEqual((state.x, state.y, state.dash), (-1, -1, True))

    def test_standard_pad_ignores_duplicate_raw_events(self):
        nav = MenuInput(self.inputs)
        events = [pygame.event.Event(pygame.JOYBUTTONDOWN, instance_id=7, button=0),
                  pygame.event.Event(pygame.CONTROLLERBUTTONDOWN, instance_id=7, button=0)]
        self.assertEqual(nav.read(events), ["confirm"])

    def test_menu_stick_repeat_is_delayed(self):
        nav = MenuInput(self.inputs)
        self.pad.axes[1] = 32767
        with patch("pygame.time.get_ticks", return_value=0):
            self.assertEqual(nav.read([]), ["down"])
        with patch("pygame.time.get_ticks", return_value=100):
            self.assertEqual(nav.read([]), [])
        with patch("pygame.time.get_ticks", return_value=351):
            self.assertEqual(nav.read([]), ["down"])

    def test_capture_requires_a_held_axis_to_return_to_neutral(self):
        self.pad.axes[1] = 32767
        capture = BindingCapture(self.pad)
        event = pygame.event.Event(pygame.CONTROLLERAXISMOTION, instance_id=7, axis=1, value=32767)
        self.assertIsNone(capture.read(event))
        self.pad.axes[1] = 0
        capture.read(pygame.event.Event(pygame.CONTROLLERAXISMOTION, instance_id=7, axis=1, value=0))
        self.pad.axes[1] = 32767
        self.assertEqual(capture.read(event), Binding("axis", 1, 1))

    def test_capture_accepts_b_and_does_not_treat_it_as_cancel(self):
        capture = BindingCapture(self.pad)
        self.assertEqual(capture.read(pygame.event.Event(pygame.CONTROLLERBUTTONDOWN, instance_id=7, button=1)), Binding("button", 1))

    def make_app(self):
        image = pygame.Surface((100, 100))
        return SimpleNamespace(screen=self.screen, inputs=self.inputs, selected_skin="default",
                               assets=SimpleNamespace(skins={"default": image, "skin2": image}),
                               audio=SimpleNamespace(volume=0.5, set_volume=Mock()))

    def run_menu_frames(self, call, batches):
        """Injecte une suite d'événements, puis ferme pour éviter toute boucle infinie."""
        with patch("pygame.event.get", side_effect=[*batches, [pygame.event.Event(pygame.QUIT)]]):
            return call()

    def test_controls_screen_rebinds_keyboard_then_returns(self):
        app = self.make_app()
        result = self.run_menu_frames(lambda: show_controls_menu(app), [
            [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)],
            [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_z)],
            [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)]])
        self.assertEqual(result, "back")
        self.assertEqual(ControlSettings(self.path).keyboard["up"], pygame.K_z)

    def test_controls_screen_rebinds_pad_using_only_controller(self):
        app = self.make_app()
        def frames():
            self.pad.axes[0] = 32767
            yield []  # colonne manette
            self.pad.axes[0] = 0
            yield [pygame.event.Event(pygame.CONTROLLERBUTTONDOWN, instance_id=7, button=0)]
            yield [pygame.event.Event(pygame.CONTROLLERBUTTONDOWN, instance_id=7, button=2)]
            yield [pygame.event.Event(pygame.CONTROLLERBUTTONDOWN, instance_id=7, button=1)]
            yield [pygame.event.Event(pygame.QUIT)]
        with patch("pygame.event.get", side_effect=frames()):
            result = show_controls_menu(app)
        self.assertEqual(result, "back")
        self.assertEqual(ControlSettings(self.path).profile(self.pad.profile_name)["up"], [Binding("button", 2)])

    def test_capture_cancel_preserves_old_binding(self):
        app = self.make_app()
        self.run_menu_frames(lambda: show_controls_menu(app), [
            [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)],
            [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)],
            [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)]])
        self.assertEqual(self.settings.keyboard, DEFAULT_KEYS)

    def test_controller_can_start_resume_and_restart(self):
        app = self.make_app()
        confirm = pygame.event.Event(pygame.CONTROLLERBUTTONDOWN, instance_id=7, button=0)
        back = pygame.event.Event(pygame.CONTROLLERBUTTONDOWN, instance_id=7, button=1)
        self.assertEqual(self.run_menu_frames(lambda: show_main_menu(app), [[confirm]]), "infinite")
        self.assertEqual(self.run_menu_frames(lambda: show_pause_menu(app, self.screen.copy()), [[back]]), "resume")
        self.assertEqual(self.run_menu_frames(lambda: show_game_over_screen(app, [], 0), [[confirm]]), "restart")

    def test_controller_selects_all_six_characters_across_rows(self):
        app = self.make_app()
        app.assets = Assets(self.screen.get_size())
        app.selected_skin = "remanent"
        names = list(SKINS)
        for expected in names[1:] + names[:1]:
            def frames():
                self.pad.axes[0] = 32767
                yield []
                self.pad.axes[0] = 0
                yield []
                yield [pygame.event.Event(pygame.CONTROLLERBUTTONDOWN, instance_id=7, button=0)]
                yield [pygame.event.Event(pygame.QUIT)]
            with patch("pygame.event.get", side_effect=frames()):
                self.assertEqual(show_main_menu(app), "infinite")
            self.assertEqual(app.selected_skin, expected)

    def test_pause_controls_menu_does_not_resume_the_game(self):
        app = self.make_app()
        with patch("Notundertale.menus.show_controls_menu", return_value="back") as controls_menu:
            result = self.run_menu_frames(lambda: show_pause_menu(app, self.screen.copy()), [
                [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN),
                 pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)],
                [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)]])
        self.assertEqual(result, "resume")
        controls_menu.assert_called_once_with(app)


if __name__ == "__main__":
    unittest.main()
