"""PPK: Post-Processed Kinematic GNSS using RTKLIB or pure-Python fallback."""

import os, sys, struct, subprocess, tempfile, glob as globmod
import numpy as np


def find_base_rinex(directory):
    """Find base station RINEX files in a directory."""
    obs_file = None
    nav_file = None

    for f in os.listdir(directory):
        full = os.path.join(directory, f)
        if not os.path.isfile(full):
            continue

        # Check for RINEX observation files by reading header
        try:
            with open(full, "r", errors="replace") as fh:
                first_line = fh.readline()
                if "OBSERVATION DATA" in first_line or "RINEX VERSION" in first_line:
                    if "OBSERVATION" in first_line:
                        if obs_file is None:
                            obs_file = full
                elif "NAVIGATION DATA" in first_line:
                    if nav_file is None:
                        nav_file = full
        except Exception:
            continue

        # Also check by extension
        base = os.path.basename(f)
        for ext in ["26O", "27O", "25O", "24O", "23O", "22O", ".obs"]:
            if base.endswith(ext) and obs_file is None:
                obs_file = full
        for ext in ["26P", "27P", "25P", "24P", "23P", "22P", "26N", "27N", ".nav"]:
            if base.endswith(ext) and nav_file is None:
                nav_file = full

    return obs_file, nav_file


def check_time_overlap(rover_start_gps_ms, rover_end_gps_ms, obs_file):
    """Check if base station RINEX covers the rover observation window.

    Returns (overlaps, base_start, base_end) where times are GPS milliseconds of week.
    """
    try:
        with open(obs_file, "r") as f:
            header = ""
            for _ in range(50):
                line = f.readline()
                header += line
                if "END OF HEADER" in line:
                    break

            # Parse TIME OF FIRST OBS and TIME OF LAST OBS
            import re

            first_match = re.search(
                r"(\d{4})\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+([\d.]+).*TIME OF FIRST OBS",
                header,
            )
            last_match = re.search(
                r"(\d{4})\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+([\d.]+).*TIME OF LAST OBS",
                header,
            )

            if first_match and last_match:
                # Convert GPS time to milliseconds of week
                y, m, d, hh, mm, ss = [float(x) for x in first_match.groups()]
                base_start_sow = _gps_to_sow(y, m, d, hh, mm, ss)
                y, m, d, hh, mm, ss = [float(x) for x in last_match.groups()]
                base_end_sow = _gps_to_sow(y, m, d, hh, mm, ss)

                rover_start_s = rover_start_gps_ms / 1000.0
                rover_end_s = rover_end_gps_ms / 1000.0

                overlaps = not (rover_end_s < base_start_sow or rover_start_s > base_end_sow)
                return overlaps, base_start_sow * 1000, base_end_sow * 1000

    except Exception:
        pass

    return True, 0, 0  # Assume overlap if we can't parse


def _gps_to_sow(year, month, day, hour, minute, second):
    """Convert GPS date/time to seconds of GPS week (approximate)."""
    import datetime
    from datetime import timedelta

    # Simple: convert to seconds since GPS epoch, then mod by week
    gps_epoch = datetime.datetime(1980, 1, 6, 0, 0, 0)
    dt = datetime.datetime(int(year), int(month), int(day), int(hour), int(minute), 0)
    dt = dt + timedelta(seconds=second)
    total_seconds = (dt - gps_epoch).total_seconds()
    # Remove leap seconds (approximate 18 for 2026)
    total_seconds -= 18
    sow = total_seconds % 604800
    return sow


