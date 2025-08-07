from PyQt5.QtCore import Qt, QProcess, pyqtSignal
from PyQt5.QtGui import QFont, QTextCursor
from PyQt5.QtWidgets import QWidget, QApplication , QLabel, QHBoxLayout, QVBoxLayout, QLineEdit, QPlainTextEdit
import sys,re
sys.path.append('/usr/lib/python3.13/site-packages')
# import QTermWidget
# from pyqterm import QTermWidget
# Qtermwidget = sip.import_module('QTermWidget')
from apps.rayshell.core.shell import RayShell

class MainWindow(QWidget):
    outputRecieved = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.setWindowTitle("rayshell")
        layout = QVBoxLayout()

        self.inputLine = QLineEdit()
        self.inputLine.returnPressed.connect(self.handleInput)
        self.inputLine.setFont(QFont("JetBrains Mono", 11))

        layout.addWidget(self.inputLine)

        self.outputArea = QPlainTextEdit()
        self.outputArea.setFont(QFont("JetBrains Mono", 11))

        self.outputArea.setReadOnly(True)
        layout.addWidget(self.outputArea)

        self.setLayout(layout)

        self.shell = RayShell()

        self.shell.addListener(self.OnOutput)

        self.outputRecieved.connect(self.displayOutput)

    def handleInput(self):
        cmd = self.inputLine.text()
        self.shell.parseCmd(cmd + "\n")
        self.inputLine.clear()

    def OnOutput(self,text):
        self.outputRecieved.emit(text)

    def displayOutput(self, text):
        clean_text = self.ESC_SEQ.sub('', self.ansi_escape.sub('', text))
        self.outputArea.moveCursor(QTextCursor.End)
        self.outputArea.insertPlainText(clean_text)
        self.outputArea.moveCursor(QTextCursor.End)

    def close(self, event):
        self.shell.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    terminal = MainWindow()
    terminal.resize(800,500)
    terminal.show()
    sys.exit(app.exec_())

