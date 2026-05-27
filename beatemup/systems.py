import math
import random
import pygame

from .constants import (
    WIDTH, HEIGHT, GROUND_Y, ZONE_WIDTH, ZONE_COUNT, WORLD_WIDTH, SPRINT_SPEED_MULT, GRAVITY,
    REGULAR_ENEMY_HP, BOSS_HP,
    DIFFICULTY_SCALE_PER_STAGE, MIN_WAVE_ENEMIES, MAX_WAVE_ENEMIES_PER_STAGE,
    SCORE_PER_ENEMY, SCORE_PER_BOSS, SCORE_PER_STAGE_COMPLETE, STAGE_TRANSITION_DURATION,
    KICK_DAMAGE, KICK_BOSS_DAMAGE, KICK_COOLDOWN_FRAMES, KICK_ATTACK_RANGE, KICK_KNOCKBACK, KICK_HITSTUN
)
from .models import Fighter


def zone_bounds(zone_idx):
    min_x = zone_idx * ZONE_WIDTH + 10
    max_x = (zone_idx + 1) * ZONE_WIDTH - 70
    return min_x, max_x


def clamp_fighter_world(f: Fighter, min_x, max_x, min_y=260, max_y=HEIGHT - 90):
    f.x = max(min_x, min(max_x, f.x))
    f.y = max(min_y, min(max_y, f.y))


def update_jump(f: Fighter):
    if not f.is_jumping:
        return
    f.z += f.vz
    f.vz += GRAVITY
    if f.z >= 0:
        f.z = 0
        f.vz = 0
        f.is_jumping = False
        f.jump_attack_active = False


def handle_player_input(keys, player: Fighter, min_x, max_x, sprint_active=False):
    if player.is_dead:
        return
    move_speed = player.speed * (SPRINT_SPEED_MULT if sprint_active else 1.0)
    dx = dy = 0.0
    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        dx -= move_speed
        player.facing = -1
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        dx += move_speed
        player.facing = 1
    if keys[pygame.K_UP] or keys[pygame.K_w]:
        dy -= move_speed * 0.7
    if keys[pygame.K_DOWN] or keys[pygame.K_s]:
        dy += move_speed * 0.7
    player.x += dx
    player.y += dy
    clamp_fighter_world(player, min_x=min_x, max_x=max_x)


