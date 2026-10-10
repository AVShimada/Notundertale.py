"""Les tirages du vaisseau restent reliés, traversables et renouvelés à chaque vie."""

import os
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import random
import unittest

import pygame

from Notundertale.story.rooms import FLOOR_Y, WEAPON_IDS, make_rooms


def signature(rooms):
    return tuple((name, room.width, room.platforms, room.doors, room.decor_seed,
                  room.theme, room.tier, room.is_exit,
                  tuple((enemy.rect.x, enemy.rect.y, enemy.health) for enemy in room.enemies),
                  tuple((pickup.x, pickup.weapon_id) for pickup in room.loot))
                 for name, room in rooms.items())


class GenerationTests(unittest.TestCase):
    def test_same_seed_reproduces_world_and_does_not_use_global_random(self):
        before = random.getstate()
        self.assertEqual(signature(make_rooms(431)), signature(make_rooms(431)))
        self.assertEqual(random.getstate(), before)
        self.assertNotEqual(signature(make_rooms(431)), signature(make_rooms(432)))

    def test_many_seeds_have_bidirectional_cockpit_to_exit_route(self):
        for seed in range(64):
            with self.subTest(seed=seed):
                rooms = make_rooms(seed)
                route = list(rooms)
                self.assertEqual(route[0], "cockpit")
                self.assertEqual(set(route), {"cockpit", "service", "cargo", "medbay", "reactor", "laboratory", "hangar"})
                self.assertEqual(sum(room.is_exit for room in rooms.values()), 1)
                self.assertTrue(rooms[route[-1]].is_exit)
                for index, name in enumerate(route):
                    room = rooms[name]
                    expected = set(route[max(0, index - 1):index] + route[index + 1:index + 2])
                    self.assertEqual({door.target for door in room.doors}, expected)
                    for door in room.doors:
                        destination = rooms[door.target]
                        self.assertTrue(any(back.target == name for back in destination.doors))
                        arrival = pygame.Rect(door.arrival_x, FLOOR_Y - 86, 44, 86)
                        self.assertGreaterEqual(arrival.left, 0)
                        self.assertLessEqual(arrival.right, destination.width)
                        self.assertFalse(any(arrival.colliderect(p) for p in destination.solids))
                        self.assertFalse(any(arrival.colliderect(enemy.rect) for enemy in destination.enemies))
                self.assertEqual(rooms[route[-1]].doors[0].x, 80)

    def test_corridors_remain_walkable_and_enemies_start_safely_apart(self):
        for seed in range(64):
            with self.subTest(seed=seed):
                for index, room in enumerate(make_rooms(seed).values()):
                    self.assertEqual(room.width % 4, 0)
                    self.assertGreaterEqual(room.width, 1800 if index == 0 else 2600)
                    self.assertLessEqual(room.width, 3200)
                    ground_route = pygame.Rect(0, FLOOR_Y - 86, room.width, 86)
                    for platform in room.platforms:
                        rectangle = pygame.Rect(platform)
                        self.assertFalse(ground_route.colliderect(rectangle))
                        self.assertGreaterEqual(rectangle.left, 0)
                        self.assertLessEqual(rectangle.right, room.width)
                    if index == 0:
                        self.assertFalse(room.enemies)
                        self.assertEqual(room.loot[0].x, 610)
                        continue
                    self.assertGreaterEqual(len(room.enemies), 7)
                    self.assertLessEqual(len(room.enemies), 8)
                    for i, enemy in enumerate(room.enemies):
                        self.assertGreaterEqual(enemy.rect.left, 440)
                        self.assertLessEqual(enemy.rect.right, room.width - 200)
                        self.assertEqual(enemy.rect.bottom, FLOOR_Y)
                        self.assertFalse(any(enemy.rect.colliderect(p) for p in room.platforms))
                        self.assertFalse(any(enemy.rect.colliderect(other.rect) for other in room.enemies[i + 1:]))

    def test_fights_support_progression_and_both_weapon_types(self):
        for seed in range(64):
            with self.subTest(seed=seed):
                rooms = list(make_rooms(seed).values())
                self.assertEqual([room.tier for room in rooms], [1, 1, 1, 2, 3, 4, 5])
                self.assertGreaterEqual(sum(enemy.xp_reward for room in rooms[1:3] for enemy in room.enemies), 100)
                self.assertGreaterEqual(sum(enemy.xp_reward for room in rooms for enemy in room.enemies), 770)
                self.assertEqual({rooms[0].loot[0].weapon_id, rooms[1].loot[0].weapon_id}, set(WEAPON_IDS))
                for room in rooms:
                    for pickup in room.loot:
                        self.assertIn(pickup.weapon_id, WEAPON_IDS)
                        self.assertGreater(pickup.x, 140)
                        self.assertLess(pickup.x, room.width - 200)

    def test_each_run_owns_its_enemies_loot_and_experience(self):
        original = make_rooms(91)
        fresh = make_rooms(91)
        first_fight = list(original)[1]
        original[first_fight].enemies[0].health = 0
        original["cockpit"].loot[0].collected = True
        original[first_fight].xp_drops.append(object())
        self.assertGreater(fresh[first_fight].enemies[0].health, 0)
        self.assertTrue(fresh["cockpit"].weapon_available)
        self.assertFalse(fresh[first_fight].xp_drops)
        self.assertFalse(original["cockpit"].weapon_available)


if __name__ == "__main__":
    unittest.main()
