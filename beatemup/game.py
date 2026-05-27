import random
import json
from pathlib import Path
import pygame
from PIL import Image

from .constants import (
    WIDTH,
    HEIGHT,
    GROUND_Y,
    FPS,
    ZONE_COUNT,
    ZONE_WIDTH,
    WORLD_WIDTH,
    PLAYER_SPAWN_X,
    PLAYER_SPAWN_Y,
    DOUBLE_TAP_WINDOW_MS,
    SPRINT_DURATION_FRAMES,
    COMBO_TAP_WINDOW_FRAMES,
    SPAWN_ANIM_FRAMES,
    JUMP_VELOCITY,
    POWER_GAIN_ON_HIT,
    POWER_MAX,
    POWER_SKILL_COST,
    PLAYER_COLOR,
    ENEMY_COLOR,
    BOSS_COLOR,
    BOSS_HP,
    SCORE_PER_ENEMY,
    SCORE_PER_BOSS,
    SCORE_PER_STAGE_COMPLETE,
    SCORE_POPUP_DURATION,
    CONTROLS_FADE_FRAMES,
    KICK_DAMAGE,
    KICK_BOSS_DAMAGE,
    KICK_COOLDOWN_FRAMES,
    KICK_ATTACK_RANGE,
    KICK_KNOCKBACK,
    KICK_HITSTUN,
)
from .models import Fighter, GameState
from .systems import (
    handle_player_input,
    get_zone_for_x,
    update_camera_x,
    enemy_ai,
    try_attack,
    try_free_attack,
    try_kick_attack,
    try_attack_with_miss_logic,
    apply_hit_reaction,
    spawn_enemy_wave,
    spawn_boss,
    zone_bounds,
    update_jump,
)

from .render import (
    draw_bg,
    draw_foreground,
    draw_zone_dividers,
    draw_player,
    draw_fighter,
    draw_enemy_hp_bar,
    draw_player_free_attack_hitbox,
    draw_player_kick_hitbox,
    draw_ui,
    draw_zone_indicator,
    draw_spawn_text,
    draw_stage_complete_screen,
    draw_game_over_screen,
    draw_boss_hp_bar,
    draw_score_popups,
    draw_debug_menu,
)


def combo_indicator_text(combo_taps):
    combo_tokens = ["j", "j", "j"]
    for i in range(combo_taps):
        combo_tokens[i] = "J"
    return " ".join(combo_tokens)


def make_player(x=PLAYER_SPAWN_X, y=PLAYER_SPAWN_Y):
    return Fighter(x=x, y=y, color=PLAYER_COLOR, hp=100, max_hp=100)


def reset_run(state: GameState):
    state.active_zone = 0
    state.unlocked_zone = 1
    state.next_encounter_zone = 1
    state.combat_active = False
    state.game_cleared = False
    state.game_over = False
    state.player_lives = 3
    state.camera_x = 0.0
    state.combo_taps = 0
    state.combo_timer = 0
    state.player_attack_timer = 0
    state.player_attack_hit_latch = False
    state.sprint_timer = 0
    state.last_tap_left_ms = -1000
    state.last_tap_right_ms = -1000
    state.show_attack_flash = 0
    state.spawn_timer = SPAWN_ANIM_FRAMES
    state.power_meter = 0
    state.wave_index = 0
    state.waves_per_zone = 3
    state.total_stage = 1
    state.score = 0
    state.stage_complete = False
    state.stage_score = 0
    state.enemies_killed_this_stage = 0
    state.score_popups = []
    state.controls_timer = 0
    state.zone_status = ["SAFE", "OPEN", "LOCKED", "LOCKED"]


def begin_zone_encounter(state: GameState, zone_idx: int):
    state.combat_active = True
    state.active_zone = zone_idx
    state.zone_status[zone_idx] = "ACTIVE"
    state.wave_index = 1


def complete_zone_encounter(state: GameState):
    zone_idx = state.active_zone
    state.combat_active = False
    state.zone_status[zone_idx] = "CLEARED"

    state.score += SCORE_PER_STAGE_COMPLETE
    state.stage_score += SCORE_PER_STAGE_COMPLETE

    if zone_idx + 1 < ZONE_COUNT:
        state.next_encounter_zone = zone_idx + 1
        state.unlocked_zone = max(state.unlocked_zone, zone_idx + 1)
        if state.zone_status[zone_idx + 1] == "LOCKED":
            state.zone_status[zone_idx + 1] = "OPEN"
        state.active_zone = zone_idx + 1
    else:
        state.stage_complete = True
        state.game_cleared = True


