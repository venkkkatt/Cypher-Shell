#!/usr/bin/env python3
import sys, os, platform, datetime, json, subprocess, glob, socket, time, cpuinfo
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QListWidget, QListWidgetItem, QStackedWidget,
    QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame, QPushButton, QSlider,
    QColorDialog, QMessageBox, QGridLayout, QCheckBox, QSpinBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QTextEdit, QLineEdit
)
from PyQt5.QtCore import Qt, QTimer, QRect, QPropertyAnimation, QEasingCurve, QCoreApplication
from PyQt5.QtGui import QFont, QColor, QFontDatabase
import psutil

APP_NAME = "synapse"
CONFIG_DIR = Path.home() / ".config" / APP_NAME
CONFIG_FILE = CONFIG_DIR / "config.json"
DEFAULT_CONFIG = {
    "theme": "dark",
    "accent": "#00FFFF",
    "general_accent": "#005555",
    "last_brightness": 60,
    "last_volume": 80,
    "ui_opacity": 95,
    "general_font": "JetBrains Mono",
    "display_font": "VT323",
}

FONT_GENERAL = "JetBrains Mono"
FONT_DISPLAY = "VT323"

def get_available_fonts():
    try:
        return QFontDatabase().families()
    except Exception:
        return ["Monospace", "Arial", "Courier New"]

def save_config(config):
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving config to {CONFIG_FILE}: {e}", file=sys.stderr)
        return False

def load_config():
    cfg = DEFAULT_CONFIG.copy()
    
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"Error creating config directory {CONFIG_DIR}: {e}", file=sys.stderr)
        return cfg 

    if CONFIG_FILE.is_file():
        try:
            with open(CONFIG_FILE, 'r') as f:
                loaded_config = json.load(f)
                for key in loaded_config:
                    if key in cfg:
                        cfg[key] = loaded_config[key]
        except json.JSONDecodeError as e:
            print(f"Warning: Config file {CONFIG_FILE} is corrupted. Resetting to default. Error: {e}", file=sys.stderr)
            save_config(cfg)
        except Exception as e:
            print(f"Error loading config file {CONFIG_FILE}: {e}", file=sys.stderr)
            save_config(cfg)
    else:
        print(f"Config file not found at {CONFIG_FILE}. Creating default.", file=sys.stderr)
        save_config(cfg)
            
    return cfg

def get_brightness_brightnessctl():
    try:
        output = subprocess.check_output(["brightnessctl", "g"]).decode().strip()
        current = int(output)
        output = subprocess.check_output(["brightnessctl", "m"]).decode().strip()
        max_b = int(output)
        if max_b > 0:
            return int(round(current * 100 / max_b))
        return 0
    except Exception:
        return None

