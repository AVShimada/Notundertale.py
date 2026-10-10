"""Décors de l'épave sur une grille de quatre pixels, sans modifier les collisions."""

import random

import pygame

from .rooms import FLOOR_Y


PALETTES = {
    "cockpit": ((8, 16, 25), (20, 35, 47), (83, 157, 161)),
    "service": ((8, 17, 25), (21, 37, 47), (74, 129, 142)),
    "cargo": ((17, 18, 23), (42, 40, 42), (135, 109, 68)),
    "medbay": ((10, 22, 24), (33, 49, 50), (91, 155, 140)),
    "reactor": ((14, 20, 22), (35, 46, 43), (94, 142, 102)),
    "laboratory": ((17, 17, 29), (40, 36, 55), (115, 102, 153)),
    "hangar": ((11, 17, 27), (30, 42, 56), (90, 124, 152)),
}


def _window(surface, rng, rectangle, divided=True):
    x, y, width, height = rectangle
    pygame.draw.rect(surface, (51, 70, 81), (x - 3, y - 3, width + 6, height + 6))
    pygame.draw.rect(surface, (13, 24, 37), (x - 1, y - 1, width + 2, height + 2))
    view = pygame.Surface((width, height))
    view.fill((40, 37, 59))
    pygame.draw.rect(view, (54, 47, 67), (0, height // 3, width, height))
    for _ in range(max(3, width // 12)):
        view.fill((105, 103, 126), (rng.randrange(width), rng.randrange(max(1, height // 3)), 1, 1))
    moon_x = max(9, width - 20)
    pygame.draw.circle(view, (155, 128, 145), (moon_x, 12), 8)
    pygame.draw.circle(view, (82, 70, 91), (moon_x - 4, 9), 7)
    for base, color, variation in ((height * 2 // 3, (69, 63, 82), 16),
                                   (height - 7, (33, 43, 56), 10)):
        horizon = [(0, height)]
        for px in range(0, width + 20, 20):
            horizon.append((px, max(18, base - rng.randrange(variation))))
        horizon.append((width, height))
        pygame.draw.polygon(view, color, horizon)
    # Rochers noirs et lueur verte : la planète reste inquiétante, peu documentée.
    for _ in range(max(2, width // 45)):
        px = rng.randrange(4, max(5, width - 5))
        pygame.draw.line(view, (20, 31, 43), (px, height - 4), (px + 2, height - 11), 2)
        view.fill((75, 112, 97), (px + 1, height - 8, 1, 1))
    surface.blit(view, (x, y))
    if divided:
        for px in range(x + 42, x + width - 10, 46):
            pygame.draw.rect(surface, (53, 72, 84), (px, y, 3, height))
            pygame.draw.rect(surface, (83, 101, 108), (px, y, 1, height))
    if rng.random() < 0.8:
        px = x + rng.randrange(5, max(6, width - 20))
        pygame.draw.lines(surface, (107, 119, 129), False,
                          [(px, y), (px + 6, y + 11), (px + 2, y + 18), (px + 12, y + 27)], 1)
        pygame.draw.line(surface, (73, 94, 105), (px + 6, y + 11), (px + 14, y + 9), 1)


def _console(surface, x, y, accent, broken=False):
    pygame.draw.polygon(surface, (38, 52, 63), [(x, y), (x + 29, y), (x + 33, y + 11), (x - 3, y + 11)])
    pygame.draw.rect(surface, (21, 32, 43), (x + 1, y + 11, 27, 22))
    pygame.draw.rect(surface, (67, 83, 88), (x - 1, y + 33, 33, 2))
    pygame.draw.rect(surface, (7, 18, 29), (x + 3, y + 2, 21, 6))
    pygame.draw.rect(surface, (99, 58, 67) if broken else accent, (x + 5, y + 4, 8, 2))
    for offset in (17, 21, 25):
        surface.fill((87, 93, 93), (x + offset, y + 8, 2, 1))
    if broken:
        pygame.draw.lines(surface, (8, 17, 25), False,
                          [(x + 15, y), (x + 12, y + 6), (x + 18, y + 10), (x + 14, y + 24)], 2)


def _theme_features(surface, room, rng, accent):
    width = surface.get_width()
    theme = room.theme
    if theme == "cockpit":
        _window(surface, rng, (42, 48, 126, 53))
        _window(surface, rng, (246, 48, 112, 53))
        for index, x in enumerate((29, 72, 118, 310, 360)):
            _console(surface, x, 113, accent, index in (1, 4))
        # Fauteuil renversé près du corps, et câbles du tableau de bord.
        pygame.draw.polygon(surface, (50, 56, 64), [(42, 141), (51, 132), (64, 137), (54, 146)])
        pygame.draw.lines(surface, (80, 49, 59), False, [(57, 149), (65, 145), (79, 147)], 2)
        pygame.draw.rect(surface, (49, 71, 82), (188, 48, 30, 48))
        pygame.draw.rect(surface, (12, 29, 40), (191, 51, 24, 39))
        pygame.draw.lines(surface, accent, False, [(194, 80), (199, 75), (204, 78), (211, 63)], 1)
    elif theme == "service":
        for x in range(91, width - 128, 206):
            _window(surface, rng, (x, 48, 98, 49))
        for x in range(36, width - 30, 138):
            pygame.draw.rect(surface, (27, 45, 56), (x, 104, 25, 43))
            pygame.draw.rect(surface, (58, 77, 83), (x + 2, 107, 21, 2))
            for y in range(116, 141, 5):
                pygame.draw.rect(surface, (9, 23, 33), (x + 4, y, 17, 2))
            surface.fill(accent, (x + 18, 111, 2, 2))
        for y in (68, 73, 78):
            pygame.draw.rect(surface, (34, 56, 61), (0, y, 71, 3))
            pygame.draw.rect(surface, (65, 89, 91), (0, y, 71, 1))
    elif theme == "cargo":
        for x in (79, width - 138):
            _window(surface, rng, (x, 47, 74, 30), divided=False)
        # Racks muraux : leurs ombres les distinguent des passerelles jouables.
        for x in range(46, width - 70, 105):
            pygame.draw.rect(surface, (18, 22, 29), (x - 4, 88, 79, 59))
            for row in range(2):
                for column in range(2):
                    cx, cy = x + column * 36, 94 + row * 25
                    color = rng.choice(((55, 54, 53), (52, 55, 54), (62, 52, 48)))
                    pygame.draw.rect(surface, color, (cx, cy, 31, 22))
                    pygame.draw.rect(surface, (29, 33, 36), (cx + 3, cy + 3, 25, 16), 1)
                    pygame.draw.rect(surface, (80, 76, 66), (cx + 6, cy + 3, 3, 16))
                    surface.fill(accent, (cx + 20, cy + 8, 6, 3))
            for y in (91, 117, 143):
                pygame.draw.rect(surface, (76, 75, 66), (x - 3, y, 75, 2))
        pygame.draw.rect(surface, (83, 72, 52), (0, 84, width, 2))
    elif theme == "medbay":
        for x in range(88, width - 150, 218):
            _window(surface, rng, (x, 48, 114, 35))
        for x in range(43, width - 70, 113):
            pygame.draw.rect(surface, (53, 69, 70), (x, 96, 61, 40))
            pygame.draw.rect(surface, (21, 38, 43), (x + 3, 99, 55, 33))
            pygame.draw.rect(surface, (82, 98, 96), (x + 6, 120, 44, 7))
            pygame.draw.rect(surface, (64, 79, 79), (x + 6, 116, 12, 7))
            pygame.draw.rect(surface, (37, 54, 57), (x + 10, 137, 3, 11))
            pygame.draw.rect(surface, (37, 54, 57), (x + 49, 137, 3, 11))
            pygame.draw.rect(surface, (12, 25, 31), (x + 43, 102, 11, 10))
            pygame.draw.lines(surface, accent, False, [(x + 44, 108), (x + 47, 108), (x + 49, 104), (x + 51, 108)], 1)
            if rng.random() < 0.6:
                pygame.draw.rect(surface, (89, 43, 56), (x + 28, 122, 11, 3))
        for x in range(51, width - 20, 112):
            pygame.draw.rect(surface, accent, (x + 3, 50, 3, 11))
            pygame.draw.rect(surface, accent, (x - 1, 54, 11, 3))
    elif theme == "reactor":
        for x in range(48, width - 70, 124):
            pygame.draw.rect(surface, (49, 65, 59), (x + 7, 44, 42, 7))
            pygame.draw.rect(surface, (30, 43, 39), (x + 4, 52, 48, 89))
            pygame.draw.rect(surface, (13, 29, 28), (x + 11, 56, 34, 76))
            pygame.draw.rect(surface, (37, 80, 58), (x + 18, 60, 20, 68))
            pygame.draw.rect(surface, (67, 120, 78), (x + 25, 63, 6, 62))
            for y in range(67, 131, 15):
                pygame.draw.rect(surface, (49, 64, 60), (x + 8, y, 40, 3))
            pygame.draw.rect(surface, (65, 75, 62), (x + 4, 139, 48, 8))
            pygame.draw.line(surface, (32, 52, 47), (x + 54, 80), (x + 104, 80), 6)
            pygame.draw.line(surface, (66, 85, 68), (x + 54, 78), (x + 104, 78), 1)
        _console(surface, width // 2 - 15, 112, accent, True)
    elif theme == "laboratory":
        _window(surface, rng, (width - 144, 47, 100, 39))
        for index, x in enumerate(range(53, width - 92, 116)):
            pygame.draw.rect(surface, (69, 64, 85), (x, 55, 46, 5))
            pygame.draw.rect(surface, (13, 26, 36), (x + 3, 60, 40, 61))
            pygame.draw.rect(surface, (34, 52, 61), (x + 6, 63, 34, 55))
            specimen = (88, 62, 115) if index % 2 else (48, 83, 64)
            pygame.draw.polygon(surface, specimen, [(x + 14, 111), (x + 17, 99), (x + 13, 87),
                                                   (x + 23, 77), (x + 31, 87), (x + 28, 99), (x + 34, 113)])
            pygame.draw.rect(surface, (71, 110, 117), (x + 8, 65, 2, 41))
            for _ in range(5):
                surface.fill((97, 129, 132), (x + rng.randrange(13, 37), rng.randrange(65, 114), 1, 1))
            pygame.draw.rect(surface, (57, 59, 75), (x, 121, 46, 8))
            pygame.draw.rect(surface, (23, 32, 43), (x + 4, 130, 38, 17))
            pygame.draw.rect(surface, accent, (x + 16, 124, 11, 2))
        _console(surface, 20, 113, accent, True)
    elif theme == "hangar":
        for x in range(60, width - 145, 179):
            _window(surface, rng, (x, 50, 119, 70))
        for x in range(40, width - 35, 89):
            pygame.draw.rect(surface, (30, 42, 55), (x, 37, 6, 109))
            pygame.draw.rect(surface, (61, 78, 88), (x, 37, 2, 105))
            pygame.draw.line(surface, (42, 58, 72), (x + 4, 38), (x + 25, 57), 4)
        # Épave d'une navette au fond du hangar, volontairement en teintes sombres.
        x = width // 2 - 65
        pygame.draw.polygon(surface, (34, 43, 55), [(x, 135), (x + 34, 110), (x + 78, 115),
                                                  (x + 108, 133), (x + 130, 140), (x + 130, 145), (x, 145)])
        pygame.draw.polygon(surface, (51, 69, 79), [(x + 34, 115), (x + 57, 117), (x + 70, 128), (x + 21, 128)])
        pygame.draw.line(surface, (82, 64, 65), (x + 83, 119), (x + 78, 140), 3)
        pygame.draw.rect(surface, (14, 27, 37), (x + 10, 139, 27, 6))


def room_background(room):
    """Composer une surface statique à l'échelle du monde, reproductible par salle."""
    background, wall, accent = PALETTES.get(room.theme, PALETTES["service"])
    rng = random.Random(room.decor_seed)
    small = pygame.Surface((room.width // 4, 180))
    small.fill(background)
    width = small.get_width()
    for x in range(0, width, 48):
        pygame.draw.rect(small, wall, (x + 2, 36, 44, 112))
        pygame.draw.rect(small, (43, 56, 65), (x + 3, 37, 42, 1))
        pygame.draw.rect(small, background, (x + 7, 115, 34, 27))
        for bx in (x + 5, x + 40):
            for by in (41, 141):
                small.fill((64, 78, 80), (bx, by, 1, 1))
    _theme_features(small, room, rng, accent)
    # Les conduites et luminaires cadrent les accessoires sans recouvrir le sol.
    for y, color in ((30, (44, 59, 67)), (33, (23, 38, 48)), (146, (40, 55, 60))):
        pygame.draw.rect(small, color, (0, y, width, 2))
    for x in range(18, width, 64):
        pygame.draw.rect(small, (52, 69, 74), (x, 29, 2, 8))
        light = accent if rng.random() > 0.22 else (74, 54, 63)
        pygame.draw.rect(small, (23, 39, 48), (x + 5, 38, 24, 5))
        pygame.draw.rect(small, light, (x + 8, 39, 18, 2))
    for _ in range(max(3, width // 150)):
        x = rng.randrange(40, width - 35)
        y = rng.randrange(44, 102)
        pygame.draw.polygon(small, (49, 44, 49), [(x - 4, y), (x + 7, y - 5), (x + 14, y + 5),
                                                       (x + 7, y + 18), (x - 5, y + 12)])
        pygame.draw.polygon(small, (5, 12, 21), [(x, y), (x + 6, y - 2), (x + 11, y + 5),
                                                     (x + 6, y + 14), (x - 2, y + 10)])
        pygame.draw.lines(small, (85, 66, 67), False, [(x + 9, y + 8), (x + 14, y + 19),
                                                      (x + 7, y + 31), (x + 10, y + 40)], 1)
    for _ in range(width // 9):
        x, y = rng.randrange(width), rng.randrange(133, 149)
        pygame.draw.rect(small, rng.choice(((30, 44, 48), (63, 42, 52), (36, 60, 48))),
                         (x, y, rng.randrange(2, 6), 1))
    floor = FLOOR_Y // 4
    pygame.draw.rect(small, (25, 40, 50), (0, floor, width, 180 - floor))
    pygame.draw.rect(small, (98, 115, 118), (0, floor, width, 2))
    pygame.draw.rect(small, (9, 20, 31), (0, floor + 5, width, 2))
    for x in range(0, width, 12):
        pygame.draw.line(small, (10, 24, 34), (x, floor + 8), (x + 5, floor + 21), 2)
    for x in range(9, width, 48):
        pygame.draw.rect(small, accent, (x, floor + 3, 11, 1))
    # Seuls ces éléments décoratifs correspondent à de vraies plateformes.
    for x, y, platform_width, height in room.platforms:
        rectangle = pygame.Rect(x // 4, y // 4, platform_width // 4, height // 4)
        pygame.draw.rect(small, (28, 47, 57), rectangle)
        pygame.draw.rect(small, (101, 145, 151), (rectangle.x, rectangle.y, rectangle.width, 1))
        pygame.draw.rect(small, (12, 29, 40), (rectangle.x, rectangle.bottom - 1, rectangle.width, 1))
        for px in range(rectangle.x + 3, rectangle.right - 2, 6):
            small.fill((170, 143, 85), (px, rectangle.y + 2, 3, 1))
    return pygame.transform.scale(small, (room.width, 720))
