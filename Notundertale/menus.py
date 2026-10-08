"""Menus : choix du mode et du skin, pause, fin de partie."""

import pygame

from .config import DISPLAY_TOP, FPS
from .controls_menu import show_controls_menu
from .input import MenuInput
from .ui import draw_button, draw_text, draw_volume_slider
from .theme import (UiCanvas, pixel_font, panel as draw_panel, focus_corners,
                    draw_space, text_at, fit_label, footer, CYAN, ICE, MUTED,
                    DIM, EDGE, PANEL, PANEL_LIGHT, GOLD, CORAL)


def show_main_menu(app):
    canvas = UiCanvas(app.screen)
    screen = canvas.surface
    font = pixel_font(2)
    skin_size = min(144, (392 - 16 * (len(app.assets.skins) - 1)) // len(app.assets.skins))
    skin_panel = pygame.Rect(764, 244, 452, 344)
    skin_rects = {
        name: pygame.Rect(round(skin_panel.centerx + (i - (len(app.assets.skins) - 1) / 2) * (skin_size + 16) - skin_size / 2),
                          320, skin_size, 168)
        for i, name in enumerate(app.assets.skins)
    }
    previews = {name: pygame.transform.scale(app.assets.skins[name], (96, 96))
                for name, rect in skin_rects.items()}
    buttons = [(action, label, pygame.Rect(96, 280 + i * 72, 528, 56))
               for i, (action, label) in enumerate([
                   ("infinite", "Mode Infini"), ("story", "Mode Histoire"),
                   ("controls", "Commandes"), ("quit", "Quitter")])]
    clock = pygame.time.Clock()
    nav = MenuInput(app.inputs)
    focused = 0
    while True:
        events = canvas.events()
        commands = nav.read(events)
        selected = None
        for event in events:
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.MOUSEMOTION:
                for i, (_, _, rect) in enumerate(buttons):
                    if rect.collidepoint(event.pos):
                        focused = i
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for name, rect in skin_rects.items():
                    if rect.collidepoint(event.pos):
                        app.selected_skin = name
                for action, _, rect in buttons:
                    if rect.collidepoint(event.pos):
                        selected = action
        for command in commands:
            if command == "back":
                return "quit"
            if command in ("up", "down"):
                focused = (focused + (1 if command == "down" else -1)) % len(buttons)
            elif command in ("left", "right"):
                names = list(app.assets.skins)
                index = names.index(app.selected_skin)
                app.selected_skin = names[(index + (1 if command == "right" else -1)) % len(names)]
            elif command == "confirm":
                selected = buttons[focused][0]
        if selected == "controls":
            if show_controls_menu(app) == "quit":
                return "quit"
            nav = MenuInput(app.inputs)
            continue
        if selected:
            return selected
        draw_space(screen)
        pygame.draw.rect(screen, CYAN, (96, 68, 8, 8))
        text_at(screen, "SURVIVRE / ESQUIVER / RECOMMENCER", (120, 64), 2, MUTED)
        text_at(screen, "NOTUNDERTALE", (92, 112), 7, ICE, shadow=True)
        pygame.draw.rect(screen, CYAN, (96, 196, 84, 4))
        text_at(screen, "COMBIEN DE TEMPS TIENDRAS-TU ?", (96, 216), 2, MUTED)
        draw_panel(screen, skin_panel)
        text_at(screen, "APPARENCE", (skin_panel.x + 28, 270), 2, ICE)
        text_at(screen, "<  >", (skin_panel.right - 88, 270), 2, CYAN)
        for i, (name, rect) in enumerate(skin_rects.items()):
            chosen = name == app.selected_skin
            draw_panel(screen, rect, PANEL_LIGHT if chosen else PANEL, CYAN if chosen else EDGE, shadow=False)
            screen.blit(previews[name], (rect.centerx - 48, rect.y + 14))
            fit_label(screen, f"SKIN {i + 1:02d}", pygame.Rect(rect.x, rect.y + 122, rect.width, 30), ICE if chosen else MUTED)
            if chosen:
                focus_corners(screen, rect)
                pygame.draw.rect(screen, CYAN, (rect.centerx - 12, rect.bottom - 7, 24, 4))
        fit_label(screen, "SÉLECTIONNÉ", pygame.Rect(780, 512, 420, 24), CYAN, 2)
        fit_label(screen, "GAUCHE / DROITE : CHANGER", pygame.Rect(780, 546, 420, 24), MUTED, 2)
        for i, (_, label, rect) in enumerate(buttons):
            draw_button(screen, rect, label, font, focused == i)
        footer(screen, "HAUT / BAS : MENU    A / ENTRÉE : CHOISIR    B / ÉCHAP : RETOUR")
        canvas.present()
        clock.tick(FPS)


def show_coming_soon_screen(app):
    canvas = UiCanvas(app.screen)
    screen = canvas.surface
    font = pixel_font(4)
    small = pixel_font(2)
    clock = pygame.time.Clock()
    nav = MenuInput(app.inputs)
    while True:
        events = canvas.events()
        commands = nav.read(events)
        for event in events:
            if event.type == pygame.QUIT:
                return "quit"
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                return "menu"
        if any(command in ("confirm", "back", "pause") for command in commands):
            return "menu"
        draw_space(screen)
        draw_panel(screen, pygame.Rect(248, 192, 784, 340))
        text_at(screen, "À VENIR", (548, 236), 3, GOLD)
        draw_text(screen, "MODE HISTOIRE", font, ICE, 640, 332)
        draw_text(screen, "L'AVENTURE SE PRÉPARE.", small, MUTED, 640, 410)
        footer(screen, "A / B OU UNE TOUCHE POUR REVENIR")
        canvas.present()
        clock.tick(FPS)


def show_pause_menu(app, background, notice=""):
    canvas = UiCanvas(app.screen)
    screen = canvas.surface
    x, y = screen.get_rect().center
    panel = pygame.Rect(x - 300, 40, 600, 600)
    font = pixel_font(2)
    title_font = pixel_font(5)
    buttons = [(action, label, pygame.Rect(x - 240, panel.y + 148 + i * 64, 480, 48))
               for i, (action, label) in enumerate([
                   ("resume", "Reprendre"), ("controls", "Commandes"), ("restart", "Recommencer"),
                   ("menu", "Menu principal"), ("quit", "Quitter")])]
    slider = pygame.Rect(x - 240, panel.bottom - 64, 480, 16)
    paused = canvas.paused_background(background)
    dragging = False
    clock = pygame.time.Clock()
    nav = MenuInput(app.inputs)
    focused = 0
    while True:
        events = canvas.events()
        commands = nav.read(events)
        selected = None
        for event in events:
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.MOUSEMOTION and not dragging:
                for i, (_, _, rect) in enumerate(buttons):
                    if rect.collidepoint(event.pos):
                        focused = i
                if slider.collidepoint(event.pos):
                    focused = len(buttons)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for action, _, rect in buttons:
                    if rect.collidepoint(event.pos):
                        selected = action
                dragging = slider.collidepoint(event.pos)
                if dragging:
                    app.audio.set_volume((event.pos[0] - slider.x) / slider.width)
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                dragging = False
            if event.type == pygame.MOUSEMOTION and dragging:
                app.audio.set_volume((event.pos[0] - slider.x) / slider.width)
        for command in commands:
            if command in ("back", "pause"):
                return "resume"
            if command in ("up", "down"):
                focused = (focused + (1 if command == "down" else -1)) % (len(buttons) + 1)
            elif command in ("left", "right") and focused == len(buttons):
                app.audio.set_volume(app.audio.volume + (-0.05 if command == "left" else 0.05))
            elif command == "confirm" and focused < len(buttons):
                selected = buttons[focused][0]
        if selected == "controls":
            if show_controls_menu(app) == "quit":
                return "quit"
            nav = MenuInput(app.inputs)
            continue
        if selected:
            return selected
        screen.blit(paused, (0, 0))
        draw_panel(screen, panel)
        draw_text(screen, "PAUSE", title_font, ICE, x, panel.y + 58)
        draw_text(screen, notice or "PARTIE SUSPENDUE", font, GOLD if notice else MUTED, x, panel.y + 110)
        for i, (_, label, rect) in enumerate(buttons):
            draw_button(screen, rect, label, font, focused == i)
        text_at(screen, "VOLUME", (slider.x, slider.y - 36), 2, MUTED)
        text_at(screen, f"{round(app.audio.volume * 100):3d} %", (slider.right - 76, slider.y - 36), 2, CYAN)
        draw_volume_slider(screen, slider, app.audio.volume)
        if focused == len(buttons):
            focus_corners(screen, slider.inflate(6, 8))
        footer(screen, "A / ENTRÉE : CHOISIR    B / ÉCHAP : REPRENDRE")
        canvas.present()
        clock.tick(FPS)


def show_game_over_screen(app, scores, final_score):
    canvas = UiCanvas(app.screen)
    screen = canvas.surface
    panel = pygame.Rect(160, 72, 960, 552)
    font = pixel_font(2)
    title_font = pixel_font(6)
    background = canvas.paused_background(app.screen.copy())
    buttons = [(action, label, pygame.Rect(208 + i * 296, 520, 272, 56))
               for i, (action, label) in enumerate([
                   ("restart", "Rejouer"), ("menu", "Menu principal"), ("quit", "Quitter")])]
    clock = pygame.time.Clock()
    nav = MenuInput(app.inputs)
    focused = 0
    while True:
        events = canvas.events()
        commands = nav.read(events)
        for event in events:
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.MOUSEMOTION:
                for i, (_, _, rect) in enumerate(buttons):
                    if rect.collidepoint(event.pos):
                        focused = i
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for action, _, rect in buttons:
                    if rect.collidepoint(event.pos):
                        return action
        for command in commands:
            if command == "back":
                return "menu"
            if command in ("up", "down", "left", "right"):
                focused = (focused + (1 if command in ("down", "right") else -1)) % len(buttons)
            elif command == "confirm":
                return buttons[focused][0]
        screen.blit(background, (0, 0))
        draw_panel(screen, panel)
        draw_text(screen, "GAME OVER", title_font, CORAL, panel.centerx, 144)
        draw_text(screen, "UNE AUTRE TENTATIVE ?", font, MUTED, panel.centerx, 208)
        pygame.draw.line(screen, EDGE, (640, 264), (640, 472), 2)
        text_at(screen, "TON SCORE", (232, 272), 2, MUTED)
        fit_label(screen, f"{final_score:06d}", pygame.Rect(208, 316, 400, 64), ICE, 5)
        text_at(screen, "CHAQUE SECONDE COMPTE.", (232, 420), 2, MUTED)
        text_at(screen, "MEILLEURS SCORES", (688, 272), 2, CYAN)
        for i, entry in enumerate(scores[:DISPLAY_TOP]):
            color = GOLD if i == 0 else MUTED
            text_at(screen, f"{i + 1:02d}", (688, 312 + i * 32), 2, DIM)
            fit_label(screen, str(entry['score']), pygame.Rect(740, 310 + i * 32, 316, 28), color, 2)
        if not scores:
            text_at(screen, "À TOI DE JOUER.", (688, 336), 2, DIM)
        for i, (_, label, rect) in enumerate(buttons):
            draw_button(screen, rect, label, font, focused == i)
        footer(screen, "DIRECTIONS : CHOISIR    A / ENTRÉE : VALIDER    B / ÉCHAP : MENU")
        canvas.present()
        clock.tick(FPS)
