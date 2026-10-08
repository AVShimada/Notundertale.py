"""Écran de réaffectation des commandes, accessible depuis les deux menus."""

import pygame

from .config import FPS, WHITE
from .controls import ACTIONS, ACTION_LABELS, key_label
from .input import BindingCapture, MenuInput
from .ui import draw_button, draw_text
from .theme import (UiCanvas, pixel_font, panel as draw_panel,
                    draw_space, fit_label, CYAN, ICE, MUTED, DIM, EDGE,
                    PANEL, PANEL_LIGHT, GOLD)


def fit_text(surface, text, rect, color=WHITE, size=28):
    fit_label(surface, text, rect, color, max(1, size // 14))


def show_controls_menu(app):
    canvas = UiCanvas(app.screen)
    screen = canvas.surface
    width, height = screen.get_size()
    panel = pygame.Rect((width - min(1080, width - 32)) // 2, 18, min(1080, width - 32), height - 36)
    inputs = app.inputs
    settings = inputs.settings
    nav = MenuInput(inputs)
    row, column = 0, 0
    capture = None
    capture_started = 0
    capture_pad = None
    clock = pygame.time.Clock()
    font = pixel_font(2)
    title_font = pixel_font(4)
    top = panel.y + 158
    row_height = min(48, (panel.height - 380) // 6)
    key_x = panel.x + 190
    key_width = 250
    pad_x = key_x + key_width + 18
    cells = [[pygame.Rect(key_x, top + i * row_height, key_width, row_height - 6),
              pygame.Rect(pad_x, top + i * row_height, panel.right - pad_x - 24, row_height - 6)]
             for i in range(6)]
    zone_rect = pygame.Rect(key_x, top + 6 * row_height + 12, panel.right - key_x - 24, 42)
    reset_rect = pygame.Rect(panel.x + 24, zone_rect.bottom + 22, 420, 44)
    back_rect = pygame.Rect(panel.right - 240, reset_rect.y, 216, 44)
    cancel_rect = pygame.Rect(panel.centerx - 100, panel.bottom - 70, 200, 38)

    def begin_capture():
        nonlocal capture, capture_started, capture_pad
        if column == 1 and not inputs.pad:
            settings.message = "Branche une manette pour changer ses commandes."
            return
        capture = (ACTIONS[row], column)
        capture_started = pygame.time.get_ticks()
        capture_pad = BindingCapture(inputs.pad) if column else None
        settings.message = ""

    while True:
        events = canvas.events()
        if any(event.type == pygame.QUIT for event in events):
            return "quit"
        if capture:
            for event in events:
                inputs.handle_event(event)
                if (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE) or (
                    event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and cancel_rect.collidepoint(event.pos)):
                    capture = None
                    settings.message = "Modification annulée."
                    break
                action, device_column = capture
                if device_column == 0 and event.type == pygame.KEYDOWN:
                    if not getattr(event, "repeat", False) and settings.bind_key(action, event.key):
                        capture = None
                        break
                elif device_column == 1:
                    if not inputs.pad or inputs.pad.id != capture_pad.pad.id:
                        capture = None
                        settings.message = "Manette déconnectée : modification annulée."
                        break
                    binding = capture_pad.read(event)
                    if binding:
                        settings.bind_pad(inputs.pad.profile_name, inputs.pad.standard, action, binding)
                        capture = None
                        break
            if capture and pygame.time.get_ticks() - capture_started >= 10_000:
                capture = None
                settings.message = "Délai écoulé : ancienne commande conservée."
            nav.direction = None
        else:
            commands = nav.read(events)
            for event in events:
                if event.type == pygame.MOUSEMOTION:
                    for i, pair in enumerate(cells):
                        for j, rect in enumerate(pair):
                            if rect.collidepoint(event.pos):
                                row, column = i, j
                    for i, rect in enumerate((zone_rect, reset_rect, back_rect), start=6):
                        if rect.collidepoint(event.pos):
                            row = i
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for i, pair in enumerate(cells):
                        for j, rect in enumerate(pair):
                            if rect.collidepoint(event.pos):
                                row, column = i, j
                                begin_capture()
                    if reset_rect.collidepoint(event.pos):
                        row = 7
                        commands.append("confirm")
                    if back_rect.collidepoint(event.pos):
                        return "back"
                    if zone_rect.collidepoint(event.pos):
                        row = 6
                        settings.deadzone = round(0.1 + 0.4 * (event.pos[0] - zone_rect.x) / zone_rect.width, 2)
                        settings.save()
            if not capture:
                for command in commands:
                    if command == "back":
                        return "back"
                    if command in ("up", "down"):
                        row = (row + (1 if command == "down" else -1)) % 9
                    elif command in ("left", "right"):
                        if row < 6:
                            column = 0 if command == "left" else 1
                        elif row == 6:
                            settings.deadzone = round(max(0.1, min(0.5, settings.deadzone + (-0.05 if command == "left" else 0.05))), 2)
                            settings.save()
                        elif row in (7, 8):
                            row = 7 if command == "left" else 8
                    elif command == "confirm":
                        if row < 6:
                            begin_capture()
                            break
                        if row == 7:
                            pad = inputs.pad
                            settings.reset(pad.profile_name if pad else None, pad.standard if pad else True)
                        elif row == 8:
                            return "back"

        draw_space(screen)
        draw_panel(screen, panel)
        draw_text(screen, "COMMANDES", title_font, ICE, panel.centerx, panel.y + 42)
        name = inputs.pad.name if inputs.pad else "Aucune manette connectée — clavier disponible"
        fit_text(screen, name, pygame.Rect(panel.x + 24, panel.y + 75, panel.width - 48, 28), MUTED)
        fit_text(screen, "Clavier", pygame.Rect(key_x, top - 37, key_width, 30), CYAN)
        fit_text(screen, "Manette", pygame.Rect(pad_x, top - 37, panel.right - pad_x - 24, 30), CYAN)
        profile = settings.profile(inputs.pad.profile_name, inputs.pad.standard) if inputs.pad else None
        for i, action in enumerate(ACTIONS):
            fit_text(screen, ACTION_LABELS[action], pygame.Rect(panel.x + 20, cells[i][0].y, 155, row_height - 6), MUTED)
            labels = [key_label(settings.keyboard[action]),
                      " / ".join(inputs.pad.label(binding) for binding in profile[action]) if profile else "Connecter une manette"]
            for j, rect in enumerate(cells[i]):
                focused = row == i and column == j
                draw_panel(screen, rect, PANEL_LIGHT if focused else PANEL,
                           GOLD if capture == (action, j) else CYAN if focused else EDGE, shadow=False)
                if focused:
                    pygame.draw.rect(screen, CYAN, (rect.x + 3, rect.y + 12, 3, rect.height - 24))
                fit_text(screen, "En attente..." if capture == (action, j) else labels[j], rect,
                         ICE if j == 0 or profile else DIM)
        fit_text(screen, "Zone morte", pygame.Rect(panel.x + 20, zone_rect.y, 155, 42), MUTED)
        draw_button(screen, zone_rect, f"<  {round(settings.deadzone * 100)} %  >", font, row == 6)
        draw_button(screen, reset_rect, "Réglages par défaut", font, row == 7)
        draw_button(screen, back_rect, "Retour", font, row == 8)
        if capture:
            remaining = max(0, 10 - (pygame.time.get_ticks() - capture_started) // 1000)
            text = settings.message or ("Appuie sur une touche" if capture[1] == 0 else "Appuie sur un bouton, une gâchette ou une direction")
            fit_text(screen, f"{text} ({remaining} s) — Échap pour annuler", pygame.Rect(panel.x + 16, reset_rect.bottom + 10, panel.width - 32, 30), GOLD)
            draw_button(screen, cancel_rect, "Annuler", font)
        else:
            fit_text(screen, settings.message or "Stick / croix : naviguer · A : modifier · B : retour · Entrée / Échap au clavier",
                     pygame.Rect(panel.x + 16, reset_rect.bottom + 10, panel.width - 32, 30), MUTED, 28)
            fit_text(screen, "Zone morte : augmente-la si le stick fait bouger le joueur tout seul.",
                     pygame.Rect(panel.x + 16, reset_rect.bottom + 44, panel.width - 32, 30), DIM, 28)
        canvas.present()
        clock.tick(FPS)