def get_zone_for_x(x):
    zone = int(max(0, min(ZONE_COUNT - 1, x // ZONE_WIDTH)))
    return zone


def update_camera_x(camera_x, player_x):
    desired = player_x - WIDTH * 0.42
    desired = max(0, min(WORLD_WIDTH - WIDTH, desired))
    next_x = camera_x + (desired - camera_x) * 0.16
    return max(0, min(WORLD_WIDTH - WIDTH, next_x))


def _repulsion_force(enemy: Fighter, others: list[Fighter], min_dist=70):
    sx = sy = 0.0
    for other in others:
        if other is enemy or other.is_dead:
            continue
        dx = enemy.x - other.x
        dy = enemy.y - other.y
        dist = math.sqrt(dx * dx + dy * dy)
        if 0 < dist < min_dist:
            strength = (min_dist - dist) / min_dist
            sx += (dx / dist) * strength * 1.8
            sy += (dy / dist) * strength * 1.2
    return sx, sy


def enemy_ai(enemy: Fighter, player: Fighter, zone_min_x, zone_max_x, all_enemies=None):
    if enemy.is_dead or enemy.hitstun > 0:
        enemy.ai_vx *= 0.8
        enemy.ai_vy *= 0.8
        return

    dx = player.x - enemy.x
    dy = player.y - enemy.y
    distance_x = abs(dx)
    preferred_x_min = 56
    preferred_x_max = 118

    if dx > 0:
        enemy.facing = 1
    elif dx < 0:
        enemy.facing = -1

    t = pygame.time.get_ticks() / 1000.0
    mood_wave = (math.sin(t * (1.8 if enemy.is_boss else 2.4) + enemy.x * 0.01) + 1.0) * 0.5
    desired_min = preferred_x_min + int(22 * mood_wave)
    desired_max = preferred_x_max + int(30 * (1.0 - mood_wave))
    engage_speed = 0.62 + 0.25 * mood_wave
    retreat_speed = 0.42 + 0.22 * (1.0 - mood_wave)

    target_vx = 0.0
    if distance_x > desired_max:
        target_vx = enemy.speed * engage_speed * (1 if dx > 0 else -1)
    elif distance_x < desired_min:
        target_vx = -enemy.speed * retreat_speed * (1 if dx > 0 else -1)

    strafe_dir = 1 if math.sin(t * (2.1 if enemy.is_boss else 2.9) + enemy.y * 0.02) > 0 else -1
    target_vy = 0.0
    if abs(dy) < 30:
        target_vy = strafe_dir * enemy.speed * (0.35 + 0.22 * mood_wave)
    elif dy > 0:
        target_vy = enemy.speed * (0.24 + 0.12 * mood_wave)
    else:
        target_vy = -enemy.speed * (0.24 + 0.12 * mood_wave)

    if all_enemies:
        rx, ry = _repulsion_force(enemy, all_enemies)
        target_vx += rx * 1.6
        target_vy += ry * 1.6

    blend = 0.22 if enemy.is_boss else 0.26
    enemy.ai_vx += (target_vx - enemy.ai_vx) * blend
    enemy.ai_vy += (target_vy - enemy.ai_vy) * blend

    enemy.x += enemy.ai_vx
    enemy.y += enemy.ai_vy

    clamp_fighter_world(enemy, min_x=zone_min_x, max_x=zone_max_x)


def try_attack(attacker: Fighter, defender: Fighter, damage=10, knockback=8.0, hitstun=10):
    if attacker.is_dead or defender.is_dead:
        return False
    if attacker.attack_cooldown > 0:
        return False
    attacker.attack_cooldown = 22
    if attacker.attack_box().colliderect(defender.hurtbox()):
        defender.hp = max(0, defender.hp - damage)
        if defender.hp <= 0:
            defender.is_dead = True
            defender.knockback_x = attacker.facing * 5.0
            defender.hitstun = 24
            # Award points for defeating enemy
            if hasattr(attacker, 'score'):
                attacker.score += SCORE_PER_BOSS if defender.is_boss else SCORE_PER_ENEMY
            return True
        defender.knockback_x = attacker.facing * knockback
        defender.hitstun = hitstun
        return True
    return False


def try_free_attack(
    attacker: Fighter,
    defender: Fighter,
    damage=10,
    knockback=8.0,
    hitstun=10,
    radius=46,
    consume_cooldown=True,
):
    if attacker.is_dead or defender.is_dead:
        return False
    if consume_cooldown:
        if attacker.attack_cooldown > 0:
            return False
        attacker.attack_cooldown = 22
    if attacker.radial_attack_box(radius=radius).colliderect(defender.hurtbox()):
        if defender.x < attacker.x:
            attacker.facing = -1
        elif defender.x > attacker.x:
            attacker.facing = 1
        defender.hp = max(0, defender.hp - damage)
        if defender.hp <= 0:
            defender.is_dead = True
            defender.knockback_x = attacker.facing * 5.0
            defender.hitstun = 24
            # Award points for defeating enemy
            if hasattr(attacker, 'score'):
                attacker.score += SCORE_PER_BOSS if defender.is_boss else SCORE_PER_ENEMY
            return True
        defender.knockback_x = attacker.facing * knockback
        defender.hitstun = hitstun
        return True
    return False


def apply_hit_reaction(f: Fighter, min_x=10, max_x=WORLD_WIDTH - 70):
    if abs(f.knockback_x) > 0.05:
        f.x += f.knockback_x
        f.knockback_x *= 0.78
    else:
        f.knockback_x = 0.0
    if f.hitstun > 0:
        f.hitstun -= 1
    clamp_fighter_world(f, min_x=min_x, max_x=max_x)


def spawn_enemy_wave(zone_idx, enemy_color, total_stage=1):
    zone_start = zone_idx * ZONE_WIDTH
    count = random.randint(2, 3)
    
    # Scale HP based on stage difficulty
    difficulty_mult = get_difficulty_multiplier(total_stage)
    hp_min = int((80 + zone_idx * 12) * difficulty_mult)
    hp_max = int((110 + zone_idx * 18) * difficulty_mult)
    
    enemies = []
    for i in range(count):
        from_left = i % 2 == 0
        # Spawn from zone corners/edges for a more natural entrance.
        x = zone_start + 20 if from_left else zone_start + ZONE_WIDTH - 90
        facing = 1 if from_left else -1
        hp = random.randint(hp_min, hp_max)
        enemy = Fighter(
            x=x,
            y=320 + random.choice([-24, 0, 24]),
            color=enemy_color,
            facing=facing,
            hp=hp,
            max_hp=hp,
        )
        enemy._sprite_scale_target_h = 140
        enemy._sprite_bottom_pad = 32
        enemies.append(enemy)
    return enemies


def spawn_boss(zone_idx, boss_color, hp, total_stage=1):
    zone_start = zone_idx * ZONE_WIDTH
    # Scale boss HP based on stage difficulty
    difficulty_mult = get_difficulty_multiplier(total_stage)
    scaled_hp = int(hp * difficulty_mult)
    boss = Fighter(
        x=zone_start + ZONE_WIDTH - 180,
        y=310,
        color=boss_color,
        facing=-1,
        speed=2.6,
        hp=scaled_hp,
        max_hp=scaled_hp,
        is_boss=True,
    )
    boss._sprite_scale_target_h = 140
    boss._sprite_bottom_pad = 32
    return boss


def get_difficulty_multiplier(total_stage: int) -> float:
    """Calculate difficulty multiplier based on stage number."""
    from .constants import DIFFICULTY_SCALE_PER_STAGE
    return 1.0 + (total_stage - 1) * DIFFICULTY_SCALE_PER_STAGE


def calculate_attack_accuracy(attacker: Fighter, defender: Fighter) -> float:
    """Calculate attack accuracy based on various factors.
    
    Returns a value between 0.0 and 1.0 representing hit probability.
    """
    # Base accuracy - bosses are more accurate
    base_accuracy = 0.25 if attacker.is_boss else 0.15
    
    # Distance factor - closer targets are easier to hit
    distance = abs(attacker.x - defender.x)
    distance_factor = max(0.3, 1.0 - (distance / 200.0))
    
    # Movement factor - moving targets are harder to hit
    movement_factor = 1.0
    if defender.is_jumping:
        movement_factor *= 0.6  # Jumping players are harder to hit
    
    # Attack type factor
    attack_type_factor = 1.0
    
    # Combined accuracy
    accuracy = base_accuracy * distance_factor * movement_factor * attack_type_factor
    return min(0.9, max(0.05, accuracy))  # Clamp between 5% and 90%


def should_attack_hit(attacker: Fighter, defender: Fighter) -> bool:
    """Determine if an attack should hit based on accuracy calculation."""
    accuracy = calculate_attack_accuracy(attacker, defender)
    return random.random() < accuracy


def try_attack_with_miss_logic(attacker: Fighter, defender: Fighter, damage=10, knockback=8.0, hitstun=10):
    """Enhanced attack function with proper hit/miss logic."""
    if attacker.is_dead or defender.is_dead:
        return False
    if attacker.attack_cooldown > 0:
        return False
    
    # Check if attack should hit or miss
    if should_attack_hit(attacker, defender):
        # Attack hits
        attacker.attack_cooldown = 22
        if attacker.attack_box().colliderect(defender.hurtbox()):
            defender.hp = max(0, defender.hp - damage)
            if defender.hp <= 0:
                defender.is_dead = True
                defender.knockback_x = attacker.facing * 5.0
                defender.hitstun = 24
                # Award points for defeating enemy
                if hasattr(attacker, 'score'):
                    attacker.score += SCORE_PER_BOSS if defender.is_boss else SCORE_PER_ENEMY
                return True
            defender.knockback_x = attacker.facing * knockback
            defender.hitstun = hitstun
            return True
    else:
        # Attack misses - set cooldown but no damage
        attacker.attack_cooldown = 22
    
    return False


def try_kick_attack(attacker: Fighter, defender: Fighter, damage=10, knockback=8.0, hitstun=10, radius=36, consume_cooldown=True):
    if attacker.is_dead or defender.is_dead:
        return False
    if consume_cooldown:
        if attacker.attack_cooldown > 0:
            return False
        attacker.attack_cooldown = KICK_COOLDOWN_FRAMES
    if attacker.radial_attack_box(radius=radius).colliderect(defender.hurtbox()):
        if defender.x < attacker.x:
            attacker.facing = -1
        elif defender.x > attacker.x:
            attacker.facing = 1
        defender.hp = max(0, defender.hp - damage)
        if defender.hp <= 0:
            defender.is_dead = True
            defender.knockback_x = attacker.facing * 5.0
            defender.hitstun = 24
            if hasattr(attacker, 'score'):
                attacker.score += SCORE_PER_BOSS if defender.is_boss else SCORE_PER_ENEMY
            return True
        defender.knockback_x = attacker.facing * knockback
        defender.hitstun = hitstun
        return True
    return False
