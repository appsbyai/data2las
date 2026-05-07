# Data2Las

**Double-click → .data → .las** — no Python, no terminal, no license key.

## Download

| Platform | File |
|----------|------|
| Windows | [Data2Las-Windows.exe](https://github.com/appsbyai/data2las/releases/latest/download/Data2Las-Windows.exe) |
| Linux | [Data2Las-Linux](https://github.com/appsbyai/data2las/releases/latest/download/Data2Las-Linux) |
| macOS | [Data2Las-macOS](https://github.com/appsbyai/data2las/releases/latest/download/Data2Las-macOS) |

## Quick start

1. Download for your platform
2. **Windows:** Double-click the `.exe`
3. **Linux:** `chmod +x Data2Las-Linux && ./Data2Las-Linux`
4. **macOS:** Right-click → Open (first time)
5. Drag your folder with `ROCK-*.data` files onto the window
6. Click **Process to LAS**

## Centimeter accuracy with PPK

By default, accuracy is ~0.2m (standalone GPS). For centimeter-level accuracy, add your base station RINEX files to the same folder as your `.data` files:

```
my_flight/
  ROCK-2026-05-05-23-36-13-001.data
  base_station.obs               ← observation file
  base_station.nav               ← navigation file (optional)
```

Data2Las auto-detects these and uses PPK if RTKLIB is installed:

| Platform | Install RTKLIB |
|----------|---------------|
| Linux | `sudo apt install rtklib` |
| macOS | Download [RTKLIB demo5](https://github.com/rtklibexplorer/RTKLIB/releases) binary |
| Windows | Download [RTKLIB demo5 binaries](https://github.com/rtklibexplorer/RTKLIB/releases) |

Without RTKLIB, Data2Las still works — just at standalone GPS accuracy (~0.2m).

## For Python users

```bash
pip install "data2las[gui] @ git+https://github.com/appsbyai/data2las.git"
data2las-gui          # desktop app
data2las ./my_data/   # command line
```

## Features

- Zero dependencies (standalone executables)
- PPK support for centimeter accuracy
- 3D point cloud preview
- JPEG photo extraction
- Configurable range filters and calibration
- MIT license — free for everything

## Hardware

Rock Robotic R2A • Livox Avia • uBlox ZED-F9P • Emlid Reach base stations
