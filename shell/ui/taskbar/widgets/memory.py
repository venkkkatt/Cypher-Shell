from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QLabel
import psutil

class MemWidget(QLabel):
    def __init__(self):
        super().__init__()

        self.setStyleSheet("color:#ce92ff; padding : 0px 5px; border: 1px solid rgba(255, 156, 255, 0.273); border-radius: 0%;background-color: rgba(68, 64, 68, 0.256);")
        psutil.virtual_memory()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(1000)
        self.refresh()

    def refresh(self):
        usage = psutil.virtual_memory()

    
        self.setText(f"MEM:{usage.percent:.0f}%")


