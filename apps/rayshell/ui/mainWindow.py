from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QTimer, QMetaObject, Q_ARG
from PyQt5.QtGui import QFont, QTextCursor, QColor
from PyQt5.QtWidgets import (
    QWidget, QMainWindow, QApplication, QVBoxLayout, QLabel, QTextEdit,
    QTabWidget, QSizePolicy, QHBoxLayout, QPushButton, QGraphicsDropShadowEffect,
    QMessageBox
)
from apps.rayshell.core.shell import RayShell
from apps.storyEngine.engine import Main
from apps.rayshell.core.terminal import Terminal
import os, re

class TextWidget(QTextEdit):
    commandEntered = pyqtSignal(str)

    def __init__(self, prompt="", parent=None):
        super().__init__(parent)
        self.prompt = prompt
        self.setFont(QFont("JetBrains Mono", 11))
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setUndoRedoEnabled(False)
        self.setWordWrapMode(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.loaderStates = [".", "..", "..."]
        self.loaderIndex = 0
        self.loaderActive = False
        self.loader_block_number = None

        self.loaderTimer = QTimer()
        self.loaderTimer.timeout.connect(self.updateLoader)
        # self.insertPrompt()

    def insertPrompt(self):
        self.append(self.prompt)
        self.prompt_block = self.document().lastBlock()
        self.setReadOnly(False)

    def startLoader(self):
        if self.loaderActive:
            return
        self.loaderActive = True
        self.append("") 
        self.loader_block_number = self.document().blockCount() - 1
        self.loaderIndex = 0
        self.updateLoader()
        self.loaderTimer.start(500)

    def stopLoader(self):
        self.loaderTimer.stop()
        self.loaderActive = False
        if self.loader_block_number is not None:
            block = self.document().findBlockByNumber(self.loader_block_number)
            cursor = QTextCursor(block)
            cursor.select(QTextCursor.BlockUnderCursor)
            cursor.removeSelectedText()
            self.loader_block_number = None

    def updateLoader(self):
        if not self.loaderActive or self.loader_block_number is None:
            return

        cursor = QTextCursor(self.document().findBlockByNumber(self.loader_block_number))
        cursor.movePosition(QTextCursor.StartOfBlock)
        cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)
        cursor.removeSelectedText()
        cursor.insertText(self.loaderStates[self.loaderIndex])
        
        self.loaderIndex = (self.loaderIndex + 1) % len(self.loaderStates)

        self.moveCursor(QTextCursor.End)

    def keyPressEvent(self, event):
        cursor = self.textCursor()
        
        if cursor.blockNumber() < self.prompt_block.blockNumber():
            cursor.movePosition(QTextCursor.End)
            self.setTextCursor(cursor)

        if event.key() == Qt.Key_Return:
            cursor.movePosition(QTextCursor.End)
            self.setTextCursor(cursor)
            user_input = self.toPlainText()[self.prompt_block.position() + len(self.prompt):].strip()
            if user_input:
                self.commandEntered.emit(user_input)
                self.setReadOnly(True)
            return

        elif event.key() == Qt.Key_Backspace:
            if cursor.position() <= self.prompt_block.position() + len(self.prompt):
                return

        super().keyPressEvent(event)