def advance_to_next_stage(state: GameState, player):
    state.total_stage += 1
    state.game_cleared = False
    state.stage_complete = False
    state.stage_score = 0
    state.enemies_killed_this_stage = 0
    state.score_popups = []
    state.combat_active = False
    state.active_zone = 0
    state.next_encounter_zone = 1
    state.unlocked_zone = 1
    state.wave_index = 0
    state.zone_status = ["SAFE", "OPEN", "LOCKED", "LOCKED"]
    state.camera_x = 0.0
    state.power_meter = 0
    state.spawn_timer = SPAWN_ANIM_FRAMES
    player.x = PLAYER_SPAWN_X
    player.y = PLAYER_SPAWN_Y
    player.hp = player.max_hp
    player.is_dead = False
    player.knockback_x = 0.0
    player.hitstun = 0
    player.score = state.score


def spawn_wave_for_zone(state: GameState):
    if state.active_zone == ZONE_COUNT - 1:
        # Final zone: first 2 waves are regular enemies, wave 3 is boss.
        if state.wave_index >= state.waves_per_zone:
            return [spawn_boss(state.active_zone, BOSS_COLOR, BOSS_HP, state.total_stage)]
        return spawn_enemy_wave(state.active_zone, ENEMY_COLOR, state.total_stage)
    return spawn_enemy_wave(state.active_zone, ENEMY_COLOR, state.total_stage)


def log_asset_diagnostics(project_root: Path):
    exports_dir = project_root / "assets" / "exports"
    sprites_dir = project_root / "assets" / "sprites" / "player"
    sheet_path = exports_dir / "player_sheet.png"
    meta_path = exports_dir / "player_sheet.json"
    raw_walk = sorted(sprites_dir.glob("walk_*.png"))
    raw_idle = sorted(sprites_dir.glob("idle_*.png"))

    print("[beatemup][assets] project_root:", project_root)
    print("[beatemup][assets] sheet exists:", sheet_path.exists(), sheet_path)
    print("[beatemup][assets] meta exists:", meta_path.exists(), meta_path)
    print("[beatemup][assets] raw walk count:", len(raw_walk))
    if raw_walk:
        print("[beatemup][assets] raw walk sample:", raw_walk[0].name, raw_walk[-1].name)
    print("[beatemup][assets] raw idle count:", len(raw_idle))
    if raw_idle:
        print("[beatemup][assets] raw idle sample:", raw_idle[0].name, raw_idle[-1].name)


def load_surface_any(path: Path):
    # First try pygame's native loader.
    try:
        loaded = pygame.image.load(str(path))
        try:
            return loaded.convert_alpha()
        except Exception:
            return loaded.convert()
    except Exception:
        pass

    # Fallback: decode via Pillow, then create a pygame surface.
    img = Image.open(path).convert("RGBA")
    mode = img.mode
    size = img.size
    data = img.tobytes()
    surface = pygame.image.fromstring(data, size, mode)
    return surface.convert_alpha()


def load_player_walk_frames(project_root: Path):
    walk_frames = []
    sheet_path = project_root / "assets" / "exports" / "player_sheet.png"
    meta_path = project_root / "assets" / "exports" / "player_sheet.json"

    try:
        if sheet_path.exists() and meta_path.exists():
            sprite_sheet = load_surface_any(sheet_path)
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            walk_entries = []
            for f in meta.get("frames", []):
                anim = str(f.get("animation", "")).lower()
                name = str(f.get("name", ""))
                if anim == "walk" or name.lower().startswith("walk_"):
                    rect = pygame.Rect(f["x"], f["y"], f["w"], f["h"])
                    frame = sprite_sheet.subsurface(rect).copy()
                    walk_entries.append((name, frame))
            if not walk_entries:
                for f in meta.get("frames", []):
                    rect = pygame.Rect(f["x"], f["y"], f["w"], f["h"])
                    frame = sprite_sheet.subsurface(rect).copy()
                    walk_entries.append((str(f.get("name", "")), frame))
            walk_entries.sort(key=lambda item: item[0])
            walk_frames = [frame for _, frame in walk_entries]
            if walk_frames:
                print(f"[beatemup] loaded {len(walk_frames)} walk frames from exported sheet")
                return walk_frames
            print("[beatemup] exported sheet loaded but no walk frames resolved")
    except Exception as e:
        print(f"[beatemup] export sheet load failed: {e}")

    # Fallback: direct raw frame files.
    try:
        raw_dir = project_root / "assets" / "sprites" / "player"
        raw_paths = sorted(raw_dir.glob("walk_*.png"))
        for p in raw_paths:
            walk_frames.append(load_surface_any(p))
        if walk_frames:
            print(f"[beatemup] loaded {len(walk_frames)} walk frames from raw sprites folder")
            return walk_frames
    except Exception as e:
        print(f"[beatemup] raw walk frame load failed: {e}")

    print("[beatemup] no player walk frames found; using rectangle fallback")
    return []


