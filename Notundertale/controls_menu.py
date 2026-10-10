"""Écran de réaffectation des commandes, accessible depuis les deux menus."""

import pygame

from .config import FPS, WHITE
from .controls import ACTION_LABELS, key_label, Binding
from .input import BindingCapture, MenuInput
from .ui import draw_button, draw_text
from .theme import (UiCanvas, pixel_font, panel as draw_panel,
                    draw_space, fit_label, CYAN, ICE, MUTED, DIM, EDGE,
                    PANEL, PANEL_LIGHT, GOLD)


def fit_text(surface, text, rect, color=WHITE, size=28):
    fit_label(surface, text, rect, color, max(1, size // 14))


def show_controls_menu(app):
    original_mode = app.inputs.settings.mode
    try:
        while True:
            result = _show_controls_page(app)
            if result != "switch":
                return result
            app.inputs.set_mode("story" if app.inputs.settings.mode == "infinite" else "infinite")
    finally:
        app.inputs.set_mode(original_mode)


def _show_controls_page(app):
    canvas = UiCanvas(app.screen)
    screen = canvas.surface
    width, height = screen.get_size()
    panel = pygame.Rect((width - min(1080, width - 32)) // 2, 18, min(1080, width - 32), height - 36)
    inputs = app.inputs
    settings = inputs.settings
    actions = settings.actions
    count = len(actions)
    nav = MenuInput(inputs)
    row, column = 0, 0
    capture = None
    capture_started = 0
    capture_pad = None
    clock = pygame.time.Clock()
    font = pixel_font(2)
    title_font = pixel_font(4)
    top = panel.y + (133 if count > 7 else 158)
    row_height = 35 if count > 7 else min(48, (panel.height - 380) // count)
    key_x = panel.x + 190
    key_width = 250
    pad_x = key_x + key_width + 18
    cells = [[pygame.Rect(key_x, top + i * row_height, key_width, row_height - 6),
              pygame.Rect(pad_x, top + i * row_height, panel.right - pad_x - 24, row_height - 6)]
             for i in range(count)]
    zone_rect = pygame.Rect(key_x, top + count * row_height + 12, panel.right - key_x - 24, 42)
    reset_rect = pygame.Rect(panel.x + 24, zone_rect.bottom + 22, 420, 44)
    back_rect = pygame.Rect(panel.right - 240, reset_rect.y, 216, 44)
    cancel_rect = pygame.Rect(panel.centerx - 100, panel.bottom - (40 if count > 7 else 70),
                             200, 32 if count > 7 else 38)
    mode_rect = pygame.Rect(panel.right - 294, panel.y + 20, 270, 36)

    def begin_capture():
        nonlocal capture, capture_started, capture_pad
        if column == 1 and not inputs.pad:
            settings.message = "Branche une manette pour changer ses commandes."
            return
        capture = (actions[row], column)
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
                elif device_column == 0 and event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 2, 3):
                    if settings.bind_key(action, -event.button):
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
            for event in events:
                if ((event.type == pygame.KEYDOWN and event.key == pygame.K_TAB)
                    or (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and mode_rect.collidepoint(event.pos))
                    or (inputs.pad and inputs.pad.event_binding(event) == Binding("button", 3))):
                    return "switch"
            commands = nav.read(events)
            for event in events:
                if event.type == pygame.MOUSEMOTION:
                    for i, pair in enumerate(cells):
                        for j, rect in enumerate(pair):
                            if rect.collidepoint(event.pos):
                                row, column = i, j
                    for i, rect in enumerate((zone_rect, reset_rect, back_rect), start=count):
                        if rect.collidepoint(event.pos):
                            row = i
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for i, pair in enumerate(cells):
                        for j, rect in enumerate(pair):
                            if rect.collidepoint(event.pos):
                                row, column = i, j
                                begin_capture()
                    if reset_rect.collidepoint(event.pos):
                        row = count + 1
                        commands.append("confirm")
                    if back_rect.collidepoint(event.pos):
                        return "back"
                    if zone_rect.collidepoint(event.pos):
                        row = count
                        settings.deadzone = round(0.1 + 0.4 * (event.pos[0] - zone_rect.x) / zone_rect.width, 2)
                        settings.save()
            if not capture:
                for command in commands:
                    if command == "back":
                        return "back"
                    if command in ("up", "down"):
                        row = (row + (1 if command == "down" else -1)) % (count + 3)
                    elif command in ("left", "right"):
                        if row < count:
                            column = 0 if command == "left" else 1
                        elif row == count:
                            settings.deadzone = round(max(0.1, min(0.5, settings.deadzone + (-0.05 if command == "left" else 0.05))), 2)
                            settings.save()
                        elif row in (count + 1, count + 2):
                            row = count + 1 if command == "left" else count + 2
                    elif command == "confirm":
                        if row < count:
                            begin_capture()
                            break
                        if row == count + 1:
                            pad = inputs.pad
                            settings.reset(pad.profile_name if pad else None, pad.standard if pad else True)
                        elif row == count + 2:
                            return "back"

        draw_space(screen)
        draw_panel(screen, panel)
        draw_text(screen, "COMMANDES", title_font, ICE, panel.centerx, panel.y + 42)
        draw_button(screen, mode_rect, "Histoire >" if settings.mode == "story" else "Infini >", font)
        name = inputs.pad.name if inputs.pad else "Aucune manette connectée — clavier disponible"
        fit_text(screen, name, pygame.Rect(panel.x + 24, panel.y + 75, panel.width - 48, 28), MUTED)
        fit_text(screen, "Clavier / souris", pygame.Rect(key_x, top - 37, key_width, 30), CYAN)
        fit_text(screen, "Manette", pygame.Rect(pad_x, top - 37, panel.right - pad_x - 24, 30), CYAN)
        profile = settings.profile(inputs.pad.profile_name, inputs.pad.standard) if inputs.pad else None
        for i, action in enumerate(actions):
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
        draw_button(screen, zone_rect, f"<  {round(settings.deadzone * 100)} %  >", font, row == count)
        draw_button(screen, reset_rect, "Réglages par défaut", font, row == count + 1)
        draw_button(screen, back_rect, "Retour", font, row == count + 2)
        if capture:
            remaining = max(0, 10 - (pygame.time.get_ticks() - capture_started) // 1000)
            text = settings.message or ("Appuie sur une touche ou clique" if capture[1] == 0 else "Appuie sur un bouton, une gâchette ou une direction")
            fit_text(screen, f"{text} ({remaining} s) — Échap pour annuler", pygame.Rect(panel.x + 16, reset_rect.bottom + 10, panel.width - 32, 30), GOLD)
            draw_button(screen, cancel_rect, "Annuler", font)
        else:
            fit_text(screen, settings.message or "Stick / croix : naviguer · A : modifier · B : retour · Entrée / Échap au clavier",
                     pygame.Rect(panel.x + 16, reset_rect.bottom + 10, panel.width - 32, 30), MUTED, 28)
            fit_text(screen, "Tab / Y : changer de mode · Zone morte : corriger la dérive du stick.",
                     pygame.Rect(panel.x + 16, reset_rect.bottom + 44, panel.width - 32, 30), DIM, 28)
        canvas.present()
        clock.tick(FPS)
