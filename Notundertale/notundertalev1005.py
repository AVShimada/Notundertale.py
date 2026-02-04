import pygame
import sys
import random
import json
import math
from datetime import datetime

# =========================
# INIT
# =========================
pygame.init()

info_screen = pygame.display.Info()
screen_width = info_screen.current_w
screen_height = info_screen.current_h

screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
pygame.display.set_caption('NotUndertale')

# Couleurs
black = (0, 0, 0)
white = (255, 255, 255)
red = (255, 0, 0)
yellow = (255, 255, 0)
gray = (169, 169, 169)

# =========================
# ASSETS
# =========================
heart_image = pygame.image.load('heart.png')
heart_image = pygame.transform.scale(heart_image, (50, 50))
heart_rect = heart_image.get_rect()

shield_icon = pygame.image.load('shield.png')
shield_icon = pygame.transform.scale(shield_icon, (75, 75))
shield_icon_rect = shield_icon.get_rect()

background_image = pygame.image.load('space_background.png')
background_image = pygame.transform.scale(background_image, (screen_width, screen_height))
background_surface = pygame.Surface((screen_width, screen_height))
background_surface.blit(background_image, (0, 0))

# Skins
skins = {
    "default": pygame.image.load('player.png'),
    "skin1": pygame.image.load('player_skin1.png'),
    "skin2": pygame.image.load('player_skin2.png')
}
selected_skin = "default"

# =========================
# SCOREBOARD (JSON)
# =========================
SCORE_FILE = "scores.json"
MAX_SCORES = 10
DISPLAY_TOP = 5

