"""XP, recharge des soins et propriétés de combat propres au mode Histoire."""

import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

from types import SimpleNamespace
import unittest
from unittest.mock import patch

import pygame

from Notundertale.story.enemies import Alien
from Notundertale.story.progression import BOSS_XP, Progression
from Notundertale.story.weapons import Armory, WEAPONS, WeaponSpec


class ProgressionTests(unittest.TestCase):
    def test_ten_early_rewards_level_up_but_kills_alone_do_not_grant_xp(self):
        progression = Progression()
        for _ in range(10):
            progression.record_kill()
        self.assertEqual((progression.level, progression.xp, progression.kills), (1, 0, 10))
        for _ in range(9):
            self.assertEqual(progression.add_xp(10), 0)
        self.assertEqual(progression.add_xp(10), 1)
        self.assertEqual((progression.level, progression.xp, progression.total_xp), (2, 0, 100))
        self.assertEqual(progression.xp_required, 135)
        self.assertEqual(progression.max_health, 120)
        self.assertAlmostEqual(progression.damage_multiplier, 1.12)

    def test_large_reward_keeps_surplus_and_grows_thresholds(self):
        progression = Progression()
        self.assertEqual(progression.add_xp(BOSS_XP), 2)
        self.assertEqual((progression.level, progression.xp), (3, 15))
        self.assertEqual(progression.xp_required, 185)
        self.assertEqual(progression.max_health, 140)
        self.assertAlmostEqual(progression.damage_multiplier, 1.24)
        with self.assertRaises(ValueError):
            progression.add_xp(-10)

    def test_heal_costs_one_charge_only_if_alive_and_hurt(self):
        progression = Progression()
        player = SimpleNamespace(health=100)
        self.assertFalse(progression.use_heal(player))
        player.health = 0
        self.assertFalse(progression.use_heal(player))
        player.health = 50
        self.assertTrue(progression.use_heal(player))
        self.assertEqual((player.health, progression.heal_charges), (90, 0))
        self.assertFalse(progression.use_heal(player))

    def test_five_kills_restore_one_charge_without_banking_at_full(self):
        progression = Progression()
        for _ in range(12):
            progression.record_kill()
        player = SimpleNamespace(health=1)
        self.assertTrue(progression.use_heal(player))
        for _ in range(4):
            self.assertFalse(progression.record_kill())
        self.assertEqual((progression.heal_charges, progression.heal_kills), (0, 4))
        self.assertTrue(progression.record_kill())
        self.assertEqual((progression.heal_charges, progression.heal_kills), (1, 0))

    def test_level_five_unlocks_ready_second_charge_and_sequential_refills(self):
        progression = Progression()
        progression.use_heal(SimpleNamespace(health=1))
        progression.record_kill()
        # 100 + 135 + 185 + 250 : quatre passages de niveau.
        self.assertEqual(progression.add_xp(670), 4)
        self.assertEqual((progression.level, progression.heal_capacity, progression.heal_charges), (5, 2, 1))
        player = SimpleNamespace(health=10)
        self.assertTrue(progression.use_heal(player))
        self.assertEqual(player.health, 82)
        self.assertEqual(progression.heal_kills, 1)
        for _ in range(4):
            progression.record_kill()
        self.assertEqual((progression.heal_charges, progression.heal_kills), (1, 0))
        for _ in range(5):
            progression.record_kill()
        self.assertEqual((progression.heal_charges, progression.heal_kills), (2, 0))
        progression.record_kill(is_boss=True)
        self.assertEqual(progression.heal_charges, 2)

    def test_boss_restores_one_charge_and_consumes_partial_recharge(self):
        progression = Progression(level=5, heal_charges=0, heal_kills=3)
        self.assertTrue(progression.record_kill(is_boss=True))
        self.assertEqual((progression.heal_charges, progression.heal_kills), (1, 0))
        self.assertEqual(progression.xp, 0)
        self.assertEqual(Progression().heal_charges, 1)


