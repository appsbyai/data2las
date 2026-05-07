"""Coordinate reference system utilities.

Supports the "hundreds of projections" that Rock Desktop offers,
auto-detects UTM zone, and provides CRS selection.
"""

from pyproj import CRS

# Common projections used in surveying, matching Rock Desktop's export options
COMMON_CRS = {
    "Auto UTM (WGS84)": None,  # Auto-detected
    "WGS84 (EPSG:4326)": 4326,
    "Web Mercator (EPSG:3857)": 3857,
    "UTM 1N (EPSG:32601)": 32601, "UTM 2N (EPSG:32602)": 32602,
    "UTM 10N (EPSG:32610)": 32610, "UTM 11N (EPSG:32611)": 32611,
    "UTM 12N (EPSG:32612)": 32612, "UTM 13N (EPSG:32613)": 32613,
    "UTM 14N (EPSG:32614)": 32614, "UTM 15N (EPSG:32615)": 32615,
    "UTM 16N (EPSG:32616)": 32616, "UTM 17N (EPSG:32617)": 32617,
    "UTM 18N (EPSG:32618)": 32618, "UTM 19N (EPSG:32619)": 32619,
    "UTM 20N (EPSG:32620)": 32620,
    "UTM 1S (EPSG:32701)": 32701, "UTM 2S (EPSG:32702)": 32702,
    "UTM 10S (EPSG:32710)": 32710, "UTM 11S (EPSG:32711)": 32711,
    "UTM 12S (EPSG:32712)": 32712, "UTM 13S (EPSG:32713)": 32713,
    "UTM 14S (EPSG:32714)": 32714, "UTM 15S (EPSG:32715)": 32715,
    "UTM 16S (EPSG:32716)": 32716, "UTM 17S (EPSG:32717)": 32717,
    "UTM 18S (EPSG:32718)": 32718, "UTM 19S (EPSG:32719)": 32719,
    "UTM 20S (EPSG:32720)": 32720,
    "UTM 55S (EPSG:32755)": 32755, "UTM 56S (EPSG:32756)": 32756,
}


def auto_utm(lats, lons):
    """Auto-detect UTM EPSG code from latitude/longitude."""
    import numpy as np
    mlon = np.mean(lons)
    mlat = np.mean(lats)
    zone = int((mlon + 180) // 6) + 1
    return 32700 + zone if mlat < 0 else 32600 + zone


def get_crs(epsg):
    """Get a pyproj CRS object from EPSG code."""
    return CRS.from_epsg(epsg)


def get_crs_name(epsg):
    """Get human-readable name for an EPSG code."""
    try:
        crs = CRS.from_epsg(epsg)
        return crs.name
    except Exception:
        return f"EPSG:{epsg}"
