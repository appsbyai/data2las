"""Calibration: parse Rock Desktop project files for lever arm and boresight."""

import os
import numpy as np
import xml.etree.ElementTree as ET


DEFAULT_LEVER_ARM = [0.0, 0.048, -0.073]
DEFAULT_BORESIGHT = [0.9, 0.12, 0.11]
DEFAULT_MOUNT_YAW = 180.0


def read_from_pcpp(calib_path):
    """Extract LiDAR calibration from a .pcpp file."""
    if not calib_path or not os.path.exists(calib_path):
        return np.array(DEFAULT_LEVER_ARM), np.array(DEFAULT_BORESIGHT), DEFAULT_MOUNT_YAW

    la = np.array(DEFAULT_LEVER_ARM)
    bs = np.array(DEFAULT_BORESIGHT)
    my = DEFAULT_MOUNT_YAW

    try:
        tree = ET.parse(calib_path)
        root = tree.getroot()
        offsets = root.find(".//Offsets")
        if offsets is not None:
            linear = offsets.find("linear")
            angular = offsets.find("angular")
            orientation = offsets.find("orientation")
            if linear is not None:
                la = np.array([
                    float(linear.get("x", DEFAULT_LEVER_ARM[0])),
                    float(linear.get("y", DEFAULT_LEVER_ARM[1])),
                    float(linear.get("z", DEFAULT_LEVER_ARM[2])),
                ])
            if angular is not None:
                bs = np.array([
                    float(angular.get("yaw", DEFAULT_BORESIGHT[0])),
                    float(angular.get("pitch", DEFAULT_BORESIGHT[1])),
                    float(angular.get("roll", DEFAULT_BORESIGHT[2])),
                ])
            if orientation is not None:
                my = float(orientation.get("yaw", DEFAULT_MOUNT_YAW))
    except Exception:
        pass

    return la, bs, my
