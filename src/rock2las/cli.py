#!/usr/bin/env python3
"""CLI entry point for rock2las."""

import sys, os, argparse, glob as globmod
import numpy as np

from rock2las.engine import Pipeline
from rock2las.camera import extract_photos


def main():
    parser = argparse.ArgumentParser(
        description="Convert Rock Robotic R2A .data files to georeferenced LAS")
    parser.add_argument("directory", nargs="?", default=".",
                        help="Directory with .data files (default: current)")
    parser.add_argument("-o", "--output", help="Output LAS path")
    parser.add_argument("--min-range", type=float, default=1.0)
    parser.add_argument("--max-range", type=float, default=200.0)
    parser.add_argument("--extract-photos", action="store_true",
                        help="Also extract JPEG photos")
    parser.add_argument("--compress", action="store_true",
                        help="Write LAZ (compressed)")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    workdir = os.path.abspath(args.directory)
    os.chdir(workdir)

    if not args.output:
        dfs = sorted(globmod.glob(os.path.join(workdir, "ROCK-*.data")))
        base = os.path.splitext(os.path.basename(dfs[0]))[0] if dfs else "output"
        output = f"{base}.las"
    else:
        output = args.output

    print("rock2las v1.0.0")
    print(f"Processing: {workdir}")
    print(f"Output:     {output}")
    print()

    pipeline = Pipeline(
        on_progress=lambda p, m: print(f"  [{p:3d}%] {m}"),
        on_log=lambda m: print(f"  {m}"))

    try:
        result = pipeline.run(workdir, output,
                              min_range=args.min_range,
                              max_range=args.max_range)
        print()
        print("=" * 50)
        print(f"Points:     {result['points']:,}")
        print(f"X: [{result['x_rng'][0]:.2f}, {result['x_rng'][1]:.2f}] m")
        print(f"Y: [{result['y_rng'][0]:.2f}, {result['y_rng'][1]:.2f}] m")
        print(f"Z: [{result['z_rng'][0]:.2f}, {result['z_rng'][1]:.2f}] m")
        print(f"Intensity: [{result['i_rng'][0]}, {result['i_rng'][1]}]")
        print(f"CRS: EPSG:{result['epsg']}")
        print(f"File: {result['file']}")
        print(f"\nOpen {output} in CloudCompare or similar.")

        if args.extract_photos:
            photo_dir = os.path.join(workdir, "extracted_photos")
            dfs = sorted(globmod.glob(os.path.join(workdir, "ROCK-*.data")))
            n = extract_photos(dfs, photo_dir)
            print(f"Photos: {n} extracted to {photo_dir}")

    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
