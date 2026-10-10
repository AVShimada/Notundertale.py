"""Collisions de plateforme, en petits pas de simulation indépendants du rendu."""

import pygame

GRAVITY = 1850


def move_body(body, vx, dt, solids, width):
    body.pos.x += vx * dt
    body.rect.x = round(body.pos.x)
    for solid in solids:
        if body.rect.colliderect(solid):
            if vx > 0:
                body.rect.right = solid.left
            elif vx < 0:
                body.rect.left = solid.right
    body.rect.x = max(0, min(width - body.rect.width, body.rect.x))
    # Garder les fractions tant qu'aucune collision n'a modifié la position.
    if body.rect.x != round(body.pos.x):
        body.pos.x = body.rect.x
    body.pos.y += body.vy * dt
    body.rect.y = round(body.pos.y)
    body.grounded = False
    for solid in solids:
        if body.rect.colliderect(solid):
            if body.vy >= 0:
                body.rect.bottom = solid.top
                body.grounded = True
            else:
                body.rect.top = solid.bottom
            body.pos.y = body.rect.y
            body.vy = 0
    # Détecter l'appui même si le déplacement arrondi est encore nul.
    if body.vy >= 0 and any(body.rect.move(0, 1).colliderect(s) for s in solids):
        body.grounded = True
        body.vy = 0
    if body.rect.top < 140:
        body.rect.top = 140
        body.pos.y = body.rect.y
        body.vy = max(0, body.vy)


class Body:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.pos = pygame.Vector2(x, y)
        self.vy = 0.0
        self.grounded = False

    def place(self, x, bottom):
        self.rect.x = x
        self.rect.bottom = bottom
        self.pos.update(self.rect.topleft)
        self.vy = 0
        self.grounded = True
