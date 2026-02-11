from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import pygame
from .settings import ASSETS_DIR

@dataclass
class ImagePack:
    background: pygame.Surface
    heart: pygame.Surface
    shield: pygame.Surface
    player_skins: dict[str, pygame.Surface]
    meteors: list[pygame.Surface]

def _img(path: Path, alpha: bool = True) -> pygame.Surface:
    surf = pygame.image.load(str(path))
    return surf.convert_alpha() if alpha else surf.convert()

def load_images(screen_size: tuple[int, int]) -> ImagePack:
    screen_w, screen_h = screen_size
    img_dir = ASSETS_DIR / "images"

    # ✅ Background EXACTEMENT à la taille de l'écran (comme ton code)
    background_image = _img(img_dir / "space_background.png", alpha=False)
    background_image = pygame.transform.scale(background_image, (screen_w, screen_h))
    background_surface = pygame.Surface((screen_w, screen_h))
    background_surface.blit(background_image, (0, 0))

    # ✅ UI icons scalés fixes (comme ton code)
    heart_image = pygame.transform.scale(_img(img_dir / "heart.png"), (50, 50))
    shield_icon = pygame.transform.scale(_img(img_dir / "shield.png"), (75, 75))

    # ✅ Player skins (on garde la taille "source" ici, et on scale dans Player)
    player_skins = {
        "default": _img(img_dir / "player.png"),
        "skin1": _img(img_dir / "player_skin1.png"),
        "skin2": _img(img_dir / "player_skin2.png"),
    }

    # ✅ Meteors: on charge brut, on scale dans les classes météores
    meteors = [
        _img(img_dir / "meteor1.png"),
        _img(img_dir / "meteor2.png"),
        _img(img_dir / "meteor3.png"),
    ]

    return ImagePack(
        background=background_surface,
        heart=heart_image,
        shield=shield_icon,
        player_skins=player_skins,
        meteors=meteors,
    )
def play_music(volume: float = 0.5) -> None:
    try:
        music_path = ASSETS_DIR / "audio" / "background_music.mp3"
        pygame.mixer.music.load(str(music_path))
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(-1)
    except Exception:
        # Ne bloque pas le jeu si la musique échoue
        pass
