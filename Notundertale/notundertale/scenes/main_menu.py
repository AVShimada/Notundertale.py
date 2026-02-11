from __future__ import annotations
import sys
import pygame

from ..core.settings import GameConfig
from ..core.assets import load_images
from .game import run_game


WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
GRAY = (169, 169, 169)


def _draw_text(surface: pygame.Surface, text: str, font: pygame.font.Font, color, x: int, y: int) -> None:
    t = font.render(text, True, color)
    r = t.get_rect(center=(x, y))
    surface.blit(t, r)


def show_coming_soon_screen(screen: pygame.Surface) -> None:
    w, h = screen.get_size()
    font = pygame.font.Font(None, 72)
    text = font.render("Coming Soon!", True, WHITE)
    rect = text.get_rect(center=(w // 2, h // 2))

    screen.fill(BLACK)
    screen.blit(text, rect)
    pygame.display.flip()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                return


def show_main_menu(screen: pygame.Surface, images) -> tuple[str, str]:
    """
    Retourne (mode, selected_skin)
    mode: "infinite" | "story" | "quit"
    selected_skin: "default" | "skin1" | "skin2"
    """
    w, h = screen.get_size()
    selected_skin = "default"

    title_font = pygame.font.Font(None, 96)
    button_font = pygame.font.Font(None, 36)
    small_font = pygame.font.Font(None, 28)

    skin_size = 140
    skin_y = h // 2 - 120
    skin_spacing = 180
    center_x = w // 2

    skin1_rect = pygame.Rect(center_x - skin_spacing, skin_y, skin_size, skin_size)
    skin2_rect = pygame.Rect(center_x + skin_spacing - skin_size, skin_y, skin_size, skin_size)

    skin1_preview = pygame.transform.scale(images.player_skins["skin1"], (skin_size, skin_size))
    skin2_preview = pygame.transform.scale(images.player_skins["skin2"], (skin_size, skin_size))

    button_width = 260
    button_height = 55
    button_margin = 20

    inf_button_rect = pygame.Rect(center_x - button_width // 2, skin_y + skin_size + 60, button_width, button_height)
    story_button_rect = pygame.Rect(center_x - button_width // 2, inf_button_rect.bottom + button_margin, button_width, button_height)
    quit_button_rect = pygame.Rect(center_x - button_width // 2, story_button_rect.bottom + button_margin, button_width, button_height)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "quit", selected_skin

            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()

                if skin1_rect.collidepoint(mouse_pos):
                    selected_skin = "skin1"
                if skin2_rect.collidepoint(mouse_pos):
                    selected_skin = "skin2"

                if inf_button_rect.collidepoint(mouse_pos):
                    return "infinite", selected_skin
                if story_button_rect.collidepoint(mouse_pos):
                    return "story", selected_skin
                if quit_button_rect.collidepoint(mouse_pos):
                    return "quit", selected_skin

        screen.fill(BLACK)
        _draw_text(screen, "NotUndertale", title_font, WHITE, center_x, h // 4)

        screen.blit(skin1_preview, skin1_rect)
        screen.blit(skin2_preview, skin2_rect)

        pygame.draw.rect(screen, YELLOW if selected_skin == "skin1" else WHITE, skin1_rect, 4, border_radius=12)
        pygame.draw.rect(screen, YELLOW if selected_skin == "skin2" else WHITE, skin2_rect, 4, border_radius=12)

        if selected_skin == "skin1":
            _draw_text(screen, "SELECTED", small_font, YELLOW, skin1_rect.centerx, skin1_rect.bottom + 20)
        if selected_skin == "skin2":
            _draw_text(screen, "SELECTED", small_font, YELLOW, skin2_rect.centerx, skin2_rect.bottom + 20)

        pygame.draw.rect(screen, GRAY, inf_button_rect, border_radius=12)
        pygame.draw.rect(screen, WHITE, inf_button_rect, 2, border_radius=12)
        _draw_text(screen, "Mode Infini", button_font, WHITE, inf_button_rect.centerx, inf_button_rect.centery)

        pygame.draw.rect(screen, GRAY, story_button_rect, border_radius=12)
        pygame.draw.rect(screen, WHITE, story_button_rect, 2, border_radius=12)
        _draw_text(screen, "Mode Histoire", button_font, WHITE, story_button_rect.centerx, story_button_rect.centery)

        pygame.draw.rect(screen, GRAY, quit_button_rect, border_radius=12)
        pygame.draw.rect(screen, WHITE, quit_button_rect, 2, border_radius=12)
        _draw_text(screen, "Quitter", button_font, WHITE, quit_button_rect.centerx, quit_button_rect.centery)

        pygame.display.flip()
