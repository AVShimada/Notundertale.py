"""Ancien point d'entrée conservé pour les habitudes de lancement existantes."""

if __package__ in (None, ""):
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from Notundertale.app import main

if __name__ == "__main__":
    main()
