#!/usr/bin/env python3
import sys
import subprocess
import datetime
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QCalendarWidget,
    QSlider, QHBoxLayout, QGridLayout, QFrame
)
from PyQt6.QtCore import Qt, QTimer, QSize, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont

COLOR_ACCENT = "#90EE90"
COLOR_BG_DARK = "#0a131f79"
COLOR_BG_SOLID = "#17212b"
COLOR_PRIMARY_TEXT = "#F0FFF0"
COLOR_INACTIVE = "#36414d"
COLOR_CRITICAL = "#FF6347"
COLOR_ACCENT_HOVER = "#A2FCA2"

class CyberDeck(QWidget):
    def __init__(self):
        super().__init__()
        self.is_wifi_enabled = False
        self.is_volume_muted = False
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(480, 720)
        self.font_mono = QFont(["JetBrains Mono", "Consolas", "Courier New", "monospace"], 11)
        self.font_mono.setStyleHint(QFont.StyleHint.Monospace)
        self.font_stats = QFont(["JetBrains Mono", "Consolas", "Courier New", "monospace"], 10)
        self.font_time = QFont(["OCR A", "OCR A Extended", "monospace"], 34)
        self.font_time.setBold(True)
        self.font_date = QFont(["OCR A", "OCR A Extended", "monospace"], 11)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {COLOR_BG_DARK};
                color: {COLOR_PRIMARY_TEXT};
                border-radius: 4px;
                border: 2px solid {COLOR_INACTIVE};
            }}
            QLabel, QCalendarWidget, QSlider, QPushButton, QFrame {{
                background-color: {COLOR_BG_SOLID};
                color: {COLOR_PRIMARY_TEXT};
                border: none;
            }}
            #clock_label {{
                color: {COLOR_ACCENT};
                padding-top: 8px;
                padding-bottom: 0px;
            }}
            #date_label {{
                color: {COLOR_ACCENT};
                padding-top: 0px;
                padding-bottom: 8px;
            }}
            QCalendarWidget {{
                border: 1px solid {COLOR_INACTIVE};
                border-radius: 6px;
                font-family: "JetBrains Mono";
                font-size: 10pt;
                background-color: {COLOR_BG_SOLID};
            }}
            QCalendarWidget QWidget#qt_calendar_navigationbar {{
                background-color: {COLOR_INACTIVE};
                color: {COLOR_PRIMARY_TEXT};
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }}
            QCalendarWidget QToolButton {{
                background-color: {COLOR_INACTIVE};
                color: {COLOR_PRIMARY_TEXT};
                border: none;
                border-radius: 4px;
                padding: 4px;
            }}
            QCalendarWidget QToolButton:hover {{ background-color: {COLOR_ACCENT}; color: {COLOR_BG_SOLID}; }}
            QCalendarWidget QSpinBox {{ border: 1px solid {COLOR_PRIMARY_TEXT}; color: {COLOR_PRIMARY_TEXT}; background-color: {COLOR_BG_DARK}; }}
            QCalendarWidget QAbstractItemView {{
                background-color: {COLOR_BG_SOLID};
                selection-background-color: {COLOR_ACCENT};
                selection-color: {COLOR_BG_SOLID};
                color: {COLOR_PRIMARY_TEXT};
                outline: 0;
                border: none;
                padding: 2px;
            }}
            QCalendarWidget QAbstractItemView::item {{
                background-color: {COLOR_BG_SOLID};
                color: {COLOR_PRIMARY_TEXT};
                border: 1px solid {COLOR_BG_SOLID};
            }}
            QCalendarWidget QAbstractItemView::item:selected {{
                background-color: {COLOR_ACCENT};
                color: {COLOR_BG_SOLID};
                border-radius: 3px;
                font-weight: bold;
            }}
            QCalendarWidget QAbstractItemView::item:!enabled {{
                color: {COLOR_INACTIVE};
            }}
            QPushButton {{
                background-color: {COLOR_BG_SOLID};
                color: {COLOR_PRIMARY_TEXT};
                border: 1px solid {COLOR_INACTIVE};
                padding: 8px;
                border-radius: 1px;
                font-size: 14px;
                font-family: "JetBrains Mono";
                text-align: center;
                min-height: 45px;
            }}
            QPushButton:hover {{
                background-color: {COLOR_INACTIVE};
            }}
            QPushButton.active {{
                background-color: {COLOR_ACCENT};
                color: {COLOR_BG_SOLID};
                font-weight: bold;
                border: 1px solid {COLOR_ACCENT};
            }}
            QPushButton.critical {{
                background-color: {COLOR_CRITICAL};
                color: {COLOR_BG_SOLID};
                font-weight: bold;
                border: 1px solid {COLOR_CRITICAL};
            }}
            QSlider::groove:horizontal {{
                background: {COLOR_INACTIVE};
                height: 8px;
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: {COLOR_ACCENT};
                width: 16px;
                border-radius: 8px;
                margin: -4px 0;
            }}
            QFrame[frameShape="4"] {{
                border: none;
                background-color: {COLOR_INACTIVE};
                height: 1px;
                margin-top: 5px;
                margin-bottom: 5px;
            }}
        """)
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        time_date_vbox = QVBoxLayout()
        time_date_vbox.setSpacing(0)
        self.time_label = QLabel("-")
        self.time_label.setObjectName("clock_label")
        self.time_label.setFont(self.font_time)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        time_date_vbox.addWidget(self.time_label)
        self.date_label = QLabel("DATE: ----/--/--")
        self.date_label.setObjectName("date_label")
        self.date_label.setFont(self.font_date)
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        time_date_vbox.addWidget(self.date_label)
        layout.addLayout(time_date_vbox)
        layout.addWidget(self._create_separator("CALENDAR"))
        self.calendar = QCalendarWidget()
        self.calendar.setMaximumHeight(190)
        layout.addWidget(self.calendar)
        layout.addWidget(self._create_separator("AUDIO"))
        vol_layout = QHBoxLayout()
        vol_layout.setSpacing(10)
        self.vol_slider = QSlider(Qt.Orientation.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(self.get_volume())
        self.vol_slider.valueChanged.connect(self.set_volume)
        vol_layout.addWidget(self.vol_slider)
        self.vol_mute_btn = self._create_toggle_button("🔊\nAUD", self.toggle_volume, "volume", min_size=QSize(70, 45))
        vol_layout.addWidget(self.vol_mute_btn)
        layout.addLayout(vol_layout)
        layout.addWidget(self._create_separator("BRIGHTNESS"))
        brightness_layout = QHBoxLayout()
        brightness_layout.setSpacing(10)
        self.brightness_slider = QSlider(Qt.Orientation.Horizontal)
        self.brightness_slider.setRange(0, 100)
        self.brightness_slider.setValue(self.get_brightness())
        self.brightness_slider.valueChanged.connect(self.set_brightness)
        brightness_layout.addWidget(self.brightness_slider)
        self.brightness_icon_label = QLabel("🔆\nBTR")
        self.brightness_icon_label.setFont(self.font_mono)
        self.brightness_icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.brightness_icon_label.setFixedSize(QSize(70, 45))
        self.brightness_icon_label.setStyleSheet(f"""
            QLabel {{
                background-color: {COLOR_BG_SOLID};
                color: {COLOR_PRIMARY_TEXT};
                border: 1px solid {COLOR_INACTIVE};
                padding: 8px;
                border-radius: 1px;
                font-size: 14px;
            }}
        """)
        brightness_layout.addWidget(self.brightness_icon_label)
        layout.addLayout(brightness_layout)
        layout.addWidget(self._create_separator("UTILITIES"))
        self.controls_grid = QGridLayout()
        self.controls_grid.setSpacing(10)
        self._setup_control_grid()
        layout.addLayout(self.controls_grid)
        layout.addStretch(1)
        self.setLayout(layout)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.timer_slow = QTimer(self)
        self.timer_slow.timeout.connect(self.update_clock)
        self.timer_slow.start(1000)
        self.update_toggle_states()
        self.render_toggle_states()

    def _create_separator(self, title):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Plain)
        line.setObjectName("separator_line")
        title_label = QLabel(f"  {title}")
        title_label.setFont(self.font_stats)
        hbox = QHBoxLayout()
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.setSpacing(10)
        hbox.addWidget(title_label)
        hbox.addWidget(line, 1)
        widget = QWidget()
        widget.setLayout(hbox)
        widget.setStyleSheet(f"background-color: {COLOR_BG_DARK}; border: none;")
        return widget

    def _create_toggle_button(self, text, handler, obj_name, min_size=QSize(0,0)):
        btn = QPushButton(text)
        btn.setObjectName(obj_name)
        btn.clicked.connect(handler)
        btn.setFont(self.font_mono)
        btn.setMinimumSize(min_size)
        return btn

    def _set_button_state(self, button, is_active, active_icon, inactive_icon, active_label=None, inactive_label=None):
        icon = active_icon if is_active else inactive_icon
        if button.objectName() == "volume":
            label = 'UNMUTED' if not self.is_volume_muted else 'MUTED'
        elif button.objectName() == "wifi":
            label = 'ONLINE' if is_active else 'OFFLINE'
        elif button.objectName() == "file_manager":
            label = 'FILES'
            icon = '📁'
        else:
            label = (active_label if is_active and active_label else
                     inactive_label if not is_active and inactive_label else
                     ('ACTIVE' if is_active else 'INACTIVE'))
        button.setText(f"{icon}\n{label}")
        if button.objectName() == "wifi" or button.objectName() == "volume":
            if is_active:
                button.setProperty("class", "active")
            else:
                button.setProperty("class", "")
        else:
            button.setProperty("class", "")
        button.style().polish(button)

    def _setup_control_grid(self):
        self.wifi_btn = self._create_toggle_button("🌐\nNET", self.toggle_wifi, "wifi")
        self.controls_grid.addWidget(self.wifi_btn, 0, 0)
        self.file_manager_btn = QPushButton("📁\nFILES")
        self.file_manager_btn.setFont(self.font_mono)
        self.file_manager_btn.clicked.connect(self.launch_file_manager)
        self.file_manager_btn.setObjectName("file_manager")
        self.controls_grid.addWidget(self.file_manager_btn, 0, 1)
        self.snapshot_btn = QPushButton("📸\nSCRN")
        self.snapshot_btn.setFont(self.font_mono)
        self.snapshot_btn.clicked.connect(self.take_snapshot)
        self.controls_grid.addWidget(self.snapshot_btn, 0, 2)
        self.settings_btn = QPushButton("⚙️\nSYNAPSE")
        self.settings_btn.setFont(self.font_mono)
        self.settings_btn.clicked.connect(self.launch_settings)
        self.controls_grid.addWidget(self.settings_btn, 1, 0)
        self.reboot_btn = QPushButton("↻\nREBOOT")
        self.reboot_btn.setFont(self.font_mono)
        self.reboot_btn.clicked.connect(self.reboot_system)
        self.reboot_btn.setProperty("class", "critical")
        self.reboot_btn.style().polish(self.reboot_btn)
        self.controls_grid.addWidget(self.reboot_btn, 1, 1)
        self.power_btn = QPushButton("⏻\nTERMINATE")
        self.power_btn.setFont(self.font_mono)
        self.power_btn.clicked.connect(self.shutdown_now)
        self.power_btn.setProperty("class", "critical")
        self.power_btn.style().polish(self.power_btn)
        self.controls_grid.addWidget(self.power_btn, 1, 2)

    def launch_settings(self):
        settings_commands = ["/usr/local/bin/synapse-settings", "gnome-control-center"]
        for cmd in settings_commands:
            try:
                subprocess.Popen([cmd])
                self.close_window()
                return
            except FileNotFoundError:
                continue
        pass

    def launch_file_manager(self):
        fm_commands = ["/usr/local/bin/cypher-vault-dir/cypher-vault","nautilus", "dolphin", "thunar", "pcmanfm"]
        for cmd in fm_commands:
            try:
                subprocess.Popen([cmd])
                self.close_window()
                return
            except FileNotFoundError:
                continue
        pass

    def close_window(self):
        self.hide()

    def take_snapshot(self):
        was_visible = self.isVisible()
        if was_visible:
            self.hide()
        QTimer.singleShot(100, lambda: self._execute_snapshot_sequence(was_visible))

    def _execute_snapshot_sequence(self, was_visible):
        slurp_output = None
        try:
            slurp_result = subprocess.run(["slurp"], capture_output=True, text=True, check=True)
            slurp_output = slurp_result.stdout.strip()
            if not slurp_output:
                raise subprocess.CalledProcessError(1, "slurp", "User cancelled selection.")
        except subprocess.CalledProcessError:
            if was_visible:
                self.show()
            return
        except FileNotFoundError:
            pass
        success = False
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        home_dir = os.path.expanduser("~")
        screenshot_path = os.path.join(home_dir, "Pictures", f"screenshot-{timestamp}.png")
        snapshot_commands = []
        if slurp_output:
            snapshot_commands.append(["grim", "-g", slurp_output, screenshot_path])
        snapshot_commands.append(["spectacle", "-f"])
        for cmd in snapshot_commands:
            try:
                subprocess.run(cmd, check=True)
                success = True
                break
            except (FileNotFoundError, subprocess.CalledProcessError):
                continue
        if success:
            self.close_window()
        elif was_visible:
            self.show()

    def reboot_system(self):
        try:
            subprocess.run(["trinity","reboot"], check=True)
        except:
            pass

    def shutdown_now(self):
        try:
            subprocess.run(["trinity","shutdown"], check=True)
        except:
            pass

    def update_clock(self):
        now = datetime.datetime.now()
        self.time_label.setText(now.strftime("%H:%M:%S"))
        self.date_label.setText(now.strftime("%Y-%m-%d"))

    def update_toggle_states(self):
        try:
            status = subprocess.run(["nmcli", "radio", "wifi"], capture_output=True, text=True).stdout.strip().lower()
            self.is_wifi_enabled = "enabled" in status
        except:
            self.is_wifi_enabled = False
        try:
            out = subprocess.run(["pactl", "get-sink-mute", "@DEFAULT_SINK@"], capture_output=True, text=True).stdout
            self.is_volume_muted = "yes" in out
        except:
            self.is_volume_muted = False

    def render_toggle_states(self):
        self._set_button_state(self.wifi_btn, self.is_wifi_enabled, "🌐", "🚫")
        self._set_button_state(self.vol_mute_btn, not self.is_volume_muted, "🔊", "🔇")
        self._set_button_state(self.file_manager_btn, False, "📁", "📁", active_label="FILES", inactive_label="FILES")

    def toggle_wifi(self):
        try:
            action = "off" if self.is_wifi_enabled else "on"
            subprocess.run(["nmcli", "radio", "wifi", action], check=True)
            self.is_wifi_enabled = not self.is_wifi_enabled
            self.render_toggle_states()
        except subprocess.CalledProcessError:
            pass
        except FileNotFoundError:
            pass

    def toggle_volume(self):
        try:
            subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle"], check=True)
            self.is_volume_muted = not self.is_volume_muted
            self.render_toggle_states()
            self.vol_slider.setValue(self.get_volume())
        except subprocess.CalledProcessError:
            pass
        except FileNotFoundError:
            pass

    def get_volume(self):
        try:
            out = subprocess.run(["pactl", "get-sink-volume", "@DEFAULT_SINK@"],
                                 capture_output=True, text=True, check=True).stdout
            for line in out.splitlines():
                if "Volume:" in line:
                    pct_str = line.split("/")[1].strip().split(" ")[0].replace("%", "")
                    return int(pct_str)
        except:
            return 50

    def set_volume(self, val):
        try:
            subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{val}%"], check=True)
            if val > 0 and self.is_volume_muted:
                subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "0"], check=True)
                self.is_volume_muted = False
                self.render_toggle_states()
        except:
            pass

    def get_brightness(self):
        try:
            current = subprocess.run(["brightnessctl", "g"], capture_output=True, text=True, check=True).stdout.strip()
            maximum = subprocess.run(["brightnessctl", "m"], capture_output=True, text=True, check=True).stdout.strip()
            current_val = int(current)
            max_val = int(maximum)
            if max_val == 0:
                return 50
            return round((current_val / max_val) * 100)
        except:
            return 50

    def set_brightness(self, val):
        try:
            subprocess.run(["brightnessctl", "s", f"{val}%"], check=True)
        except:
            pass

    def toggle_visibility(self):
        if self.isVisible():
            self.animation = QPropertyAnimation(self, b"windowOpacity")
            self.animation.setDuration(200)
            self.animation.setStartValue(1.0)
            self.animation.setEndValue(0.0)
            self.animation.setEasingCurve(QEasingCurve.Type.OutQuad)
            self.animation.finished.connect(self.hide)
            self.animation.start()
        else:
            self.setWindowOpacity(0.0)
            screen = QApplication.primaryScreen().availableGeometry()
            self.move(screen.width() - self.width() - 30, screen.height() - self.height() - 50)
            self.show()
            self.activateWindow()
            self.animation = QPropertyAnimation(self, b"windowOpacity")
            self.animation.setDuration(200)
            self.animation.setStartValue(0.0)
            self.animation.setEndValue(1.0)
            self.animation.setEasingCurve(QEasingCurve.Type.OutQuad)
            self.animation.start()

    def focusOutEvent(self, event):
        QTimer.singleShot(50, self.check_and_hide)

    def check_and_hide(self):
        if not self.isActiveWindow():
            self.hide()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    try:
        QFont.insertSubstitute("OCR A", "monospace")
    except:
        pass
    deck = CyberDeck()
    deck.setFixedSize(400,700)
    deck.show()
    sys.exit(app.exec())
