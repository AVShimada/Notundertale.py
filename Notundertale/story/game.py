"""Une tentative dans l'épave : combat, absorption et progression de la substance."""

import math
import random

import pygame

from ..config import FPS
from ..input import MenuInput
from ..menus import show_pause_menu
from ..theme import UiCanvas, panel, fit_label, pixel_font, ICE, MUTED, GREEN, CORAL
from ..ui import draw_button
from .player import StoryPlayer
from .rendering import StoryRenderer
from .rooms import FLOOR_Y, make_rooms
from .weapons import Armory, WEAPONS
from .progression import BOSS_XP
from .experience import ExperienceDrop


class StoryGame:
    def __init__(self, app, seed=None):
        self.app = app
        self.previous_mode = app.inputs.settings.mode
        app.inputs.set_mode("story")
        app.clock.reset()
        self.canvas = UiCanvas(app.screen)
        if seed is None:
            seed = random.SystemRandom().getrandbits(64)
            while seed == getattr(app, "_last_story_seed", None):
                seed = random.SystemRandom().getrandbits(64)
        self.seed = seed
        app._last_story_seed = seed
        self.rooms = make_rooms(seed)
        self.current_room = "cockpit"
        self.visited = {"cockpit"}
        self.player = StoryPlayer()
        self.player.skin_name = app.selected_skin
        self.player.animation = app.assets.character_animation(app.selected_skin)
        self.progression = self.player.progression
        self.weapon = Armory()
        self.phase = "awakening"
        self.elapsed = 0.0
        self.camera_x = 0.0
        self._held = set()
        self.level_flash = 0.0
        self.heal_flash = 0.0
        self.feedback = []
        self.notice_text = ""
        self.notice_time = 0.0
        self.renderer = StoryRenderer(self)

    @property
    def room(self):
        return self.rooms[self.current_room]

    @property
    def cleared(self):
        return all(enemy.health <= 0 for room in self.rooms.values() for enemy in room.enemies)

    @property
    def remaining_enemies(self):
        return sum(enemy.health > 0 for room in self.rooms.values() for enemy in room.enemies)

    def near(self, x):
        return abs(self.player.rect.centerx - x) < 82 and self.player.rect.bottom >= FLOOR_Y - 30

    def prompt(self):
        key = self.app.inputs.action_label("interact")
        if self.notice_time:
            return self.notice_text
        for pickup in self.room.loot:
            if not pickup.collected and self.near(pickup.x):
                label = WEAPONS[pickup.weapon_id].label
                return f"{label} déjà équipé" if pickup.weapon_id in self.weapon.slots else f"{key} : récupérer {label}"
        for door in self.room.doors:
            if self.near(door.x):
                return f"{key} : rejoindre {door.label}" if self.player.has_weapon else "Récupérer l'arme avant de quitter le cockpit."
        if self.room.is_exit and self.near(self.room.width - 130):
            return f"{key} : terminer l'exploration" if self.cleared else f"{self.remaining_enemies} créatures rôdent encore dans l'épave."
        if not self.player.has_weapon:
            return "Explorer le cockpit et récupérer une arme."
        if self.current_room == "cockpit":
            return "Rejoindre la porte à droite. Les plateformes permettent de s'entraîner au saut."
        if any(not drop.collected for drop in self.room.xp_drops):
            return "La substance a faim. Approcher des restes verts pour absorber leur expérience."
        if not self.cleared:
            return f"Explorer l'épave / {self.progression.kills} ennemis abattus / absorber leurs restes pour évoluer."
        return "Épave sécurisée. Rejoindre le sas du dernier secteur."

    def notify(self, message):
        self.notice_text = message
        self.notice_time = 2.0

    def interact(self):
        for pickup in self.room.loot:
            if not pickup.collected and self.near(pickup.x):
                if pickup.weapon_id in self.weapon.slots:
                    self.notify("Cette arme est déjà équipée.")
                    return
                weapon_id = pickup.weapon_id
                displaced = self.weapon.equip(weapon_id)
                pickup.collected = displaced is None
                if displaced:
                    pickup.weapon_id = displaced
                self.player.has_weapon = bool(self.weapon.slots)
                self.app.audio.play("power_up")
                self.notify(f"{WEAPONS[weapon_id].label} / emplacement {self.weapon.selected + 1}")
                return
        for door in self.room.doors:
            if self.near(door.x) and self.player.has_weapon:
                self.current_room = door.target
                self.visited.add(door.target)
                self.player.place(door.arrival_x, FLOOR_Y)
                self.player.dash_left = 0
                self.player.animation.update(0)
                self.weapon.rays.clear()
                self.weapon.impacts.clear()
                self.weapon.shot_flash = 0
                self.camera_x = max(0, min(self.room.width - 1280, door.arrival_x - 550))
                return
        if self.room.is_exit and self.near(self.room.width - 130) and self.cleared:
            self.phase = "complete"

    def record_deaths(self):
        for enemy in self.room.enemies:
            if enemy.health <= 0 and not enemy.rewarded:
                enemy.rewarded = True
                is_boss = getattr(enemy, "is_boss", False)
                value = BOSS_XP if is_boss else enemy.xp_reward
                # Poser les restes sur le support sous le cadavre, jamais dans un mur.
                floors = [s.top for s in self.room.solids
                          if s.left <= enemy.rect.centerx < s.right and s.top >= enemy.rect.bottom - 2]
                floor = min(floors, default=FLOOR_Y)
                self.room.xp_drops.append(ExperienceDrop(pygame.Vector2(enemy.rect.centerx, floor - 18), value))
                if self.progression.record_kill(is_boss):
                    self.notify("Une charge de soin est prête.")

    def absorb_experience(self, dt):
        gained = sum(drop.update(dt, self.player) for drop in self.room.xp_drops)
        self.room.xp_drops[:] = [drop for drop in self.room.xp_drops if not drop.collected]
        if not gained:
            return
        old_max = self.player.max_health
        levels = self.progression.add_xp(gained)
        self.player.health = min(self.player.max_health, self.player.health + self.player.max_health - old_max)
        # Regrouper les absorptions rapprochées pour éviter des chiffres superposés.
        if self.feedback and self.feedback[-1][3] > 0.5:
            gained += self.feedback.pop()[0]
        self.feedback.append((gained, self.player.rect.centerx, self.player.rect.top - 24, 0.8))
        if levels:
            self.level_flash = 2.0
            self.app.audio.play("power_up")

    def update_effects(self, dt):
        self.level_flash = max(0, self.level_flash - dt)
        self.heal_flash = max(0, self.heal_flash - dt)
        self.notice_time = max(0, self.notice_time - dt)
        self.feedback = [(amount, x, y - 30 * dt, life - dt)
                         for amount, x, y, life in self.feedback if life > dt]

    def update(self, state, dt):
        if self.phase in ("dead", "complete"):
            return
        dt = max(0.0, min(dt, 0.1))
        held = {name for name in ("jump", "dash", "interact", "weapon_1", "weapon_2", "heal")
                if getattr(state, name)}
        pressed = held - self._held
        self._held = held
        self.elapsed += dt
        if self.phase == "awakening":
            if self.elapsed >= 2.4:
                self.phase = "playing"
            return
        self.update_effects(dt)
        for index, action in enumerate(("weapon_1", "weapon_2")):
            if action in pressed:
                if index < len(self.weapon.slots):
                    self.weapon.select(index)
                else:
                    self.notify(f"Emplacement {index + 1} vide : trouver une autre arme.")
        if "heal" in pressed:
            if self.progression.use_heal(self.player):
                self.heal_flash = 0.7
                self.app.audio.play("power_up")
            else:
                self.notify("Vie déjà au maximum." if self.player.health >= self.player.max_health
                            else "Soin vide : abattre 5 ennemis pour recharger une dose.")
        if "interact" in pressed:
            self.interact()
            if self.phase == "complete":
                return
        # Des pas de 1/120 s évitent de traverser plateformes et ennemis pendant le dash.
        remaining = dt
        first = True
        while remaining > 1e-8:
            step = min(remaining, 1 / 120)
            remaining -= step
            if self.player.update(state, step, self.room,
                                  first and "jump" in pressed, first and "dash" in pressed):
                self.app.audio.play("dash")
            first = False
            if self.weapon.update(step, state.shoot, self.player, self.room):
                self.app.audio.play("ray")
            self.record_deaths()
            for enemy in self.room.enemies:
                enemy.update(step, self.player, self.room)
                if (enemy.health > 0 and enemy.phase == "attack"
                        and enemy.rect.colliderect(self.player.rect) and self.player.hurt(enemy.contact_damage)):
                    self.app.audio.play("hit")
                    if self.player.health == 0:
                        self.phase = "dead"
                        self.app.audio.play("game_over")
                        return
            self.absorb_experience(step)
            target = max(0, min(self.room.width - 1280, self.player.rect.centerx - 550))
            self.camera_x += (target - self.camera_x) * (1 - math.exp(-9 * step))

    def draw(self):
        self.renderer.draw(self)
        self.canvas.present()

    def run(self):
        inputs = self.app.inputs
        inputs.release_actions()
        inputs.disconnected = False
        self.app.audio.play_music()
        clock = pygame.time.Clock()
        try:
            self.draw()
            while True:
                dt = clock.tick(FPS) / 1000
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return "quit"
                    inputs.handle_event(event)
                state = inputs.sample()
                if state.pause or inputs.disconnected:
                    notice = "Manette déconnectée" if inputs.disconnected else ""
                    inputs.disconnected = False
                    self.app.clock.pause()
                    try:
                        action = show_pause_menu(self.app, self.app.screen.copy(), notice)
                    finally:
                        self.app.clock.resume()
                    if action != "resume":
                        return action
                    inputs.disconnected = False
                    inputs.release_actions()
                    self._held.clear()
                    clock.tick()  # Le temps passé dans le menu ne devient pas du mouvement.
                    continue
                self.update(state, dt)
                self.draw()
                if self.phase in ("dead", "complete"):
                    self.app.audio.stop_music()
                    return show_story_result(self.app, self.phase == "complete")
        finally:
            self.app.audio.stop_music()
            inputs.set_mode(self.previous_mode)
            inputs.release_actions()


