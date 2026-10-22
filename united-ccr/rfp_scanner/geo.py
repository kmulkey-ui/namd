"""Locate opportunities and measure their distance from United CCR's headquarters.

Lookup order: exact lat/lon -> ZIP (Census ZCTA gazetteer, if downloaded) ->
city+state (Census place gazetteer if downloaded, else the built-in table) ->
state centroid (only for states small enough for a centroid to mean something).
"""
import csv
import math
import os
import re

# Built-in fallback: Houston region in depth, then major cities across the service area.
CITIES = {
    ("CYPRESS", "TX"): (29.9691, -95.6972), ("HOUSTON", "TX"): (29.7604, -95.3698),
    ("KATY", "TX"): (29.7858, -95.8245), ("TOMBALL", "TX"): (30.0972, -95.6161),
    ("SUGAR LAND", "TX"): (29.6197, -95.6349), ("THE WOODLANDS", "TX"): (30.1658, -95.4613),
    ("CONROE", "TX"): (30.3119, -95.4561), ("SPRING", "TX"): (30.0799, -95.4172),
    ("HUMBLE", "TX"): (29.9988, -95.2622), ("PASADENA", "TX"): (29.6911, -95.2091),
    ("BAYTOWN", "TX"): (29.7355, -94.9774), ("PEARLAND", "TX"): (29.5636, -95.2860),
    ("LEAGUE CITY", "TX"): (29.5075, -95.0949), ("GALVESTON", "TX"): (29.3013, -94.7977),
    ("TEXAS CITY", "TX"): (29.3838, -94.9027), ("RICHMOND", "TX"): (29.5822, -95.7608),
    ("ROSENBERG", "TX"): (29.5572, -95.8086), ("MISSOURI CITY", "TX"): (29.6186, -95.5377),
    ("HEMPSTEAD", "TX"): (30.0974, -96.0783), ("WALLER", "TX"): (30.0566, -95.9269),
    ("BROOKSHIRE", "TX"): (29.7860, -95.9511), ("BELLVILLE", "TX"): (29.9502, -96.2572),
    ("NAVASOTA", "TX"): (30.3880, -96.0878), ("HUNTSVILLE", "TX"): (30.7235, -95.5508),
    ("BRYAN", "TX"): (30.6744, -96.3698), ("COLLEGE STATION", "TX"): (30.6280, -96.3344),
    ("BRENHAM", "TX"): (30.1669, -96.3977), ("BEAUMONT", "TX"): (30.0802, -94.1266),
    ("PORT ARTHUR", "TX"): (29.8850, -93.9399), ("ORANGE", "TX"): (30.0930, -93.7366),
    ("LAKE JACKSON", "TX"): (29.0339, -95.4344), ("FREEPORT", "TX"): (28.9541, -95.3597),
    ("ANGLETON", "TX"): (29.1694, -95.4319), ("BAY CITY", "TX"): (28.9828, -95.9694),
    ("VICTORIA", "TX"): (28.8053, -97.0036), ("CORPUS CHRISTI", "TX"): (27.8006, -97.3964),
    ("AUSTIN", "TX"): (30.2672, -97.7431), ("SAN ANTONIO", "TX"): (29.4241, -98.4936),
    ("WACO", "TX"): (31.5493, -97.1467), ("DALLAS", "TX"): (32.7767, -96.7970),
    ("FORT WORTH", "TX"): (32.7555, -97.3308), ("ARLINGTON", "TX"): (32.7357, -97.1081),
    ("PLANO", "TX"): (33.0198, -96.6989), ("TYLER", "TX"): (32.3513, -95.3011),
    ("LONGVIEW", "TX"): (32.5007, -94.7405), ("LUFKIN", "TX"): (31.3382, -94.7291),
    ("NACOGDOCHES", "TX"): (31.6035, -94.6555), ("LAREDO", "TX"): (27.5306, -99.4803),
    ("MCALLEN", "TX"): (26.2034, -98.2300), ("BROWNSVILLE", "TX"): (25.9017, -97.4975),
    ("HARLINGEN", "TX"): (26.1906, -97.6961), ("EL PASO", "TX"): (31.7619, -106.4850),
    ("LUBBOCK", "TX"): (33.5779, -101.8552), ("AMARILLO", "TX"): (35.2220, -101.8313),
    ("MIDLAND", "TX"): (31.9973, -102.0779), ("ODESSA", "TX"): (31.8457, -102.3676),
    ("ABILENE", "TX"): (32.4487, -99.7331), ("SAN ANGELO", "TX"): (31.4638, -100.4370),
    ("WICHITA FALLS", "TX"): (33.9137, -98.4934), ("TEMPLE", "TX"): (31.0982, -97.3428),
    ("KILLEEN", "TX"): (31.1171, -97.7278), ("FORT HOOD", "TX"): (31.1349, -97.7756),
    ("ROUND ROCK", "TX"): (30.5083, -97.6789), ("SAN MARCOS", "TX"): (29.8833, -97.9414),
    ("NEW BRAUNFELS", "TX"): (29.7030, -98.1245), ("LAKE CHARLES", "LA"): (30.2266, -93.2174),
    ("LAFAYETTE", "LA"): (30.2241, -92.0198), ("BATON ROUGE", "LA"): (30.4515, -91.1871),
    ("NEW ORLEANS", "LA"): (29.9511, -90.0715), ("SHREVEPORT", "LA"): (32.5252, -93.7502),
    ("MONROE", "LA"): (32.5093, -92.1193), ("ALEXANDRIA", "LA"): (31.3113, -92.4451),
    ("OKLAHOMA CITY", "OK"): (35.4676, -97.5164), ("TULSA", "OK"): (36.1540, -95.9928),
    ("LITTLE ROCK", "AR"): (34.7465, -92.2896), ("ALBUQUERQUE", "NM"): (35.0844, -106.6504),
    ("SANTA FE", "NM"): (35.6870, -105.9378), ("JACKSON", "MS"): (32.2988, -90.1848),
    ("GULFPORT", "MS"): (30.3674, -89.0928), ("BILOXI", "MS"): (30.3960, -88.8853),
    ("MOBILE", "AL"): (30.6954, -88.0399), ("BIRMINGHAM", "AL"): (33.5186, -86.8104),
    ("MONTGOMERY", "AL"): (32.3792, -86.3077), ("HUNTSVILLE", "AL"): (34.7304, -86.5861),
    ("PENSACOLA", "FL"): (30.4213, -87.2169), ("TALLAHASSEE", "FL"): (30.4383, -84.2807),
    ("JACKSONVILLE", "FL"): (30.3322, -81.6557), ("TAMPA", "FL"): (27.9506, -82.4572),
    ("ORLANDO", "FL"): (28.5383, -81.3792), ("MIAMI", "FL"): (25.7617, -80.1918),
    ("ATLANTA", "GA"): (33.7490, -84.3880), ("SAVANNAH", "GA"): (32.0809, -81.0912),
    ("NASHVILLE", "TN"): (36.1627, -86.7816), ("MEMPHIS", "TN"): (35.1495, -90.0490),
    ("KNOXVILLE", "TN"): (35.9606, -83.9207), ("CHATTANOOGA", "TN"): (35.0456, -85.3097),
    ("CHARLESTON", "SC"): (32.7765, -79.9311), ("COLUMBIA", "SC"): (34.0007, -81.0348),
}

