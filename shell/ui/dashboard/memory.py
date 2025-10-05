#!/usr/bin/env python3

import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import psutil

class MemWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._mem_usage = 0.0
        self.initUI()
        # self.setupTimer()
        
    def initUI(self):
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnBottomHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowDoesNotAcceptFocus |
            Qt.WindowType.Tool
        )
        
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(200, 120)
        
        self.setStyleSheet("""
            background-color: #00FF41;
    
            QLabel {
                color: black;
                background-color: transparent;
            }
            QProgressBar {
                border: 1px solid #00FF41;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: transparent;
            }
        """)
        
        layout = QVBoxLayout()
        # layout.setContentsMargins(20, 20, 20, 20)
        # layout.setSpacing(10)
        
        self.title_label = QLabel("RAM")
        self.title_label.setFixedHeight(30)

        title_font = QFont("OCR A", 17)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.mem_label = QLabel("0%")
        mem_font = QFont("OCR A", 20)
        self.mem_label.setFixedHeight(60)
        self.mem_label.setFont(mem_font)
        self.mem_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        
        layout.addWidget(self.title_label)
        layout.addWidget(self.mem_label)
        layout.addWidget(self.progress_bar)
        
        self.setLayout(layout)
        
    # def setupTimer(self):
    #     self.timer = QTimer()
    #     self.timer.timeout.connect(self.updateMemUsage)
    #     self.timer.start(1000) 
    #     self.updateMemUsage()
    
    def updateMemUsage(self):
        try:
            usage = int(psutil.virtual_memory().percent)
            self._mem_usage = usage
            
            self.mem_label.setText(f"{usage}%")
            self.progress_bar.setValue(usage)
            
            color = self.getMemColor(usage)
            self.mem_label.setStyleSheet("color: black;")
            
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
            
            self.setWindowOpacity(0.7 if usage > 80 else 0.85)
                
        except Exception as e:
            print(f"Error reading mem usage: {e}")
    
    def getMemColor(self, usage):
        return "#23D300" if usage < 60 else "#FF5024"

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("memdash")
    app.setApplicationDisplayName("memdash")
    
    widget = MemWidget()
    widget.setWindowTitle("memdash")
    widget.setProperty("class", "memdash")
    
    widget.show()
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