def load_player_idle_frames(project_root: Path):
    idle_frames = []
    sheet_path = project_root / "assets" / "exports" / "player_sheet.png"
    meta_path = project_root / "assets" / "exports" / "player_sheet.json"

    try:
        if sheet_path.exists() and meta_path.exists():
            sprite_sheet = load_surface_any(sheet_path)
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            idle_entries = []
            for f in meta.get("frames", []):
                anim = str(f.get("animation", "")).lower()
                name = str(f.get("name", ""))
                if anim == "idle" or name.lower().startswith("idle_"):
                    rect = pygame.Rect(f["x"], f["y"], f["w"], f["h"])
                    frame = sprite_sheet.subsurface(rect).copy()
                    idle_entries.append((name, frame))
            idle_entries.sort(key=lambda item: item[0])
            idle_frames = [frame for _, frame in idle_entries]
            if idle_frames:
                print(f"[beatemup] loaded {len(idle_frames)} idle frames from exported sheet")
                return idle_frames
            # If no idle frames in sheet, fall through to raw
    except Exception as e:
        print(f"[beatemup] export sheet load failed: {e}")

    # Fallback: direct raw frame files.
    try:
        raw_dir = project_root / "assets" / "sprites" / "player"
        raw_paths = sorted(raw_dir.glob("idle_*.png"))
        for p in raw_paths:
            idle_frames.append(load_surface_any(p))
        if idle_frames:
            print(f"[beatemup] loaded {len(idle_frames)} idle frames from raw sprites folder")
            return idle_frames
    except Exception as e:
        print(f"[beatemup] raw idle frame load failed: {e}")

    print("[beatemup] no player idle frames found; using rectangle fallback")
    return []


def load_player_attack_frames(project_root):
    attack_frames = []
    sheet_path = project_root / "assets" / "exports" / "player_sheet.png"
    meta_path = project_root / "assets" / "exports" / "player_sheet.json"

    try:
        if sheet_path.exists() and meta_path.exists():
            sprite_sheet = load_surface_any(sheet_path)
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            attack_entries = []
            for f in meta.get("frames", []):
                anim = str(f.get("animation", "")).lower()
                name = str(f.get("name", ""))
                if anim == "attack_a" or name.lower().startswith("attack_a_"):
                    rect = pygame.Rect(f["x"], f["y"], f["w"], f["h"])
                    frame = sprite_sheet.subsurface(rect).copy()
                    attack_entries.append((name, frame))
            attack_entries.sort(key=lambda item: item[0])
            attack_frames = [frame for _, frame in attack_entries]
            if attack_frames:
                print(f"[beatemup] loaded {len(attack_frames)} attack frames from exported sheet")
                return attack_frames
    except Exception as e:
        print(f"[beatemup] export sheet attack load failed: {e}")

    try:
        raw_dir = project_root / "assets" / "sprites" / "player"
        raw_paths = sorted(raw_dir.glob("attack_a_*.png"))
        for p in raw_paths:
            attack_frames.append(load_surface_any(p))
        if attack_frames:
            print(f"[beatemup] loaded {len(attack_frames)} attack frames from raw sprites folder")
            return attack_frames
    except Exception as e:
        print(f"[beatemup] raw attack frame load failed: {e}")

    print("[beatemup] no player attack frames found")
    return []