# Texas is too large for a centroid to say anything about distance, so it has none.
STATE_CENTROIDS = {
    "LA": (30.9, -92.0), "OK": (35.6, -97.5), "AR": (34.9, -92.4), "NM": (34.4, -106.1),
    "MS": (32.7, -89.7), "AL": (32.8, -86.8), "FL": (28.6, -82.4), "GA": (32.7, -83.4),
    "TN": (35.9, -86.4), "SC": (33.9, -80.9),
}

_PLACE_SUFFIX = re.compile(r"\s+(city|town|village|cdp|borough|municipality)$", re.I)


def haversine_miles(a, b):
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 3958.8 * 2 * math.asin(math.sqrt(h))


def _read_gazetteer(path):
    with open(path, newline="", encoding="latin-1") as f:
        reader = csv.reader(f, delimiter="\t")
        header = [h.strip() for h in next(reader)]
        for row in reader:
            yield dict(zip(header, (c.strip() for c in row)))


class Geocoder:
    def __init__(self, data_dir=None):
        self.zips = {}
        self.places = dict(CITIES)
        if data_dir:
            zcta = os.path.join(data_dir, "gaz_zcta.txt")
            if os.path.exists(zcta):
                for r in _read_gazetteer(zcta):
                    self.zips[r["GEOID"]] = (float(r["INTPTLAT"]), float(r["INTPTLONG"]))
            place = os.path.join(data_dir, "gaz_place.txt")
            if os.path.exists(place):
                for r in _read_gazetteer(place):
                    name = _PLACE_SUFFIX.sub("", r["NAME"]).upper()
                    self.places.setdefault((name, r["USPS"]), (float(r["INTPTLAT"]), float(r["INTPTLONG"])))

    def locate(self, city=None, state=None, zip_code=None, lat=None, lon=None):
        """Return ((lat, lon), precision) or (None, None)."""
        if lat is not None and lon is not None:
            return (float(lat), float(lon)), "exact"
        if zip_code:
            z = str(zip_code).strip()[:5]
            if z in self.zips:
                return self.zips[z], "zip"
        state = (state or "").strip().upper()
        if city and state:
            key = (city.strip().upper(), state)
            if key in self.places:
                return self.places[key], "city"
        if state in STATE_CENTROIDS:
            return STATE_CENTROIDS[state], "state"
        return None, None
