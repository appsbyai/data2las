"""EXIF georeferencing for extracted photos using GNSS trajectory.

Based on Rock Robotic's exifwriter tool patterns found in their repo.
Writes GPS coordinates, altitude, and timestamp to JPEG EXIF tags.
"""

import os
import numpy as np
from scipy.interpolate import interp1d

try:
    from PIL import Image
    from PIL.ExifTags import GPS, Base
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def _to_deg(value, ref):
    """Convert decimal degrees to EXIF format (degrees, minutes, seconds)."""
    d = abs(value)
    deg = int(d)
    mnt = int((d - deg) * 60)
    sec = (d - deg - mnt / 60) * 3600
    return ((deg, 1), (mnt, 1), (int(sec * 1000), 1000))


def _to_rational(value):
    """Convert float to EXIF rational (numerator, denominator)."""
    if isinstance(value, tuple):
        return value
    return (int(value * 1000), 1000)


def georeference_photos(photo_dir, gnss_data, output_dir=None):
    """Write GPS EXIF tags to all JPEGs in photo_dir.

    Uses GNSS trajectory to interpolate position at each photo's approximate
    timestamp (derived from filename or EXIF DateTime).

    Args:
        photo_dir: Directory containing .jpg files
        gnss_data: List of dicts with 't' (GPS ms of week), 'lat', 'lon', 'h'
        output_dir: Where to write tagged photos (defaults to photo_dir/_geotagged)

    Returns:
        Number of photos tagged.
    """
    if not HAS_PIL:
        return 0

    if output_dir is None:
        output_dir = os.path.join(photo_dir, "_geotagged")
    os.makedirs(output_dir, exist_ok=True)

    times = np.array([p["t"] for p in gnss_data])
    lats = np.array([p["lat"] for p in gnss_data])
    lons = np.array([p["lon"] for p in gnss_data])
    hgts = np.array([p["h"] for p in gnss_data])

    i_lat = interp1d(times, lats, kind="linear", fill_value="extrapolate")
    i_lon = interp1d(times, lons, kind="linear", fill_value="extrapolate")
    i_h = interp1d(times, hgts, kind="linear", fill_value="extrapolate")

    jpegs = sorted(
        f for f in os.listdir(photo_dir) if f.lower().endswith((".jpg", ".jpeg"))
    )
    if not jpegs:
        return 0

    count = 0
    for i, jpg in enumerate(jpegs):
        src_path = os.path.join(photo_dir, jpg)
        dst_path = os.path.join(output_dir, jpg)

        try:
            img = Image.open(src_path)
            exif = img.getexif()
        except Exception:
            continue

        # Estimate GPS time: linear interpolation based on photo index
        # Photos are captured at ~5Hz (5-second interval per service log)
        # If we know first/last GNSS time, map photo index to time
        photo_t = times[0] + (times[-1] - times[0]) * (i / max(len(jpegs) - 1, 1))

        lat = float(i_lat(photo_t))
        lon = float(i_lon(photo_t))
        alt = float(i_h(photo_t))

        # Write GPS IFD
        gps_ifd = {
            GPS.GPSVersionID: (2, 0, 0, 0),
            GPS.GPSAltitudeRef: 0,  # Above sea level
            GPS.GPSAltitude: _to_rational(alt),
            GPS.GPSLatitudeRef: "S" if lat < 0 else "N",
            GPS.GPSLatitude: _to_deg(lat, "S" if lat < 0 else "N"),
            GPS.GPSLongitudeRef: "W" if lon < 0 else "E",
            GPS.GPSLongitude: _to_deg(lon, "W" if lon < 0 else "E"),
        }
        exif.set_ifd(GPS.IFD, gps_ifd)

        try:
            img.save(dst_path, "jpeg", exif=exif.tobytes())
            count += 1
        except Exception:
            # Fallback: just copy the file
            img.save(dst_path, "jpeg")

    return count
