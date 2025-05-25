# constants.py

# Relationship disposition → color mapping (edges)
EDGE_COLOR_MAP = {
    "ally": "#2ECC40",     # Green
    "neutral": "#AAAAAA",  # Grey
    "enemy": "#FF4136"     # Red
}

# Faction colors (avoid red/green to not conflict with edge colors)
DEFAULT_FACTION_COLORS = {
    "The Zhentarim": "#B10DC9",   # Purple
    "The Harpers": "#0074D9",     # Blue
    "Force Grey": "#FF851B",      # Orange
    None: "#AAAAAA"               # fallback / unaffiliated
}

# Any other shared lists/dictionaries can go here
RELATIONSHIP_STATUS_LIST = ['positive', 'neutral', 'negative']
DISPOSITION_LIST = ['ally', 'neutral', 'enemy']
