"""Armes pixel art et composition des bras autour de leurs points de prise.

Les poses armées sont propres à l'Histoire. Les images sources des personnages
restent partagées en lecture seule avec les menus et le mode Infini.
"""

from functools import lru_cache

import pygame

from .weapon_pose import weapon_pose, RECOIL_PIXELS

OUTLINE = (12, 18, 28)
STEEL = (83, 107, 121)
LIGHT = (190, 211, 211)
SHADOW = (42, 59, 76)
AMBER = (246, 191, 78)
CYAN = (92, 232, 244)
WHITE = (218, 217, 193)
SUIT_SHADOW = (120, 128, 132)
BLOOD = (103, 33, 47)
GREEN = (29, 100, 63)


@lru_cache(maxsize=4)
def gun_image(weapon_id, facing=1):
    """Une silhouette de 72x30, commune au sol, aux mains et à l'interface."""
    if facing < 0:
        return pygame.transform.flip(gun_image(weapon_id), True, False)
    image = pygame.Surface((72, 30), pygame.SRCALPHA)
    rect = lambda color, box: pygame.draw.rect(image, color, box)
    poly = lambda color, points: pygame.draw.polygon(image, color, points)
    if weapon_id == "rifle":
        # Crosse ajourée et corps asymétrique, rail, poignée, chargeur incliné.
        poly(OUTLINE, [(0, 7), (12, 7), (16, 3), (49, 3), (53, 6), (68, 6),
                      (70, 8), (70, 14), (51, 14), (48, 19), (36, 19),
                      (32, 28), (24, 28), (25, 18), (20, 18), (17, 25),
                      (10, 25), (12, 14), (5, 14), (5, 18), (0, 18)])
        rect(SHADOW, (2, 9, 12, 4))
        rect(STEEL, (2, 8, 8, 2))
        rect(LIGHT, (2, 13, 2, 3))
        rect(STEEL, (15, 6, 32, 10))
        rect(LIGHT, (17, 5, 30, 2))
        rect(SHADOW, (16, 14, 31, 3))
        rect((36, 45, 59), (17, 9, 12, 4))
        rect((131, 146, 149), (19, 9, 8, 2))
        rect(AMBER, (30, 7, 3, 7))
        rect((106, 121, 128), (35, 7, 15, 7))
        for x in (37, 41, 45):
            rect(OUTLINE, (x, 8, 2, 5))
        rect(OUTLINE, (26, 0, 11, 5))
        rect(STEEL, (28, 1, 7, 2))
        rect(CYAN, (34, 1, 2, 2))
        rect(SHADOW, (49, 8, 19, 5))
        rect(LIGHT, (50, 8, 15, 2))
        rect(OUTLINE, (60, 5, 6, 10))
        rect(STEEL, (61, 6, 4, 8))
        rect(AMBER, (66, 9, 3, 3))
        poly(STEEL, [(27, 18), (34, 18), (30, 26), (26, 26)])
        for y in (20, 23):
            rect(SHADOW, (27, y, 4, 1))
        poly(SHADOW, [(14, 16), (19, 16), (16, 23), (12, 23)])
        rect((108, 79, 58), (14, 18, 2, 4))
        pygame.draw.lines(image, LIGHT, False, [(21, 17), (22, 19), (25, 19)], 1)
        rect(AMBER, (6, 9, 3, 2))
    else:
        # Batterie ventrale, cage de confinement et trois bobines lumineuses.
        poly(OUTLINE, [(1, 7), (10, 7), (14, 3), (30, 3), (34, 0), (52, 0),
                      (57, 5), (65, 5), (70, 8), (70, 15), (63, 19), (55, 19),
                      (51, 23), (32, 23), (29, 18), (23, 18), (20, 28),
                      (12, 28), (13, 16), (6, 16), (1, 13)])
        rect(SHADOW, (3, 9, 13, 4))
        rect(STEEL, (13, 6, 22, 11))
        rect(LIGHT, (16, 4, 14, 3))
        rect((37, 68, 77), (17, 8, 13, 8))
        rect(CYAN, (20, 9, 6, 4))
        rect((222, 255, 236), (21, 9, 3, 2))
        rect(SHADOW, (33, 3, 20, 17))
        rect((31, 106, 111), (35, 5, 17, 12))
        for x in (34, 41, 48):
            rect(OUTLINE, (x, 2, 5, 19))
            rect(STEEL, (x + 1, 3, 3, 17))
            rect(CYAN, (x + 1, 6, 2, 11))
            rect((224, 255, 245), (x + 1, 7, 1, 4))
        rect(STEEL, (55, 7, 10, 10))
        rect(LIGHT, (55, 6, 7, 2))
        rect(OUTLINE, (62, 8, 7, 7))
        rect(CYAN, (65, 9, 4, 4))
        rect((226, 255, 248), (67, 10, 2, 2))
        rect(STEEL, (34, 20, 15, 2))
        rect((125, 95, 53), (34, 18, 15, 2))
        rect(AMBER, (36, 18, 3, 2))
        poly(SHADOW, [(16, 17), (21, 17), (18, 26), (14, 26)])
        rect(STEEL, (15, 21, 3, 1))
        rect(STEEL, (15, 24, 3, 1))
        rect((154, 77, 60), (11, 10, 2, 3))
    return image


def draw_gun(surface, x, y, facing=1, pickup=False, weapon_id="raygun"):
    image = gun_image(weapon_id, facing)
    surface.blit(image, (round(x) - 36, round(y) - 15))


