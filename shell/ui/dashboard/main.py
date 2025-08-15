#!/usr/bin/env python3

import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QProgressBar, QGridLayout, QHBoxLayout
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont, QPalette
import psutil
from memory import MemWidget

class BatteryWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initBattery()
    
    def initBattery(self):
        self.setWindowFlags(
            Qt.WindowStaysOnBottomHint |
            Qt.FramelessWindowHint |
            Qt.WindowDoesNotAcceptFocus |
            Qt.Tool
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
        self.batteryLabel.setAlignment(Qt.AlignCenter)
        self.batteryTitle = QLabel("")
        self.batteryTitle.setFont(font)
        self.batteryLabel.setStyleSheet("color:black")

        layout.addWidget(self.batteryLabel)
        # layout.addWidget(self.batteryTitle)
        self.setLayout(layout)
        self.timerBattery()

    def timerBattery(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.updateBattery)
        self.timer.start(1000) 
        self.updateBattery()

    def updateBattery(self):
        try:
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
            self.batteryLabel.setText(f"{status} {percent:.0f}%")
        except Exception as e:
            print(f"battery error {e}")

class CPUWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._cpu_usage = 0.0
        self.initUI()
        self.setupTimer()
        
    def initUI(self):
        self.setWindowFlags(
            Qt.WindowStaysOnBottomHint |
            Qt.FramelessWindowHint |
            Qt.WindowDoesNotAcceptFocus |
            Qt.Tool
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
        # layout.setContentsMargins(20, 20, 20, 20)
        # layout.setSpacing(10)
        
        self.title_label = QLabel("CPU")
        self.title_label.setFixedHeight(30)
        title_font = QFont("OCR A", 17)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignCenter)
        
        self.cpu_label = QLabel("0%")
        cpu_font = QFont("OCR A", 20)
        self.cpu_label.setFixedHeight(60)

        self.cpu_label.setFont(cpu_font)
        self.cpu_label.setAlignment(Qt.AlignCenter)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        
        layout.addWidget(self.title_label)
        layout.addWidget(self.cpu_label)
        layout.addWidget(self.progress_bar)
        
        self.setLayout(layout)
        
    def setupTimer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.updateCpuUsage)
        self.timer.start(1000) 
        self.updateCpuUsage()
    
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
        # self.cpuWidget.setStyleSheet("background-color:#00FF41")
        self.batteryWidget.setStyleSheet("background-color:#00FF41")

        self.cpuWidget.setFixedSize(150,150)
        self.memWidget.setFixedSize(150,150)
        self.batteryWidget.setFixedSize(150,80)

        layout = QGridLayout()
        hLayout = QHBoxLayout()
        hLayout2 = QHBoxLayout()
        # hLayout2.setAlignment(Qt.AlignTop)
        hLayout.addWidget(self.cpuWidget)
        hLayout.addWidget(self.batteryWidget, alignment=Qt.AlignRight)
        # layout.addWidget(self.memWidget)
        hLayout2.addWidget(self.memWidget)
        hLayout2.addWidget(self.batteryWidget, alignment=Qt.AlignRight)
        layout.addLayout(hLayout,0, 0)
        layout.addLayout(hLayout2, 1, 0)
        self.setLayout(layout)

        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnBottomHint |
            Qt.Tool
        )

def main():
    app = QApplication(sys.argv)

    app.setApplicationName("dashboard")
    app.setApplicationDisplayName("dashboard")
    
    mainWidget = MainWindow()
    mainWidget.setStyleSheet("""
        background-color: transparent;
        border: 1px solid #007200
    """)
    mainWidget.setWindowTitle("dashboard")
    mainWidget.setProperty("class", "dashboard")
    
    mainWidget.show()
    return app.exec_()

if __name__ == "__main__":
    sys.exit(main())