def set_brightness_brightnessctl(percent):
    try:
        subprocess.check_call(["brightnessctl", "set", f"{percent}%"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True, None
    except Exception as e:
        return False, f"brightnessctl failed: {str(e)}"

def apply_brightness(percent):
    ok, msg = set_brightness_brightnessctl(percent)
    if ok:
        return True, None
    return False, msg

def get_volume():
    try:
        result = subprocess.run(['pactl', 'get-sink-volume', '@DEFAULT_SINK@'],
                                capture_output=True, text=True, check=True, timeout=1)
        line = result.stdout.strip().split('\n')[-1]
        percent_str = line.split('/')[-2].strip().replace('%', '')
        return int(percent_str)
    except Exception:
        return load_config().get("last_volume", DEFAULT_CONFIG["last_volume"])

def set_volume(percent):
    try:
        subprocess.run(['pactl', 'set-sink-volume', '@DEFAULT_SINK@', f'{percent}%'],
                       capture_output=True, text=True, check=True, timeout=1)
        return True, None
    except Exception as e:
        return False, f"Failed to set volume: {str(e)}"

def hostname_ip():
    try:
        hn = socket.gethostname()
        ip = socket.gethostbyname(hn)
        return hn, ip
    except Exception:
        return "NETWORK_UNAVAILABLE", "0.0.0.0"

def disk_usage(path="/"):
    try:
        return psutil.disk_usage(path)
    except Exception:
        class FakeDisk:
            total, used, free, percent = 0, 0, 0, 0
        return FakeDisk()

def memory_usage():
    try:
        return psutil.virtual_memory()
    except Exception:
        class FakeMemory:
            total, available, used, percent = 0, 0, 0, 0
        return FakeMemory()

def cpu_usage():
    try:
        percents = psutil.cpu_percent(interval=None, percpu=True)
        try:
            load_avg = psutil.getloadavg()
        except NotImplementedError:
            load_avg = (0, 0, 0)
        return percents, load_avg
    except Exception:
        return [0], (0, 0, 0)

def format_bytes(bytes):
    if bytes >= 1024**3:
        return f"{bytes / (1024**3):.2f} GB"
    elif bytes >= 1024**2:
        return f"{bytes / (1024**2):.2f} MB"
    elif bytes >= 1024:
        return f"{bytes / 1024:.2f} KB"
    return f"{bytes} B"

class StatLabel(QLabel):
    def __init__(self, label, value):
        super().__init__()
        self.setWordWrap(True)
        self.label_text = label
        self.set_value(value)

    def set_value(self, value):
        html = f"<span class='stat-label'>{self.label_text.upper()}:</span> <span class='stat-value'>{value}</span>"
        self.setText(html)

class Card(QFrame):
    def __init__(self, title, subtitle=""):
        super().__init__()
        self.setObjectName("Card")
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(15, 10, 15, 0)
        header_layout.setSpacing(10)

        t = QLabel(title.upper())
        t.setObjectName("CardTitle")
        header_layout.addWidget(t, alignment=Qt.AlignLeft)

        if subtitle:
            s = QLabel(subtitle)
            s.setObjectName("CardSubtitle")
            header_layout.addWidget(s, alignment=Qt.AlignRight)

        self.body = QVBoxLayout()
        self.body.setSpacing(8)
        self.body.setContentsMargins(15, 10, 15, 15)

        v_layout = QVBoxLayout(self)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.addLayout(header_layout)
        v_layout.addWidget(self.create_separator())
        v_layout.addLayout(self.body)

    def create_separator(self):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setObjectName("CardSeparator")
        line.setFixedHeight(2)
        return line

class ProgressBar(QWidget):
    def __init__(self, color_hex, max_val=100):
        super().__init__()
        self.max_val = max_val
        self._value = 0
        self.color_hex = color_hex
        self.setFixedHeight(16)
        self.setObjectName("ProgressBarContainer")

    def set_value(self, value):
        self._value = max(0, min(self.max_val, value))
        self.update()

    def paintEvent(self, event):
        from PyQt5.QtGui import QPainter, QBrush
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        accent_color = QColor(self.color_hex)
        p.setBrush(QBrush(accent_color.darker(200)))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(rect, 4, 4)
        width = int(rect.width() * self._value / self.max_val)
        p.setBrush(QBrush(accent_color))
        p.drawRoundedRect(0, 0, width, rect.height(), 4, 4)
        p.end()

class SystemPage(QWidget):
    def __init__(self):
        super().__init__()
        self.update_counter = 0
        v = QVBoxLayout(self)
        about = Card("SYSTEM CORE", "OS and processor details")
        sys_grid = QGridLayout()
        sys_grid.setContentsMargins(0, 0, 0, 0)
        processor_name = cpuinfo.get_cpu_info().get('brand_raw', 'N/A')
        sys_grid.addWidget(StatLabel("OS/Distro", f"{platform.node()} {platform.release()}"), 0, 0)
        sys_grid.addWidget(StatLabel("Kernel", platform.version()), 0, 1)
        sys_grid.addWidget(StatLabel("Processor", processor_name), 1, 0)
        self.uptime_lbl = StatLabel("Uptime", self.get_uptime())
        sys_grid.addWidget(self.uptime_lbl, 1, 1)
        about.body.addLayout(sys_grid)
        v.addWidget(about)
        perf_card = Card("PERFORMANCE MONITOR", "CPU, Memory, and Disk utilization")
        perf_card.body.addWidget(QLabel("CPU LOAD [CURRENT AVG / LOAD AVG]:"))
        self.cpu_load_lbl = StatLabel("CPU LOAD", "0% / 0.00")
        perf_card.body.addWidget(self.cpu_load_lbl)
        self.cpu_bar = ProgressBar("#FF66CC")
        perf_card.body.addWidget(self.cpu_bar)
        perf_card.body.addWidget(QLabel("MEMORY USAGE [USED / TOTAL]:"))
        self.mem_lbl = StatLabel("RAM", "0 GB / 0 GB (0%)")
        perf_card.body.addWidget(self.mem_lbl)
        self.mem_bar = ProgressBar("#00FFFF")
        perf_card.body.addWidget(self.mem_bar)
        perf_card.body.addWidget(QLabel("DISK USAGE (ROOT /)"))
        self.disk_lbl = StatLabel("STORAGE", "0 GB / 0 GB (0%)")
        perf_card.body.addWidget(self.disk_lbl)
        self.disk_bar = ProgressBar("#FFD700")
        perf_card.body.addWidget(self.disk_bar)
        v.addWidget(perf_card)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_info)
        self.timer.start(1000)
        self.update_info()
        v.addStretch()

    def get_uptime(self):
        try:
            uptime_sec = int(datetime.datetime.now().timestamp() - psutil.boot_time())
            minutes, seconds = divmod(uptime_sec, 60)
            hours, minutes = divmod(minutes, 60)
            days, hours = divmod(hours, 24)
            return f"{days}d {hours:02d}h {minutes:02d}m"
        except Exception:
            return "N/A"

    def update_info(self):
        self.update_counter += 1
        cpu_percents, load_avg = cpu_usage()
        avg_cpu = sum(cpu_percents) / len(cpu_percents) if cpu_percents else 0
        load_str = f"{load_avg[0]:.2f}, {load_avg[1]:.2f}, {load_avg[2]:.2f}"
        self.cpu_load_lbl.set_value(f"{avg_cpu:.1f}% / {load_str}")
        self.cpu_bar.set_value(int(avg_cpu))
        mem = memory_usage()
        mem_str = f"{format_bytes(mem.used)} / {format_bytes(mem.total)} ({mem.percent}%)"
        self.mem_lbl.set_value(mem_str)
        self.mem_bar.set_value(mem.percent)
        disk = disk_usage("/")
        disk_str = f"{format_bytes(disk.used)} / {format_bytes(disk.total)} ({disk.percent}%)"
        self.disk_lbl.set_value(disk_str)
        self.disk_bar.set_value(disk.percent)
        if self.update_counter % 5 == 0:
            self.uptime_lbl.set_value(self.get_uptime())


class PersonalizationPage(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        cfg = self.parent.cfg
        v = QVBoxLayout(self)
        theme = Card("VISUAL PROTOCOL", "Adjust theme, accent hue, and UI opacity")
        btn = QPushButton(":: TOGGLE DARK / LIGHT THEME ::")
        btn.clicked.connect(self.toggle_theme)
        theme.body.addWidget(btn)
        
        color_btn = QPushButton(":: SELECT PRIMARY ACCENT HUE (High Contrast) ::")
        color_btn.clicked.connect(self.pick_color)
        theme.body.addWidget(color_btn)
        
        general_accent_btn = QPushButton(":: SELECT GENERAL ACCENT HUE (Subdued) ::")
        general_accent_btn.clicked.connect(self.pick_general_accent)
        theme.body.addWidget(general_accent_btn)
        
        opacity_card = QWidget()
        opacity_layout = QHBoxLayout(opacity_card)
        opacity_layout.setContentsMargins(0, 0, 0, 0)
        opacity_layout.setSpacing(10)
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setObjectName("GeneralSlider")
        self.opacity_slider.setRange(10, 100)
        self.opacity_slider.setFixedWidth(200)
        self.opacity_slider.setValue(cfg.get("ui_opacity", DEFAULT_CONFIG['ui_opacity']))
        self.opacity_lbl = StatLabel("UI OPACITY", f"{self.opacity_slider.value()}%")
        self.opacity_slider.valueChanged.connect(lambda val: self.opacity_lbl.set_value(f"{val}%"))
        self.opacity_slider.sliderReleased.connect(self.set_opacity)
        opacity_layout.addWidget(self.opacity_lbl)
        opacity_layout.addWidget(self.opacity_slider, alignment=Qt.AlignRight)
        theme.body.addWidget(opacity_card)
        v.addWidget(theme)
        
        font_card = Card("TYPOGRAPHY MATRIX", "Select system and display fonts")
        available_fonts = get_available_fonts()
        general_font_layout = QHBoxLayout()
        general_font_combo = QComboBox()
        general_font_combo.addItems(available_fonts)
        general_font_combo.setCurrentText(cfg.get("general_font", DEFAULT_CONFIG["general_font"]))
        general_font_combo.currentTextChanged.connect(self.set_general_font)
        general_font_layout.addWidget(StatLabel("GENERAL FONT", ""))
        general_font_layout.addWidget(general_font_combo)
        font_card.body.addLayout(general_font_layout)
        display_font_layout = QHBoxLayout()
        display_font_combo = QComboBox()
        display_font_combo.addItems(available_fonts)
        display_font_combo.setCurrentText(cfg.get("display_font", DEFAULT_CONFIG["display_font"]))
        display_font_combo.currentTextChanged.connect(self.set_display_font)
        display_font_layout.addWidget(StatLabel("DISPLAY FONT", ""))
        display_font_layout.addWidget(display_font_combo)
        font_card.body.addLayout(display_font_layout)
        v.addWidget(font_card)
        
        bright = Card("DISPLAY LUMINANCE", "Adjust screen brightness level")
        def get_current_brightness_percent():
            percent = get_brightness_brightnessctl()
            if percent is not None:
                return percent
            return cfg.get("last_brightness", DEFAULT_CONFIG['last_brightness'])
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setObjectName("BrightnessSlider")
        self.slider.setRange(0, 100)
        self.slider.setValue(get_current_brightness_percent())
        self.bright_lbl = StatLabel("CURRENT LEVEL", f"{self.slider.value()}%")
        self.slider.valueChanged.connect(lambda val: self.bright_lbl.set_value(f"{val}%"))
        self.slider.sliderReleased.connect(self.set_brightness)
        bright.body.addWidget(self.bright_lbl)
        bright.body.addWidget(self.slider)
        v.addWidget(bright)
        v.addStretch()

    def toggle_theme(self):
        cfg = self.parent.cfg
        cfg["theme"] = "light" if cfg.get("theme", "dark") == "dark" else "dark"
        save_config(cfg)
        self.parent.apply_styles()

    def pick_color(self):
        col = QColorDialog.getColor(QColor(self.parent.cfg.get("accent", DEFAULT_CONFIG['accent'])), self, "Select Primary Accent Hue")
        if col.isValid():
            self.parent.cfg["accent"] = col.name()
            save_config(self.parent.cfg)
            self.parent.apply_styles()

    def pick_general_accent(self):
        cfg = self.parent.cfg
        current_color = cfg.get("general_accent", DEFAULT_CONFIG['general_accent'])
        col = QColorDialog.getColor(QColor(current_color), self, "Select General/Subdued Accent Hue")
        if col.isValid():
            cfg["general_accent"] = col.name()
            save_config(cfg)
            self.parent.apply_styles()

    def set_opacity(self):
        val = self.opacity_slider.value()
        self.parent.cfg["ui_opacity"] = val
        save_config(self.parent.cfg)
        self.parent.apply_styles()

    def set_general_font(self, font_name):
        self.parent.cfg["general_font"] = font_name
        save_config(self.parent.cfg)
        self.parent.apply_styles()

    def set_display_font(self, font_name):
        self.parent.cfg["display_font"] = font_name
        save_config(self.parent.cfg)
        self.parent.apply_styles()

    def set_brightness(self):
        val = self.slider.value()
        ok, msg = apply_brightness(val)
        if ok:
            cfg = load_config()
            cfg["last_brightness"] = val
            save_config(cfg)
        else:
            QMessageBox.critical(self, "Luminance Control Failure",
                                f"Failed to set brightness to {val}%\n\nReason: {msg}")
            self.slider.setValue(load_config().get("last_brightness", DEFAULT_CONFIG['last_brightness']))

class AudioPage(QWidget):
    def __init__(self):
        super().__init__()
        v = QVBoxLayout(self)
        card = Card("AUDIO MATRIX", "Master volume and device settings")
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setObjectName("VolumeSlider")
        self.slider.setRange(0, 100)
        initial_volume = get_volume()
        self.slider.setValue(initial_volume)
        self.vol_lbl = StatLabel("MASTER VOLUME", f"{initial_volume}%")
        self.slider.valueChanged.connect(lambda val: self.vol_lbl.set_value(f"{val}%"))
        self.slider.sliderReleased.connect(self.set_volume_handler)
        card.body.addWidget(self.vol_lbl)
        card.body.addWidget(self.slider)
        v.addWidget(card)
        v.addStretch()

    def set_volume_handler(self):
        val = self.slider.value()
        ok, msg = set_volume(val)
        if ok:
            cfg = load_config()
            cfg["last_volume"] = val
            save_config(cfg)
        else:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Audio System Error")
            msg_box.setText("Could not set volume.")
            msg_box.setDetailedText(f"Reason: {msg}")
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.exec_()
class ChronoPage(QWidget):
    def __init__(self):
        super().__init__()
        v = QVBoxLayout(self)
        
        card = Card("CHRONOS LOG", "Current System Time (Read-Only)")
        self.time_lbl = QLabel()
        self.time_lbl.setObjectName("TimeDisplayLarge")
        self.date_lbl = QLabel()
        self.date_lbl.setObjectName("DateDisplay")
        card.body.addWidget(self.time_lbl)
        card.body.addWidget(self.date_lbl)
        
        ntp_card = Card("SYNCHRONIZATION STATUS", "NTP details")
        self.ntp_lbl = StatLabel("NTP STATUS", "Searching for time stream...")
        ntp_card.body.addWidget(self.ntp_lbl)
        
        v.addWidget(card)
        v.addWidget(ntp_card)
        
        scheduler_card = Card("TASK SCHEDULER", "Execute a command after a time delay")
        command_layout = QHBoxLayout()
        command_layout.addWidget(StatLabel("COMMAND", ""))
        self.command_input = QLineEdit("notify-send 'Scheduled Task Complete!'")
        self.command_input.setObjectName("CommandInput")
        command_layout.addWidget(self.command_input)
        scheduler_card.body.addLayout(command_layout)

        delay_layout = QHBoxLayout()
        self.delay_spinbox = QSpinBox()
        self.delay_spinbox.setRange(1, 3600)
        self.delay_spinbox.setValue(10)
        self.delay_spinbox.setSuffix(" seconds")
        delay_layout.addWidget(StatLabel("DELAY", ""))
        delay_layout.addWidget(self.delay_spinbox)
        scheduler_card.body.addLayout(delay_layout)
        
        self.schedule_btn = QPushButton(":: SCHEDULE COMMAND ::")
        self.schedule_btn.clicked.connect(self.schedule_task)
        scheduler_card.body.addWidget(self.schedule_btn)

        self.scheduler_status_lbl = StatLabel("LAST TASK", "No tasks scheduled.")
        scheduler_card.body.addWidget(self.scheduler_status_lbl)
        
        v.addWidget(scheduler_card)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time_display)
        self.timer.start(100)
        self.update_time_display()

        self.ntp_timer = QTimer(self)
        self.ntp_timer.timeout.connect(self.update_ntp_status)
        self.ntp_timer.start(5000)
        self.update_ntp_status()
        
        v.addStretch()

    def update_time_display(self):
        now = datetime.datetime.now()
        self.time_lbl.setText(now.strftime("%H:%M:%S"))
        self.date_lbl.setText(now.strftime("%A, %d %B %Y"))
    
    def update_ntp_status(self):
        try:
            result = subprocess.run(['timedatectl', 'show'], capture_output=True, text=True, check=True, timeout=2)
            lines = result.stdout.splitlines()
            ntp_enabled = next((line.split('=')[1] for line in lines if line.startswith('NTP=')), 'n/a')
            ntp_synced = next((line.split('=')[1] for line in lines if line.startswith('NTPSynchronized=')), 'n/a')

            if ntp_enabled == 'yes' and ntp_synced == 'yes':
                status = "SYNCHRONIZED (NTP Enabled)"
            elif ntp_enabled == 'yes':
                status = "ATTEMPTING SYNC..."
            else:
                status = "NTP DISABLED"
            
            self.ntp_lbl.set_value(status)
        except Exception:
            self.ntp_lbl.set_value("timedatectl error (Command not found or failed)")

    def execute_task(self, command):
        try:
            subprocess.Popen(command, shell=True, start_new_session=True)
            self.scheduler_status_lbl.set_value(f"EXECUTED: '{command}'")
        except Exception as e:
            self.scheduler_status_lbl.set_value(f"EXECUTION FAILED: {str(e)}")

    def schedule_task(self):
        command = self.command_input.text()
        delay_sec = self.delay_spinbox.value()
        if not command.strip():
            self.scheduler_status_lbl.set_value("ERROR: Command cannot be empty.")
            return
        QTimer.singleShot(delay_sec * 1000, lambda: self.execute_task(command))
        self.scheduler_status_lbl.set_value(f"SCHEDULED: '{command}' in {delay_sec} seconds")


class HyprlandPage(QWidget):
    def __init__(self):
        super().__init__()
        self.active_clients = []
        self.active_workspaces = []
        v = QVBoxLayout(self)

        self.error_lbl = StatLabel("HYPRLAND STATUS", "Initializing...")
        v.addWidget(self.error_lbl)
        
        win_card = Card("ACTIVE WINDOWS", "View and manage running Hyprland clients")
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["WS", "Address", "Class", "Title"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setObjectName("ProcessTable")

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        win_card.body.addWidget(self.table)

        win_action_layout = QHBoxLayout()
        self.btn_focus = QPushButton(":: FOCUS SELECTED WINDOW ::")
        self.btn_focus.clicked.connect(self.focus_selected_window)
        win_action_layout.addWidget(self.btn_focus)
        win_card.body.addLayout(win_action_layout)
        v.addWidget(win_card)

        ws_card = Card("WORKSPACE RELOCATION", "Move active window to workspace")
        move_layout = QHBoxLayout()
        self.ws_combo = QComboBox()
        self.ws_combo.setObjectName("WorkspaceComboBox")
        move_layout.addWidget(self.ws_combo)
        self.btn_move = QPushButton(":: MOVE ACTIVE TO WS ::")
        self.btn_move.clicked.connect(self.move_active_to_workspace)
        move_layout.addWidget(self.btn_move)
        ws_card.body.addLayout(move_layout)
        v.addWidget(ws_card)
        v.addStretch()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_hyprland_info)
        self.timer.start(2000)
        self.update_hyprland_info()

    def run_hyprctl(self, command):
        try:
            return subprocess.check_output(["hyprctl"] + command, stderr=subprocess.DEVNULL).decode().strip()
        except FileNotFoundError:
            return "ERROR: hyprctl not found. Is Hyprland installed and running?"
        except subprocess.CalledProcessError:
            return "ERROR: hyprctl command failed. Is 'hyprctl' in your PATH?"
        except Exception as e:
            return f"ERROR: {str(e)}"

    def get_hyprland_data(self):
        data_str = self.run_hyprctl(["clients", "-j"])
        if data_str.startswith("ERROR"):
            return None, None, data_str
        ws_str = self.run_hyprctl(["workspaces", "-j"])
        if ws_str.startswith("ERROR"):
            return None, None, ws_str
        try:
            clients = json.loads(data_str)
            workspaces = json.loads(ws_str)
            clients = sorted(clients, key=lambda c: c.get('workspace', {}).get('id', 999))
            return clients, workspaces, "OK"
        except json.JSONDecodeError:
            return None, None, "ERROR: Failed to parse hyprctl JSON output."
        except Exception as e:
            return None, None, f"ERROR: Unknown parsing issue: {str(e)}"

    def update_hyprland_info(self):
        clients, workspaces, status = self.get_hyprland_data()
        if status.startswith("ERROR"):
            self.error_lbl.set_value(status)
            self.table.setRowCount(0)
            self.ws_combo.clear()
            self.btn_focus.setEnabled(False)
            self.btn_move.setEnabled(False)
            return
        self.error_lbl.set_value("HYPRLAND IS ACTIVE")
        self.active_clients = clients
        self.active_workspaces = workspaces
        
        self.table.setRowCount(len(clients))
        for row, c in enumerate(clients):
            ws_id = str(c.get('workspace', {}).get('id', 'N/A'))
            address = c.get('address', 'N/A')[2:]
            window_class = c.get('class', 'N/A')
            title = c.get('title', 'N/A')
            self.table.setItem(row, 0, QTableWidgetItem(ws_id))
            self.table.setItem(row, 1, QTableWidgetItem(address))
            self.table.setItem(row, 2, QTableWidgetItem(window_class))
            self.table.setItem(row, 3, QTableWidgetItem(title))

        current_ws = set()
        for ws in self.active_workspaces:
            current_ws.add(str(ws.get('id')))
        ws_list = sorted(list(current_ws), key=lambda x: int(x) if x.isdigit() else x)
        current_combo_items = [self.ws_combo.itemText(i) for i in range(self.ws_combo.count())]
        if ws_list != current_combo_items:
            self.ws_combo.clear()
            self.ws_combo.addItems(ws_list)
        enabled = len(clients) > 0
        self.btn_focus.setEnabled(enabled)
        self.btn_move.setEnabled(len(ws_list) > 0)

    def get_selected_client_address(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Selection Error", "Please select a window first.")
            return None
        row = selected_rows[0].row()
        address = self.table.item(row, 1).text()
        return address

    def focus_selected_window(self):
        address = self.get_selected_client_address()
        if not address:
            return
        command = f"focuswindow address:0x{address}"
        output = self.run_hyprctl(["dispatch", command])
        if output.startswith("ERROR"):
            QMessageBox.critical(self, "Hyprctl Error", output)
        
    def move_active_to_workspace(self):
        ws_id = self.ws_combo.currentText()
        if not ws_id:
            QMessageBox.warning(self, "Workspace Error", "No workspace selected.")
            return
        command = f"movetoworkspace {ws_id},address"
        output = self.run_hyprctl(["dispatch", command])
        if output.startswith("ERROR"):
            QMessageBox.critical(self, "Hyprctl Error", output)
        else:
            QMessageBox.information(self, "Success", f"Active window moved to workspace {ws_id}.")
            self.update_hyprland_info()


class ConfigPage(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        v = QVBoxLayout(self)
        card = Card("CORE // RAW CONFIG", f"Directly edit {CONFIG_FILE.name} (JSON format required)")
        self.editor = QTextEdit()
        self.editor.setObjectName("ConfigEditor")
        self.load_config_content()
        card.body.addWidget(self.editor)
        save_btn = QPushButton(":: APPLY & RE-SYNC CONFIG ::")
        save_btn.clicked.connect(self.save_config_content)
        card.body.addWidget(save_btn)
        self.status_lbl = StatLabel("STATUS", f"Loaded from: {CONFIG_FILE}")
        card.body.addWidget(self.status_lbl)
        v.addWidget(card)
        v.addStretch()

    def load_config_content(self):
        try:
            content = CONFIG_FILE.read_text()
            parsed = json.loads(content)
            self.editor.setText(json.dumps(parsed, indent=2))
        except FileNotFoundError:
            self.editor.setText(json.dumps(DEFAULT_CONFIG, indent=2))
            self.status_lbl.set_value("Config file not found. Showing defaults.")
        except json.JSONDecodeError:
            self.editor.setText("Error: Current config file is invalid JSON.")
            self.status_lbl.set_value("Error: Config file is corrupt (Invalid JSON).")
        except Exception as e:
            self.editor.setText(f"Error loading config: {str(e)}")
            self.status_lbl.set_value("Error loading config.")

    def save_config_content(self):
        content = self.editor.toPlainText()
        try:
            parsed_cfg = json.loads(content)
            CONFIG_FILE.write_text(json.dumps(parsed_cfg, indent=2))
            self.parent.cfg = load_config()
            self.parent.apply_styles()
            self.status_lbl.set_value("Config saved and UI styles re-synchronized.")
            self.editor.setText(json.dumps(self.parent.cfg, indent=2))
        except json.JSONDecodeError:
            QMessageBox.critical(self, "Configuration Error", "The content is not valid JSON. Please fix the formatting before saving.")
            self.status_lbl.set_value("SAVE FAILED: Invalid JSON format.")
        except Exception as e:
            QMessageBox.critical(self, "I/O Error", f"Failed to write configuration file.\nReason: {str(e)}")
            self.status_lbl.set_value("SAVE FAILED: I/O Error.")


class NetworkPage(QWidget):
    def __init__(self):
        super().__init__()
        v = QVBoxLayout(self)
        card = Card("NETWORK INTERFACE", "Host and connection status")
        self.lbl_host = StatLabel("HOSTNAME", "")
        self.lbl_ip = StatLabel("IP ADDRESS", "")
        self.lbl_stats = StatLabel("I/O MONITOR", "Initializing...")
        card.body.addWidget(self.lbl_host)
        card.body.addWidget(self.lbl_ip)
        card.body.addWidget(self.lbl_stats)
        v.addWidget(card)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(5000)
        self.refresh()
        v.addStretch()

    def refresh(self):
        h, ip = hostname_ip()
        self.lbl_host.set_value(h)
        self.lbl_ip.set_value(ip)
        try:
            net_io = psutil.net_io_counters(pernic=False)
            stats = f"TX: {format_bytes(net_io.bytes_sent)} | RX: {format_bytes(net_io.bytes_recv)}"
            self.lbl_stats.set_value(stats)
        except Exception:
            self.lbl_stats.set_value("DATA_STREAM_ERROR")


class ProcessPage(QWidget):
    def __init__(self):
        super().__init__()
        v = QVBoxLayout(self)
        card = Card("PROCESS MONITOR", "Top 10 CPU-heavy running tasks")
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["PID", "CPU%", "MEM%", "Name"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setObjectName("ProcessTable")

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        card.body.addWidget(self.table)
        
        kill_btn = QPushButton(":: TERMINATE SELECTED PROCESS (SIGTERM) ::")
        kill_btn.clicked.connect(self.kill_process)
        card.body.addWidget(kill_btn)
        
        v.addWidget(card)
        v.addStretch()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_process_list)
        self.timer.start(2000)
        self.update_process_list()

    def update_process_list(self):
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            processes.sort(key=lambda p: p['cpu_percent'], reverse=True)
            top_processes = processes[:10]
            self.table.setRowCount(len(top_processes))
            for row, p in enumerate(top_processes):
                self.table.setItem(row, 0, QTableWidgetItem(str(p['pid'])))
                self.table.setItem(row, 1, QTableWidgetItem(f"{p['cpu_percent']:.1f}"))
                self.table.setItem(row, 2, QTableWidgetItem(f"{p['memory_percent']:.1f}"))
                self.table.setItem(row, 3, QTableWidgetItem(p['name']))
        except Exception as e:
            print(f"Error updating process list: {e}")

    def kill_process(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Warning")
            msg_box.setText("No process selected for termination.")
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.exec_()
            return
        row = selected_rows[0].row()
        pid_item = self.table.item(row, 0)
        name_item = self.table.item(row, 3)
        if not pid_item or not name_item:
            return
        pid = int(pid_item.text())
        name = name_item.text()
        confirm = QMessageBox(self)
        confirm.setWindowTitle("Confirm Termination")
        confirm.setText(f"Are you sure you want to terminate process **{name}** (PID: {pid})?")
        confirm.setIcon(QMessageBox.Critical)
        confirm.addButton("AFFIRMATIVE (Kill)", QMessageBox.YesRole)
        confirm.addButton("NEGATIVE (Cancel)", QMessageBox.NoRole)
        if confirm.exec_() == QMessageBox.AcceptRole:
            try:
                os.kill(pid, 15)
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("Success")
                msg_box.setText(f"Termination signal sent to {name} (PID: {pid}).")
                msg_box.exec_()
                self.update_process_list()
            except ProcessLookupError:
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("Error")
                msg_box.setText("Process already terminated.")
                msg_box.setIcon(QMessageBox.Critical)
                msg_box.exec_()
            except Exception as e:
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("Error")
                msg_box.setText(f"Failed to terminate process.")
                msg_box.setDetailedText(str(e))
                msg_box.setIcon(QMessageBox.Critical)
                msg_box.exec_()
class UtilityPage(QWidget):
    def __init__(self):
        super().__init__()
        v = QVBoxLayout(self)
        
        card = Card("UTILITY CONSOLE", "Quick access to core desktop applications")
        grid = QGridLayout()
        
        self.app_list = [
            ("TERMINAL", "alacritty", "#00FF00"),
            ("FILE MANAGER", "cypher-vault", "#00FFFF"),
            ("WEB BROWSER", "firefox", "#FFD700"),
            ("TEXT EDITOR", "vi", "#FF66CC"),
        ]
        
        for i, (label, command, color) in enumerate(self.app_list):
            btn = QPushButton(f":: LAUNCH {label} ::")
            btn.clicked.connect(lambda _, cmd=command: self.launch_app(cmd, label))
            grid.addWidget(btn, i // 2, i % 2)
            
        card.body.addLayout(grid)
        v.addWidget(card)
        v.addStretch()

    def launch_app(self, command, label):
        try:
            subprocess.Popen([command], start_new_session=True)
        except FileNotFoundError:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Launch Error")
            msg_box.setText(f"Command '{command}' for {label} not found.")
            msg_box.setDetailedText("Please ensure the application is installed and in your system PATH.")
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.exec_()
        except Exception as e:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Launch Error")
            msg_box.setText(f"Failed to launch {label}.")
            msg_box.setDetailedText(str(e))
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.exec_()


class PowerPage(QWidget):
    def __init__(self):
        super().__init__()
        v = QVBoxLayout(self)
        
        card = Card("POWER GRID", "Critical system power actions (loginctl)")
        grid = QGridLayout()
        
        btn_suspend = QPushButton(":: EXECUTE SUSPEND ::")
        btn_suspend.clicked.connect(lambda: self.execute_loginctl_command("suspend", "Suspend System"))
        grid.addWidget(btn_suspend, 0, 0)
        
        btn_reboot = QPushButton(":: EXECUTE REBOOT ::")
        btn_reboot.clicked.connect(lambda: self.execute_loginctl_command("reboot", "Reboot System"))
        grid.addWidget(btn_reboot, 0, 1)

        btn_shutdown = QPushButton(":: EXECUTE SHUTDOWN ::")
        btn_shutdown.clicked.connect(lambda: self.execute_loginctl_command("poweroff", "Shutdown System"))
        grid.addWidget(btn_shutdown, 1, 0)
        
        card.body.addLayout(grid)
        v.addWidget(card)
        v.addStretch()
        
    def execute_loginctl_command(self, action, title):
        confirmation = QMessageBox(self)
        confirmation.setWindowTitle(f"Confirm {title}")
        confirmation.setText(f"Are you sure you want to **{title.upper()}**?")
        confirmation.setIcon(QMessageBox.Warning)
        
        yes_button = confirmation.addButton("AFFIRMATIVE (Yes)", QMessageBox.YesRole)
        no_button = confirmation.addButton("NEGATIVE (No)", QMessageBox.NoRole)
        
        if confirmation.exec_() == QMessageBox.AcceptRole: 
            command = ["loginctl", action]
            try:
                subprocess.Popen(command, start_new_session=True) 
            except Exception as e:
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("Execution Error")
                msg_box.setText(f"Failed to start command.")
                msg_box.setDetailedText(f"Command: {' '.join(command)}\nError: {e}")
                msg_box.setIcon(QMessageBox.Critical)
                msg_box.exec_()

class SynapseApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f":: {APP_NAME.upper()}")
        self.resize(1200, 760)
        self.cfg = load_config()
        self.build_ui()
        self.apply_styles()

    def build_ui(self):
        container = QWidget()
        self.setCentralWidget(container)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15) 

        self.menu_frame = QFrame()
        self.menu_frame.setObjectName("MenuFrame")
        menu_layout = QVBoxLayout(self.menu_frame)
        menu_layout.setContentsMargins(10, 10, 10, 10)
        
        self.stack_frame = QFrame()
        self.stack_frame.setObjectName("StackFrame")
        stack_layout = QVBoxLayout(self.stack_frame)
        stack_layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()
        stack_layout.addWidget(self.stack)
        menu_layout.addWidget(self.create_menu())
        
        layout.addWidget(self.menu_frame, 0)
        layout.addWidget(self.stack_frame, 1)

        self.pages = [
            ChronoPage(), SystemPage(), PersonalizationPage(self), AudioPage(), HyprlandPage(),
            NetworkPage(), ProcessPage(), UtilityPage(), PowerPage(),
            ConfigPage(self), 
        ]
        for p in self.pages:
            sa = QScrollArea()
            sa.setWidgetResizable(True)
            sa.setWidget(p)
            sa.setObjectName("PageScrollArea")
            self.stack.addWidget(sa)

        self.menu.setCurrentRow(0)

    def create_menu(self):
        self.menu = QListWidget()
        self.menu.setObjectName("MenuWidget")
        
        menu_items = [
            "TIME",
            "SYSTEM",
            "VISUALS", 
            "AUDIO", 
            "WINDOWS",
            "NETWORK", 
            "PROCESSES", 
            "UTILITIES",   
            "POWER", 
            "CORE", 
            
        ]
        
        for name in menu_items:
            item = QListWidgetItem(name)
            self.menu.addItem(item)
            
        self.menu.setFixedWidth(280)
        self.menu.currentRowChanged.connect(self.switch_page)
        return self.menu

    def switch_page(self, idx):
        if hasattr(self, "stack"):
            self.stack.setCurrentIndex(idx)
            self.animate_page()

    def animate_page(self):
        w = self.stack.currentWidget()
        if not w:
            return
        a = QPropertyAnimation(w, b"pos")
        rect = w.geometry()
        start = QRect(rect.x() + 15, rect.y(), rect.width(), rect.height()).topLeft()
        a.setStartValue(start)
        a.setEndValue(rect.topLeft())
        a.setDuration(250)
        a.setEasingCurve(QEasingCurve.OutCubic)
        a.start(QPropertyAnimation.DeleteWhenStopped)

    def apply_styles(self):
        accent = self.cfg.get("accent", DEFAULT_CONFIG['accent'])
        general_accent = self.cfg.get("general_accent", DEFAULT_CONFIG['general_accent'])
        
        theme = self.cfg.get("theme", "dark")
        opacity_percent = self.cfg.get("ui_opacity", DEFAULT_CONFIG['ui_opacity'])
        opacity = float(opacity_percent) / 100.0
        self.setWindowOpacity(opacity) 

        general_font = self.cfg.get("general_font", DEFAULT_CONFIG['general_font'])
        display_font = self.cfg.get("display_font", DEFAULT_CONFIG['display_font'])

        if theme == "light":
            BG_MAIN = "#f7f7f7"
            FG_PRIMARY = "#102020" 
            BG_CARD = "#ffffff"
        else:
            BG_MAIN = "#0a0f0a"
            FG_PRIMARY = "#cfeee0"
            BG_CARD = "rgba(10,12,12,0.75)"

        style_sheet = f"""
        * {{
            font-family: '{general_font}', 'Consolas', monospace;
            font-size: 10pt;
            color: {FG_PRIMARY}; 
            outline: none;
        }}
        
        QMainWindow, QWidget, QScrollArea {{
            background-color: {BG_MAIN};
        }}
        
        QScrollArea#PageScrollArea {{
            border: none;
        }}
        
        #MenuFrame, #StackFrame {{
            border-radius: 4px;
            padding: 5px;
            background-color: {BG_MAIN};
        }}

        QFrame#Card {{
            background: {BG_CARD};
            border: 1px solid {general_accent}40;
            border-radius: 8px; 
            margin-bottom: 20px;
        }}
        
        #CardTitle {{
            font-size: 12pt;
            font-weight: bold;
            color: {accent};
            padding: 0 0 5px 0;
            margin: 0;
        }}
        
        #CardSubtitle {{
            font-size: 9pt;
            color: {general_accent}A0;
            font-style: italic;
        }}

        #CardSeparator {{
            height: 0px; 
            border: none;
        }}
        
        QListWidget {{
            background-color: {BG_MAIN}50;
            border: 1px solid {general_accent}70;
            border-radius: 8px;
        }}
        
        QListWidget::item {{
            padding: 15px 12px;
            border-radius: 6px;
            margin-bottom: 3px;
        }}
        
        QListWidget::item:hover {{
            background: {general_accent}40;
        }}
        
        QListWidget::item:selected {{
            background: {accent};
            color: #051010; 
            font-weight: bold;
            border: 2px solid {FG_PRIMARY}90;
        }}

        #TimeDisplayLarge {{ 
            font-family: '{display_font}', monospace;
            font-size: 64pt;
            font-weight: bold;
            color: {accent};
            text-align: center;
            padding: 10px 0;
            text-shadow: 0 0 8px {accent}AA;
        }}

        #DateDisplay {{ 
            font-family: '{general_font}', monospace;
            font-size: 14pt;
            font-weight: 500;
            color: {general_accent}B0;
            text-align: center;
            padding-bottom: 10px;
        }}
        
        .stat-label {{
            color: {general_accent}A0;
            font-weight: normal;
        }}
        
        .stat-value {{
            color: {FG_PRIMARY}; 
            font-weight: 500;
        }}
        
        QPushButton {{
            background: {general_accent}20;
            color: {accent};
            border: 1px solid {general_accent}70;
            border-radius: 4px;
            padding: 10px 15px;
            text-transform: uppercase;
            font-weight: bold;
        }}
        
        QPushButton:hover {{
            background: {general_accent}40;
            color: {FG_PRIMARY};
            border: 1px solid {accent};
        }}
        
        QSlider::groove:horizontal {{
            border: 1px solid {general_accent}70;
            height: 8px; 
            background: {BG_MAIN}40;
            border-radius: 4px;
        }}
        
        QSlider::handle:horizontal {{
            background: {accent};
            border: 2px solid {general_accent};
            width: 20px;
            margin: -7px 0;
            border-radius: 10px;
        }}
        
        QSlider::sub-page:horizontal {{
            background: {accent};
            border-radius: 4px;
        }}

        QComboBox, QSpinBox {{
            background: {BG_MAIN}80;
            border: 1px solid {general_accent}70;
            border-radius: 4px;
            padding: 5px;
            min-height: 25px; 
            font-size: 10pt;
        }}
        
        QComboBox::drop-down, QSpinBox::up-button, QSpinBox::down-button {{
            border: none;
            width: 20px;
        }}
        
        QTextEdit#ConfigEditor, QLineEdit#CommandInput {{
            background: {BG_MAIN}80;
            border: 1px solid {general_accent}70;
            border-radius: 4px;
            padding: 8px;
            font-family: monospace;
            font-size: 9pt;
        }}

        QComboBox QAbstractItemView {{
            border: 1px solid {accent};
            background-color: {BG_MAIN};
            selection-background-color: {general_accent}60;
            selection-color: {BG_CARD};
            padding: 5px;
        }}

        QTableWidget {{
            background-color: {BG_MAIN}80;
            border: 1px solid {general_accent}70;
            gridline-color: {general_accent}30;
            selection-background-color: {accent}80;
            selection-color: #051010;
        }}
        
        QHeaderView::section {{
            background-color: {BG_MAIN};
            color: {accent};
            border: 1px solid {general_accent}50;
            padding: 8px;
            font-weight: bold;
        }}
        
        QTableWidget::item {{
            padding: 6px;
        }}
        
        QMessageBox {{
            background-color: {BG_CARD};
            border: 2px solid {accent};
        }}

        QMessageBox QPushButton {{
            background: {BG_CARD}; 
            color: {accent};
            border: 1px solid {accent};
            padding: 8px 15px;
        }}

        QMessageBox QPushButton:hover {{
            background: {accent}30;
        }}
        """
        self.setStyleSheet(style_sheet)

def main():
    QCoreApplication.setApplicationName(APP_NAME.capitalize())
    QCoreApplication.setOrganizationName("SynthCorp")
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    app = QApplication(sys.argv)
    win = SynapseApp()
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()