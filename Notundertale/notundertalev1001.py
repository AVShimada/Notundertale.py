import pygame
import sys
import random

# Initialisation de Pygame
pygame.init()

# Récupérer la taille de l'écran
info_screen = pygame.display.Info()
screen_width = info_screen.current_w
screen_height = info_screen.current_h

# Créer la fenêtre en mode plein écran avec la résolution de l'écran
screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
pygame.display.set_caption('NotUndertale')

# Couleurs
black = (0, 0, 0)
white = (255, 255, 255)
red = (255, 0, 0)
green = (0, 255, 0)
blue = (0, 0, 255)
yellow = (255, 255, 0)
gray = (169, 169, 169)

# Chargement et redimensionnement des images
heart_image = pygame.image.load('heart.png')
heart_image = pygame.transform.scale(heart_image, (50, 50))
heart_rect = heart_image.get_rect()

shield_icon = pygame.image.load('shield.png')
shield_icon = pygame.transform.scale(shield_icon, (75, 75))
shield_icon_rect = shield_icon.get_rect()

player_image = pygame.image.load('player.png')
player_image = pygame.transform.scale(player_image, (100, 100))
player_rect = player_image.get_rect()

background_image = pygame.image.load('space_background.png')
background_image = pygame.transform.scale(background_image, (screen_width, screen_height))

background_surface = pygame.Surface((screen_width, screen_height))
background_surface.blit(background_image, (0, 0))

# Load different skins
skins = {
    "default": pygame.image.load('player.png'),
    "skin1": pygame.image.load('player_skin1.png'),
    "skin2": pygame.image.load('player_skin2.png')
}

# Variable to store the currently selected skin
selected_skin = "default"


def load_and_play_music():
    try:
        pygame.mixer.music.load('background_music.mp3')
        pygame.mixer.music.play(-1)
        print("Musique chargée et jouée.")
    except pygame.error as e:
        print(f"Erreur de chargement de la musique : {e}")


# ===========================
# MODIF 1 : Warning laser correct
# - Warning = une seule colonne
# - Warning vertical (comme laser)
# - Laser spawn à la même position que le warning
# ===========================

class WarningLight(pygame.sprite.Sprite):
    def __init__(self, x_position):
        super().__init__()

        self.width = screen_width // 8
        self.height = screen_height

        # Surface avec transparence (RGBA)
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.image.fill((255, 255, 255, 120))  # blanc semi-transparent

        self.rect = self.image.get_rect()
        self.rect.x = x_position
        self.rect.y = 0

        self.fading = False
        self.fade_duration = 0.5
        self.start_time = pygame.time.get_ticks()

    def update(self):
        current_time = pygame.time.get_ticks()
        elapsed_time = (current_time - self.start_time) / 1000

        # après 2s, fade out
        if elapsed_time >= 2 and not self.fading:
            self.fading = True
            self.fade_start_time = current_time

        if self.fading:
            fade_elapsed_time = (current_time - self.fade_start_time) / 1000
            alpha = max(0, 255 * (1 - fade_elapsed_time / self.fade_duration))
            self.image.set_alpha(alpha)
            if alpha <= 0:
                self.kill()


