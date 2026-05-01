from __future__ import annotations

import sys
from copy import deepcopy
from pathlib import Path
from tempfile import gettempdir

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox,
                               QDoubleSpinBox, QFormLayout, QGroupBox,
                               QHBoxLayout, QLabel, QLineEdit, QMessageBox,
                               QPushButton, QSpinBox, QVBoxLayout, QWidget)

from retinomap.config import ExperimentConfig
from retinomap.player import StimulusPlayer
from retinomap.preset import list_presets, load_preset, save_preset


class RetinomapGUI(QWidget):
    """刺激のパラメータやメタ情報の編集、及び刺激の開始と終了を担うGUI"""
    def __init__(self) -> None:
        super().__init__()

        self.config = ExperimentConfig()

        self.setWindowTitle("retinomap")
        self.resize(1200, 650)

        self._build_ui()
        self._load_config_to_widgets()
        self._refresh_presets()
        self.player = StimulusPlayer(self.config)
        self.player.ensure_window()
        self.player.set_preview_callback(self._update_preview, fps=10.0)

    def _build_ui(self) -> None:
        root = QHBoxLayout()

        left_col = QVBoxLayout()
        center_col = QVBoxLayout()
        right_col = QVBoxLayout()

        # =====================
        # left: preview + control
        # =====================
        self.preview_label = QLabel()
        self.preview_label.setFixedSize(400, 290)
        self.preview_label.setStyleSheet("background-color: #777;")
        self.preview_label.setAlignment(Qt.AlignCenter)

        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")
        self.stop_button.setEnabled(False)

        control_buttons = QHBoxLayout()
        control_buttons.addWidget(self.start_button)
        control_buttons.addWidget(self.stop_button)

        # --- test stimulus ---
        self.test_type = QComboBox()
        self.test_type.addItems(["full_field_flash", "checkerboard_reversal"])

        self.test_duration = QDoubleSpinBox()
        self.test_duration.setRange(1, 600)
        self.test_duration.setDecimals(1)
        self.test_duration.setValue(20.0)

        self.test_button = QPushButton("Start test")

        test_form = QFormLayout()
        test_form.addRow("Test stimulus", self.test_type)
        test_form.addRow("Duration sec", self.test_duration)

        test_box = QGroupBox("Test")
        test_box.setLayout(test_form)

        # left_col.addWidget(self.preview_label)
        left_col.addWidget(self.preview_label, alignment=Qt.AlignHCenter)
        left_col.addLayout(control_buttons)
        left_col.addWidget(test_box)
        left_col.addWidget(self.test_button)
        left_col.addStretch()

        # =====================
        # center: experiment / preset / display / screen
        # =====================
        experiment_form = QFormLayout()

        self.experiment_id_edit = QLineEdit()
        self.experiment_id_edit.setPlaceholderText("e.g. mouse001")

        self.preset_combo = QComboBox()
        self.preset_name = QLineEdit()

        experiment_form.addRow("Experiment ID", self.experiment_id_edit)
        experiment_form.addRow("Preset", self.preset_combo)
        experiment_form.addRow("Preset name", self.preset_name)

        experiment_box = QGroupBox("Experiment")
        experiment_box.setLayout(experiment_form)

        display_form = QFormLayout()

        self.screen_index = QSpinBox()
        self.screen_index.setRange(0, 8)

        self.width = QSpinBox()
        self.width.setRange(100, 10000)

        self.height = QSpinBox()
        self.height.setRange(100, 10000)

        self.window_x = QSpinBox()
        self.window_x.setRange(-10000, 10000)

        self.window_y = QSpinBox()
        self.window_y.setRange(-10000, 10000)

        self.fps = QDoubleSpinBox()
        self.fps.setRange(1, 240)
        self.fps.setDecimals(1)

        self.fullscreen = QCheckBox()

        display_form.addRow("Stimulus screen index", self.screen_index)
        display_form.addRow("Width", self.width)
        display_form.addRow("Height", self.height)
        display_form.addRow("Window X", self.window_x)
        display_form.addRow("Window Y", self.window_y)
        display_form.addRow("FPS", self.fps)
        display_form.addRow("Fullscreen", self.fullscreen)

        display_box = QGroupBox("Display")
        display_box.setLayout(display_form)

        screen_form = QFormLayout()

        self.enable_warp = QCheckBox()

        self.screen_width_cm = QDoubleSpinBox()
        self.screen_width_cm.setRange(1, 1000)

        self.screen_height_cm = QDoubleSpinBox()
        self.screen_height_cm.setRange(1, 1000)

        self.distance_cm = QDoubleSpinBox()
        self.distance_cm.setRange(1, 1000)

        screen_form.addRow("Enable warp", self.enable_warp)
        screen_form.addRow("Screen width cm", self.screen_width_cm)
        screen_form.addRow("Screen height cm", self.screen_height_cm)
        screen_form.addRow("Distance cm", self.distance_cm)

        screen_box = QGroupBox("Screen")
        screen_box.setLayout(screen_form)

        log_form = QFormLayout()

        self.log_enable = QCheckBox()
        self.log_directory = QLineEdit()

        log_form.addRow("Enable log", self.log_enable)
        log_form.addRow("Log directory", self.log_directory)

        log_box = QGroupBox("Log")
        log_box.setLayout(log_form)

        center_col.addWidget(experiment_box)
        center_col.addWidget(log_box)
        center_col.addWidget(display_box)
        center_col.addWidget(screen_box)
        center_col.addStretch()

        # =====================
        # right: stimulus / trial / photodiode / log + preset buttons
        # =====================
        stimulus_form = QFormLayout()

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

        stimulus_form.addRow("Stimulus type", self.stimulus_type)
        stimulus_form.addRow("Speed px/s", self.speed)
        stimulus_form.addRow("Bar width px", self.bar_width)
        stimulus_form.addRow("Checker size px", self.checker_size)
        stimulus_form.addRow("Reversal rate Hz", self.reversal_rate)

        stimulus_box = QGroupBox("Stimulus")
        stimulus_box.setLayout(stimulus_form)

        trial_form = QFormLayout()

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

        trial_form.addRow("Directions", self.directions)
        trial_form.addRow("Repetitions", self.repetitions)
        trial_form.addRow("Sweeps / direction", self.sweeps_per_direction)
        trial_form.addRow("ITI sec", self.iti)
        trial_form.addRow("ISI sec", self.isi)

        trial_box = QGroupBox("Trial")
        trial_box.setLayout(trial_form)

        photodiode_form = QFormLayout()

        self.photodiode_enable = QCheckBox()

        self.photodiode_size = QSpinBox()
        self.photodiode_size.setRange(1, 1000)

        self.photodiode_margin = QSpinBox()
        self.photodiode_margin.setRange(0, 1000)

        photodiode_form.addRow("Photodiode", self.photodiode_enable)
        photodiode_form.addRow("Photodiode size px", self.photodiode_size)
        photodiode_form.addRow("Photodiode margin px", self.photodiode_margin)

        photodiode_box = QGroupBox("Photodiode")
        photodiode_box.setLayout(photodiode_form)

        self.load_button = QPushButton("Load")
        self.save_button = QPushButton("Save as")

        preset_buttons = QHBoxLayout()
        preset_buttons.addWidget(self.load_button)
        preset_buttons.addWidget(self.save_button)

        right_col.addWidget(stimulus_box)
        right_col.addWidget(trial_box)
        right_col.addWidget(photodiode_box)
        right_col.addLayout(preset_buttons)

        root.addLayout(left_col, 2)
        root.addLayout(center_col, 2)
        root.addLayout(right_col, 2)

        self.setLayout(root)

        self.load_button.clicked.connect(self._on_load)
        self.save_button.clicked.connect(self._on_save)
        self.start_button.clicked.connect(self._on_start)
        self.stop_button.clicked.connect(self._on_stop)
        self.test_button.clicked.connect(self._on_test)
        self.fullscreen.toggled.connect(self._on_fullscreen_toggled)

    def _load_config_to_widgets(self) -> None:
        c = self.config

        d = c.stimulus_display
        self.screen_index.setValue(d.screen_index)
        self.width.setValue(d.width)
        self.height.setValue(d.height)
        self.window_x.setValue(d.window_x)
        self.window_y.setValue(d.window_y)
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
        d.window_x = self.window_x.value()
        d.window_y = self.window_y.value()
        d.fps = self.fps.value()
        d.fullscreen = self.fullscreen.isChecked()
        if not d.fullscreen:
            d.width = self.width.value()
            d.height = self.height.value()

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
            self.player.ensure_window()
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

    def _on_test(self) -> None:
        try:
            self.player.config = self._widgets_to_config()
            self.player.ensure_window()
            self.player.stop_requested = False

            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)

            self.player.play_test_stimulus(
                test_type=self.test_type.currentText(),
                duration=self.test_duration.value(),
            )

            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.player.draw_gray()
        except Exception as e:
            QMessageBox.critical(self, "Test error", str(e))

    def _on_experiment_finished(self) -> None:
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

        if hasattr(self, "player"):
            self.player.draw_gray()

    def _on_fullscreen_toggled(self, checked: bool) -> None:
        self.width.setEnabled(not checked)
        self.height.setEnabled(not checked)

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
