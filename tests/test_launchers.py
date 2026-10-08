"""Régression : les lanceurs acceptent aussi un chemin de fichier absolu."""

import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


class LauncherTests(unittest.TestCase):
    def test_direct_launchers_and_module_accept_help(self):
        for entry in (ROOT / "main.py", ROOT / "Notundertale" / "__main__.py",
                      ROOT / "Notundertale" / "notundertalev1006.py"):
            with self.subTest(entry=entry.name):
                result = subprocess.run([sys.executable, str(entry), "--help"],
                                        cwd=ROOT.parent, capture_output=True, text=True, timeout=15)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("--windowed", result.stdout)
        result = subprocess.run([sys.executable, "-m", "Notundertale", "--help"],
                                cwd=ROOT, capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_direct_package_launcher_opens_and_closes_without_parent_package(self):
        environment = dict(os.environ, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
        script = (
            "import sys, runpy, pygame; entry=sys.argv[1]; "
            "sys.argv=[entry, '--windowed']; "
            "pygame.event.get=lambda: [pygame.event.Event(pygame.QUIT)]; "
            "runpy.run_path(entry, run_name='__main__')"
        )
        result = subprocess.run([sys.executable, "-c", script, str(ROOT / "Notundertale" / "__main__.py")],
                                cwd=ROOT.parent, env=environment, capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
