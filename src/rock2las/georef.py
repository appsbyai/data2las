"""Georeferencing: sensor-local to world coordinate transforms."""

import math
import numpy as np
from scipy.interpolate import interp1d
from scipy.spatial.transform import Rotation
from pyproj import CRS, Transformer


def compute_epsg(lats, lons):
    """Determine UTM EPSG code from mean lat/lon."""
    mlon = np.mean(lons)
    utm_z = int((mlon + 180) // 6) + 1
    south = np.mean(lats) < 0
    return 32700 + utm_z if south else 32600 + utm_z


def build_transforms(ref_lat, ref_lon):
    """Build ECEF↔ENU transforms centered at the reference position."""
    wgs84 = CRS.from_epsg(4979)
    ecef = CRS.from_epsg(4978)
    to_ecef = Transformer.from_crs(wgs84, ecef)

    ref_ecef = np.array(to_ecef.transform(ref_lat, ref_lon, 0))

    slat = math.sin(math.radians(ref_lat))
    clat = math.cos(math.radians(ref_lat))
    slon = math.sin(math.radians(ref_lon))
    clon = math.cos(math.radians(ref_lon))

    def to_enu(ecef_pt):
        dx, dy, dz = ecef_pt - ref_ecef
        return np.array([
            -slon * dx + clon * dy,
            -slat * clon * dx - slat * slon * dy + clat * dz,
            clat * clon * dx + clat * slon * dy + slat * dz,
        ])

    return to_ecef, to_enu, ref_ecef


def rotation_matrix(yaw, pitch, roll):
    """Build 3D rotation from ZYX Euler angles (degrees)."""
    return Rotation.from_euler("ZYX", [yaw, pitch, roll], degrees=True).as_matrix()


def georeference_points(points, total_records, gnss_data,
                        lever_arm, boresight_deg, mount_yaw,
                        on_progress=None):
    """Transform all LiDAR points to UTM coordinates.

    Returns: x, y, z, intensity, gps_time, epsg_code
    """
    from .gnss import trajectory_arrays

    times, lats, lons, hgts = trajectory_arrays(gnss_data)

    epsg = compute_epsg(lats, lons)
    to_ecef, to_enu, ref_ecef = build_transforms(lats[0], lons[0])

    i_lat = interp1d(times, lats, kind="linear", fill_value="extrapolate")
    i_lon = interp1d(times, lons, kind="linear", fill_value="extrapolate")
    i_h = interp1d(times, hgts, kind="linear", fill_value="extrapolate")

    R = (rotation_matrix(mount_yaw, 0, 0) @
         rotation_matrix(boresight_deg[0], boresight_deg[1], boresight_deg[2]))

    t0, t1 = times[0], times[-1]
    dur = t1 - t0

    def rec_time(idx):
        return t0 + dur * (idx / (total_records - 1) if total_records > 1 else 0)

    lx, ly, lz, li, lt = [], [], [], [], []

    for i, pt in enumerate(points):
        tm = rec_time(pt["rec"])
        lat = float(i_lat(tm))
        lon = float(i_lon(tm))
        h = float(i_h(tm))

        ps = np.array([pt["x"], pt["y"], pt["z"]])
        pb = R @ ps + lever_arm

        ae = np.array(to_ecef.transform(lat, lon, h))
        au = to_enu(ae)
        w = au + pb

        lx.append(w[0]); ly.append(w[1]); lz.append(w[2])
        li.append(pt["i"])
        lt.append(tm / 1000.0)

        if on_progress and i % 500000 == 0:
            on_progress(40 + 50 * i / len(points), f"{i:,}/{len(points):,}")

    return lx, ly, lz, li, lt, epsg
