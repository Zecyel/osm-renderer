def zoom_range(min_zoom, max_zoom):
    return range(min_zoom, max_zoom + 1)


ROAD_ZOOM_LEVELS = {
    'motorway': zoom_range(5, 18),
    'motorway_link': zoom_range(5, 18),
    'primary': zoom_range(8, 18),
    'primary_link': zoom_range(8, 18),
    'secondary': zoom_range(11, 18),
    'secondary_link': zoom_range(11, 18),
    'tertiary': zoom_range(13, 18),
    'tertiary_link': zoom_range(13, 18),
    'residential': zoom_range(15, 18),
    'unclassified': zoom_range(15, 18),
    'service': zoom_range(5, 18),
    'path': zoom_range(17, 18),
    'cycleway': zoom_range(17, 18),
    # 'construction': zoom_range(15, 18),
    'trunk': zoom_range(7, 18),
}

ROAD_COLORS = {
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

ROAD_OUTLINE_COLORS = {
    # 'motorway': (200, 0, 0),
    # 'motorway_link': (200, 100, 100),
    # 'primary': ROAD_COLORS['primary'],
    # 'primary_link': (200, 160, 100),
    # 'secondary': ROAD_COLORS['secondary'],
    # 'secondary_link': (200, 200, 100),
    # 'tertiary': ROAD_COLORS['tertiary'],
    # 'tertiary_link': (100, 200, 100),
    # 'residential': (0, 0, 200),
    # 'unclassified': (100, 100, 200),
    # 'service': (200, 200, 200),
    # 'path': (100, 100, 100),
    # 'cycleway': (0, 200, 200),
    # 'construction': (200, 0, 200),
    'trunk': ROAD_COLORS['trunk'],
}

ROAD_OUTLINE_DEFAULT_COLOR = (200, 200, 200)

ROAD_OUTLINE_WIDTH = {
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

GREEN_AREA_ZOOM_LEVELS = {
    'park': zoom_range(10, 18),
    'forest': zoom_range(10, 18),
    'grass': zoom_range(10, 18),
    'meadow': zoom_range(10, 18),
    'recreation_ground': zoom_range(10, 18),
    'garden': zoom_range(10, 18),
}

WATERWAY_ZOOM_LEVELS = {
    'river': zoom_range(10+2, 18),
    'stream': zoom_range(12+2, 18),
    'canal': zoom_range(10+2, 18),
    'drain': zoom_range(12+2, 18),
    'ditch': zoom_range(12+2, 18),
    'water': zoom_range(10, 18),  # Add this line
}

GREEN_AREA_COLORS = {
    'park': (200, 250, 204),
    'forest': (173, 209, 158),
    'grass': (205, 235, 176),
    'meadow': (205, 235, 176),
    'recreation_ground': (223, 252, 226),
    'garden': (0, 255, 127),
}

GREEN_AREA_DEFAULT_COLOR = (200, 250, 204)

FONT_SIZE = 20

BACKGROUND_COLOR = (242, 239, 233)
BUILDING_COLOR = (217, 208, 201)
BUILDING_OUTLINE_COLOR = (197, 184, 174)
WATERWAY_COLOR = (170, 211, 223)

EPS = 1e-7

ZOOM_BASE = 2