def load_player_run_frames(project_root):
    run_frames = []
    sheet_path = project_root / "assets" / "exports" / "player_sheet.png"
    meta_path = project_root / "assets" / "exports" / "player_sheet.json"

    try:
        if sheet_path.exists() and meta_path.exists():
            sprite_sheet = load_surface_any(sheet_path)
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            run_entries = []
            for f in meta.get("frames", []):
                anim = str(f.get("animation", "")).lower()
                name = str(f.get("name", ""))
                if anim == "run" or name.lower().startswith("run_"):
                    rect = pygame.Rect(f["x"], f["y"], f["w"], f["h"])
                    frame = sprite_sheet.subsurface(rect).copy()
                    run_entries.append((name, frame))
            run_entries.sort(key=lambda item: item[0])
            run_frames = [frame for _, frame in run_entries]
            if run_frames:
                print(f"[beatemup] loaded {len(run_frames)} run frames from exported sheet")
                return run_frames
    except Exception as e:
        print(f"[beatemup] export sheet run load failed: {e}")

    try:
        raw_dir = project_root / "assets" / "sprites" / "player"
        raw_paths = sorted(raw_dir.glob("run_*.png"))
        for p in raw_paths:
            run_frames.append(load_surface_any(p))
        if run_frames:
            print(f"[beatemup] loaded {len(run_frames)} run frames from raw sprites folder")
            return run_frames
    except Exception as e:
        print(f"[beatemup] raw run frame load failed: {e}")

    print("[beatemup] no player run frames found")
    return []


def load_enemy_frames(project_root):
    frames = {"fly": [], "attack": [], "death": []}
    enemy_dir = project_root / "assets" / "sprites" / "enemy"
    try:
        paths = sorted(enemy_dir.glob("*.png"))
        for p in paths:
            name = p.stem.lower()
            for cat in frames:
                if cat in name:
                    frames[cat].append(load_surface_any(p))
                    break
        total = sum(len(v) for v in frames.values())
        if total:
            details = ", ".join(f"{k}={len(v)}" for k, v in frames.items() if v)
            print(f"[beatemup] loaded {total} enemy frames ({details})")
            return frames
    except Exception as e:
        print(f"[beatemup] enemy frame load failed: {e}")
    print("[beatemup] no enemy frames found; using rectangle fallback")
    return frames


def load_background_assets(project_root):
    layers = {}
    bg_dir = project_root / "assets" / "backgrounds"
    expected = {
        "sky": {"parallax": 0.0, "y": 0},
        "far": {"parallax": 0.12, "y": 0},
        "mid": {"parallax": 0.30, "y": 140},
        "ground": {"parallax": 0.0, "y": GROUND_Y},
        "foreground": {"parallax": 0.60, "y": 0},
    }
    for name, info in expected.items():
        path = bg_dir / f"{name}.png"
        if not path.exists():
            for p in bg_dir.iterdir():
                if p.suffix.lower() == ".png" and p.stem.lower() == name:
                    path = p
                    break
        try:
            surf = load_surface_any(path)
            # Scale width to match game, keep aspect ratio
            if surf.get_width() != WIDTH:
                new_h = int(surf.get_height() * WIDTH / surf.get_width())
                surf = pygame.transform.smoothscale(surf, (WIDTH, new_h))
            # Crop to the visible height for this layer
            crop_h = min(HEIGHT - info["y"], surf.get_height())
            if crop_h < surf.get_height():
                surf = surf.subsurface(0, surf.get_height() - crop_h, WIDTH, crop_h).copy()
            layers[name] = {"surf": surf, **info}
            print(f"[beatemup] loaded bg layer: {name} ({surf.get_width()}x{surf.get_height()})")
        except Exception:
            layers[name] = None
    return layers


