import os, sys
os.environ.setdefault("QT_QPA_PLATFORM", "wayland")

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QWidget, QGridLayout, QHBoxLayout, QApplication
from PyQt6.QtGui import QFont

from widgets.clock import ClockWidget
from widgets.battery import BatteryWidget
from widgets.workspaces import WorkspaceWidget

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
    work = WorkspaceWidget() # Instantiation
    leftLayout.addWidget(work)
    layout.addWidget(left, 0, 0, alignment=Qt.AlignmentFlag.AlignLeft)

    center = QWidget()
    centerLayout = QHBoxLayout()
    centerLayout.setContentsMargins(0, 0, 0, 0)
    centerLayout.setSpacing(6)
    clock = ClockWidget() # Instantiation
    clock.setFixedHeight(30)
    centerLayout.addWidget(clock)
    center.setLayout(centerLayout)
    layout.addWidget(center, 0, 1, alignment=Qt.AlignmentFlag.AlignCenter)

    right = QWidget()
    rightLayout = QHBoxLayout()
    rightLayout.setContentsMargins(0, 0, 0, 0)
    rightLayout.setSpacing(10)
    right.setLayout(rightLayout)

    battery = BatteryWidget() # Instantiation
    
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