class WeaponTests(unittest.TestCase):
    def setUp(self):
        self.armory = Armory()
        self.player = SimpleNamespace(rect=pygame.Rect(100, 450, 44, 86),
                                      facing=1, health=100, damage_multiplier=1.0)
        self.room = SimpleNamespace(width=2400, solids=[], enemies=[])

    def test_two_distinct_slots_direct_selection_and_no_duplicate(self):
        self.assertIsNone(self.armory.current)
        self.assertFalse(self.armory.select(0))
        self.armory.equip("rifle")
        self.armory.equip("raygun")
        self.assertEqual(self.armory.current, "raygun")
        self.assertTrue(self.armory.select(0))
        self.assertEqual(self.armory.current, "rifle")
        self.assertFalse(self.armory.select(2))
        self.armory.equip("raygun")
        self.assertEqual(self.armory.slots, ["rifle", "raygun"])
        self.assertEqual(self.armory.selected, 1)
        with self.assertRaises(ValueError):
            self.armory.equip("unknown")

    def test_future_third_type_replaces_selected_slot(self):
        self.armory.equip("rifle")
        self.armory.equip("raygun")
        with patch.dict(WEAPONS, {"third": WeaponSpec("Test", 15, .4, 900, (1, 2, 3))}):
            self.assertEqual(self.armory.equip("third"), "raygun")
            self.assertEqual(self.armory.slots, ["rifle", "third"])

    def test_switching_and_re_equipping_preserve_individual_fire_delays(self):
        self.armory.equip("rifle")
        self.armory.equip("raygun")
        self.assertTrue(self.armory.update(0, True, self.player, self.room))
        self.armory.select(0)
        self.assertTrue(self.armory.update(0, True, self.player, self.room))
        self.armory.select(1)
        self.armory.equip("raygun")
        self.assertFalse(self.armory.update(.10, True, self.player, self.room))
        self.armory.select(0)
        self.assertTrue(self.armory.update(0, True, self.player, self.room))
        self.armory.select(1)
        self.assertTrue(self.armory.update(.45, True, self.player, self.room))

    def test_rifle_fires_more_often_and_heavy_ray_hits_harder(self):
        shots = {}
        for weapon_id in WEAPONS:
            gun = Armory()
            gun.equip(weapon_id)
            shots[weapon_id] = sum(gun.update(1 / 120, True, self.player, self.room)
                                   for _ in range(120))
        self.assertEqual(shots, {"rifle": 10, "raygun": 2})
        self.assertGreater(WEAPONS["raygun"].damage, WEAPONS["rifle"].damage)

    def test_inflight_damage_is_snapshot_of_level_and_weapon(self):
        self.armory.equip("raygun")
        self.player.damage_multiplier = 1.24
        self.armory.update(0, True, self.player, self.room)
        ray = self.armory.rays[0]
        self.player.damage_multiplier = 2
        self.armory.equip("rifle")
        self.assertEqual((ray.damage, ray.speed, ray.weapon_id), (37, 800, "raygun"))
        self.player.health = 0
        self.assertFalse(self.armory.update(1, True, self.player, self.room))

    def test_wall_stops_bullets_even_with_a_large_step_in_both_directions(self):
        for facing in (-1, 1):
            with self.subTest(facing=facing):
                self.armory = Armory()
                self.armory.equip("raygun")
                self.player.rect.x = 500
                self.player.facing = facing
                enemy = Alien(750 if facing > 0 else 250, 470)
                wall = pygame.Rect(650 if facing > 0 else 400, 440, 20, 100)
                self.room.enemies = [enemy]
                self.room.solids = [wall]
                self.armory.update(.4, True, self.player, self.room)
                self.assertEqual(enemy.health, enemy.max_health)
                self.assertFalse(self.armory.rays)
                self.assertEqual(len(self.armory.impacts), 1)

    def test_first_living_target_takes_hit_and_alien_dies_once(self):
        front, rear = Alien(220, 470), Alien(300, 470)
        self.room.enemies = [rear, front]
        self.armory.equip("raygun")
        self.armory.update(.4, True, self.player, self.room)
        self.assertEqual(front.health, 0)
        self.assertEqual(rear.health, rear.max_health)
        self.assertFalse(front.hit(30))
        self.armory.update(.55, True, self.player, self.room)
        self.assertEqual(rear.health, 0)

    def test_alien_tiers_raise_health_damage_and_reward(self):
        early, later = Alien(0, 0), Alien(0, 0, tier=3)
        self.assertEqual((early.max_health, early.xp_reward, early.contact_damage), (30, 10, 20))
        self.assertEqual((later.max_health, later.xp_reward, later.contact_damage), (50, 20, 28))
        self.assertFalse(later.hit(0))
        self.assertFalse(later.hit(49))
        self.assertTrue(later.hit(10))
        self.assertFalse(later.hit(10))
        self.assertFalse(later.rewarded)


if __name__ == "__main__":
    unittest.main()