# Classe joueur
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.original_image = pygame.transform.scale(skins[selected_skin], (100, 100))
        self.image = self.original_image
        self.rect = self.image.get_rect()
        self.rect.center = (screen_width // 2, screen_height // 2)
        self.mask = pygame.mask.from_surface(self.image)
        self.speed = 10
        self.health = 3
        self.invulnerable = False
        self.invulnerable_start_time = 0
        self.invulnerable_duration = 1

    def update(self, keys):
        if self.invulnerable:
            current_time = pygame.time.get_ticks()
            if (current_time - self.invulnerable_start_time) / 1000 > self.invulnerable_duration:
                self.invulnerable = False
                self.image = self.original_image
                self.image.set_alpha(255)
            else:
                alpha = 255 * (1 - ((current_time - self.invulnerable_start_time) % 200) / 100)
                self.image.set_alpha(alpha)

        if keys[pygame.K_LEFT]:
            self.rect.x -= self.speed
            self.image = pygame.transform.flip(self.original_image, True, False)
            self.mask = pygame.mask.from_surface(self.image)
        if keys[pygame.K_RIGHT]:
            self.rect.x += self.speed
            self.image = self.original_image
            self.mask = pygame.mask.from_surface(self.image)
        if keys[pygame.K_UP]:
            self.rect.y -= self.speed
        if keys[pygame.K_DOWN]:
            self.rect.y += self.speed

        self.rect.x = max(0, min(self.rect.x, screen_width - self.rect.width))
        self.rect.y = max(0, min(self.rect.y, screen_height - self.rect.height))

    def decrease_health(self):
        if not self.invulnerable:
            self.health -= 1
            if self.health <= 0:
                self.kill()
            else:
                self.invulnerable = True
                self.invulnerable_start_time = pygame.time.get_ticks()


# Classe Projectile de base
class Projectile(pygame.sprite.Sprite):
    def __init__(self, image_path, speed):
        super().__init__()
        self.image = pygame.image.load(image_path)
        self.image = pygame.transform.scale(self.image, (40, 40))
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, screen_width - self.rect.width)
        self.rect.y = 0
        self.speed = speed
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > screen_height:
            self.kill()


class Meteor1(Projectile):
    def __init__(self):
        super().__init__('meteor1.png', speed=11)


class Meteor2(Projectile):
    def __init__(self):
        super().__init__('meteor2.png', speed=12)


class Meteor3(Projectile):
    def __init__(self):
        super().__init__('meteor3.png', speed=10)


# Classe pour les rayons lasers
class Laser(pygame.sprite.Sprite):
    def __init__(self, x_position):
        super().__init__()
        self.width = screen_width // 8
        self.height = screen_height
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.image.fill(white)
        self.rect = self.image.get_rect()
        self.rect.x = x_position
        self.rect.y = 0
        self.mask = pygame.mask.from_surface(self.image)
        self.lifetime = 1.5
        self.fade_duration = 0.5
        self.start_time = pygame.time.get_ticks()
        self.fading = False

    def update(self):
        current_time = pygame.time.get_ticks()
        elapsed_time = (current_time - self.start_time) / 1000
        if elapsed_time >= self.lifetime and not self.fading:
            self.fading = True
            self.fade_start_time = current_time
        if self.fading:
            fade_elapsed_time = (current_time - self.fade_start_time) / 1000
            alpha = max(0, 255 * (1 - fade_elapsed_time / self.fade_duration))
            self.image.set_alpha(alpha)
            if alpha <= 0:
                self.kill()

    def draw(self, surface):
        surface.blit(self.image, self.rect.topleft)


class ShieldPowerUp(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.image.load('shield.png')
        self.image = pygame.transform.scale(self.image, (75, 75))
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, screen_width - self.rect.width)
        self.rect.y = random.randint(0, screen_height - self.rect.height)
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        pass


class HeartPowerUp(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.image.load('heart.png')
        self.image = pygame.transform.scale(self.image, (50, 50))
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, screen_width - self.rect.width)
        self.rect.y = random.randint(0, screen_height - self.rect.height)
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        pass


def create_sprites():
    all_sprites = pygame.sprite.Group()
    projectiles = pygame.sprite.Group()
    lasers = pygame.sprite.Group()
    power_ups = pygame.sprite.Group()
    player = Player()
    all_sprites.add(player)
    return all_sprites, projectiles, lasers, power_ups, player


ADD_PROJECTILE = pygame.USEREVENT + 1
ADD_LASER = pygame.USEREVENT + 2
ADD_POWER_UP = pygame.USEREVENT + 3
ADD_HEART_POWER_UP = pygame.USEREVENT + 4
pygame.time.set_timer(ADD_PROJECTILE, 300)
pygame.time.set_timer(ADD_POWER_UP, 15000)
pygame.time.set_timer(ADD_HEART_POWER_UP, 20000)

