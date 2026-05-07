"""3D point cloud preview widget with XY/XZ/YZ projections."""

import numpy as np
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPainter, QPen, QColor, QFont
import laspy


class PointCloudPreview(QWidget):
    """Widget that renders a point cloud as three orthographic projections."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._points = None
        self.setMinimumSize(400, 250)
        self._msg = "No point cloud loaded\n\nDrop .data files and click Process"

    def load(self, las_path):
        try:
            las = laspy.read(las_path)
            x, y, z = np.array(las.x), np.array(las.y), np.array(las.z)
            intensity = np.array(las.intensity, dtype=np.float64)
            n = len(x)
            if n > 300_000:
                idx = np.random.choice(n, 300_000, replace=False)
                x, y, z, intensity = x[idx], y[idx], z[idx], intensity[idx]
            self._points = (x, y, z, intensity)
            self._msg = None
            self.update()
            return True
        except Exception:
            self._msg = "Failed to load point cloud"
            self._points = None
            self.update()
            return False

    def clear(self):
        self._points = None
        self._msg = "No point cloud loaded\n\nDrop .data files and click Process"
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor(25, 25, 28))

        if self._points is None:
            p.setPen(QColor(120, 120, 120))
            f = QFont("monospace", 13)
            p.setFont(f)
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self._msg)
            p.end()
            return

        x, y, z, intensity = self._points
        ii = (intensity - intensity.min()) / (intensity.max() - intensity.min() + 0.01)

        w, h = self.width(), self.height()
        m = 25

        panels = [
            (QRectF(m, m, w - 2 * m, h * 0.55 - m), x, y, "Top-down (XY)"),
            (QRectF(m, h * 0.55 + 5, (w - 3 * m) / 2, h * 0.4 - m),
             x, z, "Front (XZ)"),
            (QRectF(w / 2 + m / 2, h * 0.55 + 5, (w - 3 * m) / 2,
                    h * 0.4 - m), y, z, "Side (YZ)"),
        ]
        for rect, a, b, title in panels:
            self._draw_panel(p, a, b, ii, rect, title)
        p.end()

    def _draw_panel(self, p, a, b, colors, rect, title):
        p.fillRect(rect, QColor(20, 20, 23))
        p.setPen(QPen(QColor(60, 60, 60), 1))
        p.drawRect(rect)

        px, py = rect.x() + 22, rect.y() + 4
        pw, ph = rect.width() - 26, rect.height() - 26

        a_min, a_max = float(a.min()), float(a.max())
        b_min, b_max = float(b.min()), float(b.max())
        if a_max == a_min:
            a_max = a_min + 1
        if b_max == b_min:
            b_max = b_min + 1

        sa, sb = pw / (a_max - a_min), ph / (b_max - b_min)

        n = min(len(a), 40000)
        step = max(1, len(a) // n)
        for j in range(0, len(a), step):
            qx = px + (a[j] - a_min) * sa
            qy = py + ph - (b[j] - b_min) * sb
            c = int(colors[j] * 255)
            p.setPen(QPen(QColor(c, c * 170 // 255, 255 - c), 1))
            p.drawPoint(QPointF(qx, qy))

        f = QFont("monospace", 8)
        f.setBold(True)
        p.setFont(f)
        p.setPen(QColor(200, 200, 200))
        p.drawText(QRectF(px, rect.y() + 1, 100, 14),
                   Qt.AlignmentFlag.AlignLeft, title)

        f2 = QFont("monospace", 7)
        p.setFont(f2)
        p.setPen(QColor(130, 130, 130))
        p.drawText(QRectF(px, py + ph + 2, pw, 12),
                   Qt.AlignmentFlag.AlignCenter,
                   f"[{a_min:.1f}, {a_max:.1f}]  /  [{b_min:.1f}, {b_max:.1f}] m")
