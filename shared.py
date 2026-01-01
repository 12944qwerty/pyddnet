from enum import IntEnum

class Vector2:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        
    def __add__(self, other):
        return Vector2(self.x + other.x, self.y + other.y)
        
    def __sub__(self, other):
        return Vector2(self.x - other.x, self.y - other.y)
        
    def __mul__(self, scalar: float):
        return Vector2(self.x * scalar, self.y * scalar)
        
    def __truediv__(self, scalar: float):
        return Vector2(self.x / scalar, self.y / scalar)
    
    def length(self) -> float:
        return (self.x ** 2 + self.y ** 2) ** 0.5
    
    def __tuple__(self):
        return (self.x, self.y)
    
    def __hash__(self):
        return hash((self.x, self.y))
        
    def __repr__(self):
        return f"Vector2({self.x}, {self.y})"

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