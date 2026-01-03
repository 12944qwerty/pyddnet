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
class GameTileType(IntEnum):
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
    
    @classmethod
    def _missing_(cls, value):
        return cls.EMPTY
    
class TeleTileType(IntEnum):
    RED_TELE = 10
    BLUE_TELE = 26
    TELE_DEST = 27
    
    CHECKPOINT = 29
    CP_TELE_DEST = 30
    CP_BLUE_TELE = 31
    CP_RED_TELE = 63
    
    WEAP_TELE = 14
    HOOK_TELE = 15

class Tile:    
    def __init__(self, id: int, position: Vector2, layer: str):
        self.id = id
        self.position = position
        
        self.layer = layer
        
    def is_tele(self) -> bool:
        return self.layer == "Tele"
    
    def is_solid(self) -> bool:
        return False
    
    def is_hookable(self) -> bool:
        return False
        
    def __repr__(self):
        return f"Tile(id={self.id}, position={self.position})"


Tile.EMPTY = Tile(0, Vector2(0, 0), "None")
    
class GameTile(Tile):
    def __init__(self, id: GameTileType, position: Vector2, uvs: list[tuple[float, float]], flags: int):
        super().__init__(GameTileType(id), position, "Game")
        self.uvs = uvs
        self.flags = flags
        
    def is_solid(self) -> bool:
        return self.id in (GameTileType.HOOKABLE, GameTileType.UNHOOKABLE)
        
    def is_hookable(self) -> bool:
        return self.id == GameTileType.HOOKABLE

class TeleTile(Tile):
    def __init__(self, id: TeleTileType, position: Vector2, uvs: list[tuple[float, float]], number: int):
        super().__init__(TeleTileType(id), position, "Tele")
        self.uvs = uvs
        self.number = number
        
    def is_destination(self) -> bool:
        return self.id in (TeleTileType.TELE_DEST, TeleTileType.CP_TELE_DEST)
    
    def is_checkpoint(self) -> bool:
        return self.id in (TeleTileType.CHECKPOINT, TeleTileType.CP_TELE_DEST, TeleTileType.CP_BLUE_TELE, TeleTileType.CP_RED_TELE)
    
    def is_teleporter(self) -> bool:
        return self.id in (TeleTileType.RED_TELE, TeleTileType.BLUE_TELE, TeleTileType.CP_BLUE_TELE, TeleTileType.CP_RED_TELE)
    
    def is_red(self) -> bool:
        return self.id in (TeleTileType.RED_TELE, TeleTileType.CP_RED_TELE)
    
class HookState(IntEnum):
    RETRACTED = -1
    IDLE = 0
    RETRACT_START = 1
    RETRACT_MIDDLE = 2
    RETRACT_END = 3
    FLYING = 4
    GRABBED = 5