from __future__ import annotations

import random
import pygame

from ..core.assets import load_images, play_music
from ..core.settings import GameConfig
from .pause_menu import pause_loop

from ..core.difficulty import compute_difficulty
from ..sprites.player import Player
from ..sprites.lasers import WarningLight, LaserBeam, random_laser_params
from ..sprites.projectiles import Meteor, ZigZagMeteor, BigSlowMeteor
from ..sprites.powerups import ShieldPowerUp, HeartPowerUp

def draw_shield_aura(surface, player_rect, remaining_ms):
    if remaining_ms <= 1000:
        blink_period_ms = 150
        if (pygame.time.get_ticks() // blink_period_ms) % 2 == 0:
            return

    aura_radius = max(player_rect.width, player_rect.height) // 2 + 18
    aura_surf = pygame.Surface((aura_radius * 2, aura_radius * 2), pygame.SRCALPHA)
    center = (aura_radius, aura_radius)

    pygame.draw.circle(aura_surf, (0, 120, 255, 70), center, aura_radius)
    pygame.draw.circle(aura_surf, (0, 170, 255, 110), center, aura_radius - 8)

    aura_pos = (player_rect.centerx - aura_radius, player_rect.centery - aura_radius)
    surface.blit(aura_surf, aura_pos)

def run_game(screen: pygame.Surface, cfg: GameConfig, selected_skin: str = "default") -> int:
    clock = pygame.time.Clock()
    bounds = screen.get_rect()

    images = load_images((cfg.width, cfg.height))
    try:
        play_music(volume=0.5)
    except Exception:
        pass

    player = Player(
        images.player_skins.get(selected_skin, images.player_skins["default"]),
        pos=(cfg.width // 2, cfg.height - 90),
    )
    player_group = pygame.sprite.GroupSingle(player)

    meteors = pygame.sprite.Group()
    power_ups = pygame.sprite.Group()
    heart_power_ups = pygame.sprite.Group()
    warnings = pygame.sprite.Group()
    enemy_lasers = pygame.sprite.Group()

    font = pygame.font.SysFont(None, 32)

    start_time = pygame.time.get_ticks()
    last_spawn = 0

    ADD_SHIELD = pygame.USEREVENT + 3
    ADD_HEART = pygame.USEREVENT + 4
    pygame.time.set_timer(ADD_SHIELD, 15000)
    pygame.time.set_timer(ADD_HEART, 20000)

    ADD_LASER_WARNING = pygame.USEREVENT + 5
    current_laser_interval = 6000
    pygame.time.set_timer(ADD_LASER_WARNING, current_laser_interval)

    pending_lasers: list[tuple[str, int, int]] = []

    shield_active = False
    shield_start_time = 0
    shield_duration_ms = 3000
    remaining_ms = 0

    while True:
        clock.tick(cfg.fps)
        now = pygame.time.get_ticks()
        elapsed_s = (now - start_time) / 1000.0
        score = int(elapsed_s * 1000)

        diff = compute_difficulty(elapsed_s)

        laser_interval = 6500
        if diff.tier == 1:
            laser_interval = 5200
        elif diff.tier == 2:
            laser_interval = 4200
        if laser_interval != current_laser_interval:
            current_laser_interval = laser_interval
            pygame.time.set_timer(ADD_LASER_WARNING, current_laser_interval)

        if shield_active:
            remaining_ms = shield_duration_ms - (now - shield_start_time)
            if remaining_ms <= 0:
                shield_active = False
                remaining_ms = 0
        else:
            remaining_ms = 0

        # EVENTS (tout doit être DANS la boucle)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_p, pygame.K_ESCAPE):
                    action = pause_loop(screen, cfg.fps, score)

                    # double sécurité
                    pygame.event.clear()

                    if action == "quit":
                        pygame.quit()
                        raise SystemExit
                    if action == "menu":
                        return -1
                    # resume
                    continue

            elif e.type == ADD_SHIELD:
                power_ups.add(ShieldPowerUp(images.shield, cfg.width, cfg.height))

            elif e.type == ADD_HEART:
                if elapsed_s >= 40:
                    heart_power_ups.add(HeartPowerUp(images.heart, cfg.width, cfg.height))

            elif e.type == ADD_LASER_WARNING:
                orient, pos = random_laser_params(cfg.width, cfg.height)
                warnings.add(WarningLight(orient, pos, cfg.width, cfg.height, duration_ms=700))
                pending_lasers.append((orient, pos, pygame.time.get_ticks() + 700))

        # Déclenche lasers planifiés
        if pending_lasers:
            now_ms = pygame.time.get_ticks()
            still: list[tuple[str, int, int]] = []
            for orient, pos, fire_at in pending_lasers:
                if now_ms >= fire_at:
                    enemy_lasers.add(LaserBeam(orient, pos, cfg.width, cfg.height, duration_ms=450))
                else:
                    still.append((orient, pos, fire_at))
            pending_lasers = still

        # Updates
        keys = pygame.key.get_pressed()
        player_group.update(keys, bounds)

        meteors.update()
        power_ups.update()
        heart_power_ups.update()
        warnings.update()
        enemy_lasers.update()

        # Spawn meteors
        if now - last_spawn >= diff.spawn_delay_ms:
            img = random.choice(images.meteors)
            if diff.tier == 0:
                cls = Meteor
            elif diff.tier == 1:
                cls = random.choices([Meteor, ZigZagMeteor], weights=[70, 30], k=1)[0]
            else:
                cls = random.choices([Meteor, ZigZagMeteor, BigSlowMeteor], weights=[55, 25, 20], k=1)[0]

            base_speed = random.uniform(3.0, 7.0) * diff.speed_mult
            meteors.add(cls(img, screen_w=cfg.width, screen_h=cfg.height, speed=base_speed))
            last_spawn = now

        # Collect shield
        if pygame.sprite.spritecollide(player, power_ups, dokill=True, collided=pygame.sprite.collide_mask):
            shield_active = True
            shield_start_time = pygame.time.get_ticks()

        # Collect heart
        if pygame.sprite.spritecollide(player, heart_power_ups, dokill=True, collided=pygame.sprite.collide_mask):
            if hasattr(player, "health"):
                player.health = min(player.health + 1, 3)

        # Hit by meteor
        if pygame.sprite.spritecollideany(player, meteors, pygame.sprite.collide_mask):
            if not shield_active and hasattr(player, "is_invincible") and hasattr(player, "decrease_health"):
                if not player.is_invincible():
                    player.decrease_health()
                    pygame.sprite.spritecollide(player, meteors, dokill=True, collided=pygame.sprite.collide_mask)
            else:
                pygame.sprite.spritecollide(player, meteors, dokill=True, collided=pygame.sprite.collide_mask)

            if not player.alive() or (hasattr(player, "health") and player.health <= 0):
                break

        # Hit by enemy laser
        if pygame.sprite.spritecollideany(player, enemy_lasers, pygame.sprite.collide_mask):
            if not shield_active and hasattr(player, "is_invincible") and hasattr(player, "decrease_health"):
                if not player.is_invincible():
                    player.decrease_health()

            if not player.alive() or (hasattr(player, "health") and player.health <= 0):
                break

        # Draw
        screen.blit(images.background, (0, 0))
        meteors.draw(screen)
        power_ups.draw(screen)
        heart_power_ups.draw(screen)
        warnings.draw(screen)
        enemy_lasers.draw(screen)

        # Draw shield aura BEHIND player
        if shield_active:
            draw_shield_aura(screen, player.rect, remaining_ms)

        player_group.draw(screen)

        # HUD hearts
        hp = getattr(player, "health", 0)
        for i in range(hp):
            screen.blit(images.heart, (10 + i * (images.heart.get_width() + 5), 10))

        # HUD shield
        if shield_active:
            screen.blit(images.shield, (10, 70))
            txt = font.render(f"{remaining_ms/1000:.1f}s", True, (255, 255, 255))
            screen.blit(txt, (10 + images.shield.get_width() + 8, 85))

        # ================= HUD =================
        hint = "SHIFT = Dash"
        pause_hint = "P/ESC = Pause"

        score_txt = font.render(f"Score: {score}", True, (255, 255, 255))
        hint_txt = font.render(hint, True, (255, 255, 255))
        pause_txt = font.render(pause_hint, True, (255, 255, 255))

        padding = 15

        screen.blit(score_txt, (cfg.width - score_txt.get_width() - padding, padding))
        screen.blit(hint_txt, (cfg.width - hint_txt.get_width() - padding, padding + 30))
        screen.blit(pause_txt, (cfg.width - pause_txt.get_width() - padding, padding + 60))

        pygame.display.flip()


    return score
