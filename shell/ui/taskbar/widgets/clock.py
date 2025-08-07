from PyQt5.QtCore import QTime, QTimer
from PyQt5.QtWidgets import QLabel

class ClockWidget(QLabel):
    def __init__(self):
        super().__init__()
        self.setMargin(5)

        self.setStyleSheet("color:#ce92ff; padding : 0px 5px; border: 1px solid #90b388eb; border-radius:1%;  background-color: rgba(68, 64, 68, 0.256); font-size:13px")

        self.updateTime()

        timer = QTimer(self)
        timer.timeout.connect(self.updateTime)
        timer.start(1000)

        
    def updateTime(self):
        now = QTime.currentTime()
        self.setText(now.toString("HH:mm"))
