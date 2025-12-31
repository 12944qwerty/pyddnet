import arcade

from .constants import *
from .player import Player

def saturated_add(min, max, current, mod):
    if mod < 0:
        if current < min:
            return current
        current += mod
        if current < min:
            current = min
        return current
    else:
        if current > max:
            return current
        current += mod
        if current > max:
            current = max
        return current

class DDNetPhysicsEngine:
    def __init__(
        self,
        player_sprite: Player,
        walls_sprite_list: arcade.SpriteList[arcade.Sprite],
    ):
        self.player = player_sprite
        self.walls = walls_sprite_list
        
    def update(self, dt):
        # check if grounded
        self.player.center_y -= 1
        grounded = arcade.check_for_collision_with_list(
            self.player,
            self.walls
        )
        self.player.center_y += 1
        
        self.player.change_y -= GRAVITY
        
        MAX_SPEED = GROUND_CONTROL_SPEED if grounded else AIR_CONTROL_SPEED
        ACCEL = GROUND_CONTROL_ACCEL if grounded else AIR_CONTROL_ACCEL
        FRICTION = GROUND_FRICTION if grounded else AIR_FRICTION
        
        if self.player.should_jump:
            if not (self.player.jumped & 1):
                if grounded and (not (self.player.jumped & 2) or self.player.jumps != 0):
                    self.player.change_y = GROUND_JUMP_IMPULSE
                    
                    if self.player.jumps > 1:
                        self.player.jumped |= 1
                    else:
                        self.player.jumped |= 3
                elif not (self.player.jumped & 2):
                    self.player.change_y = AIR_JUMP_IMPULSE
                    self.player.jumped |= 3
        else:
            self.player.jumped &= ~1
            
        if grounded:
            self.player.jumped &= ~2
        
        if self.player.direction < 0:
            self.player.change_x = saturated_add(
                -MAX_SPEED,
                MAX_SPEED,
                self.player.change_x,
                -ACCEL
            )
        if self.player.direction > 0:
            self.player.change_x = saturated_add(
                -MAX_SPEED,
                MAX_SPEED,
                self.player.change_x,
                ACCEL
            )
        if self.player.direction == 0:
            self.player.change_x *= FRICTION



        self.player.update(dt, self)