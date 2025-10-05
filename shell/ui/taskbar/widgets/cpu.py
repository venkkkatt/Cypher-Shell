# from PyQt6.QtCore import QTimer
# from PyQt6.QtWidgets import QLabel
# import psutil

# class CpuWidget(QLabel):
#     def __init__(self):
#         super().__init__()

#         self.setStyleSheet("""
#             color: #ce92ff;
#             padding: 0px 4px;
#             border: 1px solid rgba(255, 156, 255, 0.273);
#             border-radius: 1%;
#             background-color: rgba(68, 64, 68, 0.256);
#         """)

#         psutil.cpu_percent(interval=None)
#         self.timer = QTimer(self)
#         self.timer.timeout.connect(self.refresh)
#         self.timer.start(1000)
#         self.refresh()

#     def refresh(self):
#         usage = psutil.cpu_percent(interval=None)
#         self.setText(f"CPU:{usage:.0f}%")
