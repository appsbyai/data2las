# Data2Las

**Double-click → .data → .las** — no Python, no terminal, no license key.

## Download

| Platform | Download |
|----------|----------|
| Windows | [Data2Las.exe](https://github.com/appsbyai/data2las/releases/latest/download/Data2Las.exe) |
| Linux | [Data2Las](https://github.com/appsbyai/data2las/releases/latest/download/Data2Las) |
| macOS | [Data2Las](https://github.com/appsbyai/data2las/releases/latest/download/Data2Las) |

[All releases →](https://github.com/appsbyai/data2las/releases)

## How to use

1. Download the file for your platform
2. **Windows:** Double-click `Data2Las.exe`
3. **Linux:** `chmod +x Data2Las && ./Data2Las`
4. **macOS:** Right-click → Open (first time only, to bypass Gatekeeper)
5. Drag your folder with `ROCK-*.data` files onto the window
6. Click **Process to LAS**
7. Open the result in [CloudCompare](https://cloudcompare.org)

## Features

- **No dependencies** — single file, no Python/pip needed
- **No license** — MIT open source, free for everything
- **No login** — works offline, no cloud upload
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

Rock Robotic R2A (fw 4.2.0.0 tested) • Livox Avia LiDAR • uBlox ZED-F9P GNSS

Works on Windows, macOS, Linux.