def _load_score_data():
    try:
        with open(SCORE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return {"scores": []}
            if "scores" not in data or not isinstance(data["scores"], list):
                data["scores"] = []
            return data
    except FileNotFoundError:
        return {"scores": []}
    except json.JSONDecodeError:
        return {"scores": []}

def _save_score_data(data):
    with open(SCORE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def save_score(score_value: int, skin_name: str):
    data = _load_score_data()
    entry = {
        "score": int(score_value),
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "skin": str(skin_name)
    }
    data["scores"].append(entry)

    # Tri: score DESC, date ASC (plus ancien d'abord si égalité)
    data["scores"].sort(key=lambda e: (-int(e.get("score", 0)), e.get("date", "")))

    # Top 10
    data["scores"] = data["scores"][:MAX_SCORES]
    _save_score_data(data)


def load_scores():
    data = _load_score_data()
    # Tri: score DESC, date ASC (plus ancien d'abord si égalité)
    data["scores"].sort(key=lambda e: (-int(e.get("score", 0)), e.get("date", "")))
    return data["scores"][:MAX_SCORES]


# =========================
# DIFFICULTÉ PROGRESSIVE (cap vitesse/spawn)
# =========================
DIFF_STEP = 20000
DIFF_CAP = 100000
BASE_PROJECTILE_INTERVAL = 300
SPEED_INC_PER_STEP = 0.10
SPAWN_INC_PER_STEP = 0.10
MIN_PROJECTILE_INTERVAL = 120

current_speed_multiplier = 1.0

def get_difficulty_level(score_value: int) -> int:
    capped = min(score_value, DIFF_CAP)
    return capped // DIFF_STEP

def compute_difficulty(score_value: int):
    level = get_difficulty_level(score_value)
    speed_mult = 1.0 + level * SPEED_INC_PER_STEP
    interval = int(BASE_PROJECTILE_INTERVAL * ((1.0 - SPAWN_INC_PER_STEP) ** level))
    interval = max(MIN_PROJECTILE_INTERVAL, interval)
    return level, speed_mult, interval

# =========================
# EVENTS / TIMERS
# =========================
ADD_PROJECTILE = pygame.USEREVENT + 1
ADD_LASER = pygame.USEREVENT + 2
ADD_POWER_UP = pygame.USEREVENT + 3
ADD_HEART_POWER_UP = pygame.USEREVENT + 4

pygame.time.set_timer(ADD_PROJECTILE, BASE_PROJECTILE_INTERVAL)
pygame.time.set_timer(ADD_POWER_UP, 15000)
pygame.time.set_timer(ADD_HEART_POWER_UP, 20000)

# =========================
# MUSIC
# =========================
music_volume = 0.5
pygame.mixer.music.set_volume(music_volume)

def load_and_play_music():
    try:
        pygame.mixer.music.load('background_music.mp3')
        pygame.mixer.music.play(-1)
    except pygame.error as e:
        print(f"Erreur de chargement de la musique : {e}")

# =========================
# SHIELD AURA (HALO BLEU)
# =========================
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

# =========================
# UI HELPERS
# =========================
def draw_text(surface, text, font, color, x, y):
    textobj = font.render(text, True, color)
    textrect = textobj.get_rect()
    textrect.center = (x, y)
    surface.blit(textobj, textrect)

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

# =========================
# SPRITES
# =========================
class WarningLight(pygame.sprite.Sprite):
    def __init__(self, x_position):
        super().__init__()
        self.width = screen_width // 8
        self.height = screen_height
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.image.fill((255, 255, 255, 120))
        self.rect = self.image.get_rect()
        self.rect.x = x_position
        self.rect.y = 0

        self.fading = False
        self.fade_duration = 0.5
        self.start_time = pygame.time.get_ticks()

    def update(self):
        current_time = pygame.time.get_ticks()
        elapsed_time = (current_time - self.start_time) / 1000
        if elapsed_time >= 2 and not self.fading:
            self.fading = True
            self.fade_start_time = current_time

        if self.fading:
            fade_elapsed_time = (current_time - self.fade_start_time) / 1000
            alpha = max(0, 255 * (1 - fade_elapsed_time / self.fade_duration))
            self.image.set_alpha(alpha)
            if alpha <= 0:
                self.kill()

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

class Projectile(pygame.sprite.Sprite):
    def __init__(self, image_path, speed, size=(40, 40)):
        super().__init__()
        self.image = pygame.image.load(image_path).convert_alpha()
        self.image = pygame.transform.scale(self.image, size)
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, max(0, screen_width - self.rect.width))
        self.rect.y = 0

        global current_speed_multiplier
        self.speed = float(speed) * float(current_speed_multiplier)
        self.y = float(self.rect.y)

        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        self.y += self.speed
        self.rect.y = int(self.y)
        if self.rect.top > screen_height:
            self.kill()

class Meteor1(Projectile):
    def __init__(self):
        super().__init__('meteor1.png', speed=11, size=(40, 40))

class Meteor2(Projectile):
    def __init__(self):
        super().__init__('meteor2.png', speed=12, size=(40, 40))

class Meteor3(Projectile):
    def __init__(self):
        super().__init__('meteor3.png', speed=10, size=(40, 40))

# ✅ Nouvelle variante: lente mais grosse (à partir de 100k)
class BigSlowMeteor(Projectile):
    def __init__(self):
        # plus grosse, plus lente
        super().__init__('meteor3.png', speed=6, size=(90, 90))

# ✅ Nouvelle variante: zigzag (à partir de 150k)
class ZigZagMeteor(Projectile):
    def __init__(self):
        super().__init__('meteor2.png', speed=11, size=(45, 45))
        self.base_x = self.rect.x
        self.spawn_time = pygame.time.get_ticks()
        self.amplitude = 140  # amplitude du zigzag
        self.freq = 0.010     # vitesse du zigzag (rad/ms)

    def update(self):
        # mouvement vertical normal
        self.y += self.speed
        self.rect.y = int(self.y)

        # zigzag horizontal
        t = pygame.time.get_ticks() - self.spawn_time
        offset = int(math.sin(t * self.freq) * self.amplitude)
        self.rect.x = self.base_x + offset

        # clamp écran
        if self.rect.x < 0:
            self.rect.x = 0
        if self.rect.right > screen_width:
            self.rect.right = screen_width

        if self.rect.top > screen_height:
            self.kill()

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

POWERUP_LIFETIME_MS = 5000
POWERUP_BLINK_MS = 1000
POWERUP_BLINK_PERIOD_MS = 150

class TimedPowerUp(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.spawn_time = pygame.time.get_ticks()
        self.visible = True

    def _handle_lifetime(self):
        now = pygame.time.get_ticks()
        age = now - self.spawn_time

        # Supprime après 5s
        if age >= POWERUP_LIFETIME_MS:
            self.kill()
            return

        # Clignote la dernière seconde
        if age >= (POWERUP_LIFETIME_MS - POWERUP_BLINK_MS):
            # toggle visible toutes les POWERUP_BLINK_PERIOD_MS
            if (now // POWERUP_BLINK_PERIOD_MS) % 2 == 0:
                self.image.set_alpha(50)
            else:
                self.image.set_alpha(255)
        else:
            self.image.set_alpha(255)

class ShieldPowerUp(TimedPowerUp):
    def __init__(self):
        super().__init__()
        self.image = pygame.image.load('shield.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (75, 75))
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, screen_width - self.rect.width)
        self.rect.y = random.randint(0, screen_height - self.rect.height)
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        self._handle_lifetime()


class HeartPowerUp(TimedPowerUp):
    def __init__(self):
        super().__init__()
        self.image = pygame.image.load('heart.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (50, 50))
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, screen_width - self.rect.width)
        self.rect.y = random.randint(0, screen_height - self.rect.height)
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        self._handle_lifetime()


def create_sprites():
    all_sprites = pygame.sprite.Group()
    projectiles = pygame.sprite.Group()
    lasers = pygame.sprite.Group()
    power_ups = pygame.sprite.Group()
    player = Player()
    all_sprites.add(player)
    return all_sprites, projectiles, lasers, power_ups, player

# =========================
# MENUS
# =========================
def show_coming_soon_screen():
    font = pygame.font.Font(None, 72)
    text = font.render("Coming Soon!", True, white)
    text_rect = text.get_rect(center=(screen_width // 2, screen_height // 2))

    screen.fill(black)
    screen.blit(text, text_rect)
    pygame.display.flip()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                return

def show_main_menu():
    global selected_skin

    title_font = pygame.font.Font(None, 96)
    button_font = pygame.font.Font(None, 36)
    small_font = pygame.font.Font(None, 28)

    skin_size = 140
    skin_y = screen_height // 2 - 120
    skin_spacing = 180
    center_x = screen_width // 2

    skin1_rect = pygame.Rect(center_x - skin_spacing, skin_y, skin_size, skin_size)
    skin2_rect = pygame.Rect(center_x + skin_spacing - skin_size, skin_y, skin_size, skin_size)

    skin1_preview = pygame.transform.scale(skins["skin1"], (skin_size, skin_size))
    skin2_preview = pygame.transform.scale(skins["skin2"], (skin_size, skin_size))

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

            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()

                if skin1_rect.collidepoint(mouse_pos):
                    selected_skin = "skin1"
                if skin2_rect.collidepoint(mouse_pos):
                    selected_skin = "skin2"

                if inf_button_rect.collidepoint(mouse_pos):
                    return "infinite"
                if story_button_rect.collidepoint(mouse_pos):
                    return "story"
                if quit_button_rect.collidepoint(mouse_pos):
                    pygame.quit()
                    sys.exit()

        screen.fill(black)
        draw_text(screen, "NotUndertale", title_font, white, center_x, screen_height // 4)

        screen.blit(skin1_preview, skin1_rect)
        screen.blit(skin2_preview, skin2_rect)

        pygame.draw.rect(screen, yellow if selected_skin == "skin1" else white, skin1_rect, 4, border_radius=12)
        pygame.draw.rect(screen, yellow if selected_skin == "skin2" else white, skin2_rect, 4, border_radius=12)

        if selected_skin == "skin1":
            draw_text(screen, "SELECTED", small_font, yellow, skin1_rect.centerx, skin1_rect.bottom + 20)
        if selected_skin == "skin2":
            draw_text(screen, "SELECTED", small_font, yellow, skin2_rect.centerx, skin2_rect.bottom + 20)

        pygame.draw.rect(screen, gray, inf_button_rect, border_radius=12)
        pygame.draw.rect(screen, white, inf_button_rect, 2, border_radius=12)
        draw_text(screen, "Mode Infini", button_font, white, inf_button_rect.centerx, inf_button_rect.centery)

        pygame.draw.rect(screen, gray, story_button_rect, border_radius=12)
        pygame.draw.rect(screen, white, story_button_rect, 2, border_radius=12)
        draw_text(screen, "Mode Histoire", button_font, white, story_button_rect.centerx, story_button_rect.centery)

        pygame.draw.rect(screen, gray, quit_button_rect, border_radius=12)
        pygame.draw.rect(screen, white, quit_button_rect, 2, border_radius=12)
        draw_text(screen, "Quitter", button_font, white, quit_button_rect.centerx, quit_button_rect.centery)

        pygame.display.flip()

def show_game_over_screen(scores, final_score):
    overlay = pygame.Surface((screen_width, screen_height))
    overlay.set_alpha(180)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    menu_box_width = 520
    menu_box_height = 750
    menu_box_x = (screen_width // 2) - (menu_box_width // 2)
    menu_box_y = (screen_height // 2) - (menu_box_height // 2)

    pygame.draw.rect(screen, (50, 50, 50), (menu_box_x, menu_box_y, menu_box_width, menu_box_height), 0, 15)
    pygame.draw.rect(screen, white, (menu_box_x, menu_box_y, menu_box_width, menu_box_height), 3, 15)

    title_font = pygame.font.Font(None, 96)
    text_font = pygame.font.Font(None, 48)

    center_x = screen_width // 2
    content_y = menu_box_y + 30

    game_over_text = title_font.render("Game Over", True, red)
    screen.blit(game_over_text, (center_x - game_over_text.get_width() // 2, content_y))
    content_y += 120

    score_text = text_font.render(f"Final Score: {final_score}", True, white)
    screen.blit(score_text, (center_x - score_text.get_width() // 2, content_y))
    content_y += 80

    scoreboard_title = text_font.render("Top 5 Scores", True, (255, 215, 0))
    screen.blit(scoreboard_title, (center_x - scoreboard_title.get_width() // 2, content_y))
    content_y += 55

    for i, entry in enumerate(scores[:DISPLAY_TOP]):
        s = entry.get("score", 0)
        line = text_font.render(f"{i + 1}. {s}", True, white)
        screen.blit(line, (center_x - line.get_width() // 2, content_y))
        content_y += 40

    content_y += 30
    play_again_button_rect = pygame.Rect(center_x - 150, content_y, 300, 50)
    content_y += 65
    main_menu_button_rect = pygame.Rect(center_x - 150, content_y, 300, 50)
    content_y += 65
    quit_button_rect = pygame.Rect(center_x - 150, content_y, 300, 50)

    pygame.draw.rect(screen, (100, 100, 100), play_again_button_rect, border_radius=10)
    pygame.draw.rect(screen, white, play_again_button_rect, 2, border_radius=10)
    pygame.draw.rect(screen, (100, 100, 100), main_menu_button_rect, border_radius=10)
    pygame.draw.rect(screen, white, main_menu_button_rect, 2, border_radius=10)
    pygame.draw.rect(screen, (100, 100, 100), quit_button_rect, border_radius=10)
    pygame.draw.rect(screen, white, quit_button_rect, 2, border_radius=10)

    play_again_text = text_font.render("Play Again", True, white)
    main_menu_text = text_font.render("Main Menu", True, white)
    quit_text = text_font.render("Quit", True, white)

    screen.blit(play_again_text, (play_again_button_rect.centerx - play_again_text.get_width() // 2,
                                 play_again_button_rect.centery - play_again_text.get_height() // 2))
    screen.blit(main_menu_text, (main_menu_button_rect.centerx - main_menu_text.get_width() // 2,
                                 main_menu_button_rect.centery - main_menu_text.get_height() // 2))
    screen.blit(quit_text, (quit_button_rect.centerx - quit_text.get_width() // 2,
                            quit_button_rect.centery - quit_text.get_height() // 2))

    pygame.display.flip()

    while True:
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

def show_pause_menu(paused_background):
    title_font = pygame.font.Font(None, 96)
    text_font = pygame.font.Font(None, 48)

    overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))

    menu_box_width = 500
    menu_box_height = 600
    menu_box_x = (screen_width // 2) - (menu_box_width // 2)
    menu_box_y = (screen_height // 2) - (menu_box_height // 2)

    resume_button_rect = pygame.Rect(menu_box_x + 50, menu_box_y + 120, 400, 60)
    restart_button_rect = pygame.Rect(menu_box_x + 50, menu_box_y + 200, 400, 60)
    main_menu_button_rect = pygame.Rect(menu_box_x + 50, menu_box_y + 280, 400, 60)
    quit_button_rect = pygame.Rect(menu_box_x + 50, menu_box_y + 360, 400, 60)

    volume_instruction_y = menu_box_y + 450
    adjusting_volume = False
    volume_slider_rect = pygame.Rect(0, 0, 1, 1)

    while True:
        screen.blit(paused_background, (0, 0))
        screen.blit(overlay, (0, 0))

        pygame.draw.rect(screen, (50, 50, 50), (menu_box_x, menu_box_y, menu_box_width, menu_box_height), 0, 15)
        pygame.draw.rect(screen, white, (menu_box_x, menu_box_y, menu_box_width, menu_box_height), 3, 15)

        pause_text = title_font.render("Game Paused", True, red)
        screen.blit(pause_text, (screen_width // 2 - pause_text.get_width() // 2, menu_box_y + 30))

        pygame.draw.rect(screen, (100, 100, 100), resume_button_rect, border_radius=15)
        pygame.draw.rect(screen, white, resume_button_rect, 2, border_radius=15)
        pygame.draw.rect(screen, (100, 100, 100), restart_button_rect, border_radius=15)
        pygame.draw.rect(screen, white, restart_button_rect, 2, border_radius=15)
        pygame.draw.rect(screen, (100, 100, 100), main_menu_button_rect, border_radius=15)
        pygame.draw.rect(screen, white, main_menu_button_rect, 2, border_radius=15)
        pygame.draw.rect(screen, (100, 100, 100), quit_button_rect, border_radius=15)
        pygame.draw.rect(screen, white, quit_button_rect, 2, border_radius=15)

        resume_text = text_font.render("Resume", True, white)
        restart_text = text_font.render("Restart", True, white)
        main_menu_text = text_font.render("Main Menu", True, white)
        quit_text = text_font.render("Quit", True, white)

        screen.blit(resume_text, (resume_button_rect.centerx - resume_text.get_width() // 2,
                                 resume_button_rect.centery - resume_text.get_height() // 2))
        screen.blit(restart_text, (restart_button_rect.centerx - restart_text.get_width() // 2,
                                  restart_button_rect.centery - restart_text.get_height() // 2))
        screen.blit(main_menu_text, (main_menu_button_rect.centerx - main_menu_text.get_width() // 2,
                                     main_menu_button_rect.centery - main_menu_text.get_height() // 2))
        screen.blit(quit_text, (quit_button_rect.centerx - quit_text.get_width() // 2,
                                quit_button_rect.centery - quit_text.get_height() // 2))

        volume_instruction_text = text_font.render("Adjust Volume:", True, white)
        screen.blit(volume_instruction_text, (screen_width // 2 - volume_instruction_text.get_width() // 2, volume_instruction_y))

        current_volume = pygame.mixer.music.get_volume()
        volume_slider_rect = draw_volume_slider(current_volume)
        volume_slider_rect.y = volume_instruction_y + 30

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "resume"

            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()

                if resume_button_rect.collidepoint(mouse_pos):
                    return "resume"
                if restart_button_rect.collidepoint(mouse_pos):
                    return "restart"
                if main_menu_button_rect.collidepoint(mouse_pos):
                    return "menu"
                if quit_button_rect.collidepoint(mouse_pos):
                    return "quit"

                if volume_slider_rect.collidepoint(event.pos):
                    adjusting_volume = True

            if event.type == pygame.MOUSEBUTTONUP:
                adjusting_volume = False

            if event.type == pygame.MOUSEMOTION and adjusting_volume:
                mouse_x, _ = event.pos
                slider_x = volume_slider_rect.x
                slider_width = volume_slider_rect.width

                new_volume = (mouse_x - slider_x) / slider_width
                new_volume = max(0, min(new_volume, 1))
                pygame.mixer.music.set_volume(new_volume)

# =========================
# SPAWN LOGIC - variantes progressives
# =========================
def lerp(a, b, t):
    return a + (b - a) * max(0.0, min(1.0, t))

def choose_projectile_class(score_value: int):
    """
    - Base meteors au début
    - BigSlowMeteor apparait progressivement à partir de 100k (0% -> 30% jusqu'à 150k)
    - ZigZagMeteor apparait progressivement à partir de 150k (0% -> 25% jusqu'à 200k)
    """
    base_classes = [Meteor1, Meteor2, Meteor3]

    # prob BigSlow (100k -> 150k)
    if score_value < 100000:
        p_big = 0.0
    else:
        t = (score_value - 100000) / 50000.0  # 0..1 entre 100k et 150k
        p_big = lerp(0.0, 0.30, t)

    # prob ZigZag (150k -> 200k)
    if score_value < 150000:
        p_zig = 0.0
    else:
        t = (score_value - 150000) / 50000.0  # 0..1 entre 150k et 200k
        p_zig = lerp(0.0, 0.25, t)

    r = random.random()

    # On tire d'abord zigzag, puis big, sinon base.
    if r < p_zig:
        return ZigZagMeteor
    elif r < p_zig + p_big:
        return BigSlowMeteor
    else:
        return random.choice(base_classes)

# =========================
# GAME
# =========================
score = 0
high_score = 0
score_font = pygame.font.Font(None, 48)

def game_loop():
    global score, high_score, current_speed_multiplier

    all_sprites, projectiles, lasers, power_ups, player = create_sprites()
    heart_power_ups = pygame.sprite.Group()

    start_time = pygame.time.get_ticks()

    # Pause
    last_pause_time = 0
    pause_cooldown = 250
    is_paused = False

    # Shield
    shield_start_time = 0
    shield_duration = 3000
    shield_active = False
    remaining_ms = 0

    # Lasers
    laser_warning_time = 30
    laser_warning_displayed = False
    warning_lights = pygame.sprite.Group()
    next_laser_x = None

    # Difficulty
    current_level = -1

    load_and_play_music()

    running = True
    clock = pygame.time.Clock()

    while running:
        current_time = pygame.time.get_ticks()
        elapsed_time = (current_time - start_time) / 1000

        # MAJ shield remaining
        if shield_active:
            remaining_ms = shield_duration - (current_time - shield_start_time)
            if remaining_ms <= 0:
                shield_active = False
                remaining_ms = 0
        else:
            remaining_ms = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == ADD_PROJECTILE:
                # spawn variants selon score
                projectile_class = choose_projectile_class(score)
                projectile = projectile_class()
                all_sprites.add(projectile)
                projectiles.add(projectile)

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

        # Pause
        if keys[pygame.K_ESCAPE] and (current_time - last_pause_time > pause_cooldown) and not is_paused:
            is_paused = True
            last_pause_time = current_time

            paused_background = screen.copy()
            action = show_pause_menu(paused_background)

            is_paused = False
            if action == "restart":
                pygame.mixer.music.stop()
                return "restart"
            elif action == "menu":
                pygame.mixer.music.stop()
                return "menu"
            elif action == "quit":
                pygame.quit()
                sys.exit()

        if not is_paused:
            player.update(keys)
            projectiles.update()
            lasers.update()
            power_ups.update()
            heart_power_ups.update()
            warning_lights.update()

            # Collisions
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
                for _power_up in pygame.sprite.spritecollide(player, power_ups, dokill=True, collided=pygame.sprite.collide_mask):
                    shield_active = True
                    shield_start_time = pygame.time.get_ticks()

            if pygame.sprite.spritecollideany(player, heart_power_ups, pygame.sprite.collide_mask):
                for _heart in pygame.sprite.spritecollide(player, heart_power_ups, dokill=True, collided=pygame.sprite.collide_mask):
                    player.health = min(player.health + 1, 3)

            # Game Over
            if not player.alive():
                pygame.mixer.music.stop()

                save_score(score, selected_skin)
                scores_list = load_scores()
                result = show_game_over_screen(scores_list, score)

                if result == "play_again":
                    return "restart"
                elif result == "main_menu":
                    return "menu"
                else:
                    pygame.quit()
                    sys.exit()

            # Warning laser
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

            # Score
            score = int(elapsed_time * 1000)

            # Difficulty update (cap à 100k)
            level, speed_mult, interval = compute_difficulty(score)
            if level != current_level:
                current_level = level
                current_speed_multiplier = speed_mult
                pygame.time.set_timer(ADD_PROJECTILE, interval)

            # Render
            screen.blit(background_surface, (0, 0))
            all_sprites.draw(screen)
            warning_lights.draw(screen)

            if shield_active:
                draw_shield_aura(screen, player.rect, remaining_ms)

            for i in range(player.health):
                screen.blit(heart_image, (10 + i * (heart_rect.width + 5), 10))

            if shield_active:
                screen.blit(shield_icon, (10, 70))

            score_text = score_font.render(f"Score: {score}", True, white)
            screen.blit(score_text, (screen_width - score_text.get_width() - 20, 10))

            pygame.display.flip()
            clock.tick(60)

# =========================
# MAIN
# =========================
def main():
    while True:
        mode = show_main_menu()
        if mode == "infinite":
            result = game_loop()
            if result in ("restart", "menu"):
                continue
        elif mode == "story":
            show_coming_soon_screen()

if __name__ == "__main__":
    main()
