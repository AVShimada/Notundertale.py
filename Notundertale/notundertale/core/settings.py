from dataclasses import dataclass
from pathlib import Path

# .../Notundertale/notundertale/core/settings.py -> parents[2] = .../Notundertale
BASE_DIR = Path(__file__).resolve().parents[2]
ASSETS_DIR = BASE_DIR / "assets"

@dataclass(frozen=True)
class GameConfig:
    width: int = 1920
    height: int = 1080
    fps: int = 60

    score_file: Path = BASE_DIR / "scores.json"
    max_scores: int = 10
    display_top: int = 5
