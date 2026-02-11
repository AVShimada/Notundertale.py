import pygame

from notundertale.core.settings import GameConfig
from notundertale.core.assets import load_images
from notundertale.scenes.main_menu import show_main_menu, show_coming_soon_screen
from notundertale.scenes.game import run_game
from notundertale.scenes.game_over import game_over


def main():
    pygame.init()
    pygame.mixer.init()

    cfg = GameConfig()
    screen = pygame.display.set_mode((cfg.width, cfg.height))
    pygame.display.set_caption("NotUndertale")

    images = load_images((cfg.width, cfg.height))

    current_scene = "menu"
    selected_skin = "default"
    score = 0

    while True:

        # ================= MENU =================
        if current_scene == "menu":
            mode, selected_skin = show_main_menu(screen, images)

            if mode == "infinite":
                current_scene = "game"
            elif mode == "story":
                show_coming_soon_screen(screen)
                current_scene = "menu"
            else:
                current_scene = "quit"

        # ================= GAME =================
        elif current_scene == "game":
            result = run_game(screen, cfg, selected_skin)
            print("RUN_GAME RETURNED:", result)
            score = result

            if score < 0:
                current_scene = "menu"
            else:
                current_scene = "game_over"

        elif current_scene == "game_over":
            result = game_over(screen, cfg, score)

            if result == "replay":
                current_scene = "game"

            elif result == "menu":
                current_scene = "menu"

            elif result == "quit":
                break

            else:
                current_scene = "menu"

        # ================= QUIT =================
        elif current_scene == "quit":
            break

    pygame.quit()


if __name__ == "__main__":
    main()
