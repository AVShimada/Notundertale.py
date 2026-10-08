"""Lecture du clavier et des manettes, branchement à chaud et navigation."""

from dataclasses import dataclass

import pygame
from pygame._sdl2 import controller

from .controls import ACTIONS, Binding, ControlSettings, default_pad, key_label


@dataclass
class InputState:
    x: float = 0.0
    y: float = 0.0
    dash: bool = False
    pause: bool = False


class Pad:
    def __init__(self, index):
        self.joystick = pygame.joystick.Joystick(index)
        self.id = self.joystick.get_instance_id()
        self.name = self.joystick.get_name()
        self.standard = controller.is_controller(index)
        self.device = controller.Controller(index) if self.standard else self.joystick
        self.profile_name = ("sdl:" if self.standard else "raw:") + self.joystick.get_guid()

    def close(self):
        if self.standard:
            self.device.quit()
        self.joystick.quit()

    def value(self, binding):
        try:
            if binding.kind == "button":
                if not self.standard and binding.index >= self.joystick.get_numbuttons():
                    return 0.0
                return float(self.device.get_button(binding.index))
            if binding.kind == "axis":
                if not self.standard and binding.index >= self.joystick.get_numaxes():
                    return 0.0
                value = self.device.get_axis(binding.index)
                if self.standard:
                    value /= 32768.0
                return max(0.0, min(1.0, value * binding.sign))
            if binding.index < self.joystick.get_numhats():
                return max(0.0, self.joystick.get_hat(binding.index)[binding.component] * binding.sign)
        except (pygame.error, IndexError):
            pass
        return 0.0

    def label(self, binding):
        if binding.kind == "button":
            if self.standard:
                playstation = any(word in self.name.lower() for word in ("playstation", "ps4", "ps5", "dual", "wireless controller"))
                faces = ("Croix", "Rond", "Carré", "Triangle") if playstation else ("A", "B", "X", "Y")
                names = dict(enumerate(faces))
                names.update({4: "Share / Back", 5: "Guide", 6: "Options / Start",
                              7: "Clic stick G", 8: "Clic stick D", 9: "L1 / LB", 10: "R1 / RB",
                              11: "Croix haut", 12: "Croix bas", 13: "Croix gauche", 14: "Croix droite"})
                return names.get(binding.index, f"Bouton {binding.index + 1}")
            return f"Bouton {binding.index + 1}"
        if binding.kind == "hat":
            direction = ("droite" if binding.sign > 0 else "gauche") if binding.component == 0 else ("haut" if binding.sign > 0 else "bas")
            return f"Croix {binding.index + 1} {direction}"
        if self.standard and binding.index < 4:
            direction = ("droite" if binding.sign > 0 else "gauche") if binding.index % 2 == 0 else ("bas" if binding.sign > 0 else "haut")
            return f"Stick {'G' if binding.index < 2 else 'D'} {direction}"
        if self.standard and binding.index in (4, 5):
            return "L2 / LT" if binding.index == 4 else "R2 / RT"
        return f"Axe {binding.index + 1} {'+' if binding.sign > 0 else '-'}"

    def event_binding(self, event):
        if getattr(event, "instance_id", None) != self.id:
            return None
        if self.standard:
            if event.type == pygame.CONTROLLERBUTTONDOWN:
                return Binding("button", event.button)
            if event.type == pygame.CONTROLLERAXISMOTION:
                return Binding("axis", event.axis, 1 if event.value > 0 else -1)
        else:
            if event.type == pygame.JOYBUTTONDOWN:
                return Binding("button", event.button)
            if event.type == pygame.JOYAXISMOTION:
                return Binding("axis", event.axis, 1 if event.value > 0 else -1)
            if event.type == pygame.JOYHATMOTION:
                x, y = event.value
                if x:
                    return Binding("hat", event.hat, x, 0)
                if y:
                    return Binding("hat", event.hat, y, 1)
        return None


