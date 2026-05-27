WIDTH, HEIGHT = 960, 540
GROUND_Y = 420
FPS = 60

ZONE_COUNT = 4
ZONE_WIDTH = 950
WORLD_WIDTH = ZONE_COUNT * ZONE_WIDTH

PLAYER_SPAWN_X = 50
PLAYER_SPAWN_Y = 320

DOUBLE_TAP_WINDOW_MS = 260
SPRINT_DURATION_FRAMES = 150
SPRINT_SPEED_MULT = 1.85
COMBO_TAP_WINDOW_FRAMES = 24
JUMP_VELOCITY = -11.5
GRAVITY = 0.62
POWER_GAIN_ON_HIT = 10
POWER_MAX = 100
POWER_SKILL_COST = 100

SPAWN_ANIM_FRAMES = 45

PLAYER_COLOR = (232, 88, 88)
ENEMY_COLOR = (78, 156, 236)
BOSS_COLOR = (208, 92, 232)

REGULAR_ENEMY_HP = 100
BOSS_HP = 240

# Difficulty scaling for endless progression
DIFFICULTY_SCALE_PER_STAGE = 0.15  # 15% increase per stage
MIN_WAVE_ENEMIES = 2
MAX_WAVE_ENEMIES_PER_STAGE = 6

# Scoring system
SCORE_PER_ENEMY = 100
SCORE_PER_BOSS = 500
SCORE_PER_STAGE_COMPLETE = 1000
STAGE_TRANSITION_DURATION = 120  # frames (2 seconds at 60 FPS)
SCORE_POPUP_DURATION = 30  # frames for floating score text

# UI
CONTROLS_FADE_FRAMES = 300  # frames until controls hint fades
BOSS_HP_BAR_WIDTH = 400
BOSS_HP_BAR_HEIGHT = 20

# Kick attack constants
KICK_DAMAGE = 12  # Base damage for regular enemies
KICK_BOSS_DAMAGE = 14  # Base damage for bosses
KICK_COOLDOWN_FRAMES = 15  # Faster than regular attack (22 frames)
KICK_ATTACK_RANGE = 76  # Shorter range than regular attack (100 pixels)
KICK_KNOCKBACK = 10.0  # Less knockback than regular attack (14.0)
KICK_HITSTUN = 12  # Less hitstun than regular attack (16 frames)
