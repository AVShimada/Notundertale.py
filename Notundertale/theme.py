"""Thème spatial pixel art : palette, lettres bitmap et dessin des panneaux.

Tout est dessiné par le jeu, sans police à installer ni image à télécharger.
Les menus utilisent un canevas logique de 1280 × 720, adapté à l'écran.
"""

from functools import lru_cache
import random
import unicodedata

import pygame

NIGHT = (7, 12, 24)
PANEL = (12, 24, 42)
PANEL_LIGHT = (18, 38, 58)
EDGE = (36, 65, 87)
CYAN = (92, 232, 244)
ICE = (226, 249, 250)
MUTED = (128, 167, 183)
DIM = (71, 108, 131)
GOLD = (255, 211, 112)
CORAL = (255, 112, 134)
GREEN = (134, 242, 192)

# Sept lignes de cinq pixels par caractère, précédées de deux lignes d'accent.
GLYPHS = {
    "A": (14,17,17,31,17,17,17), "B": (30,17,17,30,17,17,30),
    "C": (14,17,16,16,16,17,14), "D": (30,17,17,17,17,17,30),
    "E": (31,16,16,30,16,16,31), "F": (31,16,16,30,16,16,16),
    "G": (14,17,16,23,17,17,15), "H": (17,17,17,31,17,17,17),
    "I": (14,4,4,4,4,4,14), "J": (7,2,2,2,2,18,12),
    "K": (17,18,20,24,20,18,17), "L": (16,16,16,16,16,16,31),
    "M": (17,27,21,21,17,17,17), "N": (17,25,21,19,17,17,17),
    "O": (14,17,17,17,17,17,14), "P": (30,17,17,30,16,16,16),
    "Q": (14,17,17,17,21,18,13), "R": (30,17,17,30,20,18,17),
    "S": (15,16,16,14,1,1,30), "T": (31,4,4,4,4,4,4),
    "U": (17,17,17,17,17,17,14), "V": (17,17,17,17,17,10,4),
    "W": (17,17,17,21,21,21,10), "X": (17,17,10,4,10,17,17),
    "Y": (17,17,10,4,4,4,4), "Z": (31,1,2,4,8,16,31),
    "0": (14,17,19,21,25,17,14), "1": (4,12,4,4,4,4,14),
    "2": (14,17,1,2,4,8,31), "3": (30,1,1,14,1,1,30),
    "4": (2,6,10,18,31,2,2), "5": (31,16,16,30,1,1,30),
    "6": (14,16,16,30,17,17,14), "7": (31,1,2,4,8,8,8),
    "8": (14,17,17,14,17,17,14), "9": (14,17,17,15,1,1,14),
    ".": (0,0,0,0,0,12,12), ",": (0,0,0,0,0,4,8),
    ":": (0,12,12,0,12,12,0), ";": (0,12,12,0,4,4,8),
    "!": (4,4,4,4,4,0,4), "?": (14,17,1,2,4,0,4),
    "-": (0,0,0,31,0,0,0), "+": (0,4,4,31,4,4,0),
    "/": (1,1,2,4,8,16,16), "\\": (16,16,8,4,2,1,1),
    "(": (2,4,8,8,8,4,2), ")": (8,4,2,2,2,4,8),
    "[": (14,8,8,8,8,8,14), "]": (14,2,2,2,2,2,14),
    "<": (2,4,8,16,8,4,2), ">": (8,4,2,1,2,4,8),
    "=": (0,0,31,0,31,0,0), "_": (0,0,0,0,0,0,31),
    "'": (4,4,8,0,0,0,0), '"': (10,10,0,0,0,0,0),
    "%": (25,25,2,4,8,19,19), "*": (0,21,14,31,14,21,0),
    "#": (10,10,31,10,31,10,10), "&": (12,18,20,8,21,18,13),
    "|": (4,4,4,4,4,4,4), "·": (0,0,0,4,0,0,0),
}


def _text(value):
    return str(value).replace("œ", "oe").replace("Œ", "OE").replace("’", "'").replace("—", "-").replace("–", "-").replace("…", "...").upper()


class PixelFont:
    def __init__(self, scale):
        self.scale = max(1, int(scale))

    def size(self, text):
        text = _text(text)
        return max(1, sum(4 if char == " " else 6 for char in text) * self.scale - self.scale), self.get_height()

    def get_height(self):
        return 10 * self.scale

    def render(self, text, antialias, color):
        return self._render(_text(text), tuple(color))

    @lru_cache(maxsize=192)
    def _render(self, text, color):
        image = pygame.Surface(self.size(text), pygame.SRCALPHA)
        x = 0
        scale = self.scale
        for char in text:
            if char != " ":
                decomposition = unicodedata.normalize("NFD", char)
                rows = [0, 0, *GLYPHS.get(decomposition[0], GLYPHS["?"]), 0]
                accent = decomposition[1:]
                if "\u0301" in accent:
                    rows[0:2] = [2, 4]
                elif "\u0300" in accent:
                    rows[0:2] = [8, 4]
                elif "\u0302" in accent:
                    rows[0:2] = [4, 10]
                elif "\u0308" in accent:
                    rows[0:2] = [10, 0]
                elif "\u0327" in accent:
                    rows[9] = 4
                for y, bits in enumerate(rows):
                    for column in range(5):
                        if bits & (1 << (4 - column)):
                            image.fill(color, (x + column * scale, y * scale, scale, scale))
            x += (4 if char == " " else 6) * scale
        return image


@lru_cache(maxsize=8)
def pixel_font(scale=2):
    return PixelFont(scale)


def text_at(surface, text, pos, scale=2, color=ICE, shadow=False):
    font = pixel_font(scale)
    if shadow:
        surface.blit(font.render(text, False, NIGHT), (pos[0] + scale, pos[1] + scale))
    surface.blit(font.render(text, False, color), pos)


