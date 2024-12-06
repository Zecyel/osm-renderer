import math
import osmium
from shapely.geometry import LineString, Polygon, MultiPolygon, GeometryCollection, MultiLineString
from shapely.ops import transform
from pyproj import Transformer
from PIL import Image, ImageDraw, ImageFont
import os
import pyqtree
from constants import *
from drawer import *

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
            if road_type in ROAD_ZOOM_LEVELS:
                min_z = ROAD_ZOOM_LEVELS[road_type]['min_zoom']
                max_z = ROAD_ZOOM_LEVELS[road_type]['max_zoom']
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
            if landuse_type in GREEN_AREA_ZOOM_LEVELS:
                min_z = GREEN_AREA_ZOOM_LEVELS[landuse_type]['min_zoom']
                max_z = GREEN_AREA_ZOOM_LEVELS[landuse_type]['max_zoom']
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
            if waterway_type in WATERWAY_ZOOM_LEVELS:
                min_z = WATERWAY_ZOOM_LEVELS[waterway_type]['min_zoom']
                max_z = WATERWAY_ZOOM_LEVELS[waterway_type]['max_zoom']
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

def generate_tiles(z, x_start, x_end, y_start, y_end, quadtrees, output_dir='tiles'):
    font = ImageFont.truetype("C:/Windows/fonts/Dengl.ttf", FONT_SIZE)
    for x in range(x_start, x_end + 1):
        for y in range(y_start, y_end + 1):
            drawer = TileDrawer(z, x, y, quadtrees, font)
            img = drawer.result
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
