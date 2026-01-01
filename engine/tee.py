from math import pow
import numpy as np

from engine.maploader import MapLoader
from shared import Vector2

from engine.constants import *

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

def velocity_ramp(value: float, start: float, range: float, curvature: float):
    if value < start:
        return 1.0
    return 1.0 / pow(curvature, (value - start) / range)

class Tee:
    def __init__(self):
        self.position = Vector2(0, 0)
        self.velocity = Vector2(0, 0)
        
        self.jumps = 2
        self.jumped = 0
        self.should_jump = False
        self.jump_count = 0
        
        self.direction = 0
        
    def tick(self, dt, map: MapLoader):
        grounded = map.get_tile(self.position.x + HITBOX_SIZE / 2, self.position.y + HITBOX_SIZE / 2 + 5).is_solid() or \
                   map.get_tile(self.position.x - HITBOX_SIZE / 2, self.position.y + HITBOX_SIZE / 2 + 5).is_solid()
                   
        # print(grounded, self.position / 32)
        
        self.velocity.y += GRAVITY
        
        MAXSPEED = GROUND_CONTROL_SPEED if grounded else AIR_CONTROL_SPEED
        ACCELERATION = GROUND_CONTROL_ACCEL if grounded else AIR_CONTROL_ACCEL
        FRICTION = GROUND_FRICTION if grounded else AIR_FRICTION
        
        if self.should_jump:
            if not (self.jumped & 1):
                if grounded and (not (self.jumped & 2) or self.jumps != 0):
                    self.velocity.y = -GROUND_JUMP_IMPULSE
                    if self.jumps > 1:
                        self.jumped |= 1
                    else:
                        self.jumped |= 3
                    self.jump_count = 0
                elif not (self.jumped & 2):
                    self.velocity.y = -AIR_JUMP_IMPULSE
                    self.jumped |= 3
                    self.jump_count += 1
        else:
            self.jumped &= ~1
        
        if grounded:
            self.jumped &= ~2
            self.jump_count = 0
            
        if self.direction < 0:
            self.velocity.x = saturated_add(-MAXSPEED, MAXSPEED, self.velocity.x, -ACCELERATION)
        if self.direction > 0:
            self.velocity.x = saturated_add(-MAXSPEED, MAXSPEED, self.velocity.x, ACCELERATION)
        if self.direction == 0:
            self.velocity.x *= FRICTION
        
    def move(self, dt, map: MapLoader):
        rampval = velocity_ramp(self.velocity.length() * 50, VELRAMP_START, VELRAMP_RANGE, VELRAMP_CURVATURE)
        
        self.velocity.x *= rampval
        
        newpos = self.position * 1
        oldvel = self.velocity * 1
        
        newpos, self.velocity, grounded = self._move_box(newpos, oldvel, map)
        
        if grounded:
            self.jumped &= ~2
            self.jump_count = 0
            
        colliding = 0
        if self.velocity.x < 0.001 and self.velocity.x > -0.001:
            if oldvel.x > 0:
                colliding = 1
            elif oldvel.x < 0:
                colliding = -1
        else:
            left_wall = True
            
        self.velocity.x *= 1.0 / rampval
        
        self.position = newpos
        
    def _move_box(self, _pos: Vector2, _vel: Vector2, map: MapLoader):
        grounded = False
        
        pos = _pos * 1
        vel = _vel * 1
        
        dist = vel.length()
        max = int(dist)
        
        if dist > 0.0001:
            fraction = 1.0 / (max + 1)
            
            for _ in range(max + 1):
                if vel == Vector2(0, 0):
                    break
                
                newpos = pos + vel * fraction
                
                if newpos == pos:
                    break
                
                if self._test_box(newpos, map):
                    hits = 0
                    
                    if self._test_box(Vector2(pos.x, newpos.y), map):
                        # grounded turns true if elasticity > 0
                        
                        newpos.y = pos.y
                        vel.y *= 0
                        hits += 1
                        
                    if self._test_box(Vector2(newpos.x, pos.y), map):
                        newpos.x = pos.x
                        vel.x *= 0
                        hits += 1
                        
                    if hits == 0:
                        newpos.y = pos.y
                        vel.y *= 0
                        newpos.x = pos.x
                        vel.x *= 0
                
                pos = newpos
                
        return pos, vel, grounded
                
    def _test_box(self, pos: Vector2, map: MapLoader) -> bool:
        # Check 4 corners
        if self._check_point(pos.x - HITBOX_SIZE / 2, pos.y - HITBOX_SIZE / 2, map):
            return True
        if self._check_point(pos.x + HITBOX_SIZE / 2, pos.y - HITBOX_SIZE / 2, map):
            return True
        if self._check_point(pos.x - HITBOX_SIZE / 2, pos.y + HITBOX_SIZE / 2, map):
            return True
        if self._check_point(pos.x + HITBOX_SIZE / 2, pos.y + HITBOX_SIZE / 2, map):
            return True
        return False
                        
    def _check_point(self, x, y, map: MapLoader) -> bool:
        return map.get_tile(x, y).is_solid()
        