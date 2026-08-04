"""
Product search terms organized by category.
Focused on items with arbitrage potential - products that:
- Have established resale markets on eBay
- Are frequently discounted/clearanced at retail
- Have enough price variance to create profit opportunities
"""

# Large list of search terms across categories with arbitrage potential
# Rotated randomly each discovery cycle to avoid repetitive searches

SEARCH_TERMS = {
    'electronics': [
        'wireless earbuds', 'bluetooth speaker', 'gaming headset', 'mechanical keyboard',
        'gaming mouse', 'webcam', 'usb-c hub', 'phone charger', 'power bank',
        'portable monitor', 'laptop stand', 'tablet case', 'smart watch',
        'fitness tracker', 'drone', 'action camera', 'instant camera',
        'bluetooth receiver', 'wifi router', 'mesh wifi', 'range extender',
        'HDMI cable', 'USB cable', 'SD card', 'external hard drive',
        'SSD drive', 'USB flash drive', 'wireless charger', 'car charger',
    ],
    'gaming': [
        'gaming controller', 'gaming keyboard', 'gaming headset',
        'Nintendo Switch games', 'PlayStation games', 'Xbox games',
        'gaming chair', 'gaming monitor', 'gaming mouse pad',
        'retro console', 'gaming capture card', 'streaming microphone',
    ],
    'home_appliances': [
        'air fryer', 'instant pot', 'blender', 'food processor',
        'coffee maker', 'espresso machine', 'toaster oven', 'microwave',
        'vacuum cleaner', 'robot vacuum', 'handheld vacuum',
        'air purifier', 'humidifier', 'dehumidifier', 'space heater',
        'fan', 'tower fan', 'electric blanket', 'mattress topper',
    ],
    'tools': [
        'cordless drill', 'impact driver', 'circular saw', 'angle grinder',
        'tool set', 'socket set', 'wrench set', 'torque wrench',
        'pressure washer', 'wet dry vac', 'heat gun', 'soldering iron',
        'multimeter', 'stud finder', 'laser level', 'tape measure',
    ],
    'outdoor': [
        'camping tent', 'sleeping bag', 'camping stove', 'folding chair',
        'cooler', 'grill', 'pellet grill', 'smoker', 'fire pit',
        'patio heater', 'hammock', 'bike rack', 'roof rack',
        'e-bike', 'electric scooter', 'kayak', 'paddle board',
    ],
    'fitness': [
        'adjustable dumbbells', 'kettlebell', 'resistance bands',
        'yoga mat', 'foam roller', 'pull up bar', 'weight bench',
        'treadmill', 'exercise bike', 'rowing machine', 'jump rope',
        'fitness watch', 'heart rate monitor', 'wireless earbuds sports',
    ],
    'beauty_health': [
        'hair dryer', 'flat iron', 'curling iron', 'beard trimmer',
        'electric razor', 'electric toothbrush', 'water flosser',
        'massager', 'heating pad', 'blood pressure monitor',
        'digital scale', 'air purifier bedroom',
    ],
}

# Flatten into a single list with category tags
ALL_SEARCH_TERMS = []
for category, terms in SEARCH_TERMS.items():
    for term in terms:
        ALL_SEARCH_TERMS.append((term, category))

def get_random_search_terms(count: int = 5, exclude: set = None):
    """Get random search terms, avoiding recently used ones.
    
    Args:
        count: Number of terms to return
        exclude: Set of terms to exclude (recently searched)
    
    Returns:
        List of (term, category) tuples
    """
    import random
    exclude = exclude or set()
    
    available = [(term, cat) for term, cat in ALL_SEARCH_TERMS if term not in exclude]
    
    if len(available) < count:
        # If we've used most terms, just use all available
        selected = available
    else:
        # Pick random terms, spread across categories
        selected = random.sample(available, count)
    
    return selected

def get_all_terms():
    """Get all search terms as a flat list"""
    return [term for term, _ in ALL_SEARCH_TERMS]
