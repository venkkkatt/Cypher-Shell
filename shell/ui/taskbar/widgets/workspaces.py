import json, subprocess
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtWidgets import QLabel, QWidget, QHBoxLayout

class WsEvListener(QThread):
    wsChanged = pyqtSignal()

    def run(self):
        p = subprocess.Popen(
            ["hyprctl", "-s"], stdout=subprocess.PIPE, text=True, bufsize=1
        )
        for line in p.stdout:
            line = line.strip()
            if not line:
                continue
            if (
                line.startswith("workspace>>")
                or line.startswith("createworkspace>>")
                or line.startswith("destroyworkspace>>")
                or line.startswith("focusedmon>>")
                or line.startswith("moveworkspace>>")
                or line.startswith("activewindow>>")
            ):
                self.wsChanged.emit()


class WorkspaceLabel(QLabel):
    def __init__(self, name, isActive):
        super().__init__("●" if isActive else "○")
        self.name = name
        self.setMargin(5)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.updateStyle(isActive)

    def updateStyle(self, active):
        if active:
            self.setText("●")
            self.setStyleSheet("""
                color: #b7efc5;
                font-size:12px;
                padding: 0px 10px;
                margin: 0px;
                background: transparent;
                border-left: 1px solid #111d1370;
            """)
        else:
            self.setText("○")
            self.setStyleSheet("""
                color: #05668d;
                font-size:12px;
                padding: 0px 10px;
                margin: 0px;
                background: transparent;
                border-left: 1px solid #111d1370;
            """)

    def mousePressEvent(self, ev):
        subprocess.Popen(["hyprctl", "dispatch", "workspace", self.name])
        super().mousePressEvent(ev)


class WorkspaceWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 6, 0, 6)
        self.layout.setSpacing(4)
        self.setLayout(self.layout)
        self.labels = {}
        self.wsRefresh()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.wsRefresh)
        self.timer.start(500)

    def getWSdata(self):
        try:
            raw = subprocess.check_output(["hyprctl", "workspaces", "-j"], text=True)
            return json.loads(raw)
        except:
            return []

    def getActive(self):
        try:
            raw = subprocess.check_output(["hyprctl", "activeworkspace", "-j"], text=True)
            return json.loads(raw).get("name")
        except:
            return None

    def wsRefresh(self):
        wsList = self.getWSdata()
        names = []
        active = self.getActive()

        for ws in wsList:
            name = ws.get("name") or str(ws.get("id"))
            names.append(name)

        for old in list(self.labels.keys()):
            if old not in names:
                lbl = self.labels.pop(old)
                self.layout.removeWidget(lbl)
                lbl.deleteLater()

        for name in names:
            isActive = (name == active)
            if name in self.labels:
                self.labels[name].updateStyle(isActive)
            else:
                lbl = WorkspaceLabel(name, isActive)
                self.labels[name] = lbl
                self.layout.addWidget(lbl)
