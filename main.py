import random
import arcade
from arcade.math import clamp

from src.engine import DDNetPhysicsEngine
from src.renderer import MapRenderer
from src.player import Player


SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
SCREEN_TITLE = "TWMap Arcade Renderer"

class GameWindow(arcade.Window):
    def __init__(self):
        super().__init__(
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
            SCREEN_TITLE,
            draw_rate=1/50,
            update_rate=1/50
        )
        arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)

        self.camera = arcade.Camera2D(zoom=0.5)

        self.map = None
        self.players = None
        self.player = None
        
        self.physics_engine = None
        
        self.pressed_keys = set()

    def setup(self):
        self.map = MapRenderer(
            "maps/ctf7.map",
            "assets/ddnet.png"
        )

        self.player = Player()
        self.player.center_x, self.player.center_y = random.choice(self.map.spawners)
        
        self.players = arcade.SpriteList()
        self.players.append(self.player)
        
        self.physics_engine = DDNetPhysicsEngine(
            self.player,
            self.map.terrain
        )

    def on_draw(self):
        self.clear()
        self.camera.use()

        self.map.draw()
        self.players.draw()

    def on_update(self, dt):        
        if arcade.key.A in self.pressed_keys and arcade.key.D in self.pressed_keys:
            self.player.direction = 0
        elif arcade.key.A in self.pressed_keys:
            self.player.direction = -1
        elif arcade.key.D in self.pressed_keys:
            self.player.direction = 1
        else:
            self.player.direction = 0
        
        self.physics_engine.update(dt)

        self.camera.position = self.player.center_x, self.player.center_y

    def on_key_press(self, key, modifiers):
        if key == arcade.key.Q:
            arcade.close_window()
            
        if key == arcade.key.SPACE:
            self.player.should_jump = True
                
        if key == arcade.key.A:
            self.pressed_keys.add(key)
        if key == arcade.key.D:
            self.pressed_keys.add(key)

    def on_key_release(self, key, modifiers):            
        if key == arcade.key.R:
            self.player.center_x, self.player.center_y = random.choice(self.map.spawners)
            
        if key == arcade.key.F: 
            self.camera.zoom = 0.5
            
        if key == arcade.key.SPACE:
            self.player.should_jump = False
            
        self.pressed_keys.discard(key)
            
    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        self.camera.zoom = clamp(self.camera.zoom + scroll_y / 50, 0.1, 10)


if __name__ == "__main__":
    window = GameWindow()
    window.setup()
    arcade.run()
