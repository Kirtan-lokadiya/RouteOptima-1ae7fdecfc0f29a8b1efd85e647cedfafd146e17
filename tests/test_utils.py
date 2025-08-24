import pytest
from utils.route_utils import haversine  # Ensure PYTHONPATH is set correctly

def test_haversine():
    # Test the distance between two known points
    lat1, lon1 = 52.5200, 13.4050  # Berlin
    lat2, lon2 = 48.8566, 2.3522   # Paris
    distance = haversine(lat1, lon1, lat2, lon2)
    assert round(distance, 2) == 877.46  # Approximate distance in km