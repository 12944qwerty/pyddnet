import arcade
from math import pow

from engine.constants import TILE_SIZE
from engine.tee import Tee

# from engine import DDNetPhysicsEngine

def velocity_ramp(value: float, start: float, range: float, curvature: float):
    if value < start:
        return 1.0
    return 1.0 / pow(curvature, (value - start) / range)

class TeeSprite(arcade.Sprite):
    def __init__(self, tee: Tee):
        super().__init__(
            arcade.make_soft_circle_texture(
                72, arcade.color.ORANGE, 255, 255
            )
        )
        
        # self.atlas = arcade.load_texture("assets/game_06.png")
        # self.region = arcade.Texture(
        #     name="tee_region",
        #     image=self.atlas.image.crop((64, 0, 96, 32))
        # )
        
        # self.texture = self.region
        
        self.tee = tee
        
    def update(self, delta_time: float):
        self.center_x = self.tee.position.x * 2
        self.center_y = -self.tee.position.y * 2