from __future__ import annotations

import sys
from copy import deepcopy
from pathlib import Path
from tempfile import gettempdir

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox,
                               QDoubleSpinBox, QFormLayout, QHBoxLayout,
                               QLabel, QLineEdit, QMessageBox, QPushButton,
                               QSpinBox, QVBoxLayout, QWidget)

from retinomap.config import ExperimentConfig
from retinomap.player import StimulusPlayer
from retinomap.preset import list_presets, load_preset, save_preset


class RetinomapGUI(QWidget):
    """刺激のパラメータやメタ情報の編集、及び刺激の開始と終了を担うGUI"""
    def __init__(self) -> None:
        super().__init__()

        self.config = ExperimentConfig()

        self.setWindowTitle("retinomap")
        self.resize(420, 600)

        self._build_ui()
        self._load_config_to_widgets()
        self._refresh_presets()
        self.player = StimulusPlayer(self.config)
        self.player.open_window()
        self.player.set_preview_callback(self._update_preview, fps=10.0)

    def _build_ui(self) -> None:
        root = QVBoxLayout()
        form = QFormLayout()

        self.experiment_id_edit = QLineEdit()
        self.experiment_id_edit.setPlaceholderText("e.g. mouse001")

        form.addRow("Experiment ID", self.experiment_id_edit)

        # --- preset ---
        self.preset_combo = QComboBox()
        self.preset_name = QLineEdit()

        preset_buttons = QHBoxLayout()
        self.load_button = QPushButton("Load")
        self.save_button = QPushButton("Save as")
        preset_buttons.addWidget(self.load_button)
        preset_buttons.addWidget(self.save_button)

        form.addRow("Preset", self.preset_combo)
        form.addRow("Preset name", self.preset_name)

        # --- display ---
        self.screen_index = QSpinBox()
        self.screen_index.setRange(0, 8)

        self.width = QSpinBox()
        self.width.setRange(100, 10000)

        self.height = QSpinBox()
        self.height.setRange(100, 10000)

        self.fps = QDoubleSpinBox()
        self.fps.setRange(1, 240)
        self.fps.setDecimals(1)

        self.fullscreen = QCheckBox()

        form.addRow("Stimulus screen index", self.screen_index)
        form.addRow("Width", self.width)
        form.addRow("Height", self.height)
        form.addRow("FPS", self.fps)
        form.addRow("Fullscreen", self.fullscreen)

        # --- stimulus ---
        self.stimulus_type = QComboBox()
        self.stimulus_type.addItems(["moving_bar", "checker_bar", "sparse_noise"])

        self.speed = QDoubleSpinBox()
        self.speed.setRange(1, 5000)

        self.bar_width = QSpinBox()
        self.bar_width.setRange(1, 5000)

        self.checker_size = QSpinBox()
        self.checker_size.setRange(1, 1000)

        self.reversal_rate = QDoubleSpinBox()
        self.reversal_rate.setRange(0, 60)
        self.reversal_rate.setDecimals(2)

        form.addRow("Stimulus type", self.stimulus_type)
        form.addRow("Speed px/s", self.speed)
        form.addRow("Bar width px", self.bar_width)
        form.addRow("Checker size px", self.checker_size)
        form.addRow("Reversal rate Hz", self.reversal_rate)

        # --- trial ---
        self.directions = QLineEdit()

        self.repetitions = QSpinBox()
        self.repetitions.setRange(1, 1000)

        self.sweeps_per_direction = QSpinBox()
        self.sweeps_per_direction.setRange(1, 1000)

        self.iti = QDoubleSpinBox()
        self.iti.setRange(0, 600)
        self.iti.setDecimals(2)

        self.isi = QDoubleSpinBox()
        self.isi.setRange(0, 600)
        self.isi.setDecimals(2)

        form.addRow("Directions", self.directions)
        form.addRow("Repetitions", self.repetitions)
        form.addRow("Sweeps / direction", self.sweeps_per_direction)
        form.addRow("ITI sec", self.iti)
        form.addRow("ISI sec", self.isi)

        # --- screen / warp ---
        self.enable_warp = QCheckBox()

        self.screen_width_cm = QDoubleSpinBox()
        self.screen_width_cm.setRange(1, 1000)

        self.screen_height_cm = QDoubleSpinBox()
        self.screen_height_cm.setRange(1, 1000)

        self.distance_cm = QDoubleSpinBox()
        self.distance_cm.setRange(1, 1000)

        form.addRow("Enable warp", self.enable_warp)
        form.addRow("Screen width cm", self.screen_width_cm)
        form.addRow("Screen height cm", self.screen_height_cm)
        form.addRow("Distance cm", self.distance_cm)

        # --- photodiode ---
        self.photodiode_enable = QCheckBox()

        self.photodiode_size = QSpinBox()
        self.photodiode_size.setRange(1, 1000)

        self.photodiode_margin = QSpinBox()
        self.photodiode_margin.setRange(0, 1000)

        form.addRow("Photodiode", self.photodiode_enable)
        form.addRow("Photodiode size px", self.photodiode_size)
        form.addRow("Photodiode margin px", self.photodiode_margin)

        # --- log ---
        self.log_enable = QCheckBox()
        self.log_directory = QLineEdit()

        form.addRow("Enable log", self.log_enable)
        form.addRow("Log directory", self.log_directory)

        self.preview_label = QLabel()
        self.preview_label.setFixedSize(320, 240)
        self.preview_label.setStyleSheet("background-color: #777;")
        self.preview_label.setAlignment(Qt.AlignCenter)

        root.addWidget(self.preview_label)

        # --- buttons ---
        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)

        root.addLayout(form)
        root.addLayout(preset_buttons)
        root.addLayout(button_layout)

        self.setLayout(root)

        self.load_button.clicked.connect(self._on_load)
        self.save_button.clicked.connect(self._on_save)
        self.start_button.clicked.connect(self._on_start)
        self.stop_button.clicked.connect(self._on_stop)

        self.stop_button.setEnabled(False)

    def _load_config_to_widgets(self) -> None:
        c = self.config

        d = c.stimulus_display
        self.screen_index.setValue(d.screen_index)
        self.width.setValue(d.width)
        self.height.setValue(d.height)
        self.fps.setValue(d.fps)
        self.fullscreen.setChecked(d.fullscreen)

        s = c.stimulus
        self.stimulus_type.setCurrentText(s.stimulus_type)
        self.speed.setValue(s.speed)
        self.bar_width.setValue(s.bar_width)
        self.checker_size.setValue(s.checker_size)
        self.reversal_rate.setValue(s.checker_reversal_rate)

        t = c.trial
        self.directions.setText(",".join(t.directions))
        self.repetitions.setValue(t.repetitions)
        self.sweeps_per_direction.setValue(t.sweeps_per_direction)
        self.iti.setValue(t.iti)
        self.isi.setValue(t.inter_stimulus_interval)

        sc = c.screen
        self.enable_warp.setChecked(sc.enable_warp)
        self.screen_width_cm.setValue(sc.width_cm)
        self.screen_height_cm.setValue(sc.height_cm)
        self.distance_cm.setValue(sc.distance_cm)

        p = c.photodiode
        self.photodiode_enable.setChecked(p.enable)
        self.photodiode_size.setValue(p.size_px)
        self.photodiode_margin.setValue(p.margin_px)

        l = c.log
        self.log_enable.setChecked(l.enable)
        self.log_directory.setText(l.directory)

    def _widgets_to_config(self) -> ExperimentConfig:
        c = deepcopy(self.config)

        c.experiment_id = self.experiment_id_edit.text().strip().replace("/", "_").replace("\\", "_")

        d = c.stimulus_display
        d.screen_index = self.screen_index.value()
        d.width = self.width.value()
        d.height = self.height.value()
        d.fps = self.fps.value()
        d.fullscreen = self.fullscreen.isChecked()

        s = c.stimulus
        s.stimulus_type = self.stimulus_type.currentText()
        s.speed = self.speed.value()
        s.bar_width = self.bar_width.value()
        s.checker_size = self.checker_size.value()
        s.checker_reversal_rate = self.reversal_rate.value()

        t = c.trial
        t.directions = tuple(
            x.strip()
            for x in self.directions.text().split(",")
            if x.strip()
        )
        t.repetitions = self.repetitions.value()
        t.sweeps_per_direction = self.sweeps_per_direction.value()
        t.iti = self.iti.value()
        t.inter_stimulus_interval = self.isi.value()

        sc = c.screen
        sc.enable_warp = self.enable_warp.isChecked()
        sc.width_cm = self.screen_width_cm.value()
        sc.height_cm = self.screen_height_cm.value()
        sc.distance_cm = self.distance_cm.value()

        p = c.photodiode
        p.enable = self.photodiode_enable.isChecked()
        p.size_px = self.photodiode_size.value()
        p.margin_px = self.photodiode_margin.value()

        l = c.log
        l.enable = self.log_enable.isChecked()
        l.directory = self.log_directory.text()

        return c

    def _refresh_presets(self) -> None:
        self.preset_combo.clear()
        self.preset_combo.addItems(list_presets())

    def _on_load(self) -> None:
        name = self.preset_combo.currentText()
        if not name:
            return

        try:
            self.config = load_preset(name)
            self._load_config_to_widgets()
        except Exception as e:
            QMessageBox.critical(self, "Load error", str(e))

    def _on_save(self) -> None:
        name = self.preset_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Save error", "Preset name is empty")
            return

        try:
            self.config = self._widgets_to_config()
            save_preset(self.config, name, overwrite=True)
            self._refresh_presets()
        except Exception as e:
            QMessageBox.critical(self, "Save error", str(e))

    def _update_preview(self, frame: np.ndarray) -> None:
        if frame.ndim != 2:
            return

        frame = np.ascontiguousarray(frame)

        h, w = frame.shape
        qimg = QImage(
            frame.data,
            w,
            h,
            w,
            QImage.Format_Grayscale8,
        )

        pixmap = QPixmap.fromImage(qimg).scaled(
            self.preview_label.width(),
            self.preview_label.height(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )

        self.preview_label.setPixmap(pixmap)

    def _on_start(self) -> None:
        try:
            config = self._widgets_to_config()
            self.config = config

            self.player.config = config
            self.player.stop_requested = False

            self.player.warp_map = None
            if config.screen.enable_warp:
                from retinomap.warp import WarpMap
                self.player.warp_map = WarpMap(config)

            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)

            self.player.play_experiment()

            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.player.draw_gray()
            self.show()

        except Exception as e:
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            QMessageBox.critical(self, "Run error", str(e))

    def _on_stop(self) -> None:
        if hasattr(self, "player"):
            self.player.request_stop()

            frame = np.full(
                (
                    self.config.stimulus_display.height,
                    self.config.stimulus_display.width,
                ),
                127,
                dtype=np.uint8,
            )
            self._update_preview(frame)

    def _on_experiment_finished(self) -> None:
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

        if hasattr(self, "player"):
            self.player.draw_gray()

    def closeEvent(self, event) -> None:
        if hasattr(self, "player"):
            self.player.close_window()
        super().closeEvent(event)


def main() -> None:
    app = QApplication(sys.argv)
    window = RetinomapGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