def fit_label(surface, text, rect, color=ICE, scale=2, align="center"):
    font = pixel_font(scale)
    while scale > 1 and font.size(text)[0] > rect.width - 24:
        scale -= 1
        font = pixel_font(scale)
    # Les noms de périphériques externes peuvent être très longs.
    while text and font.size(text)[0] > rect.width - 24:
        text = text[:-4] + "..." if len(text) > 4 else ""
    image = font.render(text, False, color)
    target = image.get_rect(centery=rect.centery)
    target.x = rect.x + 12 if align == "left" else rect.centerx - image.get_width() // 2
    surface.blit(image, target)


def _cut_rect(surface, rect, color, cut=8):
    r = pygame.Rect(rect)
    pygame.draw.polygon(surface, color, [(r.x + cut,r.y),(r.right - cut,r.y),
        (r.right - cut,r.y + cut),(r.right,r.y + cut),(r.right,r.bottom - cut),
        (r.right - cut,r.bottom - cut),(r.right - cut,r.bottom),(r.x + cut,r.bottom),
        (r.x + cut,r.bottom - cut),(r.x,r.bottom - cut),(r.x,r.y + cut),(r.x + cut,r.y + cut)])


def panel(surface, rect, color=PANEL, border=EDGE, shadow=True):
    rect = pygame.Rect(rect)
    if shadow:
        _cut_rect(surface, rect.move(6, 8), (3, 7, 16))
    _cut_rect(surface, rect, border)
    _cut_rect(surface, rect.inflate(-4, -4), color, 6)
    pygame.draw.line(surface, tuple(min(255, channel + 15) for channel in border),
                     (rect.x + 12, rect.y + 4), (rect.right - 12, rect.y + 4), 2)


def focus_corners(surface, rect, color=CYAN):
    r = pygame.Rect(rect).inflate(8, 8)
    for x, y, dx, dy in [(r.x,r.y,1,1),(r.right,r.y,-1,1),
                          (r.x,r.bottom,1,-1),(r.right,r.bottom,-1,-1)]:
        pygame.draw.line(surface, color, (x,y), (x + dx * 12,y), 3)
        pygame.draw.line(surface, color, (x,y), (x,y + dy * 12), 3)


@lru_cache(maxsize=1)
def space_background():
    small = pygame.Surface((320, 180))
    small.fill(NIGHT)
    for y in range(100, 180, 8):
        pygame.draw.rect(small, (8, 15 + (y - 100) // 9, 29 + (y - 100) // 6), (0,y,320,8))
    rng = random.Random(71)
    for _ in range(115):
        x, y = rng.randrange(320), rng.randrange(165)
        color = rng.choice([(30, 53, 77), (53, 94, 113), (83, 143, 159)])
        small.fill(color, (x, y, 1, 1))
    # Planète lointaine : contours dessinés en basse résolution, sans lissage.
    pygame.draw.circle(small, (16, 39, 58), (264, 45), 29)
    pygame.draw.circle(small, (22, 53, 71), (262, 43), 26, 2)
    pygame.draw.circle(small, NIGHT, (274, 36), 23)
    pygame.draw.ellipse(small, (30, 72, 89), (220, 36, 88, 20), 1)
    for x, y in ((206,25),(46,28),(302,82),(181,150)):
        pygame.draw.line(small, (83, 153, 170), (x-1,y), (x+1,y))
        pygame.draw.line(small, (83, 153, 170), (x,y-1), (x,y+1))
    pygame.draw.line(small, (20, 44, 65), (0,163), (320,163))
    for x in range(-120, 441, 40):
        pygame.draw.line(small, (14, 31, 49), (160 + (x-160)//3,164), (x,180))
    for y in (168,175):
        pygame.draw.line(small, (14, 31, 49), (0,y), (320,y))
    return pygame.transform.scale(small, (1280,720))


def draw_space(surface):
    surface.blit(space_background(), (0, 0))


def footer(surface, text):
    pygame.draw.line(surface, EDGE, (64, 650), (1216, 650), 2)
    fit_label(surface, text, pygame.Rect(64,665,1152,30), MUTED, 2)


class UiCanvas:
    """Conserve les proportions et convertit aussi les clics après mise à l'échelle."""
    def __init__(self, display, transparent=False):
        self.display = display
        self.surface = pygame.Surface((1280,720), pygame.SRCALPHA if transparent else 0)
        width, height = display.get_size()
        scale = min(width / 1280, height / 720)
        size = (round(1280 * scale), round(720 * scale))
        self.viewport = pygame.Rect((width - size[0]) // 2, (height - size[1]) // 2, *size)

    def events(self):
        result = []
        for event in pygame.event.get():
            if hasattr(event, "pos"):
                data = event.dict.copy()
                x, y = event.pos
                data["pos"] = (int((x - self.viewport.x) * 1280 / self.viewport.width),
                               int((y - self.viewport.y) * 720 / self.viewport.height))
                event = pygame.event.Event(event.type, data)
            result.append(event)
        return result

    def blit(self):
        if self.viewport.size == self.surface.get_size():
            self.display.blit(self.surface, self.viewport)
        else:
            self.display.blit(pygame.transform.scale(self.surface, self.viewport.size), self.viewport)

    def present(self):
        self.display.fill(NIGHT)
        self.blit()
        pygame.display.flip()

    def paused_background(self, background):
        result = pygame.transform.scale(background, (1280,720))
        overlay = pygame.Surface((1280,720), pygame.SRCALPHA)
        overlay.fill((4, 10, 23, 205))
        result.blit(overlay, (0,0))
        return result
