import math
import osmium
from shapely.geometry import LineString, Polygon, MultiPolygon, GeometryCollection, MultiLineString
from shapely.ops import transform
from pyproj import Transformer
from PIL import Image, ImageDraw, ImageFont
import os
import pyqtree

road_zoom_levels = {
    'motorway': {'min_zoom': 5, 'max_zoom': 18},
    'motorway_link': {'min_zoom': 5, 'max_zoom': 18},
    'primary': {'min_zoom': 8, 'max_zoom': 18},
    'primary_link': {'min_zoom': 8, 'max_zoom': 18},
    'secondary': {'min_zoom': 11, 'max_zoom': 18},
    'secondary_link': {'min_zoom': 11, 'max_zoom': 18},
    'tertiary': {'min_zoom': 13, 'max_zoom': 18},
    'tertiary_link': {'min_zoom': 13, 'max_zoom': 18},
    'residential': {'min_zoom': 15, 'max_zoom': 18},
    'unclassified': {'min_zoom': 15, 'max_zoom': 18},
    'service': {'min_zoom': 5, 'max_zoom': 18},
    'path': {'min_zoom': 17, 'max_zoom': 18},
    'cycleway': {'min_zoom': 17, 'max_zoom': 18},
    # 'construction': {'min_zoom': 15, 'max_zoom': 18},
    'trunk': {'min_zoom': 7, 'max_zoom': 18},
}

road_colors = {
    # 'motorway': (255, 0, 0),
    # 'motorway_link': (255, 128, 128),
    'primary': (252, 214, 164),
    # 'primary_link': (255, 200, 128),
    'secondary': (255, 255, 255),
    # 'secondary_link': (255, 255, 128),
    'tertiary': (255, 255, 255),
    # 'tertiary_link': (128, 255, 128),
    # 'residential': (255, 255, 255),
    # 'unclassified': (128, 128, 255),
    # 'service': (255, 255, 255),
    # 'path': (128, 128, 128),
    # 'cycleway': (0, 255, 255),
    # 'construction': (255, 0, 255),
    'trunk': (249, 178, 156),
}

ROAD_DEFAULT_COLOR = (255, 255, 255)

road_outline_colors = {
    # 'motorway': (200, 0, 0),
    # 'motorway_link': (200, 100, 100),
    # 'primary': road_colors['primary'],
    # 'primary_link': (200, 160, 100),
    # 'secondary': road_colors['secondary'],
    # 'secondary_link': (200, 200, 100),
    # 'tertiary': road_colors['tertiary'],
    # 'tertiary_link': (100, 200, 100),
    # 'residential': (0, 0, 200),
    # 'unclassified': (100, 100, 200),
    # 'service': (200, 200, 200),
    # 'path': (100, 100, 100),
    # 'cycleway': (0, 200, 200),
    # 'construction': (200, 0, 200),
    'trunk': road_colors['trunk'],
}

ROAD_OUTLINE_DEFAULT_COLOR = (200, 200, 200)

road_outline_width = {
    # 'motorway': 10,
    # 'motorway_link': 10,
    'primary': 48,
    # 'primary_link': 10,
    'secondary': 36,
    # 'secondary_link': 10,
    'tertiary': 24,
    # 'tertiary_link': 10,
    # 'residential': 10,
    # 'unclassified': 10,
    # 'service': 10,
    # 'path': 10,
    # 'cycleway': 10,
    # 'construction': 10,
    'trunk': 24,
}

ROAD_OUTLINE_DEFAULT_WIDTH = 20

green_area_zoom_levels = {
    'park': {'min_zoom': 10, 'max_zoom': 18},
    'forest': {'min_zoom': 10, 'max_zoom': 18},
    'grass': {'min_zoom': 10, 'max_zoom': 18},
    'meadow': {'min_zoom': 10, 'max_zoom': 18},
    'recreation_ground': {'min_zoom': 10, 'max_zoom': 18},
    'garden': {'min_zoom': 10, 'max_zoom': 18},
}

waterway_zoom_levels = {
    'river': {'min_zoom': 10+2, 'max_zoom': 18},
    'stream': {'min_zoom': 12+2, 'max_zoom': 18},
    'canal': {'min_zoom': 10+2, 'max_zoom': 18},
    'drain': {'min_zoom': 12+2, 'max_zoom': 18},
    'ditch': {'min_zoom': 12+2, 'max_zoom': 18},
    'water': {'min_zoom': 10, 'max_zoom': 18},  # Add this line
}

