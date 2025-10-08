from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QTimer, QMetaObject, Q_ARG, QEvent
from PyQt6.QtGui import QFont, QTextCursor, QColor, QPainter, QTextOption
from PyQt6.QtWidgets import (
    QWidget, QMainWindow, QApplication, QVBoxLayout, QLabel, QTextEdit,
    QTabWidget, QSizePolicy, QHBoxLayout, QPushButton, QGraphicsDropShadowEffect,
    QMessageBox
)
from apps.rayshell.core.shell import RayShell
from apps.rayshell.core.terminal import Terminal
import os, re, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))


class CRTOverlay(QWidget):
    def __init__(self, parent=None, line_spacing=5):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.line_spacing = line_spacing
        self.scanlineOffset = 0

        self.scanlineTimer = QTimer()
        self.scanlineTimer.timeout.connect(self.updateScanline)
        self.scanlineTimer.start(100)

    def updateScanline(self):
        self.scanlineOffset = (self.scanlineOffset + 1) % self.line_spacing
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(QColor(51, 53, 51, 20))
        for y in range(-self.scanlineOffset, self.height(), self.line_spacing):
            painter.drawLine(0, y, self.width(), y)
        painter.end()


class TextWidget(QTextEdit):
    commandEntered = pyqtSignal(str)

    def __init__(self, prompt="", parent=None, terminal="", font="", size=10):
        super().__init__(parent)
        self.prompt = prompt
        self.setFont(QFont(font, size))
        self.terminal = terminal

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setUndoRedoEnabled(False)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setWordWrapMode(QTextOption.WrapMode.WordWrap)

        self.crtOverlay = CRTOverlay(self)
        self.crtOverlay.resize(self.size())
        self.installEventFilter(self)

        glow = QGraphicsDropShadowEffect()
        glow.setColor(QColor(0, 25, 0))
        glow.setOffset(0, 0)
        glow.setBlurRadius(4)
        self.setGraphicsEffect(glow)

        self.loaderStates = [".", "..", "..."]
        self.loaderIndex = 0
        self.loaderActive = False
        self.loader_block_number = None

        self.loaderTimer = QTimer()
        self.loaderTimer.timeout.connect(self.updateLoader)

    def eventFilter(self, source, event):
        if source == self and event.type() == QEvent.Type.Resize:
            self.crtOverlay.resize(self.size())
        return super().eventFilter(source, event)

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
            cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
            cursor.removeSelectedText()
            self.loader_block_number = None

    def updateLoader(self):
        if not self.loaderActive or self.loader_block_number is None:
            return
        cursor = QTextCursor(self.document().findBlockByNumber(self.loader_block_number))
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()
        cursor.insertText(self.loaderStates[self.loaderIndex])
        self.loaderIndex = (self.loaderIndex + 1) % len(self.loaderStates)
        self.moveCursor(QTextCursor.MoveOperation.End)

    def keyPressEvent(self, event):
        cursor = self.textCursor()

        if cursor.blockNumber() < self.prompt_block.blockNumber():
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.setTextCursor(cursor)

        if event.key() == Qt.Key.Key_C and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if hasattr(self, "terminal") and self.terminal:
                os.write(self.terminal.masterfd, b'\x03')
            else:
                self.commandEntered.emit("__LLM_INTERRUPT__")

        elif event.key() == Qt.Key.Key_Z and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if hasattr(self, "terminal") and self.terminal:
                os.write(self.terminal.masterfd, b'\x1A')
            else:
                self.commandEntered.emit("__LLM_PAUSE__")

        if event.key() == Qt.Key.Key_Return:
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.setTextCursor(cursor)
            user_input = self.toPlainText()[self.prompt_block.position() + len(self.prompt):].strip()
            if user_input:
                self.commandEntered.emit(user_input)
                self.setReadOnly(True)
            return
        elif event.key() == Qt.Key.Key_Backspace:
            if cursor.position() <= self.prompt_block.position() + len(self.prompt):
                return
        super().keyPressEvent(event)


