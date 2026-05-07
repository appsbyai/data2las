"""Processing engine: orchestrates the full .data → LAS pipeline."""

import os
import numpy as np

from . import utils
from .gnss import extract_gnss, trajectory_arrays
from .lidar import decode_points
from .georef import georeference_points
from .las_writer import write_las, get_stats
from .calibration import read_from_pcpp, DEFAULT_LEVER_ARM, DEFAULT_BORESIGHT, DEFAULT_MOUNT_YAW


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
            lever_arm=None, boresight=None, mount_yaw=None, compress=False):
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

        # Phase 3: GNSS
        self.progress(10, "Extracting GNSS...")
        gnss = extract_gnss(files["data_files"])
        if not gnss:
            raise ValueError("No valid GNSS positions")
        self.log(f"GNSS: {len(gnss)} positions, "
                 f"{(gnss[-1]['t'] - gnss[0]['t'])/1000:.1f}s")

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
            on_progress=lambda pct, msg: self.progress(pct, msg))

        # Phase 6: Write
        self.progress(90, "Writing LAS...")
        write_las(lx, ly, lz, li, lt, epsg, output_path, compress)
        self.progress(100, f"Done - {len(lx):,} points")

        stats = get_stats(lx, ly, lz, li)
        stats["epsg"] = epsg
        stats["file"] = output_path
        return stats
