from __future__ import annotations
import sys
import pygame

from ..core.score import save_score, load_scores
from ..core.settings import GameConfig


WHITE = (255, 255, 255)
RED = (255, 60, 60)
GOLD = (255, 215, 0)


def game_over(screen: pygame.Surface, cfg: GameConfig, score: int) -> str:
    clock = pygame.time.Clock()
    w, h = screen.get_size()

    save_score(cfg.score_file, "Player", score, cfg.max_scores)
    scores = load_scores(cfg.score_file)

    title_font = pygame.font.Font(None, 100)
    text_font = pygame.font.Font(None, 40)

    while True:
        clock.tick(cfg.fps)

        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))

        box_w = 600
        box_h = 650
        box_x = w // 2 - box_w // 2
        box_y = h // 2 - box_h // 2

        pygame.draw.rect(screen, (30, 30, 30), (box_x, box_y, box_w, box_h), border_radius=20)
        pygame.draw.rect(screen, WHITE, (box_x, box_y, box_w, box_h), 3, border_radius=20)

        center_x = w // 2
        y = box_y + 50

        title = title_font.render("GAME OVER", True, RED)
        screen.blit(title, title.get_rect(center=(center_x, y)))
        y += 90

        score_txt = text_font.render(f"FINAL SCORE : {score}", True, WHITE)
        screen.blit(score_txt, score_txt.get_rect(center=(center_x, y)))
        y += 60

        pygame.draw.line(screen, (80, 80, 80), (box_x + 50, y), (box_x + box_w - 50, y), 2)
        y += 40

        top_txt = text_font.render("TOP SCORES", True, GOLD)
        screen.blit(top_txt, top_txt.get_rect(center=(center_x, y)))
        y += 40

        for i, entry in enumerate(scores[:5]):
            line = text_font.render(f"{i+1}. {entry.score}", True, WHITE)
            screen.blit(line, line.get_rect(center=(center_x, y)))
            y += 35

        y += 30

        btn_w = 280
        btn_h = 55

        play_rect = pygame.Rect(center_x - btn_w // 2, y, btn_w, btn_h)
        y += 75
        menu_rect = pygame.Rect(center_x - btn_w // 2, y, btn_w, btn_h)
        y += 75
        quit_rect = pygame.Rect(center_x - btn_w // 2, y, btn_w, btn_h)

        mouse = pygame.mouse.get_pos()

        for text, rect in [
            ("PLAY AGAIN", play_rect),
            ("MAIN MENU", menu_rect),
            ("QUIT", quit_rect),
        ]:
            hovered = rect.collidepoint(mouse)
            color = (120, 120, 120) if hovered else (70, 70, 70)

            pygame.draw.rect(screen, color, rect, border_radius=15)
            pygame.draw.rect(screen, WHITE, rect, 2, border_radius=15)

            label = text_font.render(text, True, WHITE)
            screen.blit(label, label.get_rect(center=rect.center))

        pygame.display.flip()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return "quit"

            if e.type == pygame.MOUSEBUTTONDOWN:
                if play_rect.collidepoint(e.pos):
                    return "replay"
                if menu_rect.collidepoint(e.pos):
                    return "menu"
                if quit_rect.collidepoint(e.pos):
                    return "quit"
