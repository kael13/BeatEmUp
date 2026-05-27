from beatemup.constants import WIDTH, HEIGHT, WORLD_WIDTH, ZONE_WIDTH
from beatemup.models import Fighter
from beatemup.systems import clamp_fighter_world, get_zone_for_x, update_camera_x


def test_clamp_fighter_world_limits_x_and_y():
    fighter = Fighter(x=-100, y=999, color=(255, 255, 255))
    clamp_fighter_world(fighter, min_x=10, max_x=200)
    assert fighter.x == 10
    assert fighter.y == 450  # HEIGHT - 90 = 540 - 90 = 450


def test_get_zone_for_x_maps_boundaries():
    assert get_zone_for_x(0) == 0
    assert get_zone_for_x(ZONE_WIDTH + 5) == 1
    assert get_zone_for_x(ZONE_WIDTH * 2 + 10) == 2
    assert get_zone_for_x(ZONE_WIDTH * 3 + 40) == 3


def test_update_camera_x_stays_within_world_bounds():
    left = update_camera_x(0.0, -100)
    assert left >= 0

    right = update_camera_x(float(WORLD_WIDTH), WORLD_WIDTH + 500)
    assert right <= WORLD_WIDTH - WIDTH
