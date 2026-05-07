"""QThread worker for background processing."""

from PySide6.QtCore import QThread, Signal
import numpy as np

from data2las.engine import Pipeline


class ProcessWorker(QThread):
    progress_signal = Signal(int, str)
    log_signal = Signal(str)
    done_signal = Signal(dict)
    error_signal = Signal(str)

    def __init__(self, input_dir, output_path, min_range, max_range,
                 lever_arm, boresight, mount_yaw):
        super().__init__()
        self.args = (input_dir, output_path, min_range, max_range,
                     lever_arm, boresight, mount_yaw)

    def run(self):
        try:
            pipeline = Pipeline(
                on_progress=lambda p, m: self.progress_signal.emit(p, m),
                on_log=lambda m: self.log_signal.emit(m))
            result = pipeline.run(*self.args)
            self.done_signal.emit(result)
        except Exception as e:
            self.error_signal.emit(str(e))
