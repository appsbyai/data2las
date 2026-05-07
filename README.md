# Data2Las

**One command to convert Rock Robotic R2A `.data` → `.las` point cloud.**

No license key. No login. No cloud. Works on Windows, macOS, Linux.

## Install (copy-paste this)

```bash
pip install "data2las[gui] @ git+https://github.com/appsbyai/data2las.git"
```

## Use

**Desktop app** (drag & drop, preview, export):
```bash
data2las-gui
```

**Command line:**
```bash
data2las ./my_flight_data/
data2las . -o cloud.las --min-range 2 --max-range 150
data2las . --extract-photos
```

## What it does

Drag a folder with `ROCK-*.data` files → click **Process** → get a georeferenced LAS 1.4 file:

- Extracts GNSS trajectory from uBlox ZED-F9P (standalone or PPK)
- Decodes Livox Avia LiDAR points (240k pts/sec)
- Applies boresight + lever arm calibration
- Outputs UTM-projected LAS with GPS time + intensity
- Extracts JPEG photos from the camera channel
- Built-in 3D preview (XY/XZ/YZ projections)

## Supported hardware

| Component | Tested |
|-----------|--------|
| ROCK R2A (fw 4.2.0.0) | Yes |
| Livox Avia | Yes |
| uBlox ZED-F9P | Yes |
| Livox Mid-40/100 | Untested |
| Older firmware versions | Likely works |

## Why

Rock Desktop requires a paid processing license. This tool is MIT-licensed open source — use it anywhere, modify it, share it.

## Build standalone .exe (Windows)

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name Data2Las src/data2las/gui/app.py
```
