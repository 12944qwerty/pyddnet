from twmap import Map

from engine.utils import get_tiles_mesh
from shared import *

class MapLoader:
    def __init__(self, map_path: str):
        self.map = Map(map_path)
        
        print(self.map.info.settings)
        
        self.tiles: dict[tuple, list[Tile]] = {}
        
        # Unhookable and Hookable collidables
        self.collidables: list[GameTile] = []
        
        self.spawners: list[GameTile] = []
        
        self.teles: dict[tuple, TeleTile] = {}
        self.dests: dict[tuple, TeleTile] = {}
        self.cps: dict[tuple, TeleTile] = {}
        
        self._build()
        
    def _build(self):
        for group in self.map.groups:
            for layer in group.layers:
                match layer.kind():
                    case "Game":
                        for _id, position, uvs, flags in get_tiles_mesh(layer.tiles, "Game"):
                            tile = GameTile(
                                id=_id,
                                position=position,
                                uvs=uvs,
                                flags=flags
                            )
                            
                            if (position.x, position.y) not in self.tiles:
                                self.tiles[(position.x, position.y)] = []
                            self.tiles[(position.x, position.y)].append(tile)
                                                
                            match _id:
                                case GameTileType.UNHOOKABLE | GameTileType.HOOKABLE:
                                    self.collidables.append(tile)
                                case GameTileType.SPAWN | GameTileType.REDSPAWN | GameTileType.BLUESPAWN:
                                    self.spawners.append(tile)
                                case _:
                                    pass
                        
                    case "Tele":
                        for _id, position, uvs, number in get_tiles_mesh(layer.tiles, "Tele"):
                            # print(_id, number)
                            tile = TeleTile(
                                id=_id,
                                position=position,
                                uvs=uvs,
                                number=number
                            )
                            
                            if (position.x, position.y) not in self.tiles:
                                self.tiles[(position.x, position.y)] = []
                            self.tiles[(position.x, position.y)].append(tile)
                            
                            if tile.is_teleporter():
                                self.teles[(position.x, position.y)] = tile
                            elif tile.is_destination():
                                self.dests[(position.x, position.y)] = tile
                            elif tile.is_checkpoint():
                                self.cps[(position.x, position.y)] = tile
                        
    def get_tile(self, x, y, layer: str = "Game") -> Tile:
        x = int(x // 32)
        y = int(y // 32)
    
        if (x, y) in self.tiles:
            for tile in self.tiles[(x, y)]:
                if tile.layer == layer:
                    return tile
        return Tile.EMPTY
    
    def get_teleport_destination(self, tele_tile: TeleTile) -> Vector2 | None:
        for dest in self.dests.values():
            if dest.number == tele_tile.number:
                return dest.position * 32 + Vector2(16, 16)
        return None