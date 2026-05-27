import pygame

from .constants import WIDTH, HEIGHT, GROUND_Y, ZONE_COUNT, ZONE_WIDTH, KICK_ATTACK_RANGE
from .constants import BOSS_HP_BAR_WIDTH, BOSS_HP_BAR_HEIGHT, CONTROLS_FADE_FRAMES


def _draw_label(screen, font, text, x, y, color):
    lbl = font.render(text, True, color)
    bg = pygame.Surface((lbl.get_width() + 6, lbl.get_height() + 4))
    bg.set_alpha(180)
    bg.fill((0, 0, 0))
    screen.blit(bg, (x - 2, y - 1))
    screen.blit(lbl, (x, y))


def _tile_blit(screen, surf, camera_x, parallax, y):
    if surf is None:
        return
    offset = int(camera_x * parallax) % surf.get_width()
    screen.blit(surf, (-offset, y))
    screen.blit(surf, (surf.get_width() - offset, y))


def draw_bg(screen, camera_x, bg_layers=None, font=None, debug_labels=False):
    screen.fill((10, 14, 26))

    if bg_layers:
        sky = bg_layers.get("sky")
        far = bg_layers.get("far")
        mid = bg_layers.get("mid")
        ground = bg_layers.get("ground")
    else:
        sky = far = mid = ground = None

    # Sky
    if sky and sky["surf"]:
        _tile_blit(screen, sky["surf"], camera_x, 0.0, 0)
    else:
        for i in range(180):
            c = (14 + int(i * 0.25), 18 + int(i * 0.2), 36 + int(i * 0.15))
            pygame.draw.line(screen, c, (0, i), (WIDTH, i))
        pygame.draw.circle(screen, (220, 225, 240), (760, 55), 22)
        pygame.draw.circle(screen, (10, 14, 26), (772, 48), 20)
        for sx, sy in [(120, 30), (300, 45), (480, 25), (600, 60), (820, 35)]:
            pygame.draw.circle(screen, (200, 210, 230), (sx, sy), 2)
    if debug_labels and font is not None:
        _draw_label(screen, font, "[sky]", 10, 10, (255, 100, 100))

    # Far layer
    far_off = int(camera_x * 0.12)
    if far and far["surf"]:
        _tile_blit(screen, far["surf"], camera_x, 0.12, 0)
    else:
        for bx, bh, bw in [(40, 180, 70), (140, 130, 55), (240, 170, 65), (340, 140, 50),
                           (430, 185, 75), (540, 120, 60), (640, 165, 70), (740, 145, 55),
                           (840, 175, 65), (940, 130, 50)]:
            bx_adj = bx - far_off
            bx_adj = bx_adj % (WIDTH * 3) - WIDTH
            pygame.draw.rect(screen, (20, 28, 48), (bx_adj, 180 - bh, bw, bh))
    if debug_labels and font is not None:
        _draw_label(screen, font, "[far]", 10, 30, (100, 255, 100))

    # Mid layer
    mid_off = int(camera_x * 0.30)
    if mid and mid["surf"]:
        _tile_blit(screen, mid["surf"], camera_x, 0.30, 140)
    else:
        for mbx, mbh, mbw, mby in [(80, 220, 80, 160), (280, 170, 70, 210),
                                   (480, 240, 90, 140), (680, 190, 75, 190),
                                   (860, 230, 85, 150)]:
            mbx_adj = mbx - mid_off
            mbx_adj = mbx_adj % (WIDTH * 3) - WIDTH
            pygame.draw.rect(screen, (28, 38, 60), (mbx_adj, mby, mbw, mbh))
            for wy in range(mby + 16, mby + mbh - 10, 22):
                for wx in range(mbx_adj + 10, mbx_adj + mbw - 10, 20):
                    lit = ((wx + wy) % 3 != 0)
                    wc = (60, 80, 130) if lit else (20, 28, 48)
                    pygame.draw.rect(screen, wc, (wx, wy, 8, 12))
    if debug_labels and font is not None:
        _draw_label(screen, font, "[mid]", 10, 150, (100, 100, 255))

    # Wall below mid, above ground
    wall_y = GROUND_Y - 90
    pygame.draw.rect(screen, (34, 44, 62), (0, wall_y, WIDTH, 90))
    for wx in range(0, WIDTH, 25):
        pygame.draw.line(screen, (40, 52, 72), (wx, wall_y), (wx + 12, wall_y + 90), 2)

    # Ground / street
    if ground and ground["surf"]:
        _tile_blit(screen, ground["surf"], camera_x, 0.0, GROUND_Y)
    else:
        ground_h = HEIGHT - GROUND_Y
        pygame.draw.rect(screen, (42, 46, 52), (0, GROUND_Y, WIDTH, ground_h))
        for i in range(0, WIDTH, 70):
            pygame.draw.rect(screen, (70, 75, 85), (i, GROUND_Y + 34, 34, 4))
        pygame.draw.rect(screen, (55, 60, 68), (0, GROUND_Y, WIDTH, 6))
        pygame.draw.rect(screen, (65, 70, 78), (0, GROUND_Y + 60, WIDTH, 8))
    if debug_labels and font is not None:
        _draw_label(screen, font, "[ground]", 10, GROUND_Y + 5, (255, 255, 100))

    # Lamp posts (always procedural accent)
    for lx in [80, 400, 720]:
        lx_adj = lx - mid_off
        lx_adj = lx_adj % (WIDTH * 3) - WIDTH
        pygame.draw.rect(screen, (50, 55, 65), (lx_adj, wall_y, 4, GROUND_Y - wall_y))
        glow = 180 + int((lx_adj * 0.3) % 40)
        pygame.draw.circle(screen, (glow, glow * 0.85, 100), (lx_adj + 2, wall_y + 4), 8)


