from __future__ import annotations
import pygame

def pause_loop(screen: pygame.Surface, fps: int, score: int = 0) -> str:
    clock = pygame.time.Clock()
    w, h = screen.get_size()

    WHITE = (255, 255, 255)
    GOLD = (255, 215, 0)

    title_font = pygame.font.Font(None, 100)
    text_font = pygame.font.Font(None, 42)
    small_font = pygame.font.Font(None, 32)

    box_w = 600
    box_h = 650
    box_x = w // 2 - box_w // 2
    box_y = h // 2 - box_h // 2

    btn_w = 320
    btn_h = 60

    resume_rect = pygame.Rect(w//2 - btn_w//2, box_y + 260, btn_w, btn_h)
    restart_rect = pygame.Rect(w//2 - btn_w//2, box_y + 340, btn_w, btn_h)
    menu_rect = pygame.Rect(w//2 - btn_w//2, box_y + 420, btn_w, btn_h)
    quit_rect = pygame.Rect(w//2 - btn_w//2, box_y + 500, btn_w, btn_h)

    while True:
        clock.tick(fps)

        # Dark overlay
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))

        # Main panel
        pygame.draw.rect(screen, (30, 30, 30), (box_x, box_y, box_w, box_h), border_radius=20)
        pygame.draw.rect(screen, WHITE, (box_x, box_y, box_w, box_h), 3, border_radius=20)

        # Title
        title = title_font.render("PAUSED", True, WHITE)
        screen.blit(title, title.get_rect(center=(w//2, box_y + 80)))

        # Divider
        pygame.draw.line(screen, (80, 80, 80), (box_x + 50, box_y + 150), (box_x + box_w - 50, box_y + 150), 2)

        # Stats section
        stats_y = box_y + 180
        score_txt = text_font.render(f"SCORE : {score}", True, GOLD)
        screen.blit(score_txt, score_txt.get_rect(center=(w//2, stats_y)))

        mouse = pygame.mouse.get_pos()

        # Buttons
        for text, rect in [
            ("RESUME", resume_rect),
            ("RESTART", restart_rect),
            ("MAIN MENU", menu_rect),
            ("QUIT", quit_rect),
        ]:
            hovered = rect.collidepoint(mouse)
            color = (120,120,120) if hovered else (70,70,70)

            pygame.draw.rect(screen, color, rect, border_radius=15)
            pygame.draw.rect(screen, WHITE, rect, 2, border_radius=15)

            label = text_font.render(text, True, WHITE)
            screen.blit(label, label.get_rect(center=rect.center))

        pygame.display.flip()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return "quit"

            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                return "resume"

            if e.type == pygame.MOUSEBUTTONDOWN:
                if resume_rect.collidepoint(e.pos):
                    return "resume"
                if restart_rect.collidepoint(e.pos):
                    return "restart"
                if menu_rect.collidepoint(e.pos):
                    return "menu"
                if quit_rect.collidepoint(e.pos):
                    return "quit"