score = 0
high_score = 0
score_font = pygame.font.Font(None, 48)


def show_coming_soon_screen():
    font = pygame.font.Font(None, 72)
    text = font.render("Coming Soon!", True, white)
    text_rect = text.get_rect(center=(screen_width // 2, screen_height // 2))

    screen.fill(black)
    screen.blit(text, text_rect)
    pygame.display.flip()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                waiting = False


def show_game_over_screen():
    overlay = pygame.Surface((screen_width, screen_height))
    overlay.set_alpha(180)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    menu_box_width = 500
    menu_box_height = 450
    menu_box_x = (screen_width // 2) - (menu_box_width // 2)
    menu_box_y = (screen_height // 2) - (menu_box_height // 2)

    pygame.draw.rect(screen, (50, 50, 50), (menu_box_x, menu_box_y, menu_box_width, menu_box_height), 0, 15)
    pygame.draw.rect(screen, (255, 255, 255), (menu_box_x, menu_box_y, menu_box_width, menu_box_height), 3, 15)

    title_font = pygame.font.Font(None, 96)
    text_font = pygame.font.Font(None, 48)

    game_over_text = title_font.render("Game Over", True, (255, 0, 0))
    screen.blit(game_over_text, (screen_width // 2 - game_over_text.get_width() // 2, menu_box_y + 30))

    score_text = text_font.render(f"Final Score: {score}", True, (255, 255, 255))
    screen.blit(score_text, (screen_width // 2 - score_text.get_width() // 2, menu_box_y + 150))

    play_again_button_rect = pygame.Rect(screen_width // 2 - 150, menu_box_y + 210, 300, 50)
    main_menu_button_rect = pygame.Rect(screen_width // 2 - 150, menu_box_y + 270, 300, 50)
    quit_button_rect = pygame.Rect(screen_width // 2 - 150, menu_box_y + 330, 300, 50)

    pygame.draw.rect(screen, (100, 100, 100), play_again_button_rect, border_radius=10)
    pygame.draw.rect(screen, (255, 255, 255), play_again_button_rect, 2, border_radius=10)
    pygame.draw.rect(screen, (100, 100, 100), main_menu_button_rect, border_radius=10)
    pygame.draw.rect(screen, (255, 255, 255), main_menu_button_rect, 2, border_radius=10)
    pygame.draw.rect(screen, (100, 100, 100), quit_button_rect, border_radius=10)
    pygame.draw.rect(screen, (255, 255, 255), quit_button_rect, 2, border_radius=10)

    play_again_text = text_font.render("Play Again", True, (255, 255, 255))
    screen.blit(play_again_text, (play_again_button_rect.centerx - play_again_text.get_width() // 2,
                                 play_again_button_rect.centery - play_again_text.get_height() // 2))

    main_menu_text = text_font.render("Main Menu", True, (255, 255, 255))
    screen.blit(main_menu_text, (main_menu_button_rect.centerx - main_menu_text.get_width() // 2,
                                 main_menu_button_rect.centery - main_menu_text.get_height() // 2))

    quit_text = text_font.render("Quit", True, (255, 255, 255))
    screen.blit(quit_text, (quit_button_rect.centerx - quit_text.get_width() // 2,
                            quit_button_rect.centery - quit_text.get_height() // 2))

    pygame.display.flip()

    waiting_for_input = True
    while waiting_for_input:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if play_again_button_rect.collidepoint(event.pos):
                    return "play_again"
                elif main_menu_button_rect.collidepoint(event.pos):
                    return "main_menu"
                elif quit_button_rect.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()


music_volume = 0.5
pygame.mixer.music.set_volume(music_volume)


def draw_volume_slider(current_volume):
    slider_width = 300
    slider_height = 20
    slider_x = (screen_width // 2) - (slider_width // 2)
    slider_y = screen_height // 2 + 180

    slider_bg_color = (150, 150, 150)
    slider_fg_color = (255, 255, 255)

    pygame.draw.rect(screen, slider_bg_color, (slider_x, slider_y, slider_width, slider_height), 0, 10)

    fill_width = int(current_volume * slider_width)
    pygame.draw.rect(screen, slider_fg_color, (slider_x, slider_y, fill_width, slider_height), 0, 10)

    return pygame.Rect(slider_x, slider_y, slider_width, slider_height)


def show_pause_menu():
    button_font = pygame.font.Font(None, 48)

    overlay = pygame.Surface((screen_width, screen_height))
    overlay.set_alpha(180)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    menu_box_width = 500
    menu_box_height = 600
    menu_box_x = (screen_width // 2) - (menu_box_width // 2)
    menu_box_y = (screen_height // 2) - (menu_box_height // 2)

    pygame.draw.rect(screen, (50, 50, 50), (menu_box_x, menu_box_y, menu_box_width, menu_box_height), 0, 15)
    pygame.draw.rect(screen, (255, 255, 255), (menu_box_x, menu_box_y, menu_box_width, menu_box_height), 3, 15)

    title_font = pygame.font.Font(None, 96)
    text_font = pygame.font.Font(None, 48)

    pause_text = title_font.render("Game Paused", True, (255, 0, 0))
    screen.blit(pause_text, (screen_width // 2 - pause_text.get_width() // 2, menu_box_y + 30))

    resume_button_rect = pygame.Rect(menu_box_x + 50, menu_box_y + 120, 400, 60)
    restart_button_rect = pygame.Rect(menu_box_x + 50, menu_box_y + 200, 400, 60)
    main_menu_button_rect = pygame.Rect(menu_box_x + 50, menu_box_y + 280, 400, 60)
    quit_button_rect = pygame.Rect(menu_box_x + 50, menu_box_y + 360, 400, 60)
    volume_instruction_y = menu_box_y + 450

    pygame.draw.rect(screen, (100, 100, 100), resume_button_rect, border_radius=15)
    pygame.draw.rect(screen, (255, 255, 255), resume_button_rect, 2, border_radius=15)
    pygame.draw.rect(screen, (100, 100, 100), restart_button_rect, border_radius=15)
    pygame.draw.rect(screen, (255, 255, 255), restart_button_rect, 2, border_radius=15)
    pygame.draw.rect(screen, (100, 100, 100), main_menu_button_rect, border_radius=15)
    pygame.draw.rect(screen, (255, 255, 255), main_menu_button_rect, 2, border_radius=15)
    pygame.draw.rect(screen, (100, 100, 100), quit_button_rect, border_radius=15)
    pygame.draw.rect(screen, (255, 255, 255), quit_button_rect, 2, border_radius=15)

    resume_text = text_font.render("Resume", True, (255, 255, 255))
    screen.blit(resume_text, (resume_button_rect.centerx - resume_text.get_width() // 2,
                             resume_button_rect.centery - resume_text.get_height() // 2))

    restart_text = text_font.render("Restart", True, (255, 255, 255))
    screen.blit(restart_text, (restart_button_rect.centerx - restart_text.get_width() // 2,
                               restart_button_rect.centery - restart_text.get_height() // 2))

    main_menu_text = text_font.render("Main Menu", True, (255, 255, 255))
    screen.blit(main_menu_text, (main_menu_button_rect.centerx - main_menu_text.get_width() // 2,
                                 main_menu_button_rect.centery - main_menu_text.get_height() // 2))

    quit_text = text_font.render("Quit", True, (255, 255, 255))
    screen.blit(quit_text, (quit_button_rect.centerx - quit_text.get_width() // 2,
                            quit_button_rect.centery - quit_text.get_height() // 2))

    volume_instruction_text = text_font.render("Adjust Volume:", True, (255, 255, 255))
    screen.blit(volume_instruction_text, (screen_width // 2 - volume_instruction_text.get_width() // 2,
                                          volume_instruction_y))

    current_volume = pygame.mixer.music.get_volume()
    volume_slider_rect = draw_volume_slider(current_volume)
    volume_slider_rect.y = volume_instruction_y + 30

    pygame.display.flip()

    adjusting_volume = False
    waiting_for_input = True
    while waiting_for_input:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    waiting_for_input = False
                if event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if resume_button_rect.collidepoint(mouse_pos):
                    waiting_for_input = False
                elif restart_button_rect.collidepoint(mouse_pos):
                    pygame.mixer.music.stop()
                    game_loop()
                elif main_menu_button_rect.collidepoint(mouse_pos):
                    pygame.mixer.music.stop()
                    show_main_menu()
                elif quit_button_rect.collidepoint(mouse_pos):
                    pygame.quit()
                    sys.exit()

                if volume_slider_rect.collidepoint(event.pos):
                    adjusting_volume = True

            if event.type == pygame.MOUSEBUTTONUP:
                adjusting_volume = False

            if event.type == pygame.MOUSEMOTION:
                if adjusting_volume:
                    mouse_x, _ = event.pos
                    slider_x = volume_slider_rect.x
                    slider_width = volume_slider_rect.width

                    new_volume = (mouse_x - slider_x) / slider_width
                    new_volume = max(0, min(new_volume, 1))
                    pygame.mixer.music.set_volume(new_volume)

                    screen.blit(overlay, (0, 0))
                    pygame.draw.rect(screen, (50, 50, 50), (menu_box_x, menu_box_y, menu_box_width, menu_box_height), 0, 15)
                    pygame.draw.rect(screen, (255, 255, 255), (menu_box_x, menu_box_y, menu_box_width, menu_box_height), 3, 15)

                    screen.blit(pause_text, (screen_width // 2 - pause_text.get_width() // 2, menu_box_y + 30))
                    screen.blit(resume_text, (resume_button_rect.centerx - resume_text.get_width() // 2,
                                             resume_button_rect.centery - resume_text.get_height() // 2))
                    screen.blit(restart_text, (restart_button_rect.centerx - restart_text.get_width() // 2,
                                               restart_button_rect.centery - restart_text.get_height() // 2))
                    screen.blit(main_menu_text, (main_menu_button_rect.centerx - main_menu_text.get_width() // 2,
                                                 main_menu_button_rect.centery - main_menu_text.get_height() // 2))
                    screen.blit(quit_text, (quit_button_rect.centerx - quit_text.get_width() // 2,
                                            quit_button_rect.centery - quit_text.get_height() // 2))

                    screen.blit(volume_instruction_text, (screen_width // 2 - volume_instruction_text.get_width() // 2,
                                                          volume_instruction_y))
                    volume_slider_rect = draw_volume_slider(new_volume)
                    volume_slider_rect.y = volume_instruction_y + 30
                    pygame.display.flip()


# Chargement des images
def load_image(image_path, size):
    image = pygame.image.load(image_path)
    return pygame.transform.scale(image, size)


def draw_text(surface, text, font, color, x, y):
    textobj = font.render(text, True, color)
    textrect = textobj.get_rect()
    textrect.center = (x, y)
    surface.blit(textobj, textrect)


# ===========================
# MODIF 2 : supprimer le show_main_menu sans skins
# -> on garde UNIQUEMENT celui avec skins
# ===========================

def show_main_menu():
    title_font = pygame.font.Font(None, 96)
    button_font = pygame.font.Font(None, 36)  # Reduced font size

    button_width = 250  # Reduced button width
    button_height = 50  # Reduced button height
    button_margin = 15  # Reduced margin

    # Adjust button positions
    skin1_button_rect = pygame.Rect(screen_width // 4 - button_width // 2, screen_height // 2 - 100, button_width, button_height)
    skin2_button_rect = pygame.Rect(3 * screen_width // 4 - button_width // 2, screen_height // 2 - 100, button_width, button_height)

    inf_button_rect = pygame.Rect(screen_width // 2 - button_width // 2, screen_height // 2, button_width, button_height)
    story_button_rect = pygame.Rect(screen_width // 2 - button_width // 2, screen_height // 2 + button_height + button_margin, button_width, button_height)
    quit_button_rect = pygame.Rect(screen_width // 2 - button_width // 2, screen_height // 2 + 2 * (button_height + button_margin), button_width, button_height)

    menu_running = True
    global selected_skin

    while menu_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()

                if skin1_button_rect.collidepoint(mouse_pos):
                    selected_skin = "skin1"
                if skin2_button_rect.collidepoint(mouse_pos):
                    selected_skin = "skin2"

                if inf_button_rect.collidepoint(mouse_pos):
                    return "infinite"
                if story_button_rect.collidepoint(mouse_pos):
                    return "story"
                if quit_button_rect.collidepoint(mouse_pos):
                    pygame.quit()
                    sys.exit()

        screen.fill(black)

        draw_text(screen, "NotUndertale", title_font, white, screen_width // 2, screen_height // 4)

        # Draw skin selection buttons
        pygame.draw.rect(screen, gray, skin1_button_rect, border_radius=15)
        pygame.draw.rect(screen, white, skin1_button_rect, 2, border_radius=15)
        draw_text(screen, "Skin 1", button_font, white, skin1_button_rect.centerx, skin1_button_rect.centery)

        pygame.draw.rect(screen, gray, skin2_button_rect, border_radius=15)
        pygame.draw.rect(screen, white, skin2_button_rect, 2, border_radius=15)
        draw_text(screen, "Skin 2", button_font, white, skin2_button_rect.centerx, skin2_button_rect.centery)

        # Draw mode selection buttons
        pygame.draw.rect(screen, gray, inf_button_rect, border_radius=15)
        pygame.draw.rect(screen, white, inf_button_rect, 2, border_radius=15)
        draw_text(screen, "Mode Infini", button_font, white, inf_button_rect.centerx, inf_button_rect.centery)

        pygame.draw.rect(screen, gray, story_button_rect, border_radius=15)
        pygame.draw.rect(screen, white, story_button_rect, 2, border_radius=15)
        draw_text(screen, "Mode Histoire", button_font, white, story_button_rect.centerx, story_button_rect.centery)

        pygame.draw.rect(screen, gray, quit_button_rect, border_radius=15)
        pygame.draw.rect(screen, white, quit_button_rect, 2, border_radius=15)
        draw_text(screen, "Quitter", button_font, white, quit_button_rect.centerx, quit_button_rect.centery)

        pygame.display.flip()


def show_main_menu():
    global selected_skin

    title_font = pygame.font.Font(None, 96)
    button_font = pygame.font.Font(None, 36)
    small_font = pygame.font.Font(None, 28)

    # Dimensions
    skin_size = 140
    skin_y = screen_height // 2 - 120
    skin_spacing = 180

    center_x = screen_width // 2

    # Positions des skins (beaucoup plus rapprochées)
    skin1_rect = pygame.Rect(center_x - skin_spacing, skin_y, skin_size, skin_size)
    skin2_rect = pygame.Rect(center_x + skin_spacing - skin_size, skin_y, skin_size, skin_size)

    # Charger les images des skins pour preview
    skin1_preview = pygame.transform.scale(skins["skin1"], (skin_size, skin_size))
    skin2_preview = pygame.transform.scale(skins["skin2"], (skin_size, skin_size))

    # Boutons modes
    button_width = 260
    button_height = 55
    button_margin = 20

    inf_button_rect = pygame.Rect(
        center_x - button_width // 2,
        skin_y + skin_size + 60,
        button_width,
        button_height
    )

    story_button_rect = pygame.Rect(
        center_x - button_width // 2,
        inf_button_rect.bottom + button_margin,
        button_width,
        button_height
    )

    quit_button_rect = pygame.Rect(
        center_x - button_width // 2,
        story_button_rect.bottom + button_margin,
        button_width,
        button_height
    )

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()

                # Sélection des skins
                if skin1_rect.collidepoint(mouse_pos):
                    selected_skin = "skin1"
                if skin2_rect.collidepoint(mouse_pos):
                    selected_skin = "skin2"

                # Modes de jeu
                if inf_button_rect.collidepoint(mouse_pos):
                    return "infinite"
                if story_button_rect.collidepoint(mouse_pos):
                    return "story"
                if quit_button_rect.collidepoint(mouse_pos):
                    pygame.quit()
                    sys.exit()

        screen.fill(black)

        # Titre
        draw_text(screen, "NotUndertale", title_font, white, center_x, screen_height // 4)

        # --- AFFICHAGE DES SKINS ---
        screen.blit(skin1_preview, skin1_rect)
        screen.blit(skin2_preview, skin2_rect)

        # Bordure selon sélection
        pygame.draw.rect(
            screen,
            yellow if selected_skin == "skin1" else white,
            skin1_rect,
            4,
            border_radius=12
        )

        pygame.draw.rect(
            screen,
            yellow if selected_skin == "skin2" else white,
            skin2_rect,
            4,
            border_radius=12
        )

        # Texte SELECTED
        if selected_skin == "skin1":
            draw_text(screen, "SELECTED", small_font, yellow,
                      skin1_rect.centerx, skin1_rect.bottom + 20)

        if selected_skin == "skin2":
            draw_text(screen, "SELECTED", small_font, yellow,
                      skin2_rect.centerx, skin2_rect.bottom + 20)

        # --- BOUTONS MODES ---
        pygame.draw.rect(screen, gray, inf_button_rect, border_radius=12)
        pygame.draw.rect(screen, white, inf_button_rect, 2, border_radius=12)
        draw_text(screen, "Mode Infini", button_font, white,
                  inf_button_rect.centerx, inf_button_rect.centery)

        pygame.draw.rect(screen, gray, story_button_rect, border_radius=12)
        pygame.draw.rect(screen, white, story_button_rect, 2, border_radius=12)
        draw_text(screen, "Mode Histoire", button_font, white,
                  story_button_rect.centerx, story_button_rect.centery)

        pygame.draw.rect(screen, gray, quit_button_rect, border_radius=12)
        pygame.draw.rect(screen, white, quit_button_rect, 2, border_radius=12)
        draw_text(screen, "Quitter", button_font, white,
                  quit_button_rect.centerx, quit_button_rect.centery)

        pygame.display.flip()

def game_loop():
    global start_time, score, high_score

    all_sprites, projectiles, lasers, power_ups, player = create_sprites()
    heart_power_ups = pygame.sprite.Group()

    start_time = pygame.time.get_ticks()
    last_pause_time = 0
    pause_cooldown = 1000
    is_paused = False
    shield_start_time = 0
    shield_duration = 3000
    shield_active = False
    heart_power_up_start_time = start_time

    load_and_play_music()

    running = True
    clock = pygame.time.Clock()
    laser_warning_time = 30
    laser_warning_displayed = False
    warning_lights = pygame.sprite.Group()

    # MODIF 1 : on mémorise la position du prochain laser
    next_laser_x = None

    while running:
        current_time = pygame.time.get_ticks()
        elapsed_time = (current_time - start_time) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == ADD_PROJECTILE:
                projectile_type = random.choice([Meteor1, Meteor2, Meteor3])
                projectile = projectile_type()
                all_sprites.add(projectile)
                projectiles.add(projectile)

            # MODIF 1 : laser spawn EXACTEMENT à next_laser_x
            elif event.type == ADD_LASER:
                laser_width = screen_width // 8
                if next_laser_x is None:
                    col = random.randint(0, 7)
                    next_laser_x = col * laser_width

                laser = Laser(next_laser_x)
                all_sprites.add(laser)
                lasers.add(laser)

                next_laser_x = None

            elif event.type == ADD_POWER_UP:
                power_up = ShieldPowerUp()
                all_sprites.add(power_up)
                power_ups.add(power_up)

            elif event.type == ADD_HEART_POWER_UP:
                if elapsed_time >= 40:
                    heart_power_up = HeartPowerUp()
                    all_sprites.add(heart_power_up)
                    heart_power_ups.add(heart_power_up)

        keys = pygame.key.get_pressed()

        if keys[pygame.K_ESCAPE]:
            if not is_paused and (current_time - last_pause_time > pause_cooldown):
                is_paused = True
                show_pause_menu()
                is_paused = False
        elif keys[pygame.K_q]:
            if is_paused and (current_time - last_pause_time > pause_cooldown):
                pygame.quit()
                sys.exit()

        if not is_paused:
            player.update(keys)
            projectiles.update()
            lasers.update()
            power_ups.update()
            heart_power_ups.update()
            warning_lights.update()

            if pygame.sprite.spritecollideany(player, projectiles, pygame.sprite.collide_mask):
                if not shield_active:
                    player.decrease_health()
                    for projectile in pygame.sprite.spritecollide(player, projectiles, dokill=True, collided=pygame.sprite.collide_mask):
                        projectile.kill()

            if pygame.sprite.spritecollideany(player, lasers, pygame.sprite.collide_mask):
                if not shield_active:
                    player.decrease_health()
                    for laser in pygame.sprite.spritecollide(player, lasers, dokill=True, collided=pygame.sprite.collide_mask):
                        laser.kill()

            if pygame.sprite.spritecollideany(player, power_ups, pygame.sprite.collide_mask):
                for power_up in pygame.sprite.spritecollide(player, power_ups, dokill=True, collided=pygame.sprite.collide_mask):
                    shield_active = True
                    shield_start_time = pygame.time.get_ticks()

            if pygame.sprite.spritecollideany(player, heart_power_ups, pygame.sprite.collide_mask):
                for heart in pygame.sprite.spritecollide(player, heart_power_ups, dokill=True, collided=pygame.sprite.collide_mask):
                    player.health = min(player.health + 1, 3)

            if shield_active:
                if current_time - shield_start_time > shield_duration:
                    shield_active = False

            if not player.alive():
                pygame.mixer.music.stop()
                if score > high_score:
                    high_score = score
                result = show_game_over_screen()
                if result == "play_again":
                    all_sprites, projectiles, lasers, power_ups, player = create_sprites()
                    heart_power_ups.empty()
                    start_time = pygame.time.get_ticks()
                    continue
                elif result == "main_menu":
                    return
                elif result == "quit":
                    pygame.quit()
                    sys.exit()

            # MODIF 1 : un seul warning, sur la même colonne que le prochain laser
            if elapsed_time > laser_warning_time - 2 and not laser_warning_displayed:
                laser_width = screen_width // 8
                col = random.randint(0, 7)
                next_laser_x = col * laser_width

                warning_lights.empty()
                warning_lights.add(WarningLight(next_laser_x))

                laser_warning_displayed = True
                pygame.time.set_timer(ADD_LASER, 2000, loops=1)

            if elapsed_time > laser_warning_time and laser_warning_displayed:
                laser_warning_time += 7
                laser_warning_displayed = False
                warning_lights.empty()

            if elapsed_time >= 40:
                if (current_time - heart_power_up_start_time) / 1000 > 20:
                    heart_power_up_start_time = current_time
                    pygame.time.set_timer(ADD_HEART_POWER_UP, random.randint(20000, 25000))

            score = int(elapsed_time * 1000)

            screen.blit(background_surface, (0, 0))
            all_sprites.draw(screen)
            warning_lights.draw(screen)

            for i in range(player.health):
                screen.blit(heart_image, (10 + i * (heart_rect.width + 5), 10))

            if shield_active:
                screen.blit(shield_icon, (10, 70))

            score_text = score_font.render(f"Score: {score}", True, white)
            screen.blit(score_text, (screen_width - score_text.get_width() - 20, 10))

            pygame.display.flip()
            clock.tick(60)

def main():
    while True:
        mode = show_main_menu()
        if mode == "infinite":
            game_loop()
        elif mode == "story":
            show_coming_soon_screen()


if __name__ == "__main__":
    main()

# Version : corrections
# - Warning laser : 1 seule colonne + vertical + laser au même endroit
# - Suppression du show_main_menu sans skins (il n'en reste qu'un)
