from dataclasses import dataclass, field
import pygame


@dataclass
class Fighter:
    x: float
    y: float
    color: tuple
    facing: int = 1
    speed: float = 3.2
    hp: int = 100
    max_hp: int = 100
    attack_cooldown: int = 0
    knockback_x: float = 0.0
    hitstun: int = 0
    is_dead: bool = False
    is_boss: bool = False
    ai_vx: float = 0.0
    ai_vy: float = 0.0
    z: float = 0.0
    vz: float = 0.0
    is_jumping: bool = False
    jump_attack_active: bool = False
    score: int = 0
    score_awarded: bool = False
    body_width: int = 60
    body_height: int = 90
    sprite_width: int = 60
    sprite_height: int = 90
    _sprite_scale_target_h: int = 350
    _sprite_src_height: int = 128
    _sprite_bottom_pad: int = 48
    sprite_offset_y: int = 0
    anim_state: str = "fly"
    anim_frame: int = 0
    anim_timer: int = 0

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.body_width, self.body_height)

    def set_sprite_dimensions(self, sprite_surface):
        if sprite_surface is None:
            return
        surf_w = sprite_surface.get_width()
        surf_h = sprite_surface.get_height()
        aspect = surf_w / surf_h
        self.sprite_height = self._sprite_scale_target_h
        self.sprite_width = int(self.sprite_height * aspect)
        self.sprite_offset_y = self.sprite_height * self._sprite_bottom_pad // self._sprite_src_height

    def hurtbox(self):
        return self.rect()

    def attack_box(self):
        r = self.hurtbox()
        reach = 72
        if self.facing > 0:
            return pygame.Rect(r.right, r.top + 10, reach, r.height - 20)
        return pygame.Rect(r.left - reach, r.top + 10, reach, r.height - 20)

    def radial_attack_box(self, radius=100):
        r = self.hurtbox()
        return pygame.Rect(r.centerx - radius, r.centery - radius, radius * 2, radius * 2)


@dataclass
class GameState:
    active_zone: int = 0
    unlocked_zone: int = 1
    next_encounter_zone: int = 1
    combat_active: bool = False
    game_cleared: bool = False
    game_over: bool = False
    player_lives: int = 3

    camera_x: float = 0.0
    combo_taps: int = 0
    combo_timer: int = 0
    player_attack_timer: int = 0
    player_attack_hit_latch: bool = False
    player_kick_active: int = 0
    sprint_timer: int = 0
    last_tap_left_ms: int = -1000
    last_tap_right_ms: int = -1000
    show_attack_flash: int = 0
    spawn_timer: int = 0
    power_meter: int = 0
    wave_index: int = 0
    waves_per_zone: int = 3
    total_stage: int = 1
    score: int = 0

    stage_complete: bool = False
    stage_score: int = 0
    enemies_killed_this_stage: int = 0
    score_popups: list = field(default_factory=list)
    controls_timer: int = 0

    zone_status: list[str] = field(default_factory=lambda: ["SAFE", "LOCKED", "LOCKED", "LOCKED"])

    debug_show_labels: bool = True
    debug_show_hitboxes: bool = True
    debug_show_zone_dividers: bool = True
    debug_show_zone_indicator: bool = True
    debug_show_spawn_text: bool = True
    debug_menu_open: bool = False
    debug_menu_selection: int = 0