class ShellWindow(QWidget):
    outputReceived = pyqtSignal(str)

    def __init__(self, shell, parent=None):
        super().__init__(parent)
        self.shell = shell
        self.outputArea = TextWidget(prompt=">>> ", parent=self, font="JetBrains Mono", size=11)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.outputArea.commandEntered.connect(self.handleInput)
        layout = QVBoxLayout()
        layout.addWidget(self.outputArea)
        self.setLayout(layout)
        self.shell.addListener(self.receiveOutput)
        self.outputReceived.connect(self.displayOutput)
        initial = getattr(self.shell, "initialMsg", lambda: "")()
        if initial:
            self.displayOutput(initial)

    def handleInput(self, cmd):
        self.outputArea.startLoader()
        if cmd in ("__LLM_INTERRUPT__", "__LLM_PAUSE__"):
            self.shell.interruptLLM()
        self.shell.parseCmd(cmd)

    def receiveOutput(self, text):
        if text.startswith("__CONFIRM_COMMAND__::"):
            cmd = text.split("::", 1)[1]
            QMetaObject.invokeMethod(
                self,
                "_showConfirmDialog",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, cmd)
            )
        else:
            self.outputReceived.emit(text)

    @pyqtSlot(str)
    def _showConfirmDialog(self, cmd):
        self.outputArea.stopLoader()
        reply = QMessageBox.question(
            self,
            "Execute command?",
            f"RayShell suggests the following command:\n\n{cmd}\n\nExecute it?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.outputArea.startLoader()
            self.shell.sendCmd(cmd)
        else:
            self.displayOutput("Command execution aborted by user.\n")

    @pyqtSlot(str)
    def displayOutput(self, text):
        self.outputArea.stopLoader()
        if text.strip().startswith("[SHELL]"):
            styled = f'\n<span style="color:#c58634;">{text}</span>'
        elif text.startswith("OUTPUT:"):
            styled = f'\n<span style="color:#fff6cc;">{text}<br></span>'
        elif "error" in text.lower():
            styled = f'\n<span style="color:#fff6cc;">{text}</span>'
        else:
            styled = f'\n<span style="color:#fff6cc;">{text}</span>'
        self.outputArea.append(styled)
        self.outputArea.insertPrompt()


class TerminalWindow(QWidget):
    outputReceived = pyqtSignal(str)

    def __init__(self, terminal, parent=None):
        super().__init__(parent)
        self.terminal = terminal
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.outputArea = TextWidget(parent=self, terminal=self.terminal, font="VT323", size=18)
        self.outputArea.setStyleSheet("font-size: 25px")
        self.outputArea.commandEntered.connect(self.handleInput)
        layout = QVBoxLayout()
        layout.addWidget(self.outputArea)
        self.setLayout(layout)
        self.terminal.addListener(self.receiveOutput)
        self.outputReceived.connect(self.displayOutput)

    def clean_ansi(self, text):
        ansi_escape = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')
        return ansi_escape.sub('', text)

    def handleInput(self, cmd):
        self._lastCmd = cmd
        self.terminal.sendCmd(cmd + '\n')

    def receiveOutput(self, text):
        if text.rstrip() == getattr(self, "_lastCmd", None):
            return
        self.outputReceived.emit(text)

    @pyqtSlot(str)
    def displayOutput(self, text):
        text = self.clean_ansi(text)
        text = text.rstrip("\n")
        self.outputArea.insertPlainText(text)
        self.outputArea.insertPrompt()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        mainWidget = QWidget()

        mainWidget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)
        self.setWindowTitle("rayshell")
        self.tabBar = QTabWidget()
        self.rayShellWindow = ShellWindow(RayShell())
        self.terminalWindow = TerminalWindow(Terminal())
        self.tabBar.addTab(self.rayShellWindow, "RayShell")
        self.tabBar.addTab(self.terminalWindow, "Terminal")
        self.rayShellWindow.outputArea.setObjectName("outputArea")
        self.terminalWindow.outputArea.setObjectName("outputArea")
        mainLayout.addWidget(self.tabBar)
        mainWidget.setLayout(mainLayout)
        self.setCentralWidget(mainWidget)
        mainWidget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'crtOverlay'):
            self.crtOverlay.resize(self.centralWidget().size())

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
        # globalPosition() returns QPointF, convert to QPoint
            self.dragPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(self.pos() + event.globalPosition().toPoint() - self.dragPos)
            self.dragPos = event.globalPosition().toPoint()
            event.accept()


if __name__ == "__main__":
    app = QApplication([])
    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(__file__)
    style_file = os.path.join(base_path, "style.css")
    if os.path.exists(style_file):
        with open(style_file, "r") as f:
            app.setStyleSheet(f.read())
    window = MainWindow()
    window.resize(800, 500)
    window.show()
    app.exec()
