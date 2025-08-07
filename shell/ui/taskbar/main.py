#!/usr/bin/env python3

import os,sys
os.environ.setdefault("QT_QPA_PLATFORM", "wayland") 

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QWidget,QGridLayout, QSizePolicy, QLabel, QPushButton, QHBoxLayout
from PyQt5.QtGui import QFont, QPixmap, QIcon
from widgets.clock import ClockWidget
from widgets.battery import BatteryWidget
from widgets.workspaces import WorkspaceWidget
from widgets.cpu import CpuWidget
from widgets.memory import MemWidget

app = QApplication(sys.argv)
main = QWidget()
main.setWindowTitle("taskbar")
app.force_quit = False

main.setWindowFlags(
    Qt.FramelessWindowHint |
    Qt.WindowStaysOnTopHint |
    Qt.Tool
)

layout = QGridLayout()

screen = app.primaryScreen()
geo = screen.geometry()
screenheight = geo.height()
bar = 30

main.setFixedSize(geo.width(), 30)
main.move(0, 0)

main.setStyleSheet("background-color: rgba(68, 64, 68, 0); border: 0px")

font = QFont("Jetbrains mono", 10)
# font.setBold(True)
app.setFont(font)

layout.setContentsMargins(6, 0, 6, 0)
layout.setSpacing(0)
main.setLayout(layout)

left = QWidget()
leftLayout = QHBoxLayout()
leftLayout.setContentsMargins(0,0,0,0)
leftLayout.setSpacing(10)
left.setLayout(leftLayout)
work = WorkspaceWidget()
# work.setFixedWidth()
leftLayout.addWidget(work)
layout.addWidget(left, 0, 0, alignment=Qt.AlignLeft)



center = QWidget()
centerLayout = QHBoxLayout()
centerLayout.setContentsMargins(0,0,0,0)
centerLayout.setSpacing(6)
clock = ClockWidget()
clock.setFixedHeight(25)

# clock.adjustSize()
centerLayout.addWidget(clock)
layout.addWidget(center, 0, 1, alignment=Qt.AlignCenter)
center.setLayout(centerLayout)

# layout.addWidget(ClockWidget())

# layout.addStretch(1)

right = QWidget()
rightLayout = QHBoxLayout()
rightLayout.setContentsMargins(0,0,0,0)
rightLayout.setSpacing(10)
# rightLayout.setSpacing(6)
right.setLayout(rightLayout)
battery = BatteryWidget()
cpu = CpuWidget()
# cpu.setMargin()
battery.setFixedHeight(24)
cpu.setFixedHeight(24)
mem = MemWidget()
mem.setFixedHeight(24)
layout.addWidget(right, 0, 2, alignment=Qt.AlignRight)

rightLayout.addWidget(mem)

rightLayout.addWidget(cpu)
rightLayout.addWidget(battery)
# layout.addStretch(1)




main.setFocusPolicy(Qt.NoFocus)
previousFocus = None

def on_focus_changed(old, new):
    global previous_focus
    if new is main or (hasattr(new, 'parent') and new.parent() is main):
        if old:
            old.setFocus()

QApplication.instance().focusChanged.connect(on_focus_changed)



main.show()
app.exec_()