class ShellWindow(QWidget):
    outputReceived = pyqtSignal(str)

    def __init__(self,shell,parent=None):
        super().__init__(parent)
        self.shell=shell
        self.outputArea = TextWidget(parent=self)
        self.outputArea.commandEntered.connect(self.handleInput)
        layout=QVBoxLayout()
        layout.addWidget(self.outputArea)
        self.setLayout(layout)
        self.shell.addListener(self.receiveOutput)
        self.outputReceived.connect(self.displayOutput)
        initial = getattr(self.shell,"initialMsg",lambda:"")()
        if initial:
            self.displayOutput(initial)

    def handleInput(self,cmd):
        self.outputArea.startLoader()
        self.shell.parseCmd(cmd)

    def receiveOutput(self,text):
        if text.startswith("__CONFIRM_COMMAND__::"):
            cmd = text.split("::",1)[1]
            QMetaObject.invokeMethod(self,"_showConfirmDialog",Qt.QueuedConnection,Q_ARG(str,cmd))
        else:
            self.outputReceived.emit(text)

    @pyqtSlot(str)
    def _showConfirmDialog(self, cmd):
        self.outputArea.stopLoader()
        reply = QMessageBox.question(
            self,
            "Execute command?",
            f"RayShell suggests the following command:\n\n{cmd}\n\nExecute it?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.outputArea.startLoader()
            self.shell.sendCmd(cmd)
        else:
            self.displayOutput("Command execution aborted by user.\n")

    @pyqtSlot(str)
    def displayOutput(self,text):
        self.outputArea.stopLoader()
        self.outputArea.append(text)
        self.outputArea.insertPrompt()

class TerminalWindow(QWidget):
    outputReceived = pyqtSignal(str)

    def __init__(self,terminal,parent=None):
        super().__init__(parent)
        self.terminal=terminal
        self.outputArea=TextWidget(parent=self)
        self.outputArea.commandEntered.connect(self.handleInput)
        layout=QVBoxLayout()
        layout.addWidget(self.outputArea)
        self.setLayout(layout)
        self.terminal.addListener(self.receiveOutput)
        self.outputReceived.connect(self.displayOutput)
        
    def clean_ansi(self, text):
        ansi_escape = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')
        return ansi_escape.sub('', text)
    
    def handleInput(self,cmd):
        self._lastCmd = cmd
        self.terminal.sendCmd(cmd+'\n')

    def receiveOutput(self,text):
        if text.strip() == getattr(self, "_lastCmd", None):
            return
        self.outputReceived.emit(text)

    @pyqtSlot(str)
    def displayOutput(self,text):
        text = self.clean_ansi(text)
        # text = text.rstrip("\n") 
        self.outputArea.insertPlainText(text)
        self.outputArea.insertPrompt()

class CustomTitleBar(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setFixedHeight(30)
        # self.setStyleSheet("background-color:#1e1e1e;")
        layout=QHBoxLayout()
        layout.setContentsMargins(10,0,10,0)
        self.titleLabel=QLabel("RayShell 1.01")
        self.titleLabel.setFont(QFont("JetBrains Mono",11))
        self.titleLabel.setStyleSheet("color:#ce92ff;")
        glow = QGraphicsDropShadowEffect()
        glow.setColor(QColor(255,13,186))
        glow.setOffset(0,0)
        glow.setBlurRadius(15)
        self.titleLabel.setGraphicsEffect(glow)
        layout.addWidget(self.titleLabel)
        layout.addStretch()
        self.btnMin = QPushButton("-")
        self.btnClose = QPushButton("x")
        for btn in [self.btnMin,self.btnClose]:
            btn.setFixedSize(30,30)
            btn.setStyleSheet("color:#ce92ff;background-color:transparent;border:none;")
        self.btnClose.clicked.connect(parent.close)
        self.btnMin.clicked.connect(parent.showMinimized)
        layout.addWidget(self.btnMin)
        layout.addWidget(self.btnClose)
        self.setLayout(layout)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        mainWidget=QWidget()
        mainLayout=QVBoxLayout()
        mainLayout.setContentsMargins(0,0,0,0)
        mainLayout.setSpacing(0)
        self.titleBar=CustomTitleBar(self)
        mainLayout.addWidget(self.titleBar)
        self.tabBar=QTabWidget()
        self.rayShellWindow=ShellWindow(RayShell())
        self.terminalWindow=TerminalWindow(Terminal())
        self.tabBar.addTab(self.rayShellWindow,"RayShell")
        self.tabBar.addTab(self.terminalWindow,"Terminal")
        mainLayout.addWidget(self.tabBar)
        mainWidget.setLayout(mainLayout)
        self.setCentralWidget(mainWidget)

    def mousePressEvent(self,event):
        if event.button()==Qt.LeftButton:
            self.dragPos=event.globalPos()

    def mouseMoveEvent(self,event):
        if event.buttons()==Qt.LeftButton:
            self.move(self.pos()+event.globalPos()-self.dragPos)
            self.dragPos=event.globalPos()
            event.accept()

if __name__=="__main__":
    app=QApplication([])
    style_file = os.path.join(os.path.dirname(__file__), "style.css")
    if os.path.exists(style_file):
        with open(style_file,"r") as f:
            app.setStyleSheet(f.read())
    window=MainWindow()
    window.resize(800,500)
    window.show()
    app.exec_()
