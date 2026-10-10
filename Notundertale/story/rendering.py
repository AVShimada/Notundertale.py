"""Sprites, absorption de biomasse et interface du mode Histoire."""

import math

import pygame

from ..theme import (CYAN, ICE, MUTED, GOLD, GREEN, EDGE, NIGHT,
                     panel, text_at, fit_label)
from .rooms import FLOOR_Y
from .scenery import room_background
from .weapons import WEAPONS
from .progression import HEAL_KILLS_REQUIRED, HEAL_FRACTION
from .weapon_art import ArmedSprites, draw_gun, recoil_amount, draw_muzzle_flash
from .weapon_pose import muzzle_position

PURPLE = (142, 81, 182)
BIOMASS = (40, 122, 76)


def alien_image():
    image = pygame.Surface((40, 28), pygame.SRCALPHA)
    pygame.draw.lines(image, (75, 42, 103), False, [(12, 19), (5, 17), (2, 9), (5, 6)], 3)
    pygame.draw.polygon(image, (31, 22, 45), [(8, 19), (12, 10), (20, 7), (29, 9), (35, 15), (33, 22), (17, 24)])
    pygame.draw.polygon(image, (103, 61, 137), [(12, 16), (17, 9), (25, 8), (28, 12), (23, 15)])
    pygame.draw.rect(image, (72, 45, 101), (26, 10, 10, 10))
    pygame.draw.rect(image, (151, 92, 169), (26, 6, 5, 7))
    pygame.draw.rect(image, (222, 178, 232), (32, 13, 3, 2))
    for x in (12, 27):
        pygame.draw.lines(image, (88, 53, 117), False, [(x, 19), (x - 2, 24), (x + 5, 24)], 3)
        pygame.draw.rect(image, (183, 151, 178), (x + 4, 24, 3, 1))
    return pygame.transform.scale(image, (80, 56))


def bar(screen, rect, fraction, color):
    pygame.draw.rect(screen, EDGE, rect)
    width = round(rect.width * max(0, min(1, fraction)))
    if width:
        pygame.draw.rect(screen, color, (rect.x, rect.y, width, rect.height))


