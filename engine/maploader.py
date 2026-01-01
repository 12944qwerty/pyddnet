from twmap import Map

from engine.utils import get_tiles_mesh
from shared import Tile, TileType, Vector2

class MapLoader:
    def __init__(self, map_path: str):
        self.map = Map(map_path)
        
        self.tiles: dict[tuple, Tile] = {}
        
        # Unhookable and Hookable collidables
        self.collidables: list[Tile] = []
        
        self.spawners: list[Tile] = []
        
        self._build()
        
    def _build(self):
        for group in self.map.groups:
            for layer in group.layers:
                if layer.kind() != "Game":
                    continue

                for _id, position, uvs, flag in get_tiles_mesh(layer.tiles):
                    tile = Tile(
                        id=_id,
                        position=position,
                        uvs=uvs,
                        flags=flag
                    )
                    
                    self.tiles[(position.x, position.y)] = tile
                                        
                    match _id:
                        case TileType.UNHOOKABLE | TileType.HOOKABLE:
                            self.collidables.append(tile)
                        case TileType.SPAWN | TileType.REDSPAWN | TileType.BLUESPAWN:
                            self.spawners.append(tile)
                        case _:
                            pass
                        
    def get_tile(self, x, y) -> Tile:
        x = int(x // 32)
        y = int(y // 32)
        # print(int(x // 32), int(y // 32), self.tiles[(int(x // 32), int(y // 32))] if (int(x // 32), int(y // 32)) in self.tiles else "None")
        return self.tiles.get((x, y), Tile(0, Vector2(x, y), [], 0))