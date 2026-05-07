# Rock2Las

Convert Rock Robotic R2A `.data` files to georeferenced LAS/LAZ point clouds.

**No license key required. No login. No cloud dependency.**

## Quick Start

```bash
pip install rock2las[gui]
rock2las-gui          # Desktop app (Windows/Linux/macOS)
rock2las ./my_data/   # CLI
```

## GUI

Drag a folder containing `ROCK-*.data` files onto the window and click **Process to LAS**. The app auto-detects calibration from `.pcpp` project files and writes a georeferenced LAS 1.4 file with GPS time and intensity.

Features:
- Drag-and-drop .data files
- Configurable range filters and calibration (lever arm, boresight)
- Built-in 3D point cloud preview (XY/XZ/YZ projections)
- JPEG photo extraction from the .data container
- Settings persistence between sessions

## CLI

```bash
rock2las /path/to/data
rock2las . -o output.las --min-range 2.0 --max-range 150.0
rock2las . --extract-photos
```

## Supported Hardware

- **Sensor:** Rock Robotic R2A
- **LiDAR:** Livox Avia (Mid-40/100 untested)
- **GNSS:** uBlox ZED-F9P (standalone ~0.2m, PPK if base RINEX available)
- **Firmware:** 4.2.0.0 tested (other versions may work)

## Build Standalone Executable

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name Rock2Las gui/app.py
```

Outputs `dist/Rock2Las.exe` (or `.app` on macOS).

## License

MIT — free for commercial and personal use.
