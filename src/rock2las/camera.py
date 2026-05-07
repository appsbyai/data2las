"""Camera: JPEG extraction from .data container and photo utilities."""

import os
import struct


def extract_photos(data_files, output_dir, on_progress=None):
    """Extract JPEG images from channel 6 of .data files.

    Returns count of extracted photos.
    """
    os.makedirs(output_dir, exist_ok=True)
    cnt = 0

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

                if cid == 6:
                    data = f.read(dlen)
                    soi = data.find(b"\xff\xd8")
                    if soi >= 0:
                        eoi = data.rfind(b"\xff\xd9")
                        if eoi > soi:
                            path = os.path.join(output_dir, f"img_{cnt:06d}.jpg")
                            with open(path, "wb") as jf:
                                jf.write(data[soi:eoi + 2])
                            cnt += 1

                off += 8 + dlen
                f.seek(off)

        if on_progress:
            on_progress(cnt)

    return cnt
