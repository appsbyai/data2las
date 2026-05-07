"""Processing engine: orchestrates the full .data → LAS pipeline."""

import os
import numpy as np

from . import utils
from .gnss import extract_gnss, trajectory_arrays
from .lidar import decode_points
from .georef import georeference_points
from .las_writer import write_las, get_stats
from .calibration import read_from_pcpp, DEFAULT_LEVER_ARM, DEFAULT_BORESIGHT, DEFAULT_MOUNT_YAW
from .ppk import find_base_rinex, check_time_overlap, extract_rover_rinex, run_ppk, parse_pos_file
from .crs_utils import auto_utm, COMMON_CRS


class Pipeline:
    """Full processing pipeline with progress callbacks."""

    def __init__(self, on_progress=None, on_log=None):
        self.on_progress = on_progress or (lambda pct, msg: None)
        self.on_log = on_log or (lambda msg: None)

    def log(self, msg):
        self.on_log(msg)

    def progress(self, pct, msg):
        self.on_progress(pct, msg)

    def run(self, input_dir, output_path, min_range=1.0, max_range=200.0,
            lever_arm=None, boresight=None, mount_yaw=None, compress=False,
            epsg=None):
        """Execute the complete .data → LAS pipeline."""
        # Phase 1: Discover
        self.progress(0, "Discovering files...")
        files = utils.discover_files(input_dir)
        if not files["data_files"]:
            raise ValueError("No ROCK-*.data files found")

        # Phase 2: Header
        self.progress(5, "Reading header...")
        hdr = utils.read_file_header(files["data_files"][0])
        self.log(f"Device: {hdr['serial']}  FW: {hdr['fw']}")
        self.log(f"LiDAR: {hdr['lidar']}  GNSS: {hdr['gnss']}")

        # Load calibration from .pcpp or use defaults
        if lever_arm is None or boresight is None:
            la, bs, my = read_from_pcpp(files["calib"])
            if lever_arm is None:
                lever_arm = la
            if boresight is None:
                boresight = bs
            if mount_yaw is None:
                mount_yaw = my

        self.log(f"Lever arm: {lever_arm}  Boresight: {boresight}")

        # Phase 3: GNSS (with optional PPK)
        self.progress(10, "Extracting GNSS...")
        gnss = extract_gnss(files["data_files"])
        if not gnss:
            raise ValueError("No valid GNSS positions")

        rover_start = gnss[0]["t"]
        rover_end = gnss[-1]["t"]

        # Look for base station RINEX
        base_obs, base_nav = find_base_rinex(input_dir)
        ppk_used = False

        if base_obs:
            self.log(f"Base station found: {os.path.basename(base_obs)}")
            overlaps, bs_start, bs_end = check_time_overlap(
                rover_start, rover_end, base_obs
            )

            if overlaps:
                self.log("Base station time overlaps rover — attempting PPK...")

                # Convert rover UBX to RINEX
                tmpdir = os.path.join(
                    os.path.dirname(output_path) or input_dir, ".data2las_tmp"
                )
                rover_obs = extract_rover_rinex(
                    files["data_files"], tmpdir, gnss
                )

                if rover_obs:
                    # Run PPK
                    pos_path = run_ppk(rover_obs, base_obs, base_nav, tmpdir)
                    if pos_path:
                        ppk_result = parse_pos_file(pos_path)
                        if ppk_result:
                            ppk_times, ppk_lats, ppk_lons, ppk_heights = ppk_result
                            # Convert to the same format as NAV-PVT
                            ppk_gnss = [
                                {
                                    "t": ppk_times[i],
                                    "lat": ppk_lats[i],
                                    "lon": ppk_lons[i],
                                    "h": ppk_heights[i],
                                    "fix": 4,
                                    "sv": 0,
                                    "h_acc": 0.02,
                                    "p_dop": 1.0,
                                    "carr": 2,
                                    "valid": True,
                                }
                                for i in range(len(ppk_times))
                            ]
                            gnss = ppk_gnss
                            ppk_used = True
                            self.log(
                                f"PPK: {len(gnss)} fixed positions "
                                f"(~0.02m accuracy)"
                            )
                        else:
                            self.log("PPK failed: too few fixed solutions")
                    else:
                        self.log("PPK failed: rnx2rtkp error (RTKLIB installed?)")
                else:
                    self.log("PPK failed: could not extract rover RINEX")
            else:
                self.log(
                    "Base station does not overlap rover time "
                    f"(base: {bs_start/1000:.0f}-{bs_end/1000:.0f}s, "
                    f"rover: {rover_start/1000:.0f}-{rover_end/1000:.0f}s)"
                )

        if not ppk_used:
            self.log(
                f"GNSS: {len(gnss)} positions (standalone, "
                f"~{np.mean([p['h_acc'] for p in gnss]):.2f}m accuracy)"
            )
            self.log(
                "For sub-centimeter accuracy, add base station RINEX files "
                "and install RTKLIB"
            )

        # Phase 4: LiDAR
        self.progress(20, "Decoding LiDAR...")
        pts, total = decode_points(files["data_files"], min_range, max_range)
        self.log(f"LiDAR: {len(pts):,} points, {total:,} frames")
        if not pts:
            raise ValueError("No LiDAR points decoded")

        # Phase 5: Georeference
        self.progress(40, "Georeferencing...")
        lx, ly, lz, li, lt, epsg = georeference_points(
            pts, total, gnss, lever_arm, boresight, mount_yaw,
            on_progress=lambda pct, msg: self.progress(pct, msg),
            epsg_override=epsg)

        # Phase 6: Write
        self.progress(90, "Writing LAS...")
        write_las(lx, ly, lz, li, lt, epsg, output_path, compress)
        self.progress(100, f"Done - {len(lx):,} points")

        stats = get_stats(lx, ly, lz, li)
        stats["epsg"] = epsg
        stats["file"] = output_path
        return stats
