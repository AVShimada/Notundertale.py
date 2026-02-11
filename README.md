A faire ajouter les mouvements d'écran etc lorsque le joueur est touché: 
✅ STEP 1 — Add Constants (Top of game.py)

Add near your imports:

# =========================
# HIT FEEDBACK
# =========================
SHAKE_DURATION_MS = 200
SHAKE_MAX_AMPLITUDE = 10
FLASH_DURATION_MS = 140
FLASH_ALPHA = 90

✅ STEP 2 — Add Timers Inside run_game()

Inside run_game(), after other state variables, add:

shake_end_time = 0
flash_end_time = 0

✅ STEP 3 — Trigger Feedback On Real Damage

Find where you handle damage:

You likely have something like:

if not player.is_invincible():
    player.decrease_health()


Change it to:

if not player.is_invincible():
    took_damage = player.decrease_health()
    if took_damage:
        shake_end_time = pygame.time.get_ticks() + SHAKE_DURATION_MS
        flash_end_time = pygame.time.get_ticks() + FLASH_DURATION_MS


Important:
Your decrease_health() must return True when damage is applied.

If it doesn’t, modify it to:

def decrease_health(self):
    if self.is_invincible():
        return False

    self.health -= 1

    if self.health <= 0:
        self.kill()

    self.invulnerable = True
    self.invulnerable_start_time = pygame.time.get_ticks()
    return True

✅ STEP 4 — Replace Normal Drawing With Frame Surface

Instead of drawing directly to screen, we use a buffer.

Inside run_game() before the loop:

frame_surface = pygame.Surface((cfg.width, cfg.height)).convert()

✅ STEP 5 — Render To frame_surface Instead of screen

Replace:

screen.blit(images.background, (0, 0))


With:

frame_surface.blit(images.background, (0, 0))


Replace all .draw(screen) with:

.draw(frame_surface)


Replace HUD blits to frame_surface.

✅ STEP 6 — Add Screen Shake

After rendering everything to frame_surface, add:

current_time = pygame.time.get_ticks()

offset_x = 0
offset_y = 0

if current_time < shake_end_time:
    remaining = shake_end_time - current_time
    t = remaining / SHAKE_DURATION_MS
    amplitude = int(SHAKE_MAX_AMPLITUDE * t)
    offset_x = random.randint(-amplitude, amplitude)
    offset_y = random.randint(-amplitude, amplitude)

screen.fill((0, 0, 0))
screen.blit(frame_surface, (offset_x, offset_y))

✅ STEP 7 — Add Red Flash Overlay

Right after the screen.blit:

if current_time < flash_end_time:
    flash = pygame.Surface((cfg.width, cfg.height), pygame.SRCALPHA)
    flash.fill((255, 0, 0, FLASH_ALPHA))
    screen.blit(flash, (0, 0))


Then:

pygame.display.flip()
