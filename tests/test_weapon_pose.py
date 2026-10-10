"""Prise en main, départ du tir et protection des sprites partagés avec l'Infini."""

import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

from types import SimpleNamespace
import unittest

import pygame

from Notundertale.assets import Assets
from Notundertale.story.enemies import Alien
from Notundertale.story.player import StoryPlayer
from Notundertale.story.weapons import Armory
from Notundertale.story.weapon_art import ArmedSprites, recoil_amount
from Notundertale.story.weapon_pose import muzzle_position


class WeaponPoseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.display.init()
        pygame.display.set_mode((1280, 720))
        cls.assets = Assets((1280, 720))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def player(self, name="remanent"):
        player = StoryPlayer()
        player.place(500, 600)
        player.skin_name = name
        player.animation = self.assets.character_animation(name)
        return player

    def test_projectile_starts_at_displayed_muzzle_for_all_poses_and_directions(self):
        room = SimpleNamespace(width=2400, solids=[], enemies=[])
        for name in self.assets.skins:
            player = self.player(name)
            for state in ("idle", "walk", "air", "dash"):
                player.animation.state = state
                for facing in (-1, 1):
                    player.facing = facing
                    for weapon in ("rifle", "raygun"):
                        with self.subTest(name=name, state=state, facing=facing, weapon=weapon):
                            armory = Armory()
                            armory.equip(weapon)
                            self.assertTrue(armory.update(0, True, player, room))
                            ray = armory.rays[0]
                            x, y = muzzle_position(player, recoil_amount(armory))
                            self.assertEqual((ray.x, ray.y), (x, y))

    def test_point_blank_target_and_wall_inside_barrel_are_not_skipped(self):
        for facing in (-1, 1):
            for obstacle in ("alien", "wall"):
                player = self.player()
                player.facing = facing
                armory = Armory()
                armory.equip("raygun")
                # La bouche du canon est plus loin que cette cible très proche.
                x = player.rect.right + 2 if facing > 0 else player.rect.left - 56
                target = Alien(x, 556)
                solids = [pygame.Rect(x + (0 if facing > 0 else 52), 530, 2, 70)] if obstacle == "wall" else []
                room = SimpleNamespace(width=2400, solids=solids, enemies=[target])
                self.assertTrue(armory.update(1/120, True, player, room))
                self.assertFalse(armory.rays)
                self.assertEqual(len(armory.impacts), 1)
                self.assertEqual(target.health, target.max_health if obstacle == "wall" else 0)

    def test_armed_render_preserves_sources_and_repeated_draw_freezes_recoil(self):
        for name in self.assets.skins:
            player = self.player(name)
            artist = ArmedSprites(name)
            originals = [self.assets.skins[name], *self.assets.animation_frames.get(name, ())]
            before = [pygame.image.tobytes(image, "RGBA") for image in originals]
            room = SimpleNamespace(width=2400, solids=[], enemies=[])
            armory = Armory()
            armory.equip("raygun")
            armory.update(0, True, player, room)
            for state, poses in player.animation.poses.items():
                player.animation.state = state
                for index in range(len(poses)):
                    player.animation.phase = index
                    player.facing = 1
                    right = artist.image(player, "raygun", recoil_amount(armory))
                    player.facing = -1
                    left = artist.image(player, "raygun", recoil_amount(armory))
                    self.assertEqual(pygame.image.tobytes(left, "RGBA"),
                                     pygame.image.tobytes(pygame.transform.flip(right, True, False), "RGBA"))
                    trail = left.copy()
                    trail.set_alpha(30)
                    self.assertEqual(artist.image(player, "raygun", recoil_amount(armory)).get_alpha(), 255)
            self.assertEqual(armory.shot_flash, armory.FLASH_DURATION)
            self.assertEqual(before, [pygame.image.tobytes(image, "RGBA") for image in originals])
            armory.update(.1, False, player, room)
            self.assertEqual(recoil_amount(armory), 0)


if __name__ == "__main__":
    unittest.main()
