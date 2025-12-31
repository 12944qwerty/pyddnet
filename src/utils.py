import numpy as np
from PIL import Image
import arcade

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

def crop_from_uvs(uvs, tex_width=1024, tex_height=1024):
    u_vals = [u for u, v in uvs]
    v_vals = [v for u, v in uvs]

    u_min, u_max = min(u_vals), max(u_vals)
    v_min, v_max = min(v_vals), max(v_vals)

    x_min = int(u_min * tex_width)
    x_max = int(u_max * tex_width)

    # flip V axis
    y_min = int((1.0 - v_max) * tex_height)
    y_max = int((1.0 - v_min) * tex_height)

    return (x_min, y_min, x_max, y_max)

def get_tiles_mesh(tiles: np.ndarray):
    height, width, n = tiles.shape
        
    for y in range(height):
        for x in range(width):
            _id, bits = tiles[y, x]
            
            if _id == 0:
                continue
            
            face = []
            for dx, dy in ((0, 0), (1, 0), (1, 1), (0, 1)):
                face.append((x + dx, y + dy))            
            
            uv_row = 15 - (_id // 16)
            uv_col = _id % 16
            
            uvs = [
                ((uv_col + dx) / 16.0, (uv_row + dy) / 16.0)
                for dx, dy in ((0, 1), (1, 1), (1, 0), (0, 0))
            ]
            
            yield _id, face, uvs, bits
        
    # return ids, verts, faces, faces_uv, flags

def get_texture_from_layer(layer, m):
    if layer.image is None:
        texture = Image.new("RGBA", (1024, 1024), (255, 255, 255, 255))
    else:
        texture = m.images[layer.image]
        if texture.is_external():
            texture = Image.open(f"assets/{texture.name}.png")
        else:
            texture = Image.fromarray(texture.data)
        
    assert texture.mode == "RGBA", texture.mode

    # multiply texture by layer color
    r, g, b, a = layer.color
    pixels = texture.load()
    for y in range(texture.height):
        for x in range(texture.width):
            pr, pg, pb, pa = pixels[x, y]
            pr = int(pr * r / 255)
            pg = int(pg * g / 255)
            pb = int(pb * b / 255)
            pa = int(pa * a / 255)
            pixels[x, y] = (pr, pg, pb, pa)
    
    return texture

def point2_length(point):
    return (point[0] ** 2 + point[1] ** 2) ** 0.5