import random
import math
import arcade
from arcade.math import clamp
from arcade.gui import UIManager, UILabel, UIAnchorLayout

from engine.constants import *
from engine.engine import DDNetPhysicsEngine
from engine.maploader import MapLoader
from engine.tee import Tee
from gaming.tee import TeeSprite
from gaming.renderer import MapRenderer
from shared import Vector2


SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
SCREEN_TITLE = "TWMap Arcade Renderer"

DEFAULT_ZOOM = 0.65

class GameWindow(arcade.Window):
    def __init__(self):
        super().__init__(
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
            SCREEN_TITLE,
            fullscreen=True,
            draw_rate=1/100,
            update_rate=1/100
        )
        arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)

        self.camera = arcade.Camera2D(zoom=DEFAULT_ZOOM)

        self.map = None
        self.maprender = None
        
        self.tee_sprite = None
        self.tees_sprites = None
        
        self.tee = None
        self.tees = None
        
        self.target = Vector2(0, 0)
        self.physics_engine = None
        
        self.pressed_keys = set()
        
        self._accumulated_time = 0.0
        
        self.ui = None
        
        self.zoom = DEFAULT_ZOOM

    def setup(self):
        self.map = MapLoader("maps/ctf7.map")
        self.maprender = MapRenderer(
            self.map,
            "assets/ddnet.png"
        )
        
        self.tee = Tee()
        self.tee.position = random.choice(self.map.spawners).position * 32 + Vector2(16, 16)
        
        self.tees = [self.tee]

        self.tee_sprite = TeeSprite(self.tee)
        
        self.tees_sprites = arcade.SpriteList()
        self.tees_sprites.append(self.tee_sprite)
        
        self.physics_engine = DDNetPhysicsEngine(self.map, self.tees)
        
        self.ui = UIManager()
        
        self.ui.enable()

        self.coordinate_label = UILabel(
            text="x: 0.00  y: 0.00",
            font_size=14,
            text_color=arcade.color.WHITE,
        )
        self.velocity_label = UILabel(
            text="vx: 0.00  vy: 0.00",
            font_size=14,
            text_color=arcade.color.WHITE,
        )
        self.fps_label = UILabel(
            text="FPS: 0",
            font_size=14,
            text_color=arcade.color.WHITE,
        )
        self.mtarget = (0, 0)
        self.angle = 0.0
        self.mtarget_label = UILabel(
            text="mx: 0.00 my: 0.00, deg: 0.00",
            font_size=14,
            text_color=arcade.color.WHITE,
        )
        
        self.anchor = UIAnchorLayout()
        self.anchor.add(
            self.coordinate_label,
            anchor_x="right",
            anchor_y="bottom",
        )
        self.anchor.add(
            self.velocity_label,
            anchor_x="right",
            anchor_y="bottom",
            align_y=20,
        )
        self.anchor.add(
            self.mtarget_label,
            anchor_x="right",
            anchor_y="bottom",
            align_y=40,
        )
        self.anchor.add(
            self.fps_label,
            anchor_x="right",
            anchor_y="bottom",
            align_y=60,
        )
        
        self.ui.add(self.anchor)
        
        arcade.enable_timings()

    def on_draw(self):
        self.clear()
        self.camera.use()

        self.maprender.draw()
        self.tees_sprites.draw()
        
        self.ui.draw()
        
        arcade.draw_line(
            self.tee_sprite.center_x,
            self.tee_sprite.center_y,
            self.tee_sprite.center_x + self.tee.target_direction.x * HOOK_LENGTH * 2,
            self.tee_sprite.center_y - self.tee.target_direction.y * HOOK_LENGTH * 2,
            arcade.color.GREEN if arcade.MOUSE_BUTTON_RIGHT in self.pressed_keys else arcade.color.RED,
            2
        )
        
        arcade.draw_line(
            self.tee_sprite.center_x,
            self.tee_sprite.center_y,
            self.tee.hookpos.x * 2,
            -self.tee.hookpos.y * 2,
            arcade.color.BLUE,
            2
        )

    def on_update(self, dt):        
        if arcade.key.A in self.pressed_keys and arcade.key.D in self.pressed_keys:
            self.tee.direction = 0
        elif arcade.key.A in self.pressed_keys:
            self.tee.direction = -1
        elif arcade.key.D in self.pressed_keys:
            self.tee.direction = 1
        else:
            self.tee.direction = 0
        
        self.target.x, self.target.y, mz = self.camera.unproject((self.mtarget[0], self.mtarget[1]))
        self.tee.target = Vector2(self.target.x / 2, -self.target.y / 2) - self.tee.position
        
        self.mtarget_label.text = f"mx: {self.target.x / 64:.2f} my: {self.target.y / 64:.2f}, deg: {self.tee.angle:.2f}"
        
        self.tee.should_hook = arcade.MOUSE_BUTTON_RIGHT in self.pressed_keys
        
        self.physics_engine.update(dt)
            
        self.tees_sprites.update(dt)

        self.camera.position = self.tee_sprite.center_x, self.tee_sprite.center_y
        self.camera.zoom += (self.zoom - self.camera.zoom) * 0.2

        self.coordinate_label.text = f"x: {self.tee.position.x / 32:.2f}  y: {self.tee.position.y / 32:.2f}"
        self.velocity_label.text = f"vx: {self.tee.velocity.x / 32:.2f}  vy: {self.tee.velocity.y / 32:.2f}"
        
        self.fps_label.text = f"FPS: {arcade.get_fps():.2f}"

    def on_key_press(self, key, modifiers):
        if key == arcade.key.Q:
            arcade.close_window()
            
        if key == arcade.key.SPACE:
            self.tee.should_jump = True
                
        if key == arcade.key.A:
            self.pressed_keys.add(key)
        if key == arcade.key.D:
            self.pressed_keys.add(key)

    def on_key_release(self, key, modifiers):
        if key == arcade.key.R:
            self.tee.position = random.choice(self.map.spawners).position * 32 + Vector2(16, 16)
            self.tee.velocity = Vector2(0, 0)
            
        if key == arcade.key.F: 
            self.zoom = DEFAULT_ZOOM
            
        if key == arcade.key.SPACE:
            self.tee.should_jump = False
            
        self.pressed_keys.discard(key)
            
    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        self.zoom = clamp(self.zoom + scroll_y / 30, 0.1, 50)
        
    def on_mouse_motion(self, x, y, dx, dy):
        self.mtarget = x, y
        
    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_RIGHT:
            self.pressed_keys.add(button)
    
    def on_mouse_release(self, x, y, button, modifiers):
        self.pressed_keys.discard(button)

def main():
    window = GameWindow()
    window.setup()
    arcade.run()

if __name__ == "__main__":
    main()