class InputManager:
    def __init__(self, settings=None):
        self.settings = settings or ControlSettings()
        self.pads = {}
        self.active_id = None
        self.last_device = "keyboard"
        self.disconnected = False
        self._pause_held = False
        self._blocked = set()
        pygame.joystick.init()
        controller.init()
        for index in range(pygame.joystick.get_count()):
            self.add_pad(index)

    @property
    def pad(self):
        return self.pads.get(self.active_id)

    def add_pad(self, index):
        try:
            joystick = pygame.joystick.Joystick(index)
            if joystick.get_instance_id() in self.pads:
                return
            pad = Pad(index)
            self.pads[pad.id] = pad
            if self.active_id is None:
                self.active_id = pad.id
        except pygame.error:
            return

    def handle_event(self, event):
        if event.type == pygame.JOYDEVICEADDED:
            self.add_pad(event.device_index)
        elif event.type == pygame.JOYDEVICEREMOVED:
            removed = self.pads.pop(event.instance_id, None)
            if removed:
                removed.close()
                if self.active_id == event.instance_id:
                    self.disconnected = self.last_device == "pad"
                    self.active_id = next(iter(self.pads), None)
                    self.last_device = "keyboard"
        elif event.type == pygame.KEYDOWN:
            self.last_device = "keyboard"
        elif self.pad:
            binding = self.pad.event_binding(event)
            if binding and (binding.kind != "axis" or self.pad.value(binding) > self.settings.deadzone):
                self.last_device = "pad"

    def pad_value(self, action, defaults=False):
        if not self.pad:
            return 0.0
        profile = default_pad(self.pad.standard) if defaults else self.settings.profile(self.pad.profile_name, self.pad.standard)
        return max((self.pad.value(binding) for binding in profile[action]), default=0.0)

    def values(self, keys=None):
        keys = pygame.key.get_pressed() if keys is None else keys
        result = {}
        for action in ACTIONS:
            keyboard = bool(keys[self.settings.keyboard[action]])
            if (action == "dash" and self.settings.keyboard[action] == pygame.K_LSHIFT
                    and pygame.K_RSHIFT not in self.settings.keyboard.values()):
                keyboard |= bool(keys[pygame.K_RSHIFT])
            raw = self.pad_value(action)
            value = max(0.0, (raw - self.settings.deadzone) / (1.0 - self.settings.deadzone))
            result[action] = max(float(keyboard), value)
        # Échap reste une issue accessible même si Pause a été changée.
        result["pause"] = max(result["pause"], float(bool(keys[pygame.K_ESCAPE])))
        return result

    def sample(self, keys=None):
        values = self.values(keys)
        for action in list(self._blocked):
            if values[action] <= 0.5:
                self._blocked.remove(action)
            values[action] = 0.0
        pause = values["pause"] > 0.5
        pressed = pause and not self._pause_held
        self._pause_held = pause
        return InputState(values["right"] - values["left"], values["down"] - values["up"],
                          values["dash"] > 0.5, pressed)

    def release_actions(self):
        """Un bouton qui ferme un menu ne déclenche pas un dash au retour."""
        self._blocked = {action for action in ("dash", "pause") if self.values()[action] > 0.5}
        self._pause_held = False

    def dash_label(self):
        if self.last_device == "pad" and self.pad:
            return self.pad.label(self.settings.profile(self.pad.profile_name, self.pad.standard)["dash"][0])
        return key_label(self.settings.keyboard["dash"])


class MenuInput:
    """Actions de menu communes ; les raccourcis de secours restent fixes."""
    def __init__(self, inputs):
        self.inputs = inputs
        self.direction = None
        self.repeat_at = 0

    def read(self, events):
        commands = []
        for event in events:
            self.inputs.handle_event(event)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    commands.append("confirm")
                elif event.key == pygame.K_ESCAPE:
                    commands.append("back")
                else:
                    fixed = {pygame.K_UP: "up", pygame.K_DOWN: "down", pygame.K_LEFT: "left", pygame.K_RIGHT: "right"}
                    action = fixed.get(event.key) or next((action for action, key in self.inputs.settings.keyboard.items() if key == event.key), None)
                    if action and action != "dash":
                        commands.append(action)
            elif self.inputs.pad:
                binding = self.inputs.pad.event_binding(event)
                if binding == Binding("button", 0):
                    commands.append("confirm")
                elif binding == Binding("button", 1):
                    commands.append("back")
                elif binding and binding.kind != "axis":
                    profile = self.inputs.settings.profile(self.inputs.pad.profile_name, self.inputs.pad.standard)
                    if binding in profile["pause"]:
                        commands.append("pause")
        direction = next((action for action in ACTIONS[:4] if max(self.inputs.pad_value(action), self.inputs.pad_value(action, True)) > max(0.55, self.inputs.settings.deadzone)), None)
        now = pygame.time.get_ticks()
        if direction:
            if direction != self.direction:
                commands.append(direction)
                self.repeat_at = now + 350
            elif now >= self.repeat_at:
                commands.append(direction)
                self.repeat_at = now + 130
        self.direction = direction
        return commands


class BindingCapture:
    """Attend un nouvel appui et le retour au neutre des axes déjà inclinés."""
    def __init__(self, pad):
        self.pad = pad
        self.blocked = {Binding("axis", axis, sign) for axis in range(6 if pad.standard else pad.joystick.get_numaxes())
                        for sign in (-1, 1) if pad.value(Binding("axis", axis, sign)) > 0.35}

    def read(self, event):
        binding = self.pad.event_binding(event)
        if not binding:
            return None
        for blocked in list(self.blocked):
            if self.pad.value(blocked) < 0.35:
                self.blocked.remove(blocked)
        if binding.kind == "axis" and (binding in self.blocked or self.pad.value(binding) < 0.65):
            return None
        return binding