def draw_foreground(screen, camera_x, bg_layers):
    fg = bg_layers.get("foreground")
    if fg is None or fg["surf"] is None:
        return
    _tile_blit(screen, fg["surf"], camera_x, fg["parallax"], fg["y"])


def draw_zone_dividers(screen, camera_x):
    for z in range(1, ZONE_COUNT):
        x = int(z * ZONE_WIDTH - camera_x)
        if -10 <= x <= WIDTH + 10:
            pygame.draw.line(screen, (200, 200, 200), (x, 0), (x, HEIGHT), 2)


def draw_fighter(screen, fighter, camera_x, show_attack=False, frame_surface=None):
    body = fighter.rect().copy()
    body.x -= int(camera_x)
    body.y += int(fighter.z)
    shadow_w = fighter.body_width - 16
    shadow = pygame.Rect(body.x + 8, body.bottom - 6, max(shadow_w, 8), 12)
    pygame.draw.ellipse(screen, (20, 20, 20), shadow)

    if frame_surface is not None:
        sprite = frame_surface
        if fighter.facing < 0:
            sprite = pygame.transform.flip(sprite, True, False)
        fighter.set_sprite_dimensions(sprite)
        sprite = pygame.transform.smoothscale(sprite, (fighter.sprite_width, fighter.sprite_height))
        sprite_rect = sprite.get_rect(midbottom=(body.centerx, body.bottom + fighter.sprite_offset_y))
        screen.blit(sprite, sprite_rect)
    else:
        draw_color = fighter.color if not fighter.is_dead else (90, 90, 90)
        pygame.draw.rect(screen, draw_color, body, border_radius=8)

    if fighter.is_dead:
        pygame.draw.line(screen, (210, 210, 210), (body.x + 10, body.y + 14), (body.x + 24, body.y + 28), 2)
        pygame.draw.line(screen, (210, 210, 210), (body.x + 24, body.y + 14), (body.x + 10, body.y + 28), 2)
        return
    if show_attack:
        atk = fighter.attack_box().copy()
        atk.x -= int(camera_x)
        pygame.draw.rect(screen, (255, 210, 70), atk, 2)