green_area_colors = {
    'park': (200, 250, 204),
    'forest': (173, 209, 158),
    'grass': (205, 235, 176),
    'meadow': (205, 235, 176),
    'recreation_ground': (223, 252, 226),
    'garden': (0, 255, 127),
}

GREEN_AREA_DEFAULT_COLOR = (200, 250, 204)

FONT_SIZE = 20

def tile_to_bbox(z, x, y):
    n = 2.0 ** z
    lon_min = x / n * 360.0 - 180.0
    lat_min = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    lon_max = (x + 1) / n * 360.0 - 180.0
    lat_max = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (y + 1) / n))))
    return (lon_min, lat_min, lon_max, lat_max)

def lonlat_to_tile(z, lon, lat):
    """
    Convert longitude and latitude to tile x, y at zoom level z.
    """
    n = 2.0 ** z
    x_tile = int((lon + 180.0) / 360.0 * n)
    lat_rad = math.radians(lat)
    y_tile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    # Clamp y_tile to [0, 2^z -1]
    y_tile = max(0, min(int(n) - 1, y_tile))
    return x_tile, y_tile

class BoundingBoxHandler(osmium.SimpleHandler):
    """
    Handler to compute the bounding box of an OSM file.
    """
    def __init__(self):
        super(BoundingBoxHandler, self).__init__()
        self.min_lon = math.inf
        self.min_lat = math.inf
        self.max_lon = -math.inf
        self.max_lat = -math.inf

    def node(self, n):
        if n.lon < self.min_lon:
            self.min_lon = n.lon
        if n.lon > self.max_lon:
            self.max_lon = n.lon
        if n.lat < self.min_lat:
            self.min_lat = n.lat
        if n.lat > self.max_lat:
            self.max_lat = n.lat

    def way(self, w):
        for node in w.nodes:
            self.node(node)

    def relation(self, r):
        for member in r.members:
            if isinstance(member, osmium.osm.Node):
                self.node(member)