def _limb(surface, points, cloth, shade, width=9):
    # Des segments carrés et des ombres franches gardent les articulations lisibles.
    pygame.draw.lines(surface, OUTLINE, False, points, width + 4)
    pygame.draw.lines(surface, shade, False, points, width)
    pygame.draw.lines(surface, cloth, False, [(x - 1, y - 2) for x, y in points], max(2, width - 4))
    for x, y in points[1:-1]:
        pygame.draw.rect(surface, shade, (x - 4, y - 3, 7, 6))
        pygame.draw.rect(surface, cloth, (x - 3, y - 3, 5, 2))


def _glove(surface, point, green=False):
    x, y = point
    pygame.draw.rect(surface, OUTLINE, (x - 4, y - 4, 9, 8))
    pygame.draw.rect(surface, GREEN if green else (82, 95, 107), (x - 3, y - 3, 7, 6))
    pygame.draw.rect(surface, (91, 155, 96) if green else (159, 175, 181), (x - 2, y - 3, 5, 2))
    for finger in (0, 2):
        pygame.draw.rect(surface, (14, 48, 33) if green else SHADOW, (x + finger, y, 1, 3))


class ArmedSprites:
    """Composer puis mettre en cache les poses armées sans toucher aux originaux."""

    WIDTH = 180
    OFFSET = 40

    def __init__(self, skin_name):
        self.skin_name = skin_name
        self.cache = {}

    def image(self, player, weapon_id, recoil=0):
        animation = player.animation
        pose = weapon_pose(player, recoil)
        key = (animation.state, animation.frame_index, weapon_id, pose, player.facing)
        if key not in self.cache:
            # Tous les points sont définis vers la droite, puis le corps et
            # l'arme se retournent ensemble autour du même pivot.
            result = self._compose(animation.image(False), pose, animation.state, weapon_id)
            if player.facing < 0:
                result = pygame.transform.flip(result, True, False)
            self.cache[key] = result
        return self.cache[key]

    def _compose(self, source, pose, state, weapon_id):
        body = source.copy()
        dx, dy = pose.dx, pose.dy
        # Retirer seulement les anciens bras de la copie de rendu. Le casque,
        # le torse, les jambes et leur cycle de marche restent ceux de la pose.
        if self.skin_name == "default":
            body.fill((0, 0, 0, 0), (23, 66, 13, 10))
            body.fill((0, 0, 0, 0), (65, 66, 13, 10))
        elif state == "dash":
            pygame.draw.polygon(body, (0, 0, 0, 0), [(0, 27), (56, 27), (56, 40),
                                (51, 47), (52, 55), (42, 60), (0, 60)])
            pygame.draw.polygon(body, (0, 0, 0, 0), [(79, 49), (100, 49), (100, 73), (76, 73), (73, 61)])
        else:
            left = [(0, 43), (27, 43), (40, 48), (43, 57), (46, 68), (38, 73), (0, 73)]
            right = [(65, 39), (100, 39), (100, 72), (69, 72), (65, 59)]
            for polygon in (left, right):
                pygame.draw.polygon(body, (0, 0, 0, 0), [(x + dx, y + dy) for x, y in polygon])
        image = pygame.Surface((self.WIDTH, 100), pygame.SRCALPHA)
        ox = self.OFFSET
        gx, gy = pose.origin
        trigger = (ox + gx + 16, gy + 20)
        support = (ox + gx + 49, gy + 17)
        near = [(ox + 36 + dx, 44 + dy), (ox + 39 + dx, 61 + dy), trigger]
        far = [(ox + 61 + dx, 44 + dy), (ox + 66 + dx, 65 + dy), support]
        cloth, shade = WHITE, SUIT_SHADOW
        if self.skin_name == "skin2":
            cloth, shade = (35, 180, 220), (38, 113, 153)
        elif self.skin_name == "default":
            cloth, shade = (236, 226, 226), (143, 135, 144)
        contaminated = self.skin_name in ("scaphandre", "colonie")
        _limb(image, far, (75, 138, 89) if contaminated else shade,
              GREEN if contaminated else SHADOW, 7)
        image.blit(body, (ox, 0))
        image.blit(gun_image(weapon_id), (ox + gx, gy))
        _limb(image, near, cloth, shade)
        if self.skin_name not in ("default", "skin2"):
            # Couture, taches bordeaux et joint sombre sur la manche visible.
            x, y = near[0]
            pygame.draw.line(image, OUTLINE, (x - 4, y + 1), (x + 2, y + 4), 1)
            pygame.draw.rect(image, BLOOD, (x - 3, y + 7, 3, 5))
            pygame.draw.rect(image, BLOOD, (near[1][0] + 4, near[1][1] - 2, 4, 2))
        _glove(image, trigger, self.skin_name == "colonie")
        _glove(image, support, contaminated)
        return image


def recoil_amount(armory):
    if armory.current != armory.last_shot_weapon or not armory.shot_flash:
        return 0
    distance = RECOIL_PIXELS.get(armory.current, 2)
    return round(distance * armory.shot_flash / armory.FLASH_DURATION)


def draw_muzzle_flash(surface, position, direction, weapon_id, remaining):
    if remaining <= 0:
        return
    x, y = map(round, position)
    color = AMBER if weapon_id == "rifle" else CYAN
    length = 10 if weapon_id == "rifle" else 15
    points = [(0, -2), (6, -5), (4, -1), (length, 0), (4, 2), (6, 5), (0, 2)]
    pygame.draw.polygon(surface, color, [(x + direction * px, y + py) for px, py in points])
    pygame.draw.rect(surface, (239, 253, 224), (x - 1, y - 1, 4, 3))
