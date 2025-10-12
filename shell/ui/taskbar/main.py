import os, sys
import subprocess
os.environ.setdefault("QT_QPA_PLATFORM", "wayland")

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QWidget, QGridLayout, QHBoxLayout, QApplication, QPushButton 
from PyQt6.QtGui import QFont
from widgets.clock import ClockWidget
from widgets.battery import BatteryWidget
from widgets.workspaces import WorkspaceWidget

def launch_cydeck():
    try:
        subprocess.Popen(["/usr/local/bin/cydeck"])
    except FileNotFoundError:
        print("Error: 'cydeck' binary not found. Please check your PATH or the command.")
    except Exception as e:
        print(f"An error occurred while launching cydeck: {e}")

def initialize_taskbar():
    app = QApplication(sys.argv)
    main = QWidget()
    main.setWindowTitle("taskbar")
    app.force_quit = False
    main.setWindowFlags(
        Qt.WindowType.FramelessWindowHint |
        Qt.WindowType.WindowStaysOnTopHint |
        Qt.WindowType.Tool
    )

    layout = QGridLayout()
    screen = app.primaryScreen()
    geo = screen.geometry()
    main.setFixedSize(geo.width(), 35)
    main.move(0, 0)
    main.setStyleSheet("background-color: transparent; border: 0px")

    font = QFont("OCR A", 10)
    app.setFont(font)
    layout.setContentsMargins(6, 0, 6, 0)
    layout.setSpacing(0)
    main.setLayout(layout)

    left = QWidget()
    leftLayout = QHBoxLayout()
    leftLayout.setContentsMargins(0, 0, 0, 0)
    leftLayout.setSpacing(10)
    left.setLayout(leftLayout)
    
    cydeck_button = QPushButton("CYDECK")
    cydeck_button.setFont(QFont("OCR A", 10))
    cydeck_button.setFixedSize(70, 35)

    COLOR_ACCENT = "#90EE90"
    COLOR_BG_SOLID = "#17212b"
    COLOR_PRIMARY_TEXT = "#F0FFF0"
    COLOR_INACTIVE = "#36414d"
    
    cydeck_button.setStyleSheet(f"""
        QPushButton {{
            background-color: {COLOR_BG_SOLID};
            color: {COLOR_PRIMARY_TEXT};
            border: 1px solid {COLOR_INACTIVE};
            padding: 2px;
            border-radius: 2px;
            text-align: center;
        }}
        QPushButton:hover {{
            background-color: {COLOR_ACCENT};
            color: {COLOR_BG_SOLID};
            font-weight: bold;
        }}
    """)
    
    leftLayout.addWidget(cydeck_button)
    cydeck_button.clicked.connect(launch_cydeck)
    work = WorkspaceWidget() 
    leftLayout.addWidget(work)
    layout.addWidget(left, 0, 0, alignment=Qt.AlignmentFlag.AlignLeft)

    center = QWidget()
    centerLayout = QHBoxLayout()
    centerLayout.setContentsMargins(0, 0, 0, 0)
    centerLayout.setSpacing(6)
    clock = ClockWidget() 
    clock.setFixedHeight(30)
    centerLayout.addWidget(clock)
    center.setLayout(centerLayout)
    layout.addWidget(center, 0, 1, alignment=Qt.AlignmentFlag.AlignCenter)

    right = QWidget()
    rightLayout = QHBoxLayout()
    rightLayout.setContentsMargins(0, 0, 0, 0)
    rightLayout.setSpacing(10)
    right.setLayout(rightLayout)
    battery = BatteryWidget()
    battery.setFixedHeight(24)
    rightLayout.addWidget(battery)
    layout.addWidget(right, 0, 2, alignment=Qt.AlignmentFlag.AlignRight)

    main.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    
    def updateAll():
        battery.updateBattery()
        clock.updateTime()

    timer = QTimer()
    timer.timeout.connect(updateAll)
    timer.start(1000)

    def on_focus_changed(old, new):
        if new is main or (hasattr(new, 'parent') and new.parent() is main):
            if old:
                old.setFocus()

    app.focusChanged.connect(on_focus_changed)
    main.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    initialize_taskbar()
