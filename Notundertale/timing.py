"""Horloge commune aux scores, au dash, aux bonus et aux projectiles."""

import pygame


class GameClock:
    def __init__(self, ticks=None):
        self._ticks = ticks or pygame.time.get_ticks
        self.reset()

    def reset(self):
        self._started = self._ticks()
        self._paused_at = None
        self._paused_total = 0

    def now(self):
        current = self._paused_at if self._paused_at is not None else self._ticks()
        return current - self._started - self._paused_total

    def pause(self):
        if self._paused_at is None:
            self._paused_at = self._ticks()

    def resume(self):
        if self._paused_at is not None:
            self._paused_total += self._ticks() - self._paused_at
            self._paused_at = None
