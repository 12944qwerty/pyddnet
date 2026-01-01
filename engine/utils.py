import numpy as np

from shared import Vector2

def get_tiles_mesh(tiles: np.ndarray):
    height, width, n = tiles.shape
        
    for y in range(height):
        for x in range(width):
            _id, bits = tiles[y, x]
            
            if _id == 0:
                continue         
            
            uv_row = 15 - (_id // 16)
            uv_col = _id % 16
            
            uvs = [
                ((uv_col + dx) / 16.0, (uv_row + dy) / 16.0)
                for dx, dy in ((0, 1), (1, 1), (1, 0), (0, 0))
            ]
            
            yield _id, Vector2(x, y), uvs, bits
        
    # return ids, verts, faces, faces_uv, flags