def extract_rover_rinex(data_files, output_dir, gnss_data):
    """Extract rover raw UBX, convert to RINEX observation file.

    Uses RTKLIB's convbin if available, otherwise writes a basic RINEX.
    Returns path to rover .obs file, or None if conversion failed.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Extract all UBX raw messages from channel 2
    ubx_path = os.path.join(output_dir, "rover.ubx")
    msg_count = _extract_ubx_raw(data_files, ubx_path)

    if msg_count == 0:
        return None

    # Try RTKLIB convbin first
    if _find_tool("convbin"):
        obs_path = os.path.join(output_dir, "rover.obs")
        nav_path = os.path.join(output_dir, "rover.nav")
        cmd = [
            "convbin", "-r", "ubx", "-v", "3.04",
            "-od", "-os", "GPS,GLO,GAL,BDS,QZS",
            "-o", obs_path, "-n", nav_path, ubx_path,
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=30)
            if os.path.exists(obs_path) and os.path.getsize(obs_path) > 100:
                return obs_path
        except Exception:
            pass

    # Fallback: write basic RINEX from RXM-RAWX messages
    obs_path = os.path.join(output_dir, "rover.obs")
    if _write_rinex_from_rawx(data_files, obs_path):
        return obs_path

    return None


def run_ppk(rover_obs, base_obs, base_nav, output_dir):
    """Run RTKLIB rnx2rtkp for PPK processing.

    Returns path to .pos file if successful, None otherwise.
    """
    if not _find_tool("rnx2rtkp"):
        return None

    pos_path = os.path.join(output_dir, "ppk_solution.pos")

    config = _write_rtklib_config(output_dir)

    cmd = [
        "rnx2rtkp",
        "-k", config,
        "-o", pos_path,
        rover_obs,
        base_obs,
    ]
    if base_nav:
        cmd.append(base_nav)

    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=60)
        if os.path.exists(pos_path) and os.path.getsize(pos_path) > 100:
            return pos_path
    except Exception:
        pass

    return None


def parse_pos_file(pos_path):
    """Parse RTKLIB .pos output into trajectory arrays.

    Returns (times_ms, lats, lons, heights) or None.
    """
    data = []
    with open(pos_path, "r") as f:
        for line in f:
            if line.startswith("%"):
                continue
            parts = line.split()
            if len(parts) < 8:
                continue
            try:
                # Format: yyyy/mm/dd hh:mm:ss.sss  lat  lon  height  Q  ns
                date_str = parts[0]
                time_str = parts[1]
                lat = float(parts[2])
                lon = float(parts[3])
                height = float(parts[4])
                q = int(parts[5])

                if q == 1:  # Fixed solution only
                    # Convert to GPS milliseconds of week
                    y, m, d = date_str.split("/")
                    hh, mm, ss = time_str.split(":")
                    sow = _gps_to_sow(
                        int(y), int(m), int(d), int(hh), int(mm), float(ss)
                    )
                    data.append((sow * 1000, lat, lon, height))
            except (ValueError, IndexError):
                continue

    if len(data) < 10:
        return None

    data.sort(key=lambda x: x[0])
    times = np.array([d[0] for d in data])
    lats = np.array([d[1] for d in data])
    lons = np.array([d[2] for d in data])
    heights = np.array([d[3] for d in data])

    return times, lats, lons, heights


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _find_tool(name):
    """Check if a command-line tool is available."""
    import shutil
    return shutil.which(name) is not None


def _extract_ubx_raw(data_files, output_path):
    """Extract all UBX messages from channel 2 into a raw file."""
    count = 0
    with open(output_path, "wb") as out:
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
                        # Scan for UBX sync words
                        i = 0
                        while i < len(data) - 8:
                            if data[i] == 0xB5 and data[i + 1] == 0x62:
                                cls, mid = data[i + 2], data[i + 3]
                                length = struct.unpack_from("<H", data, i + 4)[0]
                                if i + 8 + length <= len(data):
                                    pl = data[i + 2 : i + 6 + length]
                                    ca = cb = 0
                                    for b in pl:
                                        ca = (ca + b) & 0xFF
                                        cb = (cb + ca) & 0xFF
                                    if (
                                        ca == data[i + 6 + length]
                                        and cb == data[i + 7 + length]
                                    ):
                                        # Write valid UBX message with sync + class/id + length + payload + checksum
                                        msg = (
                                            data[i : i + 2]
                                            + data[i + 2 : i + 6]
                                            + struct.pack("<H", length)
                                            + data[i + 6 : i + 6 + length]
                                            + data[i + 6 + length : i + 8 + length]
                                        )
                                        out.write(msg)
                                        count += 1
                                    i += 8 + length
                                    continue
                            i += 1
                    off += 8 + dlen
                    f.seek(off)
    return count


def _write_rinex_from_rawx(data_files, output_path):
    """Write a basic RINEX observation file from RXM-RAWX messages.

    This is a simplified version — RTKLIB's convbin is preferred.
    """
    # For now, return False to indicate this isn't implemented
    # Pure-Python RINEX generation from RAWX is complex
    return False


def _write_rtklib_config(output_dir):
    """Write RTKLIB configuration file for PPK processing."""
    config_path = os.path.join(output_dir, "ppk.conf")

    config = """pos1-posmode       = kinematic
pos1-frequency     = l1+l2
pos1-soltype       = forward
pos1-elmask        = 15
pos1-snrmask_r     = off
pos1-snrmask_b     = off
pos1-snrmask_L1    = 0,0,0,0,0,0,0,0,0
pos1-snrmask_L2    = 0,0,0,0,0,0,0,0,0
pos1-snrmask_L5    = 0,0,0,0,0,0,0,0,0
pos1-dynamics      = on
pos1-tidecorr      = off
pos1-tropopt       = saastamoinen
pos1-ionoopt       = broadcast
pos1-sateph        = broadcast
pos1-exclsats      =
pos1-navsys        = 31
pos2-armode        = fix-and-hold
pos2-gloarmode     = on
pos2-bdsarmode     = off
pos2-arthres       = 3
pos2-arlockcnt     = 0
pos2-arelmask      = 0
pos2-arminfix      = 10
pos2-elmaskhold    = 0
pos2-aroutcnt      = 5
pos2-maxage        = 30
pos2-syncsol       = on
pos2-slipthres     = 0.05
pos2-rejionno      = 30
pos2-rejgdop       = 30
pos2-niter         = 1
pos2-baselen       = 0
pos2-basesig       = 0
out-solformat      = llh
out-outhead        = on
out-outopt         = off
out-timesys        = gpst
out-timeform       = hms
out-timendec       = 3
out-degform        = deg
out-fieldsep       =
out-height         = ellipsoidal
out-geoid          = internal
out-solstatic      = all
out-solstat        = all
out-nmeaintv1      = 0
out-nmeaintv2      = 0
out-outstat        = off
stats-errratio     = 100
"""

    with open(config_path, "w") as f:
        f.write(config)

    return config_path
