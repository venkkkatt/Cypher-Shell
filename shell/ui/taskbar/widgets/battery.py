from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QLabel
import psutil

class BatteryWidget(QLabel):
    def __init__(self):
        super().__init__()

        self.setStyleSheet("""
            color: #b7efc5;
            padding: 0px 5px;
            border: 1px solid #70e000;
            border-radius: 1%;
            background-color: #036666;
        """)

        self.updateBattery()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateBattery)
        self.timer.start(1000)

    def updateBattery(self):
        battery = psutil.sensors_battery()
        if battery is None:
            self.setText("N/A")
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
        self.setText(f"{status} {percent:.0f}%")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
