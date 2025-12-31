import arcade
from twmap import Map

from .constants import TILE_SIZE
from .utils import get_tiles_mesh, texture_region_from_uvs

class MapRenderer:
    def __init__(self, map_path: str, atlas_path: str):
        self.map = Map(map_path)
        self.atlas = arcade.load_texture(atlas_path)

        self.tiles = arcade.SpriteList(use_spatial_hash=True)
        self.terrain = arcade.SpriteList(use_spatial_hash=True)
        
        self.spawners = []

        self._build()

    def _build(self):
        for group in self.map.groups:
            for layer in group.layers:
                if layer.kind() != "Game":
                    continue

                for _id, face, uvs, flag in get_tiles_mesh(layer.tiles):
                    region = texture_region_from_uvs(uvs, self.atlas)

                    sprite = arcade.Sprite(
                        region,
                        scale=TILE_SIZE / region.width
                    )

                    x, y = face[0]
                    sprite.center_x = x * TILE_SIZE + TILE_SIZE / 2
                    sprite.center_y = -y * TILE_SIZE - TILE_SIZE / 2

                    # Flags (Teeworlds-compatible)
                    if flag & (1 << 0):
                        sprite.scale_x *= -1
                    if flag & (1 << 1):
                        sprite.scale_y *= -1
                    if flag & (1 << 3):
                        sprite.angle = 270

                    self.tiles.append(sprite)
                    
                    match _id:
                        case 1 | 3:
                            self.terrain.append(sprite)
                        case 192 | 193 | 194:
                            self.spawners.append((sprite.center_x, sprite.center_y))
                        case _:
                            pass


    def draw(self):
        self.tiles.draw()