def draw_player(screen, player, camera_x, frame_surface=None, show_attack=False):
    if frame_surface is None:
        draw_fighter(screen, player, camera_x, show_attack=show_attack)
        return

    sprite = frame_surface
    if player.facing < 0:
        sprite = pygame.transform.flip(sprite, True, False)
    player.set_sprite_dimensions(sprite)

    body = player.rect().copy()
    body.x -= int(camera_x)
    body.y += int(player.z)
    shadow_w = player.body_width - 16
    shadow = pygame.Rect(body.x + 8, body.bottom - 6, max(shadow_w, 8), 12)
    pygame.draw.ellipse(screen, (20, 20, 20), shadow)
    sprite = pygame.transform.smoothscale(sprite, (player.sprite_width, player.sprite_height))
    sprite_rect = sprite.get_rect(midbottom=(body.centerx, body.bottom + player.sprite_offset_y))
    screen.blit(sprite, sprite_rect)

    if show_attack:
        atk = player.attack_box().copy()
        atk.x -= int(camera_x)
        pygame.draw.rect(screen, (255, 210, 70), atk, 2)


def draw_enemy_hp_bar(screen, enemy, camera_x):
    if enemy.is_dead:
        return
    body = enemy.rect()
    x = int(body.x - camera_x)
    y = body.y - 10
    w = 60
    h = 6
    pygame.draw.rect(screen, (15, 15, 18), (x, y, w, h), border_radius=3)
    fill_w = int(w * max(0, enemy.hp) / max(1, enemy.max_hp))
    color = (86, 154, 236) if not enemy.is_boss else (210, 110, 240)
    pygame.draw.rect(screen, color, (x, y, fill_w, h), border_radius=3)


