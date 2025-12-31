# Render
TILE_SIZE = 64

# Physics
# https://ddnet.org/settingscommands/
# Multiplied by 2 because the values assume 32 units per tile, but we use 64 units per tile.
AIR_CONTROL_ACCEL = 1.5 * 2
AIR_CONTROL_SPEED = 5.0 * 2
AIR_FRICTION = 0.95 * 2
AIR_JUMP_IMPULSE = 12.0 * 2
GRAVITY = 0.5 * 2
GROUND_CONTROL_ACCEL = 2.0 * 2
GROUND_CONTROL_SPEED = 10.0 * 2
GROUND_ELASTICITY_X = 0.0 * 2
GROUND_ELASTICITY_Y = 0.0 * 2
GROUND_FRICTION = 0.5 * 2
GROUND_JUMP_IMPULSE = 13.2 * 2

VELRAMP_CURVATURE = 1.4
VELRAMP_START = 2000.0
VELRAMP_RANGE = 550.0