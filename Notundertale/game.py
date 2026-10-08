"""Une partie du mode infini : apparitions, collisions et affichage."""

import random

import pygame

from .config import (BASE_PROJECTILE_INTERVAL, FLASH_ALPHA, FLASH_DURATION_MS,
                     FPS, SHAKE_DURATION_MS, SHAKE_MAX_AMPLITUDE,
                     SHIELD_DURATION_MS)
from .difficulty import choose_projectile_class, compute_difficulty
from .menus import show_game_over_screen, show_pause_menu
from .player import Player
from .scores import load_scores, save_score
from .sprites import HeartPowerUp, Laser, ShieldPowerUp, WarningLight
from .ui import draw_hud, draw_shield_aura
from .theme import UiCanvas


class Game:
    def __init__(self, app):
        self.app = app
        app.clock.reset()
        app.speed_multiplier = 1.0
        self.score = 0
        self.finished = False
        self.player = Player(app)
        self.all_sprites = pygame.sprite.Group(self.player)
        self.projectiles = pygame.sprite.Group()
        self.lasers = pygame.sprite.Group()
        self.shields = pygame.sprite.Group()
        self.hearts = pygame.sprite.Group()
        self.warnings = pygame.sprite.Group()
        self.next_projectile = BASE_PROJECTILE_INTERVAL
        self.projectile_interval = BASE_PROJECTILE_INTERVAL
        self.next_shield = 15_000
        self.next_heart = 40_000
        self.next_laser = 30_000
        self.laser_x = None
        self.shield_until = 0
        self.shake_until = 0
        self.flash_until = 0
        self.frame = pygame.Surface(app.screen.get_size()).convert()
        self.hud = UiCanvas(app.screen, transparent=True)

    def add_sprite(self, sprite, group):
        self.all_sprites.add(sprite)
        group.add(sprite)

    def spawn_due(self, now):
        """Les échéances appartiennent à la partie et s'arrêtent avec sa pause."""
        if now >= self.next_projectile:
            self.add_sprite(choose_projectile_class(self.score)(self.app), self.projectiles)
            self.next_projectile = now + self.projectile_interval
        if now >= self.next_shield:
            self.add_sprite(ShieldPowerUp(self.app), self.shields)
            self.next_shield = now + 15_000
        if now >= self.next_heart:
            self.add_sprite(HeartPowerUp(self.app), self.hearts)
            self.next_heart = now + 20_000
        if now >= self.next_laser - 2000 and self.laser_x is None:
            self.laser_x = random.randint(0, 7) * (self.app.screen.get_width() // 8)
            self.warnings.add(WarningLight(self.app, self.laser_x))
        if now >= self.next_laser:
            self.add_sprite(Laser(self.app, self.laser_x), self.lasers)
            self.warnings.empty()
            self.laser_x = None
            self.next_laser = now + 7000

    def handle_collisions(self, now):
        for hazards in (self.projectiles, self.lasers):
            if now < self.shield_until or self.player.is_invincible():
                break
            hits = pygame.sprite.spritecollide(self.player, hazards, False, pygame.sprite.collide_mask)
            if hits and self.player.decrease_health():
                for sprite in hits:
                    sprite.kill()
                self.shake_until = now + SHAKE_DURATION_MS
                self.flash_until = now + FLASH_DURATION_MS
                self.app.audio.play("hit")
                if self.player.health == 0:
                    self.finished = True
                    self.app.audio.stop_music()
                    self.app.audio.play("game_over")
                    return

        shields = pygame.sprite.spritecollide(self.player, self.shields, True, pygame.sprite.collide_mask)
        if shields:
            self.shield_until = now + SHIELD_DURATION_MS
            self.app.audio.play("power_up")
        hearts = pygame.sprite.spritecollide(self.player, self.hearts, True, pygame.sprite.collide_mask)
        if hearts:
            self.player.health = min(3, self.player.health + len(hearts))
            self.app.audio.play("power_up")

    def update(self, inputs):
        if self.finished:
            return
        now = self.app.now_ms()
        self.score = now
        _, self.app.speed_multiplier, self.projectile_interval = compute_difficulty(self.score)
        self.spawn_due(now)
        self.player.update(inputs)
        self.projectiles.update()
        self.lasers.update()
        self.shields.update()
        self.hearts.update()
        self.warnings.update()
        self.handle_collisions(now)

    def draw(self):
        now = self.app.now_ms()
        self.frame.blit(self.app.assets.background, (0, 0))
        self.all_sprites.draw(self.frame)
        self.warnings.draw(self.frame)
        if now < self.shield_until:
            draw_shield_aura(self.frame, self.player.rect, self.shield_until - now, now)
        offset = (0, 0)
        if now < self.shake_until:
            amplitude = int(SHAKE_MAX_AMPLITUDE * (self.shake_until - now) / SHAKE_DURATION_MS)
            offset = (random.randint(-amplitude, amplitude), random.randint(-amplitude, amplitude))
        screen = self.app.screen
        screen.fill((0, 0, 0))
        screen.blit(self.frame, offset)
        if now < self.flash_until:
            flash = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
            flash.fill((255, 0, 0, FLASH_ALPHA))
            screen.blit(flash, (0, 0))
        # Le HUD reste stable pendant les secousses pour garder la jauge lisible.
        self.hud.surface.fill((0, 0, 0, 0))
        draw_hud(self.hud.surface, self.player, self.score, max(0, self.shield_until - now),
                 self.app.assets, self.app.inputs.dash_label())
        self.hud.blit()
        pygame.display.flip()

    def run(self):
        self.app.inputs.release_actions()
        self.app.inputs.disconnected = False
        self.app.audio.play_music()
        clock = pygame.time.Clock()
        try:
            while True:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return "quit"
                    self.app.inputs.handle_event(event)
                inputs = self.app.inputs.sample()
                if inputs.pause or self.app.inputs.disconnected:
                    notice = "Manette déconnectée" if self.app.inputs.disconnected else ""
                    self.app.inputs.disconnected = False
                    self.app.clock.pause()
                    try:
                        action = show_pause_menu(self.app, self.app.screen.copy(), notice)
                    finally:
                        self.app.clock.resume()
                    if action != "resume":
                        return action
                    self.app.inputs.disconnected = False
                    self.app.inputs.release_actions()
                    continue
                self.update(inputs)
                self.draw()
                if self.finished:
                    save_score(self.score, self.app.selected_skin)
                    return show_game_over_screen(self.app, load_scores(), self.score)
                clock.tick(FPS)
        finally:
            self.app.audio.stop_music()
