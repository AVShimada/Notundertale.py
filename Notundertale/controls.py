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
LEGACY_STORY_ACTIONS = ("left", "right", "jump", "dash", "shoot", "interact", "pause")
STORY_ACTIONS = LEGACY_STORY_ACTIONS + ("weapon_1", "weapon_2", "heal")
STORY_KEYS = dict(zip(STORY_ACTIONS, (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_SPACE,
                                    pygame.K_LSHIFT, -1, pygame.K_e, pygame.K_ESCAPE,
                                    pygame.K_1, pygame.K_2, pygame.K_r)))
# Les codes négatifs désignent les boutons souris gauche, milieu et droit.
MOUSE_LABELS = {-1: "Clic gauche", -2: "Clic milieu", -3: "Clic droit"}
ACTION_LABELS.update(jump="Sauter", shoot="Tirer", interact="Interagir",
                     weapon_1="Arme 1", weapon_2="Arme 2", heal="Se soigner")


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


def default_pad(standard=True, mode="infinite"):
    result = {
        "up": [Binding("axis", 1, -1)], "down": [Binding("axis", 1, 1)],
        "left": [Binding("axis", 0, -1)], "right": [Binding("axis", 0, 1)],
        "dash": [Binding("button", 0)], "pause": [Binding("button", 6 if standard else 7)],
    }
    for action, button, component, sign in (("up", 11, 1, 1), ("down", 12, 1, -1),
                                           ("left", 13, 0, -1), ("right", 14, 0, 1)):
        result[action].append(Binding("button", button) if standard else Binding("hat", 0, sign, component))
    if mode == "story":
        result = {action: result[action] for action in ("left", "right", "pause")}
        result.update(jump=[Binding("button", 0)], dash=[Binding("button", 2)],
                      shoot=[Binding("button", 1)], interact=[Binding("button", 3)],
                      weapon_1=[Binding("button", 10 if standard else 5)],
                      weapon_2=[Binding("axis", 5, 1)],
                      heal=[Binding("button", 9 if standard else 4)])
    return result


def _extend_story_keys(keyboard):
    """Ajouter les nouvelles actions sans remplacer les touches personnalisées."""
    missing = [action for action in STORY_ACTIONS if action not in keyboard]
    reserved = {STORY_KEYS[action] for action in missing}
    fallbacks = (pygame.K_3, pygame.K_4, pygame.K_f, pygame.K_q, pygame.K_c,
                 pygame.K_v, pygame.K_h, pygame.K_t, pygame.K_g, pygame.K_j,
                 pygame.K_k, pygame.K_l, pygame.K_u, pygame.K_i, pygame.K_o)
    for action in missing:
        preferred = STORY_KEYS[action]
        candidates = [preferred, *(key for key in fallbacks if key not in reserved)]
        keyboard[action] = next(key for key in candidates if key not in keyboard.values())


def _extend_story_pad(profile, standard):
    defaults = default_pad(standard, "story")
    missing = [action for action in STORY_ACTIONS if action not in profile]
    reserved = {defaults[action][0] for action in missing}
    buttons = (4, 7, 8, 11, 12) if standard else (8, 9, 6, 10, 11, 12)
    fallbacks = [Binding("axis", 4, 1), *(Binding("button", index) for index in buttons),
                 *(Binding("axis", axis, sign) for axis in (2, 3, 0, 1) for sign in (1, -1)),
                 *(Binding("button", index) for index in range(15 if standard else 16)
                   if not standard or index != 5)]
    for action in missing:
        preferred = defaults[action][0]
        used = {item for bindings in profile.values() for item in bindings}
        candidates = [preferred, *(item for item in fallbacks if item not in reserved)]
        profile[action] = [next(item for item in candidates if item not in used)]


