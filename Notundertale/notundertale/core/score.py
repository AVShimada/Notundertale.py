from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class ScoreEntry:
    name: str
    score: int

def load_scores(path: Path) -> list[ScoreEntry]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        out: list[ScoreEntry] = []
        for row in data:
            out.append(ScoreEntry(name=str(row.get("name", "???")), score=int(row.get("score", 0))))
        return out
    except Exception:
        return []

def save_score(path: Path, name: str, score: int, max_scores: int = 10) -> None:
    scores = load_scores(path)
    scores.append(ScoreEntry(name=name, score=score))
    scores = sorted(scores, key=lambda s: s.score, reverse=True)[:max_scores]
    payload = [{"name": s.name, "score": s.score} for s in scores]
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
