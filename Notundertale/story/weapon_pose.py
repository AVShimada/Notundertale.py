"""Points d'attache communs à la posture armée et à la sortie des projectiles."""

from dataclasses import dataclass

RECOIL_PIXELS = {"rifle": 2, "raygun": 4}


@dataclass(frozen=True)
class WeaponPose:
    dx: int = 0
    dy: int = 0
    recoil: int = 0

    @property
    def origin(self):
        return 42 + self.dx - self.recoil, 47 + self.dy

    @property
    def muzzle(self):
        x, y = self.origin
        return x + 68, y + 10


def weapon_pose(player, recoil=0):
    animation = getattr(player, "animation", None)
    state = animation.state if animation else "idle"
    dx, dy = 0, 0
    if state == "walk":
        dx, dy = ((0, -1), (0, 1), (1, -1), (0, 0), (0, 1), (0, 0))[animation.frame_index]
    elif state == "air":
        dx, dy = 2, 4
    elif state == "dash":
        dx, dy = 14, 5
    if getattr(player, "skin_name", "remanent") == "default":
        dx, dy = 0, 15
    return WeaponPose(dx, dy, round(recoil))


def muzzle_position(player, recoil=0):
    """Repère local 100x100, pivot horizontal au centre du personnage."""
    x, y = weapon_pose(player, recoil).muzzle
    return (player.rect.centerx + player.facing * (x - 50),
            player.rect.bottom - 97 + y)
