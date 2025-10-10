#!/usr/bin/env python3

import os,psutil,random,subprocess,socket,getpass,platform,sys
os.environ["QT_QPA_PLATFORM"] = "xcb"

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QProgressBar,
    QGridLayout, QHBoxLayout, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import QTimer, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from memory import MemWidget



class SystemInfoWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.updateInfo()

        self.timer = QTimer()
        self.timer.timeout.connect(self.updateInfo)
        self.timer.start(1000)

    def initUI(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.setFixedSize(250, 140)
        self.setStyleSheet("background-color:#00FF41; color:black;")

        font_title = QFont("OCR A", 10)
        font_title.setWeight(99)
        font_title.setBold(True)

        self.os_label = QLabel("OS:")
        self.os_label.setFont(font_title)
        self.os_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.host_label = QLabel("Logged in as:")
        self.host_label.setFont(font_title)
        self.host_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.uptime_label = QLabel("Uptime: 0")
        self.uptime_label.setFont(font_title)
        self.uptime_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.os_label)
        layout.addWidget(self.host_label)
        layout.addWidget(self.uptime_label)

        self.setGlow(self)

    def setGlow(self, widget):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor("#129036"))
        shadow.setOffset(0, 0)
        widget.setGraphicsEffect(shadow)

    def updateInfo(self):
        # OS / host
        self.os_label.setText(f"OS..{platform.node()}")
        self.host_label.setText(f"Logged in as..{getpass.getuser()}")

        import time
        uptime = psutil.boot_time()
        uptime_sec = int(time.time() - uptime)
        hours, rem = divmod(uptime_sec, 3600)
        minutes, seconds = divmod(rem, 60)
        self.uptime_label.setText(f"Uptime..{hours}h {minutes}m {seconds}s")


class CPUTempWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.title_label = QLabel("CPU Temp")
        self.title_label.setFont(QFont("OCR A", 14))
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setFixedSize(150, 30)

        self.temp_label = QLabel("N/A °C")
        self.temp_label.setFont(QFont("OCR A", 18))
        self.temp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.temp_label.setFixedWidth(150)
        self.temp_label.setFixedHeight(64)
        self.setFixedSize(150, 150)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)

        layout.addWidget(self.title_label)
        layout.addWidget(self.temp_label)
        layout.addWidget(self.progress_bar)

        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #23D300;
                border-radius: 4px;
                background-color: transparent;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #23D300;
                border-radius: 3px;
            }
        """)

        self.setStyleSheet("""
            background-color:#00FF41;
            color:black;
        """)

    def updateTemp(self):
        try:
            temps = psutil.sensors_temperatures()
            if not temps:
                self.temp_label.setText("N/A °C")
                self.progress_bar.setValue(0)
                return

            cpu_temps = temps.get("coretemp") or temps.get("cpu_thermal") or []
            if cpu_temps:
                temp = max([t.current for t in cpu_temps])
                self.temp_label.setText(f"{temp:.1f} °C")
                self.progress_bar.setValue(min(int(temp), 100))
            else:
                self.temp_label.setText("N/A °C")
                self.progress_bar.setValue(0)
        except Exception as e:
            self.temp_label.setText("Error")
            self.progress_bar.setValue(0)
            print(f"CPU Temp Error: {e}")


class DiskWidget(QWidget):
    def __init__(self, path="/"):
        super().__init__()
        self.path = path
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.title_label = QLabel("DISK")
        self.title_label.setFont(QFont("OCR A", 15))
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setFixedSize(134, 32)

        self.disk_label = QLabel("N/A")
        self.disk_label.setFont(QFont("OCR A", 11))
        self.disk_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.disk_label.setFixedSize(134, 60)
        self.fillerLabel = QLabel("")
        self.fillerLabel.setFixedSize(0, 9)

        self.setFixedSize(234, 138)

        layout.addWidget(self.title_label)
        layout.addWidget(self.disk_label)
        layout.addWidget(self.fillerLabel)

        self.setStyleSheet("""
            background-color:#00FF41;
            color:black;
        """)

    def updateDisk(self):
        try:
            usage = psutil.disk_usage(self.path)
            percent = usage.percent
            self.disk_label.setText(f"{usage.used // (1024**3)}GB / {usage.total // (1024**3)}GB")
        except Exception as e:
            self.disk_label.setText("Error")
            print(f"Disk Error: {e}")


class WifiThread(QThread):
    result = pyqtSignal(str, int, str)

    def run(self):
        while True:
            ssid, signal = "N/A", 0
            try:
                output = subprocess.check_output(
                    ["nmcli", "-t", "-f", "active,ssid,signal", "dev", "wifi"],
                    text=True,
                    timeout=1
                )
                for line in output.splitlines():
                    parts = line.split(":")
                    if len(parts) >= 3:
                        active, name, sig = parts[0], parts[1], parts[2]
                        if active == "yes":
                            ssid, signal = name, int(sig) if sig.isdigit() else 0
                            break
            except subprocess.TimeoutExpired:
                pass
            except Exception:
                pass

            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.settimeout(1)
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]
                s.close()
            except Exception:
                ip = "N/A"

            self.result.emit(ssid, signal, ip)
            QThread.msleep(1000)


class NetworkWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        counters = psutil.net_io_counters()
        self.prev_bytes_sent = counters.bytes_sent
        self.prev_bytes_recv = counters.bytes_recv

        self.wifiThread = WifiThread()
        self.wifiThread.result.connect(self.updateWifiLabels)
        self.wifiThread.start()

    def initUI(self):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.title = QLabel("Network")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setFont(QFont("OCR A", 15))
        self.title.setFixedSize(270, 30)

        self.infoLabel = QLabel("SSID: N/A")
        self.infoLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.infoLabel.setFont(QFont("OCR A", 8))
        self.infoLabel.setFixedWidth(270)
        self.infoLabel.setFixedHeight(27)

        self.infoLabel2 = QLabel("Signal: 0%")
        self.infoLabel2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.infoLabel2.setFont(QFont("OCR A", 11))
        self.infoLabel2.setFixedWidth(270)
        self.infoLabel2.setFixedHeight(27)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)

        self.infoLabel3 = QLabel("IP: N/A")
        self.infoLabel3.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.infoLabel3.setFont(QFont("OCR A", 11))
        self.infoLabel3.setFixedWidth(270)
        self.infoLabel3.setFixedHeight(30)

        self.label = QLabel("Up: 0 KB/s \nDown: 0 KB/s")
        self.label.setFont(QFont("OCR A", 11))
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setFixedHeight(50)
        self.label.setFixedWidth(270)

        self.setFixedSize(275, 250)

        self.layout.addWidget(self.title)
        self.layout.addWidget(self.infoLabel)
        self.layout.addWidget(self.infoLabel2)
        self.layout.addWidget(self.progress_bar)
        self.layout.addWidget(self.infoLabel3)
        self.layout.addWidget(self.label)

        self.setStyleSheet("background-color:#00FF41; color:black;")

    def updateNetwork(self):
        counters = psutil.net_io_counters()
        up = counters.bytes_sent - self.prev_bytes_sent
        down = counters.bytes_recv - self.prev_bytes_recv

        self.prev_bytes_sent = counters.bytes_sent
        self.prev_bytes_recv = counters.bytes_recv

        up_kb = up / 1024
        down_kb = down / 1024
        self.label.setText(f"Up: {up_kb:.1f} KB/s \nDown: {down_kb:.1f} KB/s")

    def updateWifiLabels(self, ssid, signal, ip):
        self.infoLabel.setText(f"SSID: {ssid}")
        self.infoLabel2.setText(f"Signal: {signal}%")
        self.infoLabel3.setText(f"IP: {ip}")
        self.progress_bar.setValue(int(signal))
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid #23D300;
                border-radius: 4px;
                background-color: transparent;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: #23D300;
                border-radius: 3px;
            }}
        """)


class BatteryWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initBattery()

    def initBattery(self):
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnBottomHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowDoesNotAcceptFocus |
            Qt.WindowType.Tool
        )
        self.setStyleSheet("""
            background-color:#00FF41;
            color:black
        """)

        layout = QVBoxLayout()
        font = QFont("OCR A", 20)
        font2 = QFont("OCR A", 20)
        self.batteryLabel = QLabel("")
        self.batteryLabel.setFont(font2)
        self.batteryLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.batteryTitle = QLabel("")
        self.batteryTitle.setFont(font)
        self.batteryLabel.setStyleSheet("color:black")

        layout.addWidget(self.batteryLabel)
        self.setLayout(layout)

    def updateBattery(self):
        try:
            battery = psutil.sensors_battery()
            if battery is None:
                # fixed bug: set the label text, not widget text
                self.batteryLabel.setText("N/A")
                return

            percent = battery.percent
            charging = battery.power_plugged

            if percent > 80:
                icon = "\uf240"
            elif percent > 60:
                icon = "\uf241"
            elif percent > 40:
                icon = "\uf242"
            elif percent > 20:
                icon = "\uf243"
            else:
                icon = "\uf244"

            status = "\uf0e7" if charging else icon
            self.batteryLabel.setText(f"{status} {percent:.0f}%")
        except Exception as e:
            print(f"battery error {e}")


class CPUWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._cpu_usage = 0.0
        self.initUI()

    def initUI(self):
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnBottomHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowDoesNotAcceptFocus |
            Qt.WindowType.Tool
        )
        self.setObjectName("mainWidget")
        self.setStyleSheet("""
            QLabel {
                color: black;
                background-color: #00FF41;
            }
            QProgressBar {
                border: 1px solid #00FF41;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: transparent
            }
        """)

        layout = QVBoxLayout()

        self.title_label = QLabel("CPU")
        self.title_label.setFixedHeight(30)
        title_font = QFont("OCR A", 17)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.cpu_label = QLabel("0%")
        cpu_font = QFont("OCR A", 20)
        self.cpu_label.setFixedHeight(60)
        self.cpu_label.setFont(cpu_font)
        self.cpu_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)

        layout.addWidget(self.title_label)
        layout.addWidget(self.cpu_label)
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)

    def updateCpuUsage(self):
        try:
            usage = psutil.cpu_percent(interval=None)
            self._cpu_usage = usage

            self.cpu_label.setText(f"{int(usage)}%")
            self.progress_bar.setValue(int(usage))

            color = self.getCpuColor(usage)
            self.cpu_label.setStyleSheet(f"color: black;")

            self.progress_bar.setStyleSheet(f"""
                QProgressBar {{
                    border: 1px solid #23D300;
                    border-radius: 4px;
                    background-color: transparent;
                    text-align: center;
                }}
                QProgressBar::chunk {{
                    background-color: {color};
                    border-radius: 3px;
                }}
            """)

            if usage > 80:
                self.setWindowOpacity(0.7)
            else:
                self.setWindowOpacity(0.85)

        except Exception as e:
            print(f"Error reading CPU usage: {e}")

    def getCpuColor(self, usage):
        if usage < 60:
            return "#23D300"
        return "#FF5024"


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.cpuWidget = CPUWidget()
        self.memWidget = MemWidget()
        self.batteryWidget = BatteryWidget()
        self.cpuTempWidget = CPUTempWidget()
        self.diskWidget = DiskWidget()
        self.batteryWidget.setStyleSheet("background-color:#00FF41")
        self.networkWidget = NetworkWidget()

        self.cpuWidget.setFixedSize(150, 150)
        self.memWidget.setFixedSize(150, 150)
        self.batteryWidget.setFixedSize(150, 80)
        self.systemWidget = SystemInfoWidget()

        layout = QGridLayout()
        hLayout3 = QHBoxLayout()
        hLayout = QHBoxLayout()
        hLayout2 = QHBoxLayout()
        hLayout4 = QHBoxLayout()

        hLayout.addWidget(self.cpuWidget, alignment=Qt.AlignmentFlag.AlignLeft)
        hLayout4.addWidget(self.cpuTempWidget, alignment=Qt.AlignmentFlag.AlignLeft)
        hLayout4.addWidget(self.systemWidget, alignment=Qt.AlignmentFlag.AlignRight)
        hLayout2.addWidget(self.memWidget)
        hLayout3.addWidget(self.diskWidget, alignment=Qt.AlignmentFlag.AlignLeft)
        hLayout2.addWidget(self.networkWidget, alignment=Qt.AlignmentFlag.AlignRight)

        layout.addLayout(hLayout4, 0, 0)
        layout.addLayout(hLayout3, 1, 0)
        layout.addLayout(hLayout, 2, 0)
        layout.addLayout(hLayout2, 3, 0)
        self.setLayout(layout)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnBottomHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setGlow(self.cpuWidget)
        self.setGlow(self.memWidget)
        self.setGlow(self.diskWidget)
        self.setGlow(self.cpuTempWidget)
        self.setGlow(self.networkWidget)
        self.addGlitchEffect(self.cpuTempWidget)
        self.addGlitchEffect(self.systemWidget, interval=4000, duration=200)

        self.timer = QTimer()
        self.timer.timeout.connect(self.updateAll)
        self.timer.start(1000)

    def updateAll(self):
        self.cpuWidget.updateCpuUsage()
        self.memWidget.updateMemUsage()
        self.networkWidget.updateNetwork()
        self.cpuTempWidget.updateTemp()
        self.diskWidget.updateDisk()

    def addGlitchEffect(self, widget, interval=2000, duration=150):
        timer = QTimer(widget)

        def glitch():
            orig_style = widget.styleSheet()
            orig_geo = widget.geometry()
            orig_opacity = widget.windowOpacity()

            effects = [
                lambda: widget.setStyleSheet("background-color:#007f5f; color:#00FF41;"),
                lambda: widget.setStyleSheet("background-color:#00FF41; color:#FF004D;"),
                lambda: widget.setGeometry(orig_geo.adjusted(
                    random.randint(-5, 5), random.randint(-5, 5),
                    random.randint(-5, 5), random.randint(-5, 5))),
                lambda: widget.setWindowOpacity(0.6),
            ]

            random.choice(effects)()

            QTimer.singleShot(duration, lambda: (
                widget.setStyleSheet(orig_style),
                widget.setGeometry(orig_geo),
                widget.setWindowOpacity(orig_opacity),
            ))

        timer.timeout.connect(glitch)
        timer.start(interval)
        return timer

    def setGlow(self, widget):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor("#18a948"))
        shadow.setOffset(0, 0)
        widget.setGraphicsEffect(shadow)


def main():
    app = QApplication(sys.argv)

    app.setApplicationName("dashboard")
    app.setApplicationDisplayName("dashboard")

    mainWidget = MainWindow()
    mainWidget.setStyleSheet("""
        background-color: transparent;
        border: 1px solid #2e7b39
    """)
    mainWidget.setWindowTitle("dashboard")
    mainWidget.setProperty("class", "dashboard")

    mainWidget.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
