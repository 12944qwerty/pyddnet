import math
import numpy as np

from engine.maploader import MapLoader
from shared import *

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
    return 1.0 / math.pow(curvature, (value - start) / range)

class Tee:
    def __init__(self):
        self.position = Vector2(0, 0)
        self.velocity = Vector2(0, 0)
        
        self.jumps = 2
        self.jumped = 0
        self.should_jump = False
        self.jump_count = 0
        
        self.direction = 0
        
        self.should_hook = False
        self.angle = 0.0
        self.target = Vector2(0, 0)
        
        self.newhook = False
        self.hookpos = Vector2(0, 0)
        self.hookdir = Vector2(0, 0)
        self.hooktick = 0
        self.hook_state = HookState.RETRACTED
        self.hook_telebase = Vector2(0, 0)
        
        self.target_direction = Vector2(0, 0)
        
        self.reset = False
        
    def tick(self, dt, map: MapLoader):
        grounded = map.get_tile(self.position.x + HITBOX_SIZE / 2, self.position.y + HITBOX_SIZE / 2 + 5).is_solid() or \
                   map.get_tile(self.position.x - HITBOX_SIZE / 2, self.position.y + HITBOX_SIZE / 2 + 5).is_solid()
                   
        self.target_direction = self.target.normal()
                   
        # print(grounded, self.position / 32)
        
        self.velocity.y += GRAVITY
        
        MAXSPEED = GROUND_CONTROL_SPEED if grounded else AIR_CONTROL_SPEED
        ACCELERATION = GROUND_CONTROL_ACCEL if grounded else AIR_CONTROL_ACCEL
        FRICTION = GROUND_FRICTION if grounded else AIR_FRICTION
        
        tmpangle = math.atan2(self.target.y / 32, self.target.x / 32)
        if tmpangle < -(math.pi / 2):
            self.angle = int(tmpangle + (2 * math.pi) * 256)
        else:
            self.angle = int(tmpangle * 256)
        
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
            
        if self.should_hook:
            if self.hook_state == HookState.IDLE:
                self.hook_state = HookState.FLYING
                self.hookpos = self.position + self.target_direction * 28 * 1.5
                self.hookdir = self.target_direction * 1
                
                self.hooktick = 50 * (1.25 - HOOK_DURATION)
        else:
            self.hook_state = HookState.IDLE
            self.hookpos = self.position * 1
        
        if grounded:
            self.jumped &= ~2
            self.jump_count = 0
            
        if self.direction < 0:
            self.velocity.x = saturated_add(-MAXSPEED, MAXSPEED, self.velocity.x, -ACCELERATION)
        if self.direction > 0:
            self.velocity.x = saturated_add(-MAXSPEED, MAXSPEED, self.velocity.x, ACCELERATION)
        if self.direction == 0:
            self.velocity.x *= FRICTION
            
        match self.hook_state:
            case HookState.IDLE | HookState.RETRACTED:
                self.hookpos = self.position * 1
            case HookState.RETRACT_START:
                self.hook_state = HookState.RETRACT_MIDDLE
            case HookState.RETRACT_MIDDLE:
                self.hook_state = HookState.RETRACT_END
            case HookState.RETRACT_END:
                self.hook_state = HookState.RETRACTED
            case HookState.FLYING:
                hookbase = self.position * 1
                
                # if self.newhook:
                #     hookbase = self.hooktelebase
                    
                newpos = self.hookpos + self.hookdir * HOOK_FIRE_SPEED
                if hookbase.distance(newpos) > HOOK_LENGTH:
                    self.hook_state = HookState.RETRACT_START
                    newpos = hookbase + (newpos - hookbase).normal() * HOOK_LENGTH
                    self.reset = True
                    
                going_to_hit_ground = False
                going_to_retract = False
                
                hit, newpos = self._intersect_line_hook(self.hookpos, newpos, map)
                
                if hit == 1: # Hookable
                    going_to_hit_ground = True
                    self.reset = True
                if hit == 2: # Unhookable
                    going_to_retract = True
                    self.reset = True
                    
                if self.hook_state == HookState.FLYING:
                    if going_to_hit_ground:
                        self.hook_state = HookState.GRABBED
                    if going_to_retract:
                        self.hook_state = HookState.RETRACT_START
                        
                    self.hookpos = newpos
                    
        if self.hook_state == HookState.GRABBED:
            if self.hookpos.distance(self.position) > 46:
                hookvel = (self.hookpos - self.position).normal() * HOOK_DRAG_ACCEL
                
                if hookvel.y > 0:
                    hookvel.y *= 0.3
                    
                if (hookvel.x < 0 and self.direction < 0) or (hookvel.x > 0 and self.direction > 0):
                    hookvel.x *= 0.95
                else:
                    hookvel.x *= 0.75
                    
                newvel = self.velocity + hookvel
                newvellen = newvel.length()
                
                if newvellen < HOOK_DRAG_SPEED or newvellen < self.velocity.length():
                    self.velocity = newvel
                    
            self.hooktick += 1
            

        if self.velocity.length() > 6000:
            self.velocity = self.velocity.normal() * 6000
        
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
        
    def post_tick(self, dt, map: MapLoader):
        tile = map.get_tile(self.position.x, self.position.y, layer="Tele")
        
        if isinstance(tile, TeleTile):
            if tile.is_teleporter():
                dest = map.get_teleport_destination(tile)
                if dest is not None:
                    self.position = dest * 1
                    if tile.is_red():
                        self.velocity = Vector2(0, 0)
                        # self.hooktelebase = self.position * 1
                        # self.newhook = True
                        
                    
        
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
        
    def _intersect_line_hook(self, pos0: Vector2, pos1: Vector2, map: MapLoader) -> tuple[int, Vector2]:
        distance = pos0.distance(pos1)
        end = int(distance + 1)
        last = pos0 * 1
        
        for i in range(end + 1):
            t = i / end
            check_pos = (pos0 * (1 - t)) + (pos1 * t)
            tile = map.get_tile(check_pos.x, check_pos.y)
            # print(check_pos, tile)
            if tile.is_solid():
                if tile.is_hookable():
                    return 1, check_pos
                else:
                    return 2, last
            last = check_pos * 1
            
        return 0, pos1