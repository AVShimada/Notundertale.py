"""Commandes sauvegardées, indépendantes de la lecture des périphériques."""

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path

import pygame

from .config import ASSET_DIR

ACTIONS = ("up", "down", "left", "right", "dash", "pause")
ACTION_LABELS = dict(zip(ACTIONS, ("Monter", "Descendre", "Gauche", "Droite", "Dash", "Pause")))
DEFAULT_KEYS = dict(zip(ACTIONS, (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT,
                                 pygame.K_RIGHT, pygame.K_LSHIFT, pygame.K_ESCAPE)))


@dataclass(frozen=True)
class Binding:
    kind: str
    index: int
    sign: int = 0
    component: int = 0

    @classmethod
    def from_json(cls, data):
        binding = cls(**data)
        if type(binding.index) is not int or not 0 <= binding.index < 128:
            raise ValueError("Indice de commande invalide")
        if binding.kind not in ("button", "axis", "hat"):
            raise ValueError("Type de commande invalide")
        if binding.sign not in ((0,) if binding.kind == "button" else (-1, 1)):
            raise ValueError("Direction invalide")
        if binding.component not in (0, 1) or (binding.kind != "hat" and binding.component != 0):
            raise ValueError("Composante invalide")
        return binding


def default_pad(standard=True):
    result = {
        "up": [Binding("axis", 1, -1)], "down": [Binding("axis", 1, 1)],
        "left": [Binding("axis", 0, -1)], "right": [Binding("axis", 0, 1)],
        "dash": [Binding("button", 0)], "pause": [Binding("button", 6 if standard else 7)],
    }
    for action, button, component, sign in (("up", 11, 1, 1), ("down", 12, 1, -1),
                                           ("left", 13, 0, -1), ("right", 14, 0, 1)):
        result[action].append(Binding("button", button) if standard else Binding("hat", 0, sign, component))
    return result


class ControlSettings:
    def __init__(self, path=ASSET_DIR / "controls.json"):
        self.path = Path(path)
        self.keyboard = DEFAULT_KEYS.copy()
        self.profiles = {}
        self.deadzone = 0.20
        self.message = ""
        self.load()

    def load(self):
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or data.get("version") != 1:
                raise ValueError("Format de commandes inconnu")
            keyboard = data["keyboard"]
            if set(keyboard) != set(ACTIONS) or len(set(keyboard.values())) != len(ACTIONS):
                raise ValueError("Touches manquantes ou en double")
            for action, key in keyboard.items():
                if type(key) is not int or not pygame.key.name(key) or key == pygame.K_RETURN:
                    raise ValueError("Touche invalide")
                if key == pygame.K_ESCAPE and action != "pause":
                    raise ValueError("Échap est réservé")
            deadzone = float(data["deadzone"])
            if not math.isfinite(deadzone) or not 0.10 <= deadzone <= 0.50:
                raise ValueError("Zone morte invalide")
            profiles = {}
            for name, raw in data["profiles"].items():
                if set(raw) != set(ACTIONS):
                    raise ValueError("Profil incomplet")
                profile = {action: [Binding.from_json(item) for item in raw[action]] for action in ACTIONS}
                bindings = [item for items in profile.values() for item in items]
                if any(not 1 <= len(items) <= 2 for items in profile.values()) or len(set(bindings)) != len(bindings):
                    raise ValueError("Profil ambigu")
                profiles[name] = profile
            self.keyboard, self.deadzone, self.profiles = keyboard, deadzone, profiles
        except (OSError, ValueError, TypeError, KeyError, AttributeError, OverflowError):
            self.message = "Fichier de commandes illisible : réglages par défaut chargés."

    def profile(self, name, standard=True):
        if name not in self.profiles:
            self.profiles[name] = default_pad(standard)
        return self.profiles[name]

    def save(self):
        data = {"version": 1, "keyboard": self.keyboard, "deadzone": self.deadzone,
                "profiles": {name: {action: [asdict(item) for item in bindings]
                                     for action, bindings in profile.items()}
                             for name, profile in self.profiles.items()}}
        try:
            temporary = self.path.with_suffix(".json.tmp")
            temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            temporary.replace(self.path)
            self.message = "Commandes sauvegardées."
            return True
        except OSError:
            self.message = "Sauvegarde impossible : changements actifs pour cette session."
            return False

    def bind_key(self, action, key):
        if key in (pygame.K_RETURN, pygame.K_ESCAPE):
            self.message = "Entrée et Échap restent disponibles pour naviguer."
            return False
        old = self.keyboard[action]
        for other in ACTIONS:
            if other != action and self.keyboard[other] == key:
                if old == pygame.K_ESCAPE:
                    self.message = f"Touche utilisée pour {ACTION_LABELS[other]} : change cette commande d'abord."
                    return False
                self.keyboard[other] = old
        self.keyboard[action] = key
        self.save()
        return True

    def bind_pad(self, name, standard, action, binding):
        profile = self.profile(name, standard)
        old = profile[action]
        # Échanger les commandes évite de perdre une action en cas de doublon.
        for other in ACTIONS:
            if other != action and binding in profile[other]:
                profile[other] = old
        profile[action] = [binding]
        self.save()

    def reset(self, profile_name=None, standard=True):
        self.keyboard = DEFAULT_KEYS.copy()
        self.deadzone = 0.20
        if profile_name:
            self.profiles[profile_name] = default_pad(standard)
        self.save()


def key_label(key):
    return {pygame.K_UP: "Flèche haut", pygame.K_DOWN: "Flèche bas",
            pygame.K_LEFT: "Flèche gauche", pygame.K_RIGHT: "Flèche droite",
            pygame.K_LSHIFT: "Maj gauche", pygame.K_RSHIFT: "Maj droite",
            pygame.K_ESCAPE: "Échap", pygame.K_SPACE: "Espace"}.get(key, pygame.key.name(key).upper())
