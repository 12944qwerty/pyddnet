from enum import IntEnum
import math

class Vector2:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        
    def dot(self, other) -> float:
        return self.x * other.x + self.y * other.y
        
    def normal(self):
        length = self.length()
        if length == 0:
            return Vector2(0, 0)
        l = 1.0 / length
        return Vector2(self.x * l, self.y * l)
    
    def length(self) -> float:
        return math.sqrt(self.dot(self))
    
    def distance(self, other) -> float:
        return (self - other).length()
        
    def __add__(self, other):
        return Vector2(self.x + other.x, self.y + other.y)
        
    def __sub__(self, other):
        return Vector2(self.x - other.x, self.y - other.y)
        
    def __mul__(self, scalar: float):
        return Vector2(self.x * scalar, self.y * scalar)
        
    def __truediv__(self, scalar: float):
        return Vector2(self.x / scalar, self.y / scalar)
    
    def __tuple__(self):
        return (self.x, self.y)
    
    def __hash__(self):
        return hash((self.x, self.y))
    
    def __iter__(self):
        yield self.x
        yield self.y
        
    def __repr__(self):
        return f"Vector2({self.x:.4f}, {self.y:.4f})"

# TODO: Fill out
class TileType(IntEnum):
    EMPTY = 0
    HOOKABLE = 1
    DEATH = 2
    UNHOOKABLE = 3
    
    FREEZE = 9
    UNFREEZE = 11
    DEEPFREEZE = 12
    UNDEEP = 13
    
    SPAWN = 192
    REDSPAWN = 193
    BLUESPAWN = 194

class Tile:
    def __init__(self, id: TileType, position: Vector2, uvs: list[tuple[float, float]], flags: int):
        self.id = id
        self.position = position
        self.uvs = uvs
        self.flags = flags
        
    def is_solid(self) -> bool:
        return self.id in {
            TileType.HOOKABLE,
            TileType.UNHOOKABLE,
        }
        
    def __repr__(self):
        return f"Tile(id={self.id}, position={self.position})"
    
class HookState(IntEnum):
    RETRACTED = -1
    IDLE = 0
    RETRACT_START = 1
    RETRACT_MIDDLE = 2
    RETRACT_END = 3
    FLYING = 4
    GRABBED = 5