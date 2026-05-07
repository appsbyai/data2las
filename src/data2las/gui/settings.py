"""Settings dialog for calibration and filter parameters."""

from PySide6.QtWidgets import (
    QDialog, QFormLayout, QDoubleSpinBox, QLabel, QDialogButtonBox
)


class SettingsDialog(QDialog):
    def __init__(self, parent=None, current=None):
        super().__init__(parent)
        self.setWindowTitle("Calibration & Filters")
        self.setMinimumWidth(380)
        c = current or {}

        ly = QFormLayout(self)
        ly.addRow(QLabel("<b>Range Filter</b>"))
        self._rng_min = QDoubleSpinBox()
        self._rng_min.setRange(0.1, 50)
        self._rng_min.setValue(c.get("rng_min", 1.0))
        self._rng_min.setSuffix(" m")
        ly.addRow("Min range:", self._rng_min)
        self._rng_max = QDoubleSpinBox()
        self._rng_max.setRange(10, 500)
        self._rng_max.setValue(c.get("rng_max", 200.0))
        self._rng_max.setSuffix(" m")
        ly.addRow("Max range:", self._rng_max)

        ly.addRow(QLabel("<b>Lever Arm</b> (m, LiDAR to IMU)"))
        self._la = []
        for lbl, dflt in [("X", 0.0), ("Y", 0.048), ("Z", -0.073)]:
            sb = QDoubleSpinBox()
            sb.setRange(-2, 2); sb.setDecimals(4)
            sb.setValue(c.get(f"la_{lbl.lower()}", dflt))
            ly.addRow(f"  {lbl}:", sb)
            self._la.append(sb)

        ly.addRow(QLabel("<b>Boresight</b> (degrees)"))
        self._bs = []
        for lbl, dflt in [("Yaw", 0.9), ("Pitch", 0.12), ("Roll", 0.11)]:
            sb = QDoubleSpinBox()
            sb.setRange(-10, 10); sb.setDecimals(3)
            sb.setValue(c.get(f"bs_{lbl.lower()}", dflt))
            ly.addRow(f"  {lbl}:", sb)
            self._bs.append(sb)

        self._my = QDoubleSpinBox()
        self._my.setRange(0, 360)
        self._my.setValue(c.get("mount_yaw", 180.0))
        ly.addRow("Mount yaw:", self._my)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        ly.addRow(btns)

    def values(self):
        return {
            "rng_min": self._rng_min.value(),
            "rng_max": self._rng_max.value(),
            "la_x": self._la[0].value(), "la_y": self._la[1].value(),
            "la_z": self._la[2].value(),
            "bs_yaw": self._bs[0].value(), "bs_pitch": self._bs[1].value(),
            "bs_roll": self._bs[2].value(),
            "mount_yaw": self._my.value(),
        }
