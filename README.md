# Data2Las

**Double-click → .data → .las** — no Python, no terminal, no license key.

## Download

| Platform | File |
|----------|------|
| Windows | [Data2Las-Windows.exe](https://github.com/appsbyai/data2las/releases/latest/download/Data2Las-Windows.exe) |
| Linux | [Data2Las-Linux](https://github.com/appsbyai/data2las/releases/latest/download/Data2Las-Linux) |
| macOS | [Data2Las-macOS](https://github.com/appsbyai/data2las/releases/latest/download/Data2Las-macOS) |

[All releases →](https://github.com/appsbyai/data2las/releases)

## Quick start

1. Download the file for your platform
2. **Windows:** Double-click `Data2Las-Windows.exe`
3. **Linux:** `chmod +x Data2Las-Linux && ./Data2Las-Linux`
4. **macOS:** Right-click → Open (first time, to bypass Gatekeeper)
5. Drag your folder with `ROCK-*.data` files onto the window
6. Click **Process to LAS**
7. Open the result in [CloudCompare](https://cloudcompare.org)

## Getting better accuracy with PPK

By default, Data2Las uses the built-in GPS positions from the uBlox receiver (~0.2m accuracy). For centimeter-level accuracy, add your base station RINEX files to the same folder:

```
my_flight/
  ROCK-2026-05-05-23-36-13-001.data   ← your .data file(s)
  base_202605050011.obs                ← base station observation file
  base_202605050011.nav                ← base station navigation file (optional)
```

When Data2Las finds base station files with time overlap, it automatically switches to PPK mode.

### Installing RTKLIB (required for PPK)

| Platform | Command |
|----------|---------|
| Linux | `sudo apt install rtklib` |
| macOS | `brew install rtklib` |
| Windows | Download [RTKLIB demo5](https://github.com/rtklibexplorer/RTKLIB/releases) and add to PATH |

If RTKLIB isn't installed, Data2Las will still work — it just falls back to standalone GPS accuracy.

## Features

- **No dependencies** — single file, no Python/pip needed
- **No license** — MIT open source, free for everything  
- **No login** — works offline, no cloud upload
- **PPK support** — centimeter accuracy with base station RINEX + RTKLIB
- **3D preview** — XY/XZ/YZ projections with intensity coloring
- **Photo extraction** — pull JPEG images from the .data container
- **Configurable** — range filters, lever arm calibration, boresight angles

## For Python users (CLI or latest dev version)

```bash
pip install "data2las[gui] @ git+https://github.com/appsbyai/data2las.git"
data2las ./my_flight_data/
data2las-gui
```

## Supported hardware

Rock Robotic R2A (fw 4.2.0.0 tested) • Livox Avia LiDAR • uBlox ZED-F9P GNSS • Emlid Reach RS2 base stations

Works on Windows, macOS, Linux.
