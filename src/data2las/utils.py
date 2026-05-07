"""File discovery and utility functions."""

import os
import glob as globmod


def discover_files(directory):
    """Find all relevant files in a directory."""
    result = {"data_files": [], "calib": None, "base_obs": None}
    for f in sorted(os.listdir(directory)):
        full = os.path.join(directory, f)
        if not os.path.isfile(full):
            continue
        if f.startswith("ROCK-") and f.endswith(".data"):
            result["data_files"].append(full)
        elif f.endswith(".pcpp"):
            result["calib"] = full
    return result


def read_file_header(path):
    """Read 1024-byte ROCK .data file header."""
    with open(path, "rb") as f:
        d = f.read(1024)
    return {
        "serial": d[8:24].rstrip(b"\x00").decode("ascii", errors="replace"),
        "fw": d[24:40].rstrip(b"\x00").decode("ascii", errors="replace"),
        "gnss": d[40:104].rstrip(b"\x00").decode("ascii", errors="replace"),
        "lidar": d[104:168].rstrip(b"\x00").decode("ascii", errors="replace"),
    }


def scan_channels(path):
    """Return summary of channels in a .data file."""
    import struct
    ch = {}
    with open(path, "rb") as f:
        f.seek(1024)
        off, end = 1024, os.path.getsize(path)
        while off + 8 <= end:
            hdr = f.read(8)
            cid = struct.unpack_from("<I", hdr, 0)[0]
            dlen = struct.unpack_from("<I", hdr, 4)[0]
            if dlen > 10_000_000:
                break
            if cid not in ch:
                data = f.read(min(dlen, 32))
                f.seek(off + 8)
                name = data[:16].split(b"\x00")[0]
                try:
                    name = name.decode("ascii", errors="replace")
                except Exception:
                    name = f"ch{cid}"
                ch[cid] = {"name": name, "count": 1, "bytes": dlen, "min": dlen, "max": dlen}
            else:
                ch[cid]["count"] += 1
                ch[cid]["bytes"] += dlen
                ch[cid]["min"] = min(ch[cid]["min"], dlen)
                ch[cid]["max"] = max(ch[cid]["max"], dlen)
            off += 8 + dlen
            f.seek(off)
    return ch