def show_story_result(app, completed):
    canvas = UiCanvas(app.screen)
    background = canvas.paused_background(app.screen.copy())
    nav = MenuInput(app.inputs)
    clock = pygame.time.Clock()
    focused = 0
    buttons = [(action, label, pygame.Rect(218 + i * 286, 450, 272, 56))
               for i, (action, label) in enumerate((("restart", "Recommencer"),
                                                     ("menu", "Menu principal"), ("quit", "Quitter")))]
    while True:
        events = canvas.events()
        commands = nav.read(events)
        for event in events:
            if event.type == pygame.QUIT:
                return "quit"
            if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
                for i, (action, _, rect) in enumerate(buttons):
                    if rect.collidepoint(event.pos):
                        focused = i
                        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                            return action
        for command in commands:
            if command == "back":
                return "menu"
            if command in ("left", "right", "up", "down"):
                focused = (focused + (1 if command in ("right", "down") else -1)) % len(buttons)
            elif command == "confirm":
                return buttons[focused][0]
        canvas.surface.blit(background, (0, 0))
        panel(canvas.surface, pygame.Rect(160, 168, 960, 390))
        fit_label(canvas.surface, "SECTEUR SÉCURISÉ" if completed else "HÔTE PERDU",
                  pygame.Rect(184, 202, 912, 64), GREEN if completed else CORAL, 4)
        lines = (("Les secteurs de l'épave sont sécurisés.",
                  "La substance a dévoré ses proies.",
                  "Une nouvelle tentative renouvelle les salles et les armes.") if completed else
                 ("Ce corps ne répond plus.", "Niveaux, expérience, soins et armes seront réinitialisés.",
                  "La prochaine tentative reconstruira le parcours."))
        for i, line in enumerate(lines):
            fit_label(canvas.surface, line, pygame.Rect(190, 292 + i * 38, 900, 30), MUTED, 2)
        for i, (_, label, rect) in enumerate(buttons):
            draw_button(canvas.surface, rect, label, pixel_font(2), i == focused)
        canvas.present()
        clock.tick(FPS)
