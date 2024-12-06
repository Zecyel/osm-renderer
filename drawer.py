
import math
from pyproj import Transformer
from shapely.geometry import LineString, Polygon, MultiPolygon, GeometryCollection, MultiLineString
from PIL import Image, ImageDraw
from constants import *

def tile_to_bbox(z, x, y):
    n = 2.0 ** z
    lon_min = x / n * 360.0 - 180.0
    lat_min = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    lon_max = (x + 1) / n * 360.0 - 180.0
    lat_max = math.degrees(
        math.atan(math.sinh(math.pi * (1 - 2 * (y + 1) / n))))
    return (lon_min, lat_min, lon_max, lat_max)


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
            geom_types.extend(
                [geom for geom in clipped if isinstance(geom, (Polygon, MultiPolygon))])

        for geom in geom_types:
            if isinstance(geom, Polygon):
                ret.append(
                    {'element': geom, 'landuse_type': item.get('landuse_type')})
            elif isinstance(geom, MultiPolygon):
                for sub_geom in geom.geoms:
                    ret.append(
                        {'element': sub_geom, 'landuse_type': item.get('landuse_type')})
    return ret


def on_border(point):
    return point[0] < EPS or 512 - point[0] < EPS or point[1] < EPS or 512 - point[1] < EPS


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
            ret.append(
                {'element': clipped, 'fined_type': item.get('fined_type')})
        elif isinstance(clipped, MultiLineString):
            for geom in clipped.geoms:
                if isinstance(geom, LineString):
                    ret.append(
                        {'element': geom, 'fined_type': item.get('fined_type')})
        elif isinstance(clipped, GeometryCollection):
            for geom in clipped:
                if isinstance(geom, LineString):
                    ret.append(
                        {'element': geom, 'fined_type': item.get('fined_type')})
    return ret