class OSMHandler(osmium.SimpleHandler):
    def __init__(self, transformer, quadtrees, font_path="arial.ttf", font_size=12):
        super(OSMHandler, self).__init__()
        self.transformer = transformer
        self.quadtrees = quadtrees
        self.lines = []
        self.polygons = []
        
        # 初始化字体
        try:
            self.font = ImageFont.truetype(font_path, font_size)
            print(f"Loaded font '{font_path}' with size {font_size}.")
        except IOError:
            # 如果指定字体加载失败，使用默认字体
            self.font = ImageFont.load_default()
            print(f"Failed to load font '{font_path}'. Using default font.")

    def way(self, w):
        # 处理道路
        if 'highway' in w.tags:
            road_type = w.tags['highway']
            if road_type == 'construction' and 'construction' in w.tags:
                road_type = w.tags['construction']
                print('fallbacked to', road_type)
            if road_type in road_zoom_levels:
                min_z = road_zoom_levels[road_type]['min_zoom']
                max_z = road_zoom_levels[road_type]['max_zoom']
                coords = [(node.lon, node.lat) for node in w.nodes]
                if len(coords) < 2:
                    return
                line = LineString(coords)
                projected = transform(self.transformer.transform, line)
                
                # 将道路插入到对应的四叉树中
                for z in range(min_z, max_z + 1):
                    self.quadtrees[z].insert({ 'type': 'road', 'element': projected, 'fined_type': road_type }, projected.bounds)

        # 处理建筑物
        if 'building' in w.tags:
            coords = [(node.lon, node.lat) for node in w.nodes]
            if len(coords) < 3:
                return
            if coords[0] != coords[-1]:
                coords.append(coords[0])
            polygon = Polygon(coords)
            if not polygon.is_valid:
                polygon = polygon.buffer(0)
            projected = transform(self.transformer.transform, polygon)
            
            # 确定显示的缩放级别
            min_z, max_z = 14, 18
            
            # 将建筑物插入到对应的四叉树中
            for z in range(min_z, max_z + 1):
                self.quadtrees[z].insert({ 'type': 'building', 'element': projected }, projected.bounds)
            
            # 处理建筑物名称标签
            if 'name' in w.tags:
                self._handle_building_name(projected, w.tags['name'], min_z + 3, max_z)

        # 处理绿地
        if 'landuse' in w.tags or 'leisure' in w.tags or 'natural' in w.tags:
            landuse_type = w.tags.get('landuse') or w.tags.get('leisure') or w.tags.get('natural')
            if landuse_type in green_area_zoom_levels:
                min_z = green_area_zoom_levels[landuse_type]['min_zoom']
                max_z = green_area_zoom_levels[landuse_type]['max_zoom']
                coords = [(node.lon, node.lat) for node in w.nodes]
                if len(coords) < 3:
                    return
                if coords[0] != coords[-1]:
                    coords.append(coords[0])
                polygon = Polygon(coords)
                if not polygon.is_valid:
                    polygon = polygon.buffer(0)
                projected = transform(self.transformer.transform, polygon)
                
                for z in range(min_z, max_z + 1):
                    self.quadtrees[z].insert({ 'type': 'green_area', 'element': projected, 'landuse_type': landuse_type }, projected.bounds)
        
        # 处理河流
        if 'waterway' in w.tags:
            waterway_type = w.tags['waterway']
            if waterway_type in waterway_zoom_levels:
                min_z = waterway_zoom_levels[waterway_type]['min_zoom']
                max_z = waterway_zoom_levels[waterway_type]['max_zoom']
                coords = [(node.lon, node.lat) for node in w.nodes]
                if len(coords) < 2:
                    return
                line = LineString(coords)
                projected = transform(self.transformer.transform, line)
                
                for z in range(min_z, max_z + 1):
                    self.quadtrees[z].insert({ 'type': 'waterway', 'element': projected }, projected.bounds)

        # 处理水域
        if 'natural' in w.tags and w.tags['natural'] == 'water':
            coords = [(node.lon, node.lat) for node in w.nodes]
            if len(coords) < 3:
                return
            if coords[0] != coords[-1]:
                coords.append(coords[0])
            polygon = Polygon(coords)
            if not polygon.is_valid:
                polygon = polygon.buffer(0)
            projected = transform(self.transformer.transform, polygon)
            
            min_z, max_z = 10, 18  # 定义水��的缩放级别
            
            for z in range(min_z, max_z + 1):
                self.quadtrees[z].insert({ 'type': 'water_area', 'element': projected }, projected.bounds)

    def _handle_building_name(self, polygon, name, min_z, max_z):
        """
        根据建筑物大小和缩放级别计算文本标签的位置和尺寸，并插入到对应的四叉树中。
        """
        # 使用PIL计算文本尺寸
        dummy_img = Image.new('RGB', (1, 1))
        draw = ImageDraw.Draw(dummy_img)
        bbox = draw.textbbox((0, 0), name, font=self.font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # 获取建筑物多边形的质心
        centroid = polygon.centroid
        projected_centroid = centroid  # 假设多边形已投影

        # 定义文本的边界框，居中于质心
        minx = projected_centroid.x - text_width / 2
        miny = projected_centroid.y - text_height / 2
        maxx = projected_centroid.x + text_width / 2
        maxy = projected_centroid.y + text_height / 2

        # 将文本信息插入到对应缩放级别的四叉树中
        for z in range(min_z, max_z +1):
            self.quadtrees[z].insert({
                'type': 'text',
                'element': {
                    'text': name,
                    'position': (projected_centroid.x, projected_centroid.y),
                    'size': (text_width, text_height)
                }
            }, (minx, miny, maxx, maxy))
    
    def relation(self, r):
        # 可以根据需要实现关系（relation）的处理
        pass
            
quadtrees = {z: pyqtree.Index(bbox=(-20037508.342789244, -20037508.342789244,
                                    20037508.342789244, 20037508.342789244)) for z in range(1, 19)}

BACKGROUND_COLOR = (242, 239, 233)
BUILDING_COLOR = (217, 208, 201)
BUILDING_OUTLINE_COLOR = (197, 184, 174)
WATERWAY_COLOR = (170, 211, 223)
eps = 1e-7

def on_border(point):
    return point[0] < eps or 512 - point[0] < eps or point[1] < eps or 512 - point[1] < eps

def draw_polygon(draw, polygon, scale, outline_color, fill_color, background_color):
    """
    绘制建筑物多边形及其内环。
    """
    def draw_polygon_outline(polygon: Polygon, color):

        is_on_border = [on_border(point) for point in polygon]
        for point_index in range(1, len(polygon)):
            if is_on_border[point_index - 1] and is_on_border[point_index]:
                continue
            draw.line([polygon[point_index - 1], polygon[point_index]], fill=color, width=2)
    
    exterior = [scale(coord) for coord in polygon.exterior.coords]
    draw.polygon(exterior, fill=fill_color)
    draw_polygon_outline(exterior, color=outline_color)

    # 绘制内环（孔洞）
    for interior in polygon.interiors:
        interior_coords = [scale(coord) for coord in interior.coords]
        draw.polygon(interior_coords, fill=background_color)
        draw_polygon_outline(interior_coords, color=outline_color)

def draw_green_area(draw, polygon, scale, landuse_type):
    """
    绘制绿地多边形。
    """
    fill_color = green_area_colors.get(landuse_type, GREEN_AREA_DEFAULT_COLOR) # default to green
    exterior = [scale(coord) for coord in polygon.exterior.coords]
    draw.polygon(exterior, fill=fill_color)

    for interior in polygon.interiors:
        interior_coords = [scale(coord) for coord in interior.coords]
        draw.polygon(interior_coords, fill=BACKGROUND_COLOR)

def real_draw_road(draw, line_pixels, width, color):
    if width <= 0:
        return
    half_width = width // 2 - 0.5

    if half_width > 0:
        for point in line_pixels:
            if not on_border(point):
                draw.ellipse([(point[0] - half_width, point[1] - half_width), (point[0] + half_width, point[1] + half_width)], fill=color)

    for i in range(1, len(line_pixels)):
        ext_1 = (50 * line_pixels[i - 1][0] - 49 * line_pixels[i][0], 50 * line_pixels[i - 1][1] - 49 * line_pixels[i][1])
        ext_2 = (50 * line_pixels[i][0] - 49 * line_pixels[i - 1][0], 50 * line_pixels[i][1] - 49 * line_pixels[i - 1][1])
        
        p1 = ext_1 if on_border(line_pixels[i - 1]) else line_pixels[i - 1]
        p2 = ext_2 if on_border(line_pixels[i]) else line_pixels[i]
        draw.line([p1, p2], fill=color, width=int(width))
        
def draw_road(draw, line, scale, road_type, width, color=None, outline_color=None, outline=False):
    """
    绘制道路（线条）。
    """
    if len(line.coords) < 2:
        return
    line_pixels = [scale(coord) for coord in line.coords]
    
    if color is None:
        color = road_colors.get(road_type, ROAD_DEFAULT_COLOR)
    if outline_color is None:
        outline_color = road_outline_colors.get(road_type, ROAD_OUTLINE_DEFAULT_COLOR)
    
    if width <= 4:
        if outline: real_draw_road(draw, line_pixels, width, color)
    elif outline:
        real_draw_road(draw, line_pixels, width, outline_color)
    else:
        real_draw_road(draw, line_pixels, width - 4, color)

def draw_waterway(draw, line, scale, color, width):
    """
    绘制河流（线条）。
    """
    if len(line.coords) < 2:
        return
    line_pixels = [scale(coord) for coord in line.coords]
    draw.line(line_pixels, fill=color, width=width)

def draw_text(draw, text_item, scale, font):
    """
    在指定位置绘制文本标签。
    """
    name = text_item.get('text', '')
    position = text_item.get('position', (0, 0))
    size = text_item.get('size', (0, 0))

    if not name:
        return  # 如果没有文本，跳过

    # 计算像素位置
    px, py = scale(position)

    # 调整位置以居中文本
    text_width, text_height = size
    text_x = px - text_width / 2
    text_y = py - text_height / 2

    # 绘制文本
    draw.text((text_x, text_y), name, font=font, fill="black")  # 示例文本颜色

def draw_water_area(draw, polygon, scale):
    """
    绘制水域多边形。
    """
    exterior = [scale(coord) for coord in polygon.exterior.coords]
    draw.polygon(exterior, fill=WATERWAY_COLOR)

    for interior in polygon.interiors:
        interior_coords = [scale(coord) for coord in interior.coords]
        draw.polygon(interior_coords, fill=BACKGROUND_COLOR)

def classify_items(items):
    ret = {}
    for item in items:
        if item['type'] not in ret:
            ret[item['type']] = []
        ret[item['type']].append(item)
    return ret

def filter_polygons(items, tile_polygon):
    ret = []
    for item in items:
        polygon = item['element']
        if not polygon.intersects(tile_polygon):
            continue
        clipped = polygon.intersection(tile_polygon)
        if clipped.is_empty:
            continue

        geom_types = []
        if isinstance(clipped, (Polygon, MultiPolygon)):
            geom_types.append(clipped)
        elif isinstance(clipped, GeometryCollection):
            geom_types.extend([geom for geom in clipped if isinstance(geom, (Polygon, MultiPolygon))])

        for geom in geom_types:
            if isinstance(geom, Polygon):
                ret.append({ 'element': geom, 'landuse_type': item.get('landuse_type') })
            elif isinstance(geom, MultiPolygon):
                for sub_geom in geom.geoms:
                    ret.append({ 'element': sub_geom, 'landuse_type': item.get('landuse_type') })
    return ret

def filter_lines(items, tile_polygon):
    ret = []
    for item in items:
        line = item['element']
        if not line.intersects(tile_polygon):
            continue
        clipped = line.intersection(tile_polygon)
        if clipped.is_empty:
            continue

        if isinstance(clipped, LineString):
            ret.append({ 'element': clipped, 'fined_type': item.get('fined_type') })
        elif isinstance(clipped, MultiLineString):
            for geom in clipped.geoms:
                if isinstance(geom, LineString):
                    ret.append({ 'element': geom, 'fined_type': item.get('fined_type') })
        elif isinstance(clipped, GeometryCollection):
            for geom in clipped:
                if isinstance(geom, LineString):
                    ret.append({ 'element': geom, 'fined_type': item.get('fined_type') })
    return ret

def generate_tile(z, x, y, quadtrees, font):
    
    # 计算瓦片边界
    bbox = tile_to_bbox(z, x, y)
    lon_min, lat_min, lon_max, lat_max = bbox

    # 初始化坐标转换器（EPSG:4326 到 EPSG:3857）
    transformer = Transformer.from_crs("epsg:4326", "epsg:3857", always_xy=True)

    # 定义瓦片在Web Mercator中的边界
    tile_min_x, tile_min_y = transformer.transform(lon_min, lat_min)
    tile_max_x, tile_max_y = transformer.transform(lon_max, lat_max)
    tile_bbox = (tile_min_x, tile_min_y, tile_max_x, tile_max_y)

    # 定义缩放函数：从Web Mercator坐标到像素坐标
    def scale(coord):
        x_coord, y_coord = coord
        px = (x_coord - tile_min_x) / (tile_max_x - tile_min_x) * img_size
        py = (y_coord - tile_min_y) / (tile_max_y - tile_min_y) * img_size
        return (px, py)
    
    # 查询当前缩放级别的四叉树
    items = classify_items(quadtrees[z].intersect(tile_bbox))

    # 创建图像
    img_size = 512
    img = Image.new("RGB", (img_size, img_size), BACKGROUND_COLOR)
    draw = ImageDraw.Draw(img)
    drawed = False  # 标记是否绘制了任何元素

    # 定义瓦片多边形，用于裁剪检查
    tile_polygon = Polygon([
        (tile_min_x, tile_min_y),
        (tile_max_x, tile_min_y),
        (tile_max_x, tile_max_y),
        (tile_min_x, tile_max_y)
    ])

    # draw buildings
    if 'building' in items:
        buildings = filter_polygons(items['building'], tile_polygon)
        drawed |= len(buildings) > 0
        for building in buildings:
            draw_polygon(draw, building['element'], scale, BUILDING_OUTLINE_COLOR, BUILDING_COLOR, BACKGROUND_COLOR)

    # draw green areas
    if 'green_area' in items:
        green_areas = filter_polygons(items['green_area'], tile_polygon)
        drawed |= len(green_areas) > 0
        for green_area in green_areas:
            draw_green_area(draw, green_area['element'], scale, green_area['landuse_type'])

    # draw waterways
    if 'waterway' in items:
        waterways = filter_lines(items['waterway'], tile_polygon)
        drawed |= len(waterways) > 0
        for waterway in waterways:
            draw_waterway(draw, waterway['element'], scale, WATERWAY_COLOR, 4)
    
    # draw water areas
    if 'water_area' in items:
        water_areas = filter_polygons(items['water_area'], tile_polygon)
        drawed |= len(water_areas) > 0
        for water_area in water_areas:
            draw_water_area(draw, water_area['element'], scale)
    
    # draw roads
    if 'road' in items:
        ROAD_WIDTH_DECEASE_RATE = 1.9
        roads = filter_lines(items['road'], tile_polygon)
        drawed |= len(roads) > 0
        for road in roads:
            road_type = road.get('fined_type', 'road')
            width = road_outline_width.get(road_type, ROAD_OUTLINE_DEFAULT_WIDTH)
            width /= ROAD_WIDTH_DECEASE_RATE ** (18 - z)
            # width -= ROAD_WIDTH_DECEASE_RATE * (18 - z)
            draw_road(draw, road['element'], scale, road_type, width, outline=True)
            
        for road in roads:
            road_type = road.get('fined_type', 'road')
            width = road_outline_width.get(road_type, ROAD_OUTLINE_DEFAULT_WIDTH)
            width /= ROAD_WIDTH_DECEASE_RATE ** (18 - z)
            # width -= ROAD_WIDTH_DECEASE_RATE * (18 - z)
            draw_road(draw, road['element'], scale, road_type, width)

    if 'text' in items:
        drawed |= len(items['text']) > 0
        for text in items['text']:
            draw_text(draw, text['element'], scale, font)

    return img if drawed else None

def generate_tiles(z, x_start, x_end, y_start, y_end, quadtrees, output_dir='tiles'):
    font = ImageFont.truetype("C:/Windows/fonts/Dengl.ttf", FONT_SIZE)
    for x in range(x_start, x_end + 1):
        for y in range(y_start, y_end + 1):
            img = generate_tile(z, x, y, quadtrees, font)
            if img is not None:
                tile_path = os.path.join(output_dir, str(z), str(x))
                os.makedirs(tile_path, exist_ok=True)
                img.save(os.path.join(tile_path, f"{y}.png"))
                print(f"Saved tile {z}/{x}/{y}.png")

if __name__ == "__main__":
    osm_file = 'map.osm'
    out_folder = 'tile'
    # osm_file = 'shanghai-latest.osm'
    # out_folder = 'shanghai'
    
    # 确定 OSM 数据的边界框
    bbox_handler = BoundingBoxHandler()
    bbox_handler.apply_file(osm_file, locations=True, idx='sparse_mem_array')
    min_lon, min_lat = bbox_handler.min_lon, bbox_handler.min_lat
    max_lon, max_lat = bbox_handler.max_lon, bbox_handler.max_lat
    print(f"OSM Data Bounding Box:")
    print(f"Min Longitude: {min_lon}, Min Latitude: {min_lat}")
    print(f"Max Longitude: {max_lon}, Max Latitude: {max_lat}")

    # 初始化多个四叉树
    quadtrees = {z: pyqtree.Index(bbox=(-20037508.342789244, -20037508.342789244,
                                         20037508.342789244,  20037508.342789244)) for z in range(1, 19)}

    # 加载所有相关元素到四叉树中
    transformer = Transformer.from_crs("epsg:4326", "epsg:3857", always_xy=True)
    osm_handler = OSMHandler(transformer, quadtrees, "C:/Windows/fonts/Dengl.ttf")
    osm_handler.apply_file(osm_file, locations=True, idx='sparse_mem_array')

    # 为每个缩放级别生成瓦片
    for z in range(1, 19):
        # 将边界框转换为瓦片索引范围
        x_start, y_start = lonlat_to_tile(z, min_lon, max_lat)
        x_end, y_end = lonlat_to_tile(z, max_lon, min_lat)
        print(f"Tile Range at Zoom {z}:")
        print(f"x_start: {x_start}, x_end: {x_end}")
        print(f"y_start: {y_start}, y_end: {y_end}")

        generate_tiles(z, x_start, x_end, y_start, y_end, quadtrees, out_folder)
    
    print("Generated all tiles successfully!")