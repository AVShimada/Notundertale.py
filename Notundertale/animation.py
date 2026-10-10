"""Lecture des poses de personnage ; l'état avance uniquement pendant la simulation."""

import pygame


class CharacterAnimation:
    WALK_FRAMES = 6

    def __init__(self, idle, frames=()):
        self.poses = {
            "idle": (idle,),
            "walk": tuple(frames[:6]) or (idle,),
            "air": tuple(frames[6:7]) or (idle,),
            "dash": tuple(frames[7:8]) or (idle,),
        }
        self.flipped = {state: tuple(pygame.transform.flip(frame, True, False) for frame in poses)
                        for state, poses in self.poses.items()}
        self.state = "idle"
        self.phase = 0.0

    @property
    def frame_index(self):
        return int(self.phase) % len(self.poses[self.state])

    def update(self, dt, distance=0.0, airborne=False, dashing=False):
        state = "dash" if dashing else "air" if airborne else "walk" if distance > 0.01 else "idle"
        if state != self.state:
            self.phase = 0.0
            self.state = state
        if state == "walk":
            # La cadence suit le déplacement réel, avec une limite pour le mode Infini.
            self.phase = (self.phase + min(distance / 28, max(0, dt) * 14)) % len(self.poses[state])
        else:
            self.phase = 0.0

    def image(self, facing_left=False):
        poses = self.flipped if facing_left else self.poses
        return poses[self.state][self.frame_index]
