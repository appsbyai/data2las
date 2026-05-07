"""GNSS: uBlox UBX message parsing and trajectory extraction."""

import struct
import os
import numpy as np


def parse_nav_pvt(payload):
    """Decode UBX-NAV-PVT (0x01 0x07) message."""
    iTOW = struct.unpack_from("<I", payload, 0)[0]
    nano = struct.unpack_from("<i", payload, 16)[0]
    valid = payload[11]
    flags = payload[21]
    valid_date = bool(valid & 1)
    valid_time = bool((valid >> 1) & 1)
    return {
        "t": iTOW + nano * 1e-6,
        "lat": struct.unpack_from("<i", payload, 28)[0] * 1e-7,
        "lon": struct.unpack_from("<i", payload, 24)[0] * 1e-7,
        "h": struct.unpack_from("<i", payload, 32)[0] * 1e-3,
        "fix": payload[20],
        "sv": payload[23],
        "h_acc": struct.unpack_from("<I", payload, 40)[0] * 1e-3,
        "p_dop": struct.unpack_from("<H", payload, 76)[0] * 0.01,
        "carr": (flags >> 6) & 0x03,
        "valid": valid_date and valid_time,
    }


def extract_gnss(data_files, on_progress=None):
    """Extract all NAV-PVT positions from .data files, sorted by GPS time."""
    all_pvt = []
    for df in data_files:
        with open(df, "rb") as f:
            f.seek(1024)
            off, end = 1024, os.path.getsize(df)
            while off + 8 <= end:
                hdr = f.read(8)
                cid = struct.unpack_from("<I", hdr, 0)[0]
                dlen = struct.unpack_from("<I", hdr, 4)[0]
                if dlen > 10_000_000:
                    break
                if cid == 2:
                    data = f.read(dlen)
                    i = 0
                    while i < len(data) - 8:
                        if data[i] == 0xB5 and data[i + 1] == 0x62:
                            cls, mid = data[i + 2], data[i + 3]
                            length = struct.unpack_from("<H", data, i + 4)[0]
                            if i + 8 + length <= len(data):
                                pl = data[i + 2:i + 6 + length]
                                ca = cb = 0
                                for b in pl:
                                    ca = (ca + b) & 0xFF
                                    cb = (cb + ca) & 0xFF
                                if (ca == data[i + 6 + length] and
                                        cb == data[i + 7 + length]):
                                    if cls == 0x01 and mid == 0x07:
                                        pvt = parse_nav_pvt(
                                            data[i + 6:i + 6 + length])
                                        if pvt["valid"]:
                                            all_pvt.append(pvt)
                                i += 8 + length
                                continue
                        i += 1
                off += 8 + dlen
                f.seek(off)
    all_pvt.sort(key=lambda p: p["t"])
    return all_pvt


def trajectory_arrays(gnss_data):
    """Extract numpy arrays from GNSS data list."""
    times = np.array([p["t"] for p in gnss_data])
    lats = np.array([p["lat"] for p in gnss_data])
    lons = np.array([p["lon"] for p in gnss_data])
    hgts = np.array([p["h"] for p in gnss_data])
    return times, lats, lons, hgts
