"""Lecture et sauvegarde du classement, compatible avec scores.json existant."""

import json
import logging
from datetime import datetime
from pathlib import Path

from .config import MAX_SCORES, SCORE_FILE

logger = logging.getLogger(__name__)


def load_scores(path=SCORE_FILE):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    if not isinstance(data, dict) or not isinstance(data.get("scores"), list):
        return []
    scores = []
    for entry in data["scores"]:
        if not isinstance(entry, dict):
            continue
        try:
            score = max(0, int(entry["score"]))
        except (KeyError, TypeError, ValueError, OverflowError):
            continue
        scores.append({"score": score, "date": str(entry.get("date", "")),
                       "skin": str(entry.get("skin", "default"))})
    return sorted(scores, key=lambda entry: (-entry["score"], entry["date"]))[:MAX_SCORES]


def save_score(score_value, skin_name, path=SCORE_FILE):
    scores = load_scores(path)
    scores.append({"score": int(score_value),
                   "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                   "skin": str(skin_name)})
    scores.sort(key=lambda entry: (-entry["score"], entry["date"]))
    path = Path(path)
    temporary = path.with_suffix(".json.tmp")
    try:
        temporary.write_text(json.dumps({"scores": scores[:MAX_SCORES]},
                                        ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(path)
        return True
    except OSError as error:
        logger.warning("Impossible de sauvegarder le score : %s", error)
        return False
