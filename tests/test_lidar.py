"""Test LiDAR point decoding against the known test dataset."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from data2las.lidar import decode_points
from data2las.utils import read_file_header


def test_header():
    """Verify header parsing on the test .data file."""
    test_file = os.path.join(os.path.dirname(__file__), '..', '..', '..',
                             'ROCK-2026-05-05-23-36-13-001.data')
    if not os.path.exists(test_file):
        print("SKIP: test .data file not found")
        return

    hdr = read_file_header(test_file)
    assert hdr["serial"] == "ROCK-537F2D"
    assert hdr["lidar"] == "Livox Avia"
    assert "ZED-F9P" in hdr["gnss"]
    print("  header: OK")


def test_decode():
    """Verify point decoding produces expected count."""
    test_file = os.path.join(os.path.dirname(__file__), '..', '..', '..',
                             'ROCK-2026-05-05-23-36-13-001.data')
    if not os.path.exists(test_file):
        print("SKIP: test .data file not found")
        return

    pts, total = decode_points([test_file], rng_min=1.0, rng_max=200.0)
    assert len(pts) == 9_191_910, f"Expected 9191910, got {len(pts)}"
    assert total == 306_397, f"Expected 306397, got {total}"
    print(f"  decode: {len(pts):,} points, {total:,} frames: OK")


if __name__ == "__main__":
    print("Testing LiDAR decoder...")
    test_header()
    test_decode()
    print("All tests passed.")
