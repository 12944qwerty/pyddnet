import arcade
from functools import lru_cache

from engine.maploader import MapLoader
from engine.constants import TILE_SIZE

@lru_cache()
def texture_region_from_uvs(uvs, texture: arcade.Texture):
    """
    uvs: [(u, v), (u, v), (u, v), (u, v)] in normalized space
    texture: arcade.Texture
    """
    us = [u for u, v in uvs]
    vs = [v for u, v in uvs]

    min_u, max_u = min(us), max(us)
    min_v, max_v = min(vs), max(vs)

    x = int(min_u * texture.width)
    y = int((1.0 - max_v) * texture.height)  # Arcade origin is bottom-left
    w = int((max_u - min_u) * texture.width)
    h = int((max_v - min_v) * texture.height)

    return arcade.Texture(
        name=f"region_{x}_{y}_{w}_{h}",
        image=texture.image.crop((x, y, x + w, y + h))
    )

class MapRenderer:
    def __init__(self, map: MapLoader, atlas_path: str):
        self.map = map
        self.atlas = arcade.load_texture(atlas_path)

        self.tiles = arcade.SpriteList(use_spatial_hash=True)
        
        self._build()
        
    def _build(self):
        for (x, y), tile in self.map.tiles.items():
            region = texture_region_from_uvs(tuple(tile.uvs), self.atlas)

            sprite = arcade.Sprite(
                region,
                scale=TILE_SIZE / region.width
            )

            sprite.center_x = x * TILE_SIZE + TILE_SIZE / 2
            sprite.center_y = -y * TILE_SIZE - TILE_SIZE / 2

            # Flags (Teeworlds-compatible)
            if tile.flags & (1 << 0):
                sprite.scale_x *= -1
            if tile.flags & (1 << 1):
                sprite.scale_y *= -1
            if tile.flags & (1 << 3):
                sprite.angle = 270

            self.tiles.append(sprite)    

    def draw(self):
        self.tiles.draw()
