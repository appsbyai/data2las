#!/usr/bin/env python3
"""Rock2Las Desktop — main application window."""

import os, sys, glob as globmod
import numpy as np

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QProgressBar, QTextEdit, QFileDialog,
    QGroupBox, QLineEdit, QDoubleSpinBox, QFormLayout,
    QMessageBox, QDialog,
)
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QAction, QColor, QPalette, QFont

from data2las.engine import Pipeline
from data2las import utils
from .worker import ProcessWorker
from .preview import PointCloudPreview
from .settings import SettingsDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rock2Las Desktop — ROCK R2A Converter")
        self.setMinimumSize(1100, 680)
        self.setAcceptDrops(True)

        self.input_dir = None
        self.result = None
        self.worker = None

        # Restore settings
        self.settings = QSettings("data2las", "desktop")
        self.rng_min = float(self.settings.value("range/min", 1.0))
        self.rng_max = float(self.settings.value("range/max", 200.0))
        self.la = np.array([
            float(self.settings.value("calib/la_x", 0.0)),
            float(self.settings.value("calib/la_y", 0.048)),
            float(self.settings.value("calib/la_z", -0.073)),
        ])
        self.bs = np.array([
            float(self.settings.value("calib/bs_yaw", 0.9)),
            float(self.settings.value("calib/bs_pitch", 0.12)),
            float(self.settings.value("calib/bs_roll", 0.11)),
        ])
        self.my = float(self.settings.value("calib/mount_yaw", 180.0))

        self._build_ui()
        self._build_menu()

    def _build_menu(self):
        mb = self.menuBar()
        f = mb.addMenu("&File")
        f.addAction("&Open Folder...", self._browse_input, "Ctrl+O")
        f.addAction("Set &Output...", self._browse_output, "Ctrl+S")
        f.addSeparator()
        f.addAction("E&xit", self.close, "Ctrl+Q")
        s = mb.addMenu("&Settings")
        s.addAction("&Processing Parameters...", self._show_settings, "Ctrl+P")
        h = mb.addMenu("&Help")
        h.addAction("&About", self._about)

    def _build_ui(self):
        cw = QWidget()
        self.setCentralWidget(cw)
        ml = QHBoxLayout(cw)

        # ---- Left panel ----
        left = QWidget()
        left.setMaximumWidth(400)
        ll = QVBoxLayout(left)
        ll.setContentsMargins(6, 6, 6, 6)

        # Input
        ig = QGroupBox("1. Input")
        igl = QVBoxLayout(ig)
        self._in_label = QLabel("Drop .data files or a folder here")
        self._in_label.setStyleSheet(
            "border:2px dashed #555;border-radius:6px;padding:18px;"
            "color:#888;font-size:12px;background:#1a1a1e;")
        self._in_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._in_label.setMinimumHeight(60)
        igl.addWidget(self._in_label)
        self._btn_in = QPushButton("Browse Folder...")
        self._btn_in.clicked.connect(self._browse_input)
        igl.addWidget(self._btn_in)
        self._info = QLabel("")
        self._info.setStyleSheet("color:#6af;font-size:11px;")
        self._info.setWordWrap(True)
        igl.addWidget(self._info)
        ll.addWidget(ig)

        # Output
        og = QGroupBox("2. Output")
        ogl = QVBoxLayout(og)
        oh = QHBoxLayout()
        self._out_edit = QLineEdit()
        self._out_edit.setPlaceholderText("auto: <input>.las")
        oh.addWidget(self._out_edit)
        bo = QPushButton("..."); bo.setMaximumWidth(28)
        bo.clicked.connect(self._browse_output)
        oh.addWidget(bo)
        ogl.addLayout(oh)
        ll.addWidget(og)

        # Filters
        fg = QGroupBox("3. Filters")
        fgl = QFormLayout(fg)
        self._sp_min = QDoubleSpinBox()
        self._sp_min.setRange(0.1, 50); self._sp_min.setValue(self.rng_min)
        self._sp_min.setSuffix(" m")
        fgl.addRow("Min range:", self._sp_min)
        self._sp_max = QDoubleSpinBox()
        self._sp_max.setRange(10, 500); self._sp_max.setValue(self.rng_max)
        self._sp_max.setSuffix(" m")
        fgl.addRow("Max range:", self._sp_max)
        ll.addWidget(fg)

        # Process button
        self._btn_proc = QPushButton("Process to LAS")
        self._btn_proc.setMinimumHeight(38)
        self._btn_proc.setStyleSheet(
            "QPushButton{background:#2a6;color:white;font-size:13px;"
            "font-weight:bold;border-radius:5px}"
            "QPushButton:hover{background:#3b7}"
            "QPushButton:disabled{background:#444;color:#888}")
        self._btn_proc.clicked.connect(self._process)
        self._btn_proc.setEnabled(False)
        ll.addWidget(self._btn_proc)

        self._pbar = QProgressBar(); self._pbar.setVisible(False)
        ll.addWidget(self._pbar)
        self._plbl = QLabel("")
        self._plbl.setStyleSheet("color:#aaa;font-size:10px;")
        ll.addWidget(self._plbl)

        # Results
        rg = QGroupBox("4. Results")
        rgl = QVBoxLayout(rg)
        self._rtext = QTextEdit()
        self._rtext.setReadOnly(True); self._rtext.setMaximumHeight(120)
        self._rtext.setStyleSheet(
            "background:#1a1a1e;color:#0f0;font-family:monospace;font-size:10px;")
        rgl.addWidget(self._rtext)

        # Action buttons
        rh = QHBoxLayout()
        self._btn_view = QPushButton("View"); self._btn_view.setEnabled(False)
        self._btn_view.clicked.connect(self._view)
        rh.addWidget(self._btn_view)
        self._btn_photos = QPushButton("Extract Photos"); self._btn_photos.setEnabled(False)
        self._btn_photos.clicked.connect(self._extract_photos)
        rh.addWidget(self._btn_photos)
        rgl.addLayout(rh)
        ll.addWidget(rg)
        ll.addStretch()

        ml.addWidget(left)

        # ---- Preview ----
        self._preview = PointCloudPreview()
        ml.addWidget(self._preview, 1)

    # ---- Drag & Drop ----
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._in_label.setStyleSheet(
                "border:2px dashed #2a6;border-radius:6px;padding:18px;"
                "color:#2a6;font-size:12px;background:#1a2a1e;")

    def dragLeaveEvent(self, event):
        self._reset_drop()

    def dropEvent(self, event):
        self._reset_drop()
        for u in event.mimeData().urls():
            p = u.toLocalFile()
            if os.path.isdir(p):
                self._load(p)
                return
            elif os.path.isfile(p):
                self._load(os.path.dirname(p))
                return

    def _reset_drop(self):
        self._in_label.setStyleSheet(
            "border:2px dashed #555;border-radius:6px;padding:18px;"
            "color:#888;font-size:12px;background:#1a1a1e;")

    # ---- Slots ----
    def _browse_input(self):
        d = QFileDialog.getExistingDirectory(self, "Select Folder with .data Files")
        if d:
            self._load(d)
            self.settings.setValue("last_dir", d)

    def _load(self, d):
        self.input_dir = d
        dfs = sorted(globmod.glob(os.path.join(d, "ROCK-*.data")))
        if not dfs:
            self._in_label.setText("No ROCK-*.data files found!")
            self._in_label.setStyleSheet(
                "border:2px dashed #a33;border-radius:6px;padding:18px;"
                "color:#a33;font-size:12px;background:#1a1a1a;")
            return

        try:
            hdr = utils.read_file_header(dfs[0])
            ch = utils.scan_channels(dfs[0])
            info = (f"{len(dfs)} file(s)  |  {hdr['serial']}  |  FW {hdr['fw']}\n"
                    f"LiDAR: {hdr['lidar']}  |  GNSS: {hdr['gnss']}\n")
            if 4 in ch:
                info += f"LiDAR records: {ch[4]['count']:,}  "
            total_mb = sum(os.path.getsize(f) / 1024 / 1024 for f in dfs)
            info += f"Total: {total_mb:.0f} MB"
            self._info.setText(info)
            self._in_label.setText("\n".join(os.path.basename(f) for f in dfs))
            self._in_label.setStyleSheet(
                "border:2px solid #2a6;border-radius:6px;padding:18px;"
                "color:#2a6;font-size:11px;background:#1a2a1e;")
            self._btn_proc.setEnabled(True)
            self._btn_photos.setEnabled(True)
            if not self._out_edit.text():
                base = os.path.splitext(os.path.basename(dfs[0]))[0]
                self._out_edit.setText(os.path.join(d, f"{base}.las"))
        except Exception as e:
            self._info.setText(f"Error: {e}")
            self._btn_proc.setEnabled(False)

    def _browse_output(self):
        p, _ = QFileDialog.getSaveFileName(self, "Output LAS", "", "LAS (*.las);;All (*)")
        if p:
            self._out_edit.setText(p)

    def _show_settings(self):
        dlg = SettingsDialog(self, {
            "rng_min": self.rng_min, "rng_max": self.rng_max,
            "la_x": self.la[0], "la_y": self.la[1], "la_z": self.la[2],
            "bs_yaw": self.bs[0], "bs_pitch": self.bs[1],
            "bs_roll": self.bs[2], "mount_yaw": self.my,
        })
        if dlg.exec() == QDialog.DialogCode.Accepted:
            v = dlg.values()
            self.rng_min, self.rng_max = v["rng_min"], v["rng_max"]
            self.la = np.array([v["la_x"], v["la_y"], v["la_z"]])
            self.bs = np.array([v["bs_yaw"], v["bs_pitch"], v["bs_roll"]])
            self.my = v["mount_yaw"]
            self._sp_min.setValue(self.rng_min)
            self._sp_max.setValue(self.rng_max)
            # Persist
            for k, val in [("range/min", self.rng_min), ("range/max", self.rng_max),
                           ("calib/la_x", self.la[0]), ("calib/la_y", self.la[1]),
                           ("calib/la_z", self.la[2]), ("calib/bs_yaw", self.bs[0]),
                           ("calib/bs_pitch", self.bs[1]), ("calib/bs_roll", self.bs[2]),
                           ("calib/mount_yaw", self.my)]:
                self.settings.setValue(k, val)

    def _about(self):
        QMessageBox.about(self, "About Rock2Las Desktop",
            "Rock2Las Desktop v1.0\n\n"
            "Converts Rock Robotic R2A .data files to georeferenced LAS point clouds.\n\n"
            "Open source (MIT) — no license, no login, no cloud dependency.\n"
            "github.com/your-org/data2las")

    def _process(self):
        if not self.input_dir:
            return
        self.rng_min = self._sp_min.value()
        self.rng_max = self._sp_max.value()
        out = self._out_edit.text() or os.path.join(self.input_dir, "output.las")

        self._btn_proc.setEnabled(False); self._btn_in.setEnabled(False)
        self._pbar.setVisible(True); self._pbar.setValue(0)
        self._rtext.clear()

        self.worker = ProcessWorker(self.input_dir, out, self.rng_min, self.rng_max,
                                    self.la, self.bs, self.my)
        self.worker.progress_signal.connect(self._on_progress)
        self.worker.log_signal.connect(self._on_log)
        self.worker.done_signal.connect(self._on_done)
        self.worker.error_signal.connect(self._on_error)
        self.worker.start()

    def _on_progress(self, pct, msg):
        self._pbar.setValue(pct)
        self._plbl.setText(msg)

    def _on_log(self, msg):
        self._rtext.append(msg)

    def _on_done(self, res):
        self.result = res
        self._pbar.setValue(100); self._plbl.setText("Complete")
        self._btn_proc.setEnabled(True); self._btn_in.setEnabled(True)
        self._btn_view.setEnabled(True)

        self._rtext.append(""); self._rtext.append("=" * 40)
        self._rtext.append(f"Points:     {res['points']:,}")
        self._rtext.append(f"X: [{res['x_rng'][0]:.2f}, {res['x_rng'][1]:.2f}] m")
        self._rtext.append(f"Y: [{res['y_rng'][0]:.2f}, {res['y_rng'][1]:.2f}] m")
        self._rtext.append(f"Z: [{res['z_rng'][0]:.2f}, {res['z_rng'][1]:.2f}] m")
        self._rtext.append(f"Intensity: [{res['i_rng'][0]}, {res['i_rng'][1]}]")
        self._rtext.append(f"CRS: EPSG:{res['epsg']}")
        self._rtext.append(f"File: {res['file']}")
        self._view()

    def _on_error(self, msg):
        self._pbar.setVisible(False); self._plbl.setText("Error")
        self._btn_proc.setEnabled(True); self._btn_in.setEnabled(True)
        self._rtext.append(f"ERROR: {msg}")
        QMessageBox.critical(self, "Processing Error", msg)

    def _view(self):
        if self.result and os.path.exists(self.result["file"]):
            self._preview.load(self.result["file"])

    def _extract_photos(self):
        if not self.input_dir:
            return
        out = os.path.join(self.input_dir, "extracted_photos")
        dfs = sorted(globmod.glob(os.path.join(self.input_dir, "ROCK-*.data")))
        from data2las.camera import extract_photos
        n = extract_photos(dfs, out)
        QMessageBox.information(self, "Photos Extracted",
                                f"{n} JPEG images written to:\n{out}")


def launch_gui():
    """Entry point for data2las-gui command."""
    app = QApplication(sys.argv)
    app.setApplicationName("Rock2Las Desktop")
    app.setStyle("Fusion")

    # Dark theme
    p = QPalette()
    p.setColor(QPalette.ColorRole.Window, QColor(35, 35, 38))
    p.setColor(QPalette.ColorRole.WindowText, QColor(220, 220, 220))
    p.setColor(QPalette.ColorRole.Base, QColor(28, 28, 30))
    p.setColor(QPalette.ColorRole.Text, QColor(220, 220, 220))
    p.setColor(QPalette.ColorRole.Button, QColor(50, 50, 55))
    p.setColor(QPalette.ColorRole.ButtonText, QColor(220, 220, 220))
    p.setColor(QPalette.ColorRole.Highlight, QColor(40, 120, 80))
    app.setPalette(p)

    w = MainWindow()

    # Restore last directory
    last = w.settings.value("last_dir", "")
    if last and os.path.isdir(last):
        w._load(last)

    if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]):
        w._load(sys.argv[1])

    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    launch_gui()
