# Data2Las

**Double-click → .data → .las** — no Python, no terminal, no license key.

[⬇ Download Data2Las.exe](https://github.com/appsbyai/data2las/releases/latest)

## How to use

1. Download `Data2Las.exe` from the link above
2. Double-click it
3. Drag your folder with `ROCK-*.data` files onto the window
4. Click **Process to LAS**
5. Open the result in [CloudCompare](https://cloudcompare.org)

## Screenshot

```
┌──────────────────────────────────────────────────────┐
│  Data2Las Desktop                                     │
│  ┌──────────────────────┐  ┌──────────────────────┐  │
│  │ 1. Input             │  │                      │  │
│  │  [drag files here]   │  │   ┌──────────────┐   │  │
│  │  [Browse Folder]     │  │   │ 3D Preview   │   │  │
│  │                      │  │   │ (XY, XZ, YZ)  │   │  │
│  │ 2. Output            │  │   └──────────────┘   │  │
│  │  [output path    ]   │  │                      │  │
│  │                      │  │                      │  │
│  │ 3. Filters           │  │                      │  │
│  │  Min range: [1.0] m  │  │                      │  │
│  │  Max range: [200] m  │  │                      │  │
│  │                      │  │                      │  │
│  │ [Process to LAS]     │  │                      │  │
│  │ [████████░░░] 67%    │  │                      │  │
│  │                      │  │                      │  │
│  │ 4. Results           │  │                      │  │
│  │  9.1M pts  EPSG:32756│  │                      │  │
│  │  [View] [Photos]     │  │                      │  │
│  └──────────────────────┘  └──────────────────────┘  │
└──────────────────────────────────────────────────────┘
```

## For command-line users

```bash
pip install "data2las[gui] @ git+https://github.com/appsbyai/data2las.git"
data2las ./my_flight_data/
data2las-gui
```

## Supported

- Rock Robotic R2A (fw 4.2.0.0 tested)
- Livox Avia LiDAR
- uBlox ZED-F9P GNSS
- Works on Windows, macOS, Linux

## License

MIT — free for everything.
