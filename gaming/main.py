import argparse
import random
from signal import signal, SIGINT
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
from shared import HookState, Vector2

from network.client import TeeworldsClient


SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
SCREEN_TITLE = "TWMap Arcade Renderer"

DEFAULT_ZOOM = 0.65

class GameWindow(arcade.Window):
    def __init__(self, args):
        super().__init__(
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
            SCREEN_TITLE,
            resizable=True,
            draw_rate=1/100,
            update_rate=1/100
        )
        arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)

        self.camera = arcade.Camera2D(zoom=DEFAULT_ZOOM)
        self.gui_camera = arcade.Camera2D()  # Screen-space camera for UI/text
        
        self.net = TeeworldsClient(args.host, args.port)

        self.map = None
        self.maprender = None
        
        self.tee_sprite = None  # Self tee sprite
        self.tees_sprites = None  # All tee sprites
        
        self.tee = None  # Self tee (controllable)
        self.tees = None  # All tees list
        self.tees_dict: dict[int, Tee] = {}  # Map of client_id -> Tee object for network tees
        
        self.mtarget = (0, 0)
        self.target = Vector2(0, 0)
        self.physics_engine = None
        
        self.pressed_keys = set()
        
        self._accumulated_time = 0.0
        
        self.ui = None
        
        self.zoom = DEFAULT_ZOOM

    def setup(self):
        self.map = MapLoader("maps/Volleyball_v2.map")
        self.maprender = MapRenderer(
            self.map,
            "assets/ddnet.png"
        )
        
        self.tee = Tee()
        self.tee.position = random.choice(self.map.spawners).position * 32 + Vector2(16, 16)
        
        self.tees = [self.tee]
        self.tees_dict[self.net.local_client_id] = self.tee

        self.tee_sprite = TeeSprite(self.tee)
        
        self.tees_sprites = arcade.SpriteList()
        self.tees_sprites.append(self.tee_sprite)
        
        self.physics_engine = DDNetPhysicsEngine(self.map, self.tees)
        
        # Text overlays (screen-space)
        self.coordinate_text = arcade.Text(
            "x: 0.00  y: 0.00",
            x=self.width - 12,
            y=12,
            color=arcade.color.WHITE,
            font_size=14,
            font_name="Courier New",
            anchor_x="right",
            anchor_y="bottom",
        )
        self.velocity_text = arcade.Text(
            "vx: 0.00  vy: 0.00",
            x=self.width - 12,
            y=32,
            color=arcade.color.WHITE,
            font_size=14,
            font_name="Courier New",
            anchor_x="right",
            anchor_y="bottom",
        )
        self.mtarget_text = arcade.Text(
            "mx: 0.00 my: 0.00, deg: 0.00",
            x=self.width - 12,
            y=52,
            color=arcade.color.WHITE,
            font_size=14,
            font_name="Courier New",
            anchor_x="right",
            anchor_y="bottom",
        )
        self.fps_text = arcade.Text(
            "FPS: 0",
            x=self.width - 12,
            y=72,
            color=arcade.color.WHITE,
            font_size=14,
            font_name="Courier New",
            anchor_x="right",
            anchor_y="bottom",
        )
        
        arcade.enable_timings()

    def on_draw(self):
        self.clear()
        self.camera.use()

        self.maprender.draw()
        self.tees_sprites.draw()
            
        for i, tee in self.tees_dict.items():
            # print(i, tee.hook_state)
            arcade.draw_line(
                tee.position.x * 2,
                tee.position.y * 2,
                tee.hookpos.x * 2,
                tee.hookpos.y * 2,
                arcade.color.YELLOW,
                3
            )

        # Draw UI/text in screen space
        self.gui_camera.use()
        self.coordinate_text.draw()
        self.velocity_text.draw()
        self.mtarget_text.draw()
        self.fps_text.draw()

    def on_update(self, dt):
        self.net.tick()
        
        for client_id, net_char in self.net.characters.items():
            if client_id == self.net.local_client_id:
                continue  # Skip self for now, just displaying other tees rn
            
            if client_id not in self.tees_dict:
                print("Created new tee for client", client_id, net_char.item_name)
                new_tee = Tee()
                new_tee.position = Vector2(net_char.x, net_char.y)
                new_tee.velocity = Vector2(net_char.vel_x, net_char.vel_y)
                new_tee.direction = net_char.direction
                new_tee.jumped = net_char.jumped
                new_tee.hook_state = HookState(net_char.hook_state)
                new_tee.hooktick = net_char.hook_tick
                new_tee.target = Vector2(net_char.hook_x, net_char.hook_y)

                self.tees_dict[client_id] = new_tee
                self.tees.append(new_tee)
                
                new_sprite = TeeSprite(new_tee)
                self.tees_sprites.append(new_sprite)
                
                self.physics_engine.add_tee(new_tee)
            else:
                # print("Updated tee for client", client_id, net_char.item_name, net_char.x, net_char.y, HookState(net_char.hook_state).name)
                tee = self.tees_dict[client_id]
                tee.position = Vector2(net_char.x, net_char.y)
                tee.velocity = Vector2(net_char.vel_x, net_char.vel_y)
                tee.direction = net_char.direction
                tee.jumped = net_char.jumped
                tee.hook_state = HookState(net_char.hook_state)
                tee.hooktick = net_char.hook_tick
                tee.target = Vector2(net_char.hook_x, net_char.hook_y)

        
        # Remove tees for disconnected clients
        # disconnected_ids = [cid for cid in self.tees_dict if cid not in self.net.characters and cid != self.net.local_client_id]
        # for client_id in disconnected_ids:
        #     tee_to_remove = self.tees_dict.pop(client_id)
        #     self.tees.remove(tee_to_remove)
        #     # Remove corresponding sprite (find and remove by tee reference)
        #     self.tees_sprites = arcade.SpriteList()
        #     for tee_obj in self.tees:
        #         self.tees_sprites.append(TeeSprite(tee_obj))
        
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
        
        self.mtarget_text.text = f"mx: {self.target.x / 64:.2f} my: {self.target.y / 64:.2f}, deg: {self.tee.angle:.2f}"
        
        self.tee.should_hook = arcade.MOUSE_BUTTON_RIGHT in self.pressed_keys
        
        self.physics_engine.update(dt)
            
        self.tees_sprites.update(dt)

        self.camera.position = self.tee_sprite.center_x, self.tee_sprite.center_y
        self.camera.zoom += (self.zoom - self.camera.zoom) * 0.2

        self.coordinate_text.text = f"x: {self.tee.position.x / 32:.2f}  y: {self.tee.position.y / 32:.2f}"
        self.velocity_text.text = f"vx: {self.tee.velocity.x / 32:.2f}  vy: {self.tee.velocity.y / 32:.2f}"
        
        self.fps_text.text = f"FPS: {arcade.get_fps():.2f}"

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
    parser = argparse.ArgumentParser(
        prog='uv run python -m gaming.main',
    )
    parser.add_argument("host")
    parser.add_argument("port", type=int)
    args = parser.parse_args()
    
    window = GameWindow(args)
    window.setup()
    
    def handler(signal_received, _):
        print(f"got signal: {signal_received}")
        print('SIGINT or CTRL-C detected. Exiting gracefully')
        window.net.disconnect()
        
        arcade.exit()       
        
        exit(0)

    signal(SIGINT, handler)
    
    arcade.run()
    
    window.net.disconnect()

if __name__ == "__main__":
    main()