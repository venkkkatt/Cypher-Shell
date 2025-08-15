from PyQt5.QtCore import Qt, QProcess, pyqtSignal, QTimer, QMetaObject, Q_ARG, pyqtSlot
from PyQt5.QtGui import QFont, QTextCursor, QColor, QTextCharFormat, QMovie
from PyQt5.QtWidgets import QWidget, QMainWindow ,QApplication ,QMenu, QMenuBar, QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QLineEdit, QTextEdit, QSizePolicy, QStackedWidget, QGridLayout, QTabBar, QTabWidget, QMessageBox

import sys,re,os, random, time
# import apps.rayshell.ui.s
from apps.rayshell.core.shell import RayShell
from apps.storyEngine.engine import Main
from apps.rayshell.core.terminal import Terminal

class TerminalWindow(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        text = QLabel("this is terminal")
        layout.addWidget(text)
        self.setLayout(layout)

class RayWindow(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        text = QLabel("Chat With me")
        layout.addWidget(text)
        self.setLayout(layout)

        inputLayout = QVBoxLayout()

        # inputLayout.addWidget(self.userName)

        self.inputLine = QLineEdit()
        # self.inputLine.returnPressed.connect(self.handleInput)
        self.inputLine.setPlaceholderText("What'd you want to execute now?")
        # self.inputLine.textChanged.connect(self.toggleSendBtn)

        self.inputLine.setFont(QFont("JetBrains Mono", 11))
        
        inputLayout.addWidget(self.inputLine)

        self.sendBtn = QPushButton("Enter")
        self.sendBtn.setEnabled(False)
        self.sendBtn.setFont(QFont("JetBrains Mono", 11))

        # self.sendBtn.clicked.connect(self.handleInput)

        inputLayout.addWidget(self.sendBtn)
        layout.addLayout(inputLayout)

class RayshellWindow(QWidget):
    outputRecieved = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.mode = "rayshell"

        self.effect1 = QGraphicsOpacityEffect()
        self.glowEffect = QGraphicsDropShadowEffect()
        self.glowEffect.setColor(QColor(255, 13, 186))
        self.glowEffect.setOffset(0,0)
        self.glowEffect.setBlurRadius(200)

        self.outputArea = TextWidget(self)
        # self.outputArea.setGraphicsEffect(self.glowEffect)
        self.outputArea.setFont(QFont("JetBrains Mono", 11))
        self.outputArea.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        # self.loader.setParent(self.outputArea.viewport())
        # self.loader.move(5, 5)
        layout = QVBoxLayout()
        # self.outputArea.setReadOnly(True)
        layout.addWidget(self.outputArea)
        self.setLayout(layout)
        # layout.addWidget(self.loader)

        self.shell = RayShell()
        self.engine = Main()
        self.terminal = Terminal()
        self.shell.addListener(self.OnOutput)
        self.engine.addListener(self.OnOutput)
        if self.mode == "terminal":
            self.terminal.addListener(self.OnOutput)
        self.outputRecieved.connect(self.displayOutput)  

    def setMode(self, mode):
        self.mode = mode
        # if mode == "ray":
        #     self.outputArea()

    def loading(pt):
            for i in ['.','..','...']:
                sys.stdout.write(f"\rLoading{i}   ")
                sys.stdout.flush()
                time.sleep(0.5) 

    def glitch(self):
        return random.choice(['█', '▓', '░', '#', '/', '\\', '|', '*', '-', '0', '1'])
    
    def typeW(self):
        if self.idx < len(self.text):
            self.widget.moveCursor(QTextCursor.End)
            self.widget.insertPlainText(self.text[self.idx])
            self.idx+=1
        else:
            self.timer.stop()
            self.widget.moveCursor(QTextCursor.End)
            self.widget.insertPlainText('\n')
            if self.addCallback:
                self.addCallback()
                
    def typeWriterEffect(self, widget, text, onFinished):
        self.text = text
        self.widget = widget
        self.idx = 0
        self.addCallback = onFinished
        self.widget.insertPlainText('\n')
        self.timer = QTimer()
        self.timer.timeout.connect(self.typeW)
        self.timer.start(30)
    
    def styled(self, text):
        return f'<span style="color:#ce92ff; text-shadow: 0 0 4px #ce92ff, 0 0 8px #ce92ff, 0 0 16px #ff0aff;">{text}</span>'

    def flicker(self):
        self.effect1.setOpacity(random.uniform(0.85, 1.0))

    def handleInput(self, cmd):
        self.outputArea.loader.setVisible(True)
        self.outputArea.loaderMovie.start()
        if self.mode == "ray":
            self.engine.interCept(cmd)
        elif self.mode == "rayshell":
            self.shell.parseCmd(cmd)
        else:
            self.terminal.sendCmd(cmd)

    def OnOutputTerminal(self, text):
        self.outputRecieved.emit(text)
        
    def OnOutput(self,text):
        if text.startswith("__CONFIRM_COMMAND__::"):
            bash_cmd = text.split("::", 1)[1]
            QMetaObject.invokeMethod(
                self,
                "_showConfirmDialog",
                Qt.QueuedConnection,
                Q_ARG(str, bash_cmd)
            )
        else:
            self.outputRecieved.emit(text)

    @pyqtSlot(str)
    def _showConfirmDialog(self, cmd):
        reply = QMessageBox.question(
            self,
            "Execute command?",
            f"RayShell suggests the following command:\n\n{cmd}\n\nExecute it?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.shell.sendCmd(cmd)
        else:
            self.displayOutput("Command execution aborted by user.\n")
    
    def displayOutput(self, text):
        self.outputArea.loaderMovie.stop()
        self.outputArea.loader.setVisible(False)
        self.outputArea.moveCursor(QTextCursor.End)
        self.typeWriterEffect(self.outputArea, text, self.outputArea.addPrompt)
        # self.outputArea.insertPlainText('\n'+text)
        
        self.outputArea.moveCursor(QTextCursor.End)
        self.outputArea.setReadOnly(False)
        # self.outputArea.addPrompt()

    def close(self, event):
        self.shell.close()
        event.accept()

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.navbar = QHBoxLayout()
        self.navbar.setSpacing(10)
        self.navbar.setContentsMargins(0,0,0,0)

        self.tabBar = QTabWidget()
        self.tabBar.setTabPosition(QTabWidget.North)
        self.tabBar.setMovable(False)
        self.tabBar.setTabsClosable(False)
        self.tabBar.setDocumentMode(True)

        self.RWS = RayshellWindow()
        self.RWE = RayshellWindow()
        self.RWT = RayshellWindow()
        initialMsg = self.RWS.shell.initialMsg()
        self.RWS.displayOutput(initialMsg)

        self.tabBar.addTab(self.RWS, "RayShell")
        self.tabBar.addTab(self.RWE, "Ray")
        self.tabBar.addTab(self.RWT, "Terminal")

        self.RWS.setMode("rayshell")
        self.RWE.setMode("ray")
        self.RWT.setMode("terminal")

        self.setWindowTitle("rayshell")
        self.menu = self.menuBar()
        self.menu.addMenu("RayShell 1.01")
        layout = QVBoxLayout()
       
        mainWidget = QWidget()
        mainWidget.setLayout(layout)
        layout.addWidget(self.tabBar)
        # layout.addWidget(self.stack)
        self.setCentralWidget(mainWidget)
        self.shell = RayShell()
        self.tabBar.currentChanged.connect(self.onTabChanged)

    def onTabChanged(self, idx):
        if idx == 0:
            self.currentMode = "rayshell"
        elif idx == 1:
            self.currentMode = "ray"
            initialMsg = self.RWE.engine.rayshell.initialMsg()
            if initialMsg:
                self.RWE.displayOutput(initialMsg)
        else:
            self.currentMode = "terminal"

class TextWidget(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setUndoRedoEnabled(False)
        self.setWordWrapMode(True)
        self.prompt = ">>> "
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.insertHtml(self.parent.styled(self.prompt))
        self.prompt_position = self.textCursor().position()
        self.setFocus()

        self.loader = QLabel(self)
        self.loader.setAlignment(Qt.AlignCenter)
        self.loaderMovie = QMovie("/home/venkat/cypher-shell/assets/loading.gif")
        self.loader.setMovie(self.loaderMovie)
        self.loader.setVisible(False)
        self.loader.setStyleSheet("background-color: transparent;")
        self.loader.setFixedSize(64,64)
        self.loader.move(
            (self.viewport().width() - self.loader.width()) // 2,
            (self.viewport().height() - self.loader.height()) // 2
        )
        self.loader.raise_()


    def keyPressEvent(self, event):
        cursor = self.textCursor()

        if cursor.position() < self.prompt_position:
            cursor.setPosition(self.document().characterCount() - 1)
            self.setTextCursor(cursor)

        if event.key() == Qt.Key_Backspace:
            if cursor.position() <= self.prompt_position:
                return 
        elif event.key() in (Qt.Key_Up, Qt.Key_Down, Qt.Key_Left):
            if cursor.position() <= self.prompt_position:
                return 
        elif event.key() == Qt.Key_Return:
            cursor.movePosition(QTextCursor.End)
            self.setTextCursor(cursor)
            user_input = self.toPlainText()[self.prompt_position:].strip()
            if user_input:
                self.insertPlainText('')
                self.parent.handleInput(user_input) 
                self.setReadOnly(True)  
            return
        super().keyPressEvent(event)

    def addPrompt(self):
        # self.insertPlainText('\n')
        # self.insertPlainText(self.prompt)
        self.insertHtml('<br>' + self.parent.styled(self.prompt))
        self.prompt_position = self.document().characterCount() - 1
        self.setReadOnly(False)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    style = os.path.join(os.path.dirname(__file__), "style.css")
    with open(style, "r") as file:
            app.setStyleSheet(file.read())
    terminal = MainWindow()
    terminal.resize(800,500)
    terminal.show()
    sys.exit(app.exec_())


