
ROAD_ZOOM_LEVELS = {
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
    'park': {'min_zoom': 10, 'max_zoom': 18},
    'forest': {'min_zoom': 10, 'max_zoom': 18},
    'grass': {'min_zoom': 10, 'max_zoom': 18},
    'meadow': {'min_zoom': 10, 'max_zoom': 18},
    'recreation_ground': {'min_zoom': 10, 'max_zoom': 18},
    'garden': {'min_zoom': 10, 'max_zoom': 18},
}

WATERWAY_ZOOM_LEVELS = {
    'river': {'min_zoom': 10+2, 'max_zoom': 18},
    'stream': {'min_zoom': 12+2, 'max_zoom': 18},
    'canal': {'min_zoom': 10+2, 'max_zoom': 18},
    'drain': {'min_zoom': 12+2, 'max_zoom': 18},
    'ditch': {'min_zoom': 12+2, 'max_zoom': 18},
    'water': {'min_zoom': 10, 'max_zoom': 18},  # Add this line
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
