"""LAS/LAZ output writer."""

import numpy as np
import laspy
from pyproj import CRS


def write_las(x, y, z, intensity, gps_time, epsg, path, compress=False):
    """Write a georeferenced LAS 1.4 file (point format 3).

    Args:
        compress: If True, attempt LAZ compression via lazrs.
    """
    hdr = laspy.LasHeader(point_format=3, version="1.4")
    hdr.offsets = [0.0, 0.0, 0.0]
    hdr.scales = [0.001, 0.001, 0.001]

    las = laspy.LasData(hdr)
    las.x = np.array(x)
    las.y = np.array(y)
    las.z = np.array(z)
    las.intensity = np.array(intensity, dtype=np.uint16)
    las.gps_time = np.array(gps_time)
    las.header.add_crs(CRS.from_epsg(epsg))

    if compress:
        try:
            import lazrs
            las.write(path, do_compress=True)
        except ImportError:
            las.write(path)
    else:
        las.write(path)


def get_stats(x, y, z, intensity):
    """Return summary statistics dict for the point cloud."""
    ax, ay, az = np.array(x), np.array(y), np.array(z)
    ai = np.array(intensity)
    return {
        "points": len(ax),
        "x_rng": (float(ax.min()), float(ax.max())),
        "y_rng": (float(ay.min()), float(ay.max())),
        "z_rng": (float(az.min()), float(az.max())),
        "i_rng": (int(ai.min()), int(ai.max())),
    }
