#-*- coding: utf-8 -*-
from math import sin, cos, asin, sqrt, radians

RADIUS = 6371.0
KMTOMILESRATIO = 0.6213712

def _haversine(angle_radians):
	return sin(angle_radians / 2.0) ** 2

def _inverse_haversine(h):
	return 2 * asin(sqrt(h))

def get_distance(lat1, lon1, lat2, lon2, return_miles=True):
	if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
		return None
	lat1 = radians(lat1)
	lat2 = radians(lat2)
	dlat = lat2-lat1
	dlon = radians(lon2-lon1)
	h = _haversine(dlat)+cos(lat1)*cos(lat2)*_haversine(dlon)
	distance = RADIUS*_inverse_haversine(h)
	if return_miles:
		distance = distance*KMTOMILESRATIO
	return round(distance, 2)