class StoryRenderer:
    def __init__(self, game):
        self.backgrounds = {name: room_background(room) for name, room in game.rooms.items()}
        self.player_images = {1: game.app.assets.skins[game.app.selected_skin]}
        self.player_images[-1] = pygame.transform.flip(self.player_images[1], True, False)
        alien = alien_image()
        self.aliens = {1: alien, -1: pygame.transform.flip(alien, True, False)}
        self.armed_sprites = ArmedSprites(game.app.selected_skin)

    def draw(self, game):
        screen = game.canvas.surface
        room, player = game.room, game.player
        cam = round(game.camera_x)
        screen.blit(self.backgrounds[room.name], (-cam, 0))
        for door in room.doors:
            x = door.x - cam
            panel(screen, pygame.Rect(x - 42, 436, 84, 164), (10, 24, 35), EDGE)
            pygame.draw.rect(screen, CYAN, (x - 30, 450, 4, 126))
            pygame.draw.rect(screen, (40, 78, 88), (x + 26, 450, 4, 126))
            fit_label(screen, door.label, pygame.Rect(x - 92, 408, 184, 24), MUTED, 1)
        if room.is_exit:
            x = room.width - 130 - cam
            panel(screen, pygame.Rect(x - 35, 486, 70, 114), (24, 37, 48), EDGE)
            pygame.draw.rect(screen, GREEN if game.cleared else PURPLE, (x - 23, 502, 46, 30))
            text_at(screen, "SAS", (x - 17, 540), 2, MUTED)
        for pickup in room.loot:
            if pickup.collected:
                continue
            x = pickup.x - cam
            color = WEAPONS[pickup.weapon_id].color
            pygame.draw.rect(screen, (20, 60, 64), (x - 36, 588, 72, 8))
            draw_gun(screen, x, 558 + int(math.sin(game.elapsed * 4) * 3),
                     pickup=True, weapon_id=pickup.weapon_id)
            label = "FUSIL" if pickup.weapon_id == "rifle" else "RAYGUN"
            fit_label(screen, label, pygame.Rect(x - 64, 526, 128, 20), color, 1)
        for enemy in room.enemies:
            if enemy.health <= 0:
                pygame.draw.rect(screen, (67, 36, 81), (enemy.rect.x - cam, enemy.rect.bottom - 6, 56, 6))
                pygame.draw.rect(screen, (34, 73, 54), (enemy.rect.centerx - 16 - cam, enemy.rect.bottom - 9, 32, 5))
                continue
            image = self.aliens[enemy.facing]
            screen.blit(image, (enemy.rect.centerx - 40 - cam, enemy.rect.bottom - 52))
            if enemy.flash:
                pygame.draw.rect(screen, ICE, enemy.rect.move(-cam, 0), 2)
            if enemy.phase == "warn":
                text_at(screen, "!", (enemy.rect.centerx - cam - 6, enemy.rect.top - 38), 3, GOLD)
            bar(screen, pygame.Rect(enemy.rect.centerx - cam - 22, enemy.rect.top - 10, 44, 4),
                enemy.health / enemy.max_health, PURPLE)
        self.biomass(game, cam)
        image = (player.animation.image(player.facing < 0) if player.animation
                 else self.player_images[player.facing])
        if game.phase == "awakening" and game.elapsed < 1.4:
            corpse = pygame.transform.rotate(image, 90)
            screen.blit(corpse, (player.rect.centerx - 50 - cam, FLOOR_Y - 58))
            for i in range(8):
                x = player.rect.centerx - cam - 38 + i * 10
                y = FLOOR_Y - 14 - int((game.elapsed * 28 + i * 9) % 44)
                pygame.draw.rect(screen, BIOMASS, (x, y, 5, 5))
        elif not player.invulnerable or int(player.invulnerable * 16) % 2 == 0:
            recoil = recoil_amount(game.weapon)
            if game.weapon.current and player.animation:
                image = self.armed_sprites.image(player, game.weapon.current, recoil)
            left = player.rect.centerx - image.get_width() // 2 - cam
            if player.dash_left:
                for i in range(1, 4):
                    trail = image.copy()
                    trail.set_alpha(70 - 15 * i)
                    screen.blit(trail, (left - player.facing * i * 18, player.rect.bottom - 97))
            screen.blit(image, (left, player.rect.bottom - 97))
            if game.weapon.current == game.weapon.last_shot_weapon:
                mx, my = muzzle_position(player, recoil)
                draw_muzzle_flash(screen, (mx - cam, my), player.facing,
                                  game.weapon.current, game.weapon.shot_flash)
        for ray in game.weapon.rays:
            pygame.draw.rect(screen, (31, 62, 69), ray.rect.move(-cam, 0).inflate(4, 8))
            pygame.draw.rect(screen, ray.color, ray.rect.move(-cam, 0))
        for x, y, life in game.weapon.impacts:
            radius = int(16 * life / 0.16) + 3
            pygame.draw.line(screen, GOLD, (x - cam - radius, y), (x - cam + radius, y), 3)
            pygame.draw.line(screen, ICE, (x - cam, y - radius), (x - cam, y + radius), 3)
        self.evolution(game, cam)
        self.hud(game)

    def biomass(self, game, cam):
        screen = game.canvas.surface
        for drop in game.room.xp_drops:
            x = round(drop.pos.x) - cam
            y = round(drop.pos.y + (0 if drop.attracted else math.sin(drop.age * 5) * 3))
            if drop.attracted:
                toward = pygame.Vector2(game.player.rect.center) - drop.pos
                if toward.length_squared():
                    toward = toward.normalize()
                    for i in range(1, 5):
                        # Les filaments suivent la matière en mouvement vers l'hôte.
                        tail = pygame.Vector2(x, y) - toward * i * 7
                        size = 6 if i < 3 else 3
                        pygame.draw.rect(screen, BIOMASS, (round(tail.x), round(tail.y), size, size))
            else:
                pygame.draw.rect(screen, (21, 61, 43), (x - 15, y + 10, 30, 4))
            pygame.draw.polygon(screen, BIOMASS,
                                [(x - 9, y + 5), (x - 9, y - 3), (x - 3, y - 3),
                                 (x - 3, y - 9), (x + 5, y - 9), (x + 5, y - 3),
                                 (x + 9, y - 3), (x + 9, y + 5), (x + 3, y + 5),
                                 (x + 3, y + 9), (x - 5, y + 9), (x - 5, y + 5)])
            pygame.draw.rect(screen, GREEN, (x - 3, y - 5, 5, 5))
            if not drop.attracted:
                pygame.draw.rect(screen, BIOMASS, (x + 10, y - 14 - int(drop.age * 8) % 6, 3, 3))

    def evolution(self, game, cam):
        screen, player = game.canvas.surface, game.player
        x, y = player.rect.centerx - cam, player.rect.centery
        if game.level_flash:
            age = 2 - game.level_flash
            # Deux ondes en marches d'escalier, sans masquer le jeu ni suspendre l'action.
            for delay in (0, .22):
                progress = (age - delay) / .65
                if 0 <= progress <= 1:
                    radius = 24 + int(progress * 66) // 4 * 4
                    points = [(x - radius, y - radius // 2), (x - radius // 2, y - radius // 2),
                              (x - radius // 2, y - radius), (x + radius // 2, y - radius),
                              (x + radius // 2, y - radius // 2), (x + radius, y - radius // 2),
                              (x + radius, y + radius // 2), (x + radius // 2, y + radius // 2),
                              (x + radius // 2, y + radius), (x - radius // 2, y + radius),
                              (x - radius // 2, y + radius // 2), (x - radius, y + radius // 2)]
                    pygame.draw.polygon(screen, GREEN if delay == 0 else BIOMASS, points, 2)
            panel(screen, pygame.Rect(456, 150, 368, 54), NIGHT, BIOMASS, shadow=False)
            fit_label(screen, f"NIVEAU {game.progression.level} / ÉVOLUTION",
                      pygame.Rect(468, 155, 344, 25), GREEN, 2)
            fit_label(screen, "+20 PV MAX / +12% DÉGÂTS PAR NIVEAU",
                      pygame.Rect(468, 183, 344, 14), MUTED, 1)
        if game.heal_flash:
            for i in range(5):
                dx = (i - 2) * 17
                dy = -int((.7 - game.heal_flash) * 70) - (i % 2) * 15
                pygame.draw.rect(screen, GREEN, (x + dx - 2, y + dy - 6, 4, 12))
                pygame.draw.rect(screen, GREEN, (x + dx - 6, y + dy - 2, 12, 4))
        for amount, fx, fy, life in game.feedback:
            fit_label(screen, f"+{amount} XP", pygame.Rect(round(fx - cam - 64), round(fy), 128, 20), GREEN, 2)

    def hud(self, game):
        screen, player, inputs = game.canvas.surface, game.player, game.app.inputs
        progress = game.progression
        panel(screen, pygame.Rect(24, 24, 304, 106))
        text_at(screen, "HÔTE", (42, 36), 1, MUTED)
        text_at(screen, f"{player.health}/{player.max_health} PV", (188, 36), 1, ICE)
        bar(screen, pygame.Rect(42, 54, 268, 10), player.health / player.max_health, GREEN)
        text_at(screen, f"NIV {progress.level}", (42, 72), 1, GREEN)
        text_at(screen, f"{progress.xp}/{progress.xp_required} XP", (172, 72), 1, MUTED)
        bar(screen, pygame.Rect(42, 87, 268, 5), progress.xp / progress.xp_required, BIOMASS)
        text_at(screen, "DASH", (42, 105), 1, MUTED)
        bar(screen, pygame.Rect(94, 107, 216, 5), 1 - player.cooldown / player.DASH_COOLDOWN, CYAN)

        text_at(screen, "ÉPAVE / PLANÈTE INCONNUE", (350, 30), 1, MUTED)
        fit_label(screen, game.room.title, pygame.Rect(350, 49, 350, 30), ICE, 2, align="left")
        heal_key = inputs.action_label("heal")
        text_at(screen, f"{heal_key} : SOIN {progress.heal_charges}/{progress.heal_capacity}", (350, 90), 1, GREEN)
        if progress.heal_charges < progress.heal_capacity:
            status = f"RECHARGE : {progress.heal_kills}/{HEAL_KILLS_REQUIRED} ÉLIMINATIONS"
        elif progress.heal_capacity == 1:
            status = f"+{int(HEAL_FRACTION * 100)}% PV / 2E CHARGE AU NIV 5"
        else:
            status = f"+{int(HEAL_FRACTION * 100)}% PV / CHARGES PRÊTES"
        text_at(screen, status, (350, 110), 1, MUTED)

        for index in range(2):
            rect = pygame.Rect(716 + index * 274, 24, 266, 106)
            active = game.weapon.selected == index and index < len(game.weapon.slots)
            panel(screen, rect, NIGHT, CYAN if active else EDGE)
            key = inputs.action_label(f"weapon_{index + 1}")
            text_at(screen, f"{key} : ARME {index + 1}" + (" / ACTIVE" if active else ""),
                    (rect.x + 16, rect.y + 12), 1, CYAN if active else MUTED)
            if index >= len(game.weapon.slots):
                text_at(screen, "EMPLACEMENT VIDE", (rect.x + 16, rect.y + 42), 1, MUTED)
                text_at(screen, "EXPLORER LES SALLES", (rect.x + 16, rect.y + 76), 1, MUTED)
                continue
            weapon_id = game.weapon.slots[index]
            spec = WEAPONS[weapon_id]
            fit_label(screen, spec.label, pygame.Rect(rect.x + 16, rect.y + 36, 232, 23), spec.color, 1, align="left")
            draw_gun(screen, rect.x + 44, rect.y + 80, weapon_id=weapon_id)
            damage = round(spec.damage * player.damage_multiplier)
            text_at(screen, f"{damage} DGT / {1 / spec.cooldown:.1f}/S", (rect.x + 86, rect.y + 72), 1, ICE)
            bar(screen, pygame.Rect(rect.x + 86, rect.y + 89, 162, 3),
                1 - game.weapon.cooldowns[weapon_id] / spec.cooldown, spec.color)

        panel(screen, pygame.Rect(24, 636, 1232, 66), NIGHT, EDGE, shadow=False)
        message = ("Un ancien corps. Une nouvelle présence. Le vaisseau est silencieux."
                   if game.phase == "awakening" else game.prompt())
        fit_label(screen, message, pygame.Rect(32, 640, 1216, 27), GOLD, 2)
        labels = [f"{inputs.action_label(action)} : {label}" for action, label in
                  (("jump", "saut"), ("dash", "dash"), ("shoot", "tir"), ("interact", "interagir"),
                   ("heal", "soin"), ("weapon_1", "arme 1"), ("weapon_2", "arme 2"), ("pause", "pause"))]
        fit_label(screen, "  /  ".join(labels), pygame.Rect(32, 672, 1216, 23), MUTED, 1)
        if game.phase == "awakening":
            panel(screen, pygame.Rect(450, 206, 380, 82))
            fit_label(screen, "LE RÉVEIL", pygame.Rect(462, 217, 356, 56), GREEN, 4)
