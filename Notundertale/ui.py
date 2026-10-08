"""Affichage du HUD et éléments communs aux menus."""

import math

import pygame

from .config import SHIELD_DURATION_MS
from .theme import (CYAN, ICE, MUTED, EDGE, PANEL_LIGHT, GREEN,
                    panel, pixel_font, fit_label, text_at)


def draw_text(surface, text, font, color, x, y):
    image = font.render(text, False, color)
    surface.blit(image, image.get_rect(center=(x, y)))


def draw_button(surface, rect, label, font, focused=False):
    panel(surface, rect, PANEL_LIGHT if focused else (13, 27, 45), CYAN if focused else EDGE)
    if focused:
        pygame.draw.rect(surface, CYAN, (rect.x + 3, rect.y + 12, 4, rect.height - 24))
        text_at(surface, ">", (rect.x + 17, rect.centery - 10), 2, CYAN)
    fit_label(surface, label, rect.inflate(-64, 0), ICE if focused else MUTED, 2)
    if focused:
        pygame.draw.rect(surface, CYAN, (rect.right - 22, rect.centery - 3, 6, 6))


def draw_volume_slider(surface, rect, volume):
    draw_meter(surface, rect, volume, CYAN, 15)


def draw_meter(surface, rect, progress, color=CYAN, segments=12):
    progress = max(0.0, min(1.0, progress))
    for index in range(segments):
        x = rect.x + index * rect.width // segments
        width = (index + 1) * rect.width // segments - index * rect.width // segments - 3
        pygame.draw.rect(surface, EDGE, (x, rect.y, width, rect.height))
        fraction = max(0.0, min(1.0, progress * segments - index))
        fill = round(width * fraction)
        if fill:
            pygame.draw.rect(surface, color, (x, rect.y, fill, rect.height))


def draw_dash_cooldown(surface, player, font, dash_label="Maj gauche"):
    box = pygame.Rect(24, surface.get_height() - 120, 344, 96)
    panel(surface, box)
    bar = pygame.Rect(box.x + 20, box.y + 65, box.width - 40, 12)
    ready = player.can_dash()
    color = GREEN if ready else CYAN
    if player.dashing:
        label = "ACTIF"
    elif ready:
        label = "PRÊT"
    else:
        seconds = math.ceil(player.dash_remaining_ms() / 100) / 10
        label = f"{seconds:.1f} S"
    text_at(surface, "DASH", (box.x + 20, box.y + 12), 2, ICE)
    fit_label(surface, f"[{dash_label}]", pygame.Rect(box.x + 88, box.y + 12, box.width - 100, 20), MUTED, 2)
    text_at(surface, label, (box.x + 20, box.y + 36), 2, color)
    draw_meter(surface, bar, player.dash_progress(), color)


def draw_hud(surface, player, score, shield_remaining, assets, dash_label):
    life_box = pygame.Rect(24, 24, 212, 96)
    panel(surface, life_box)
    text_at(surface, "VITALITÉ", (44, 36), 2, MUTED)
    heart = assets.image("heart.png", (32, 32))
    for index in range(3):
        pos = (44 + index * 52, 72)
        if index < player.health:
            surface.blit(heart, pos)
        else:
            pygame.draw.rect(surface, EDGE, (*pos, 28, 24), 2)
    score_box = pygame.Rect(surface.get_width() - 292, 24, 268, 96)
    panel(surface, score_box)
    text_at(surface, "SCORE", (score_box.x + 20, 36), 2, MUTED)
    fit_label(surface, f"{score:06d}", pygame.Rect(score_box.x + 8, 66, 252, 38), ICE, 3)
    if shield_remaining > 0:
        box = pygame.Rect(24, 132, 212, 50)
        panel(surface, box, border=CYAN)
        text_at(surface, "BOUCLIER", (40, 138), 2, CYAN)
        draw_meter(surface, pygame.Rect(40, 164, 180, 6), shield_remaining / SHIELD_DURATION_MS, CYAN)
    draw_dash_cooldown(surface, player, pixel_font(2), dash_label)


def draw_shield_aura(surface, player_rect, remaining_ms, now_ms):
    if remaining_ms <= 1000 and (now_ms // 150) % 2 == 0:
        return
    radius = max(player_rect.width, player_rect.height) // 2 + 18
    aura = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    pygame.draw.circle(aura, (0, 120, 255, 70), (radius, radius), radius)
    pygame.draw.circle(aura, (0, 170, 255, 110), (radius, radius), radius - 8)
    surface.blit(aura, (player_rect.centerx - radius, player_rect.centery - radius))