def run_game():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Beat 'Em Up Starter | Move: WASD/Arrows Attack: J Restart: R")
    clock = pygame.time.Clock()

    font = None
    try:
        from pygame._freetype import Font as _FtFont, init as _ft_init
        _ft_init()
        class _FontWrapper:
            def __init__(self, file, size):
                self._f = _FtFont(file, size)
            def render(self, text, antialias, color, background=None):
                s, _ = self._f.render(text, color, background)
                return s
        font = _FontWrapper(None, 20)
    except Exception:
        font = None

    state = GameState()
    reset_run(state)
    player = make_player()
    enemies = []
    alive_enemies = []
    walk_frames = []
    walk_anim_idx = 0
    walk_anim_timer = 0
    idle_frames = []
    idle_anim_idx = 0
    idle_anim_timer = 0
    attack_frames = []
    attack_anim_idx = 0
    attack_anim_timer = 0
    run_frames = []
    run_anim_idx = 0
    run_anim_timer = 0
    enemy_frames = {"fly": [], "attack": [], "death": []}
    prev_player_pos = (player.x, player.y)
    animation_debug_counter = 0

    project_root = Path(__file__).resolve().parent.parent
    log_asset_diagnostics(project_root)
    walk_frames = load_player_walk_frames(project_root)
    idle_frames = load_player_idle_frames(project_root)
    attack_frames = load_player_attack_frames(project_root)
    run_frames = load_player_run_frames(project_root)
    enemy_frames = load_enemy_frames(project_root)
    bg_layers = load_background_assets(project_root)

    running = True
    while running:
        clock.tick(FPS)
        keys = pygame.key.get_pressed()
        is_moving_input = (
            keys[pygame.K_a] or keys[pygame.K_d] or
            keys[pygame.K_LEFT] or keys[pygame.K_RIGHT] or
            keys[pygame.K_w] or keys[pygame.K_s] or
            keys[pygame.K_UP] or keys[pygame.K_DOWN]
        )

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F1:
                    state.debug_menu_open = not state.debug_menu_open
                    state.debug_menu_selection = 0
                    continue
                if state.debug_menu_open:
                    options = ["debug_show_labels", "debug_show_hitboxes", "debug_show_zone_dividers", "debug_show_zone_indicator", "debug_show_spawn_text"]
                    if event.key == pygame.K_UP:
                        state.debug_menu_selection = max(0, state.debug_menu_selection - 1)
                    elif event.key == pygame.K_DOWN:
                        state.debug_menu_selection = min(len(options) - 1, state.debug_menu_selection + 1)
                    elif event.key == pygame.K_j:
                        sel = state.debug_menu_selection
                        if 0 <= sel < len(options):
                            setattr(state, options[sel], not getattr(state, options[sel]))
                    continue
                if state.stage_complete:
                    if event.key == pygame.K_j:
                        advance_to_next_stage(state, player)
                        enemies = []
                    continue
                if state.game_over:
                    if event.key == pygame.K_r:
                        reset_run(state)
                        player = make_player()
                        enemies = []
                        walk_anim_idx = 0
                        walk_anim_timer = 0
                        idle_anim_idx = 0
                        idle_anim_timer = 0
                        run_anim_idx = 0
                        run_anim_timer = 0
                        prev_player_pos = (player.x, player.y)
                    continue

                now_ms = pygame.time.get_ticks()
                if event.key in (pygame.K_a, pygame.K_LEFT):
                    if now_ms - state.last_tap_left_ms <= DOUBLE_TAP_WINDOW_MS:
                        state.sprint_timer = SPRINT_DURATION_FRAMES
                    state.last_tap_left_ms = now_ms
                elif event.key in (pygame.K_d, pygame.K_RIGHT):
                    if now_ms - state.last_tap_right_ms <= DOUBLE_TAP_WINDOW_MS:
                        state.sprint_timer = SPRINT_DURATION_FRAMES
                    state.last_tap_right_ms = now_ms

                if event.key == pygame.K_j:
                    state.player_attack_timer = 10
                    state.player_attack_hit_latch = False
                    player.jump_attack_active = player.is_jumping
                    if state.combo_timer > 0:
                        state.combo_taps = min(3, state.combo_taps + 1)
                    else:
                        state.combo_taps = 1
                    state.combo_timer = COMBO_TAP_WINDOW_FRAMES
                elif event.key == pygame.K_SPACE:
                    if not player.is_jumping and state.spawn_timer == 0:
                        player.is_jumping = True
                        player.vz = JUMP_VELOCITY
                        player.z = -1
                elif event.key == pygame.K_k:
                    if player.attack_cooldown <= 0:
                        player.attack_cooldown = KICK_COOLDOWN_FRAMES
                        state.player_kick_active = 8
                        hits = 0
                        for enemy in alive_enemies:
                            damage = KICK_BOSS_DAMAGE if enemy.is_boss else KICK_DAMAGE
                            if try_kick_attack(
                                player,
                                enemy,
                                damage=damage,
                                knockback=KICK_KNOCKBACK,
                                hitstun=KICK_HITSTUN,
                                radius=KICK_ATTACK_RANGE,
                                consume_cooldown=False,
                            ):
                                hits += 1
                        if hits > 0:
                            state.show_attack_flash = 3
                            state.power_meter = min(POWER_MAX, state.power_meter + POWER_GAIN_ON_HIT * hits)
                elif event.key == pygame.K_l:
                    if state.power_meter >= POWER_SKILL_COST:
                        hits = 0
                        for enemy in [e for e in enemies if not e.is_dead]:
                            if try_free_attack(
                                player,
                                enemy,
                                damage=36 if enemy.is_boss else 42,
                                knockback=18.0,
                                hitstun=22,
                                radius=250,
                                consume_cooldown=False,
                            ):
                                hits += 1
                        if hits > 0:
                            state.show_attack_flash = 8
                        state.power_meter = 0
                elif event.key == pygame.K_r:
                    reset_run(state)
                    player = make_player()
                    enemies = []
                    walk_anim_idx = 0
                    walk_anim_timer = 0
                    idle_anim_idx = 0
                    idle_anim_timer = 0
                    attack_anim_idx = 0
                    attack_anim_timer = 0
                    run_anim_idx = 0
                    run_anim_timer = 0
                    prev_player_pos = (player.x, player.y)
                    state.score_popups = []

        player_frame = None
        combo_indicator = combo_indicator_text(state.combo_taps)

        if not state.debug_menu_open:
            if state.spawn_timer > 0:
                state.spawn_timer -= 1

            player_zone = get_zone_for_x(player.x)
            if not state.combat_active and not state.stage_complete:
                state.active_zone = min(player_zone, state.unlocked_zone)

            if not state.combat_active and not state.stage_complete and state.next_encounter_zone < ZONE_COUNT:
                if player_zone >= state.next_encounter_zone:
                    begin_zone_encounter(state, state.next_encounter_zone)
                    enemies = spawn_wave_for_zone(state)

            if state.combat_active:
                zone_min_x, zone_max_x = zone_bounds(state.active_zone)
            else:
                zone_min_x = 10
                zone_max_x = min(WORLD_WIDTH - 70, (state.unlocked_zone + 1) * ZONE_WIDTH - 70)

            if state.spawn_timer == 0 and not state.game_over and not state.stage_complete:
                handle_player_input(keys, player, min_x=zone_min_x, max_x=zone_max_x, sprint_active=state.sprint_timer > 0)
                update_jump(player)

            moved_dist = abs(player.x - prev_player_pos[0]) + abs(player.y - prev_player_pos[1])
            is_sprinting = state.sprint_timer > 0
            is_walking = is_moving_input and not player.is_jumping and not is_sprinting
            is_running = is_moving_input and not player.is_jumping and is_sprinting
            if walk_frames and is_walking:
                walk_anim_timer += 1
                if walk_anim_timer >= 6:
                    walk_anim_timer = 0
                    walk_anim_idx = (walk_anim_idx + 1) % len(walk_frames)
            elif walk_frames:
                walk_anim_idx = 0
                walk_anim_timer = 0

            if run_frames and is_running:
                run_anim_timer += 1
                if run_anim_timer >= 4:
                    run_anim_timer = 0
                    run_anim_idx = (run_anim_idx + 1) % len(run_frames)
            elif run_frames:
                run_anim_idx = 0
                run_anim_timer = 0

            if idle_frames and not is_walking:
                idle_anim_timer += 1
                if idle_anim_timer >= 12:
                    idle_anim_timer = 0
                    idle_anim_idx = (idle_anim_idx + 1) % len(idle_frames)
            elif idle_frames:
                idle_anim_idx = 0
                idle_anim_timer = 0

            if attack_frames and state.player_attack_timer > 0:
                attack_anim_timer += 1
                step = max(1, 10 // len(attack_frames))
                if attack_anim_timer >= step:
                    attack_anim_timer = 0
                    attack_anim_idx = (attack_anim_idx + 1) % len(attack_frames)
            elif attack_frames:
                attack_anim_idx = 0
                attack_anim_timer = 0

            prev_player_pos = (player.x, player.y)

            if attack_frames and state.player_attack_timer > 0:
                player_frame = attack_frames[attack_anim_idx]
            elif is_running and run_frames:
                player_frame = run_frames[run_anim_idx]
            elif is_walking and walk_frames:
                player_frame = walk_frames[walk_anim_idx]
            elif idle_frames:
                player_frame = idle_frames[idle_anim_idx]
            else:
                player_frame = None
            player.set_sprite_dimensions(player_frame)

            state.camera_x = update_camera_x(state.camera_x, player.x)

            enemy_zone_min_x, enemy_zone_max_x = zone_bounds(state.active_zone)
            alive_enemies = []
            dead_enemies = []
            for enemy in enemies:
                if enemy.is_dead:
                    dead_enemies.append(enemy)
                else:
                    alive_enemies.append(enemy)

            for enemy in alive_enemies:
                enemy_ai(enemy, player, enemy_zone_min_x, enemy_zone_max_x, all_enemies=alive_enemies)
                apply_hit_reaction(enemy, min_x=enemy_zone_min_x, max_x=enemy_zone_max_x)

                in_range = abs(enemy.x - player.x) < 72 and abs(enemy.y - player.y) < 30
                if in_range:
                    if enemy.attack_cooldown <= 0:
                        enemy.anim_state = "attack"
                        enemy.anim_frame = 0
                        enemy.anim_timer = 0
                    try_attack_with_miss_logic(enemy, player, damage=14 if enemy.is_boss else 10, knockback=10.0, hitstun=12)

            for enemy in dead_enemies:
                apply_hit_reaction(enemy, min_x=enemy_zone_min_x, max_x=enemy_zone_max_x)

            for enemy in enemies:
                if enemy.is_dead and enemy.anim_state != "death":
                    enemy.anim_state = "death"
                    enemy.anim_frame = 0
                    enemy.anim_timer = 0
                elif not enemy.is_dead and enemy.anim_state not in ("fly", "attack"):
                    enemy.anim_state = "fly"
                    enemy.anim_frame = 0
                    enemy.anim_timer = 0

                cat_frames = enemy_frames.get(enemy.anim_state, [])
                if cat_frames:
                    tick_rate = {"fly": 8, "attack": 3, "death": 4}.get(enemy.anim_state, 8)
                    enemy.anim_timer += 1
                    if enemy.anim_timer >= tick_rate:
                        enemy.anim_timer = 0
                        nxt = enemy.anim_frame + 1
                        if nxt >= len(cat_frames):
                            if enemy.anim_state == "attack":
                                enemy.anim_state = "fly"
                                enemy.anim_frame = 0
                            elif enemy.anim_state == "death":
                                enemy.anim_frame = len(cat_frames) - 1
                            else:
                                enemy.anim_frame = 0
                        else:
                            enemy.anim_frame = nxt

            if state.player_attack_timer > 0:
                if not state.player_attack_hit_latch and player.attack_cooldown <= 0:
                    player.attack_cooldown = 15
                    hits = 0
                    for enemy in alive_enemies:
                        damage = 20 if enemy.is_boss else 18
                        if player.jump_attack_active:
                            damage += 4
                        if try_free_attack(
                            player,
                            enemy,
                            damage=damage,
                            knockback=16.0 if player.jump_attack_active else 14.0,
                            hitstun=20 if player.jump_attack_active else 16,
                            radius=120 if player.jump_attack_active else 100,
                            consume_cooldown=False,
                        ):
                            hits += 1
                    if hits > 0:
                        state.show_attack_flash = 4
                        state.player_attack_hit_latch = True
                        state.power_meter = min(POWER_MAX, state.power_meter + POWER_GAIN_ON_HIT * hits)

            for enemy in enemies:
                if enemy.is_dead and enemy.hitstun > 0 and not enemy.score_awarded:
                    enemy.score_awarded = True
                    pts = SCORE_PER_BOSS if enemy.is_boss else SCORE_PER_ENEMY
                    state.score_popups.append({
                        "text": f"+{pts}",
                        "x": enemy.x,
                        "y": enemy.y - 20,
                        "timer": SCORE_POPUP_DURATION,
                    })
                    state.stage_score += pts
                    state.score += pts
                    if not enemy.is_boss:
                        state.enemies_killed_this_stage += 1

            enemies = [e for e in enemies if not (e.is_dead and e.hitstun == 0)]

            if state.combat_active and not enemies:
                if state.wave_index < state.waves_per_zone:
                    state.wave_index += 1
                    enemies = spawn_wave_for_zone(state)
                else:
                    complete_zone_encounter(state)

            if player.hp <= 0 and not state.game_over and not state.stage_complete:
                state.player_lives -= 1
                if state.player_lives > 0:
                    respawn_zone = state.active_zone if state.combat_active else max(0, state.unlocked_zone - 1)
                    player = make_player(x=respawn_zone * ZONE_WIDTH + 40)
                    state.spawn_timer = SPAWN_ANIM_FRAMES
                else:
                    player.is_dead = True
                    state.game_over = True

            if player.attack_cooldown > 0:
                player.attack_cooldown -= 1
            if state.player_attack_timer > 0:
                state.player_attack_timer -= 1
            else:
                state.player_attack_hit_latch = False
                player.jump_attack_active = False
            if state.combo_timer > 0:
                state.combo_timer -= 1
            else:
                state.combo_taps = 0
            if state.sprint_timer > 0:
                state.sprint_timer -= 1
            if state.show_attack_flash > 0:
                state.show_attack_flash -= 1
            if state.player_kick_active > 0:
                state.player_kick_active -= 1
            if state.controls_timer < CONTROLS_FADE_FRAMES:
                state.controls_timer += 1
            for popup in state.score_popups:
                popup["timer"] -= 1
                popup["y"] -= 0.8
            state.score_popups = [p for p in state.score_popups if p["timer"] > 0]

            for enemy in enemies:
                if enemy.attack_cooldown > 0:
                    enemy.attack_cooldown -= 1

        combo_indicator = combo_indicator_text(state.combo_taps)

        # Periodic runtime debug for animation state.
        animation_debug_counter += 1
        if animation_debug_counter >= 240:
            animation_debug_counter = 0
            print(
                "[beatemup][anim] walk_frames=",
                len(walk_frames),
                "walk_idx=",
                walk_anim_idx,
                "run_frames=",
                len(run_frames),
                "run_idx=",
                run_anim_idx,
                "idle_frames=",
                len(idle_frames),
                "idle_idx=",
                idle_anim_idx,
                "moving_input=",
                is_moving_input,
                "sprinting=",
                is_sprinting,
                "jumping=",
                player.is_jumping,
            )

        draw_bg(screen, state.camera_x, bg_layers, font, debug_labels=state.debug_show_labels)
        if state.debug_show_zone_dividers:
            draw_zone_dividers(screen, state.camera_x)
        draw_player(screen, player, state.camera_x, frame_surface=player_frame, show_attack=state.show_attack_flash > 0)
        if state.debug_show_hitboxes:
            draw_player_free_attack_hitbox(screen, player, state.camera_x, state.player_attack_timer > 0)
            draw_player_kick_hitbox(screen, player, state.camera_x, state.player_kick_active)
        for enemy in enemies:
            cat_frames = enemy_frames.get(enemy.anim_state, [])
            frame = cat_frames[enemy.anim_frame] if cat_frames else None
            draw_fighter(screen, enemy, state.camera_x, frame_surface=frame)
            draw_enemy_hp_bar(screen, enemy, state.camera_x)

        draw_foreground(screen, state.camera_x, bg_layers)

        draw_boss_hp_bar(screen, font, enemies, state.camera_x)
        draw_score_popups(screen, state.camera_x, state.score_popups, font)
        draw_ui(screen, font, player, enemies, state, combo_indicator)
        if state.debug_show_zone_indicator:
            draw_zone_indicator(screen, font, get_zone_for_x(player.x))
        if state.debug_show_spawn_text:
            draw_spawn_text(screen, font, state.spawn_timer > 0)

        if state.stage_complete:
            draw_stage_complete_screen(screen, font, state)
        elif state.game_over:
            draw_game_over_screen(screen, font, state)

        if state.debug_menu_open:
            draw_debug_menu(screen, font, state)

        pygame.display.flip()

    pygame.quit()
