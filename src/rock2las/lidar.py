"""LiDAR: Livox Avia point decoding from .data channel 4."""

import struct
import math
import os

FRAME_SIZE = 668
POINTS_PER_FRAME = 30
GROUP_SIZE = 22


def decode_points(data_files, rng_min=1.0, rng_max=200.0, on_progress=None):
    """Decode all LiDAR points from LIVX (channel 4) records.

    Each 668-byte frame contains 30 groups of 22 bytes:
      offset 0-1: x_mm (uint16 LE, signed)
      offset 2-3: y_mm (uint16 LE, signed)
      offset 4-5: z_mm (uint16 LE, signed)
      offset 6-7: padding
      offset 8:   intensity (uint8)
      offset 9-21:  padding
    """
    pts = []
    total_records = 0

    for df in data_files:
        with open(df, "rb") as f:
            f.seek(1024)
            off, end = 1024, os.path.getsize(df)
            rec = 0

            while off + 8 <= end:
                hdr = f.read(8)
                cid = struct.unpack_from("<I", hdr, 0)[0]
                dlen = struct.unpack_from("<I", hdr, 4)[0]
                if dlen > 10_000_000:
                    break

                if cid == 4:
                    data = f.read(dlen)
                    if rec > 0 and dlen == FRAME_SIZE:
                        for g in range(POINTS_PER_FRAME):
                            go = 8 + g * GROUP_SIZE
                            x = struct.unpack_from("<H", data, go)[0]
                            y = struct.unpack_from("<H", data, go + 2)[0]
                            z = struct.unpack_from("<H", data, go + 4)[0]
                            intensity = data[go + 8]

                            if x != 0 or y != 0 or z != 0:
                                xm = (x if x < 32768 else x - 65536) / 1000.0
                                ym = (y if y < 32768 else y - 65536) / 1000.0
                                zm = (z if z < 32768 else z - 65536) / 1000.0
                                rng = math.sqrt(xm**2 + ym**2 + zm**2)
                                if rng_min <= rng <= rng_max:
                                    pts.append({
                                        "x": xm, "y": ym, "z": zm,
                                        "i": intensity, "rec": total_records,
                                    })
                    rec += 1
                    total_records += 1

                off += 8 + dlen
                f.seek(off)

        if on_progress:
            on_progress(len(pts))

    return pts, total_records