class ControlSettings:
    def __init__(self, path=None, mode="infinite"):
        self.mode = mode
        self.actions = STORY_ACTIONS if mode == "story" else ACTIONS
        self.defaults = STORY_KEYS if mode == "story" else DEFAULT_KEYS
        self.path = Path(path) if path is not None else ASSET_DIR / (
            "controls_story.json" if mode == "story" else "controls.json")
        self.keyboard = self.defaults.copy()
        self.profiles = {}
        self.deadzone = 0.20
        self.message = ""
        self.load()

    def load(self):
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or data.get("version") not in (1, 2, 3):
                raise ValueError("Format de commandes inconnu")
            keyboard = data["keyboard"]
            allowed_actions = [set(self.actions)]
            if self.mode == "story" and data["version"] < 3:
                allowed_actions.append(set(LEGACY_STORY_ACTIONS))
            if set(keyboard) not in allowed_actions or len(set(keyboard.values())) != len(keyboard):
                raise ValueError("Touches manquantes ou en double")
            for action, key in keyboard.items():
                if (type(key) is not int or (key not in MOUSE_LABELS and
                        (key < 0 or not pygame.key.name(key))) or key == pygame.K_RETURN):
                    raise ValueError("Touche invalide")
                if key == pygame.K_ESCAPE and action != "pause":
                    raise ValueError("Échap est réservé")
            deadzone = float(data["deadzone"])
            if not math.isfinite(deadzone) or not 0.10 <= deadzone <= 0.50:
                raise ValueError("Zone morte invalide")
            profiles = {}
            for name, raw in data["profiles"].items():
                if set(raw) not in allowed_actions:
                    raise ValueError("Profil incomplet")
                profile = {action: [Binding.from_json(item) for item in items] for action, items in raw.items()}
                if self.mode == "story" and data["version"] == 1:
                    old_shoot = Binding("axis", 5, 1) if name.startswith("sdl:") else Binding("button", 3)
                    occupied = {item for action, items in profile.items()
                                if action not in ("dash", "shoot", "interact") for item in items}
                    replacements = {Binding("button", index) for index in (1, 2, 3)}
                    if (profile["dash"] == [Binding("button", 1)] and
                            profile["shoot"] == [old_shoot] and profile["interact"] == [Binding("button", 2)]
                            and not occupied & replacements):
                        profile.update(dash=[Binding("button", 2)], shoot=[Binding("button", 1)],
                                       interact=[Binding("button", 3)])
                bindings = [item for items in profile.values() for item in items]
                if any(not 1 <= len(items) <= 2 for items in profile.values()) or len(set(bindings)) != len(bindings):
                    raise ValueError("Profil ambigu")
                profiles[name] = profile
            if self.mode == "story" and data.get("version") == 1:
                if keyboard["shoot"] == pygame.K_f and -1 not in keyboard.values():
                    keyboard["shoot"] = -1
            if self.mode == "story":
                _extend_story_keys(keyboard)
                for name, profile in profiles.items():
                    _extend_story_pad(profile, name.startswith("sdl:"))
            self.keyboard, self.deadzone, self.profiles = keyboard, deadzone, profiles
        except (OSError, ValueError, TypeError, KeyError, AttributeError, OverflowError):
            self.message = "Fichier de commandes illisible : réglages par défaut chargés."

    def profile(self, name, standard=True):
        if name not in self.profiles:
            self.profiles[name] = default_pad(standard, self.mode)
        return self.profiles[name]

    def save(self):
        data = {"version": 3 if self.mode == "story" else 2, "keyboard": self.keyboard, "deadzone": self.deadzone,
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
        for other in self.actions:
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
        for other in self.actions:
            if other != action and binding in profile[other]:
                profile[other] = old
        profile[action] = [binding]
        self.save()

    def reset(self, profile_name=None, standard=True):
        self.keyboard = self.defaults.copy()
        self.deadzone = 0.20
        if profile_name:
            self.profiles[profile_name] = default_pad(standard, self.mode)
        self.save()


def key_label(key):
    if key in MOUSE_LABELS:
        return MOUSE_LABELS[key]
    return {pygame.K_UP: "Flèche haut", pygame.K_DOWN: "Flèche bas",
            pygame.K_LEFT: "Flèche gauche", pygame.K_RIGHT: "Flèche droite",
            pygame.K_LSHIFT: "Maj gauche", pygame.K_RSHIFT: "Maj droite",
            pygame.K_ESCAPE: "Échap", pygame.K_SPACE: "Espace"}.get(key, pygame.key.name(key).upper())