def draw_boss_hp_bar(screen, font, enemies, camera_x):
    boss = None
    for e in enemies:
        if e.is_boss and not e.is_dead:
            boss = e
            break
    if boss is None:
        return

    bar_x = (WIDTH - BOSS_HP_BAR_WIDTH) // 2
    bar_y = 60
    bar_w = BOSS_HP_BAR_WIDTH
    bar_h = BOSS_HP_BAR_HEIGHT

    pygame.draw.rect(screen, (20, 20, 28), (bar_x - 2, bar_y - 2, bar_w + 4, bar_h + 4), border_radius=6)
    fill_w = int(bar_w * max(0, boss.hp) / max(1, boss.max_hp))
    hp_color = (210, 110, 240)
    pygame.draw.rect(screen, hp_color, (bar_x, bar_y, fill_w, bar_h), border_radius=4)

    if font is not None:
        label = font.render(f"BOSS", True, (255, 220, 255))
        screen.blit(label, (WIDTH // 2 - label.get_width() // 2, bar_y - 18))
        hp_text = font.render(f"{max(0, boss.hp)}/{boss.max_hp}", True, (255, 255, 255))
        screen.blit(hp_text, (WIDTH // 2 - hp_text.get_width() // 2, bar_y + bar_h + 4))


def draw_player_free_attack_hitbox(screen, player, camera_x, active):
    if not active:
        return
    hitbox = player.radial_attack_box(radius=58 if player.jump_attack_active else 46).copy()
    hitbox.x -= int(camera_x)
    hitbox.y += int(player.z)
    pygame.draw.ellipse(screen, (255, 220, 110), hitbox, 2)


def draw_player_kick_hitbox(screen, player, camera_x, active):
    if not active:
        return
    hitbox = player.radial_attack_box(radius=KICK_ATTACK_RANGE).copy()
    hitbox.x -= int(camera_x)
    hitbox.y += int(player.z)
    pygame.draw.ellipse(screen, (255, 220, 110), hitbox, 2)


def draw_score_popups(screen, camera_x, popups, font):
    if font is None:
        return
    for p in popups:
        alpha = max(0, int(255 * p["timer"] / 30))
        sx = int(p["x"] - camera_x)
        sy = int(p["y"])
        color = (255, 215, 100)
        if alpha < 255:
            color = tuple(max(0, c * alpha // 255) for c in color)
        text = font.render(p["text"], True, color)
        screen.blit(text, (sx - text.get_width() // 2, sy))


def draw_ui(screen, font, player, enemies, state, combo_indicator):
    hp_bar_w = 280
    hp_bar_h = 24
    hp_bar_x = 20
    hp_bar_y = 20

    pygame.draw.rect(screen, (12, 12, 16), (hp_bar_x, hp_bar_y, hp_bar_w, hp_bar_h), border_radius=8)
    fill_w = int(hp_bar_w * max(0, player.hp) / max(1, player.max_hp))
    hp_color = (200, 70, 70)
    if player.hp < 30:
        hp_color = (220, 180, 50)
    pygame.draw.rect(screen, hp_color, (hp_bar_x, hp_bar_y, fill_w, hp_bar_h), border_radius=8)

    lives_y = 52
    for i in range(state.player_lives):
        pygame.draw.rect(screen, (220, 70, 90), (hp_bar_x + i * 22, lives_y, 16, 12), border_radius=3)

    power_y = lives_y + 22
    power_bg_w = 220
    power_bg_h = 14
    pygame.draw.rect(screen, (12, 12, 16), (hp_bar_x, power_y, power_bg_w, power_bg_h), border_radius=6)
    power_fill = int(power_bg_w * state.power_meter / 100)
    pygame.draw.rect(screen, (100, 200, 255), (hp_bar_x, power_y, power_fill, power_bg_h), border_radius=6)

    zone_box_x = WIDTH - 180
    zone_box_y = 20
    pygame.draw.rect(screen, (16, 16, 22), (zone_box_x - 10, zone_box_y - 4, 170, 96), border_radius=6)

    if font is None:
        return

    text_y = hp_bar_y + hp_bar_h + 6
    controls_alpha = max(0, min(255, 255 - int(255 * state.controls_timer / CONTROLS_FADE_FRAMES)))
    if controls_alpha > 10:
        c_surf = pygame.Surface((600, 20), pygame.SRCALPHA)
        c_text = font.render("WASD move | J attack | K kick | L power | Space jump | R restart", True, (236, 236, 236))
        c_surf.blit(c_text, (0, 0))
        c_surf.set_alpha(controls_alpha)
        screen.blit(c_surf, (hp_bar_x, text_y))

    text_y += 18
    screen.blit(font.render(f"STAGE {state.total_stage}", True, (245, 230, 180)), (hp_bar_x, text_y))

    if state.combat_active:
        text_y += 18
        screen.blit(font.render(f"Wave {state.wave_index}/{state.waves_per_zone}", True, (255, 210, 150)), (hp_bar_x, text_y))

    text_y = power_y + power_bg_h + 6
    screen.blit(font.render(f"POWER {state.power_meter}/100", True, (170, 225, 255)), (hp_bar_x, text_y))

    text_y += 18
    screen.blit(font.render(f"Combo: {combo_indicator}", True, (255, 220, 140)), (hp_bar_x, text_y))

    text_y += 18
    screen.blit(font.render(f"Score: {state.score}", True, (255, 215, 100)), (hp_bar_x, text_y))

    screen.blit(font.render("ZONES", True, (200, 200, 200)), (zone_box_x, zone_box_y))
    for i, status in enumerate(state.zone_status):
        status_colors = {
            "SAFE": (140, 220, 140),
            "OPEN": (100, 180, 255),
            "ACTIVE": (255, 210, 80),
            "CLEARED": (120, 200, 120),
            "LOCKED": (80, 80, 80),
        }
        c = status_colors.get(status, (180, 180, 180))
        dot_r = 4
        dot_x = zone_box_x
        dot_y = zone_box_y + 20 + i * 18
        pygame.draw.circle(screen, c, (dot_x + dot_r, dot_y + dot_r), dot_r)
        screen.blit(font.render(f"Z{i + 1} {status}", True, c), (dot_x + 14, dot_y))


def draw_zone_indicator(screen, font, zone_idx):
    if zone_idx < 0 or zone_idx >= ZONE_COUNT:
        return
    box_w, box_h = 180, 34
    box_x = WIDTH // 2 - box_w // 2
    box_y = 16
    pygame.draw.rect(screen, (12, 12, 16), (box_x, box_y, box_w, box_h), border_radius=8)
    pygame.draw.rect(screen, (200, 200, 200), (box_x, box_y, box_w, box_h), 2, border_radius=8)
    if font is not None:
        text = font.render(f"ZONE {zone_idx + 1}", True, (236, 236, 236))
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, box_y + 7))


def draw_spawn_text(screen, font, active):
    if not active or font is None:
        return
    text = font.render("SPAWNING...", True, (255, 230, 180))
    screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT - 48))


def draw_stage_complete_screen(screen, font, state):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    screen.blit(overlay, (0, 0))

    if font is None:
        return

    title = font.render(f"STAGE {state.total_stage} COMPLETE", True, (255, 215, 100))
    shadow = font.render(f"STAGE {state.total_stage} COMPLETE", True, (0, 0, 0))
    tx = WIDTH // 2 - title.get_width() // 2
    ty = 120
    screen.blit(shadow, (tx + 2, ty + 2))
    screen.blit(title, (tx, ty))

    stats_y = ty + 50
    stats = [
        f"Score this stage: {state.stage_score}",
        f"Enemies defeated: {state.enemies_killed_this_stage}",
        f"Total score: {state.score}",
        f"Lives remaining: {state.player_lives}",
    ]
    for stat in stats:
        s = font.render(stat, True, (220, 220, 220))
        screen.blit(s, (WIDTH // 2 - s.get_width() // 2, stats_y))
        stats_y += 26

    prompt = font.render("Press J to continue to next stage", True, (255, 245, 200))
    px = WIDTH // 2 - prompt.get_width() // 2
    screen.blit(prompt, (px, HEIGHT - 100))

    info = font.render(f"Stage {state.total_stage + 1} - difficulty +{int((state.total_stage) * 15)}%", True, (180, 200, 220))
    screen.blit(info, (WIDTH // 2 - info.get_width() // 2, HEIGHT - 70))


def draw_game_over_screen(screen, font, state):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))

    if font is None:
        return

    title = font.render("GAME OVER", True, (255, 80, 80))
    shadow = font.render("GAME OVER", True, (0, 0, 0))
    tx = WIDTH // 2 - title.get_width() // 2
    ty = 140
    screen.blit(shadow, (tx + 2, ty + 2))
    screen.blit(title, (tx, ty))

    stats_y = ty + 50
    lines = [
        f"Final Score: {state.score}",
        f"Stage reached: {state.total_stage}",
    ]
    for line in lines:
        s = font.render(line, True, (220, 220, 220))
        screen.blit(s, (WIDTH // 2 - s.get_width() // 2, stats_y))
        stats_y += 26

    prompt = font.render("Press R to restart", True, (255, 245, 200))
    px = WIDTH // 2 - prompt.get_width() // 2
    screen.blit(prompt, (px, HEIGHT - 100))


def draw_debug_menu(screen, font, state):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))

    if font is None:
        return

    title = font.render("DEBUG SETTINGS", True, (255, 215, 100))
    tx = WIDTH // 2 - title.get_width() // 2
    screen.blit(title, (tx, 80))

    items = [
        ("BG Layer Labels", "debug_show_labels"),
        ("Attack Hitboxes", "debug_show_hitboxes"),
        ("Zone Dividers", "debug_show_zone_dividers"),
        ("Zone Indicator", "debug_show_zone_indicator"),
        ("Spawn Text", "debug_show_spawn_text"),
    ]

    start_y = 120
    for i, (label, key) in enumerate(items):
        val = getattr(state, key)
        color = (255, 255, 255) if i == state.debug_menu_selection else (180, 180, 180)
        indicator = "[ON]" if val else "[OFF]"
        indicator_color = (100, 255, 100) if val else (255, 100, 100)
        prefix = "> " if i == state.debug_menu_selection else "  "
        line = font.render(f"{prefix}{label} {indicator}", True, color)
        screen.blit(line, (WIDTH // 2 - line.get_width() // 2, start_y + i * 28))
        if i == state.debug_menu_selection:
            pygame.draw.rect(screen, indicator_color,
                             (WIDTH // 2 - line.get_width() // 2 - 4,
                              start_y + i * 28 - 2,
                              line.get_width() + 8, 22), 1)

    hint = font.render("UP/DOWN navigate | J toggle | F1 close", True, (140, 140, 140))
    screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 80))