class TileDrawer:
    def __init__(self, z, x, y, quadtrees, font):

        # 计算瓦片边界
        bbox = tile_to_bbox(z, x, y)
        lon_min, lat_min, lon_max, lat_max = bbox

        # 初始化坐标转换器（EPSG:4326 到 EPSG:3857）
        transformer = Transformer.from_crs(
            "epsg:4326", "epsg:3857", always_xy=True)

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
        self.scale = scale

        # 查询当前缩放级别的四叉树
        items = classify_items(quadtrees[z].intersect(tile_bbox))

        # 创建图像
        img_size = 512
        img = Image.new("RGB", (img_size, img_size), BACKGROUND_COLOR)
        self.draw = ImageDraw.Draw(img)
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
                self.draw_polygon(
                    building['element'], BUILDING_OUTLINE_COLOR, BUILDING_COLOR, BACKGROUND_COLOR)

        # draw green areas
        if 'green_area' in items:
            green_areas = filter_polygons(items['green_area'], tile_polygon)
            drawed |= len(green_areas) > 0
            for green_area in green_areas:
                self.draw_green_area(
                    green_area['element'], green_area['landuse_type'])

        # draw waterways
        if 'waterway' in items:
            waterways = filter_lines(items['waterway'], tile_polygon)
            drawed |= len(waterways) > 0
            for waterway in waterways:
                self.draw_waterway(
                    waterway['element'],  WATERWAY_COLOR, 4)

        # draw water areas
        if 'water_area' in items:
            water_areas = filter_polygons(items['water_area'], tile_polygon)
            drawed |= len(water_areas) > 0
            for water_area in water_areas:
                self.draw_water_area(water_area['element'])

        # draw roads
        if 'road' in items:
            ROAD_WIDTH_DECEASE_RATE = 1.9
            roads = filter_lines(items['road'], tile_polygon)
            drawed |= len(roads) > 0
            for road in roads:
                road_type = road.get('fined_type', 'road')
                width = ROAD_OUTLINE_WIDTH.get(
                    road_type, ROAD_OUTLINE_DEFAULT_WIDTH)
                width /= ROAD_WIDTH_DECEASE_RATE ** (18 - z)
                # width -= ROAD_WIDTH_DECEASE_RATE * (18 - z)
                self.draw_road(road['element'],
                               road_type, width, outline=True)

            for road in roads:
                road_type = road.get('fined_type', 'road')
                width = ROAD_OUTLINE_WIDTH.get(
                    road_type, ROAD_OUTLINE_DEFAULT_WIDTH)
                width /= ROAD_WIDTH_DECEASE_RATE ** (18 - z)
                # width -= ROAD_WIDTH_DECEASE_RATE * (18 - z)
                self.draw_road(road['element'], road_type, width)

        if 'text' in items:
            drawed |= len(items['text']) > 0
            for text in items['text']:
                self.draw_text(text['element'], font)

        self.result = img if drawed else None

    def draw_polygon(self, polygon, outline_color, fill_color, background_color):
        """
        绘制建筑物多边形及其内环。
        """
        def draw_polygon_outline(polygon: Polygon, color):

            is_on_border = [on_border(point) for point in polygon]
            for point_index in range(1, len(polygon)):
                if is_on_border[point_index - 1] and is_on_border[point_index]:
                    continue
                self.draw.line([polygon[point_index - 1],
                                polygon[point_index]], fill=color, width=2)

        exterior = [self.scale(coord) for coord in polygon.exterior.coords]
        self.draw.polygon(exterior, fill=fill_color)
        draw_polygon_outline(exterior, color=outline_color)

        # 绘制内环（孔洞）
        for interior in polygon.interiors:
            interior_coords = [self.scale(coord) for coord in interior.coords]
            self.draw.polygon(interior_coords, fill=background_color)
            draw_polygon_outline(interior_coords, color=outline_color)

    def draw_green_area(self, polygon, landuse_type):
        """
        绘制绿地多边形。
        """
        fill_color = GREEN_AREA_COLORS.get(
            landuse_type, GREEN_AREA_DEFAULT_COLOR)  # default to green
        exterior = [self.scale(coord) for coord in polygon.exterior.coords]
        self.draw.polygon(exterior, fill=fill_color)

        for interior in polygon.interiors:
            interior_coords = [self.scale(coord) for coord in interior.coords]
            self.draw.polygon(interior_coords, fill=BACKGROUND_COLOR)

    def real_draw_road(self, line_pixels, width, color):
        if width <= 0:
            return
        half_width = width // 2 - 0.5

        if half_width > 0:
            for point in line_pixels:
                if not on_border(point):
                    self.draw.ellipse([(point[0] - half_width, point[1] - half_width),
                                       (point[0] + half_width, point[1] + half_width)], fill=color)

        for i in range(1, len(line_pixels)):
            ext_1 = (50 * line_pixels[i - 1][0] - 49 * line_pixels[i]
                     [0], 50 * line_pixels[i - 1][1] - 49 * line_pixels[i][1])
            ext_2 = (50 * line_pixels[i][0] - 49 * line_pixels[i - 1]
                     [0], 50 * line_pixels[i][1] - 49 * line_pixels[i - 1][1])

            p1 = ext_1 if on_border(line_pixels[i - 1]) else line_pixels[i - 1]
            p2 = ext_2 if on_border(line_pixels[i]) else line_pixels[i]
            self.draw.line([p1, p2], fill=color, width=int(width))

    def draw_road(self, line, road_type, width, color=None, outline_color=None, outline=False):
        """
        绘制道路（线条）。
        """
        if len(line.coords) < 2:
            return
        line_pixels = [self.scale(coord) for coord in line.coords]

        if color is None:
            color = ROAD_COLORS.get(road_type, ROAD_DEFAULT_COLOR)
        if outline_color is None:
            outline_color = ROAD_OUTLINE_COLORS.get(
                road_type, ROAD_OUTLINE_DEFAULT_COLOR)

        if width <= 4:
            if outline:
                self.real_draw_road(line_pixels, width, color)
        elif outline:
            self.real_draw_road(line_pixels, width, outline_color)
        else:
            self.real_draw_road(line_pixels, width - 4, color)

    def draw_waterway(self, line, color, width):
        """
        绘制河流（线条）。
        """
        if len(line.coords) < 2:
            return
        line_pixels = [self.scale(coord) for coord in line.coords]
        self.draw.line(line_pixels, fill=color, width=width)

    def draw_text(self, text_item, font):
        """
        在指定位置绘制文本标签。
        """
        name = text_item.get('text', '')
        position = text_item.get('position', (0, 0))
        size = text_item.get('size', (0, 0))

        if not name:
            return  # 如果没有文本，跳过

        # 计算像素位置
        px, py = self.scale(position)

        # 调整位置以居中文本
        text_width, text_height = size
        text_x = px - text_width / 2
        text_y = py - text_height / 2

        # 绘制文本
        self.draw.text((text_x, text_y), name,
                       font=font, fill="black")  # 示例文本颜色

    def draw_water_area(self, polygon):
        """
        绘制水域多边形。
        """
        exterior = [self.scale(coord) for coord in polygon.exterior.coords]
        self.draw.polygon(exterior, fill=WATERWAY_COLOR)

        for interior in polygon.interiors:
            interior_coords = [self.scale(coord) for coord in interior.coords]
            self.draw.polygon(interior_coords, fill=BACKGROUND_COLOR)
