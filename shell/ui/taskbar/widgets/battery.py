from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QLabel
import psutil

class BatteryWidget(QLabel):
    def __init__(self):
        super().__init__()

        self.setStyleSheet("color:#ce92ff; padding : 0px 5px; border: 1px solid rgba(255, 156, 255, 0.273); border-radius: 1%;background-color: rgba(68, 64, 68, 0.256);")

        self.updateBattery()

        timer = QTimer(self)
        timer.timeout.connect(self.updateBattery)
        timer.start(1000)


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

