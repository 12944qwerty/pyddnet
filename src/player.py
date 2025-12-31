import arcade
from math import pow

from .constants import *
from .utils import point2_length

# from engine import DDNetPhysicsEngine

def velocity_ramp(value: float, start: float, range: float, curvature: float):
    if value < start:
        return 1.0
    return 1.0 / pow(curvature, (value - start) / range)

class Player(arcade.Sprite):
    def __init__(self):
        super().__init__(
            arcade.make_soft_square_texture(
                TILE_SIZE, arcade.color.ORANGE, 255, 255
            )
        )
        self.center_x = 400
        self.center_y = 350

        self.move_x = 0
        self.move_y = 0
        
        self.jumps = 2
        self.jumped = 0
        self.should_jump = False
        
        self.direction = 0
        
    def update(self, delta_time: float, engine: "DDNetPhysicsEngine"):
        ramp_val = velocity_ramp(point2_length(self.velocity), VELRAMP_START, VELRAMP_RANGE, VELRAMP_CURVATURE)
        
        self.change_x = self.change_x * ramp_val
        
        newpos = self.position
        oldvel = self.velocity
        
        grounded = self._check_collision_along_path(engine.walls)
        
        if grounded:
            self.jumped &= ~2
            
        self.colliding = 0
        if self.change_x < 0.001 and self.change_x > -0.001:
            if oldvel[0] > 0:
                self.colliding = 1
            elif oldvel[0] < 0:
                self.colliding = 2
        else:
            self.left_wall = True
            
        self.change_x = self.change_x * (1.0 / ramp_val)
        
        # todo player collision
                
        
    def _check_collision_along_path(self, walls: arcade.SpriteList[arcade.Sprite]):
        grounded = False

        distance = point2_length(self.velocity)
        steps = int(distance)

        if distance <= 0.00001:
            return

        fraction = 1.0 / (steps + 1)
        elasticity_x = 0
        elasticity_y = 0

        for _ in range(steps + 1):
            if self.velocity == (0, 0):
                break

            prev_x, prev_y = self.center_x, self.center_y

            new_x = prev_x + self.velocity[0] * fraction
            new_y = prev_y + self.velocity[1] * fraction

            if (new_x, new_y) == (prev_x, prev_y):
                break

            
                
        return grounded
