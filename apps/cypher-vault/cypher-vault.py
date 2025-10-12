#!/usr/bin/env python3
import sys,os,json,shutil,stat
from pathlib import Path
from datetime import datetime

try:
    from send2trash import send2trash
    HAS_SEND2TRASH = True
except Exception:
    HAS_SEND2TRASH = False

from PyQt6.QtCore import Qt, QDir, QUrl, QSortFilterProxyModel, QSize
from PyQt6.QtGui import QIcon, QAction, QKeySequence, QDesktopServices, QPixmap, QFileSystemModel, QColor
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTreeView, QListWidget, QListWidgetItem,
    QSplitter, QVBoxLayout, QHBoxLayout, QToolBar, QLineEdit, QLabel, QPushButton,
    QMessageBox, QInputDialog, QMenu, QFileDialog, QTextEdit, QDialog, QFormLayout,
    QDialogButtonBox, QProgressDialog, QStyle, QStatusBar
)

APP_DIR = Path.home() / ".config" / "cypher-vault"
CONFIG_FILE = APP_DIR / "cypher-vault.json"

DEFAULT_CONFIG = {
    "theme": "cyberpunk",
    "font_family": "Jetbrains Mono",
    "font_size_pt": 10,
    "colors": {
        "background": "#0B0F14",
        "panel": "#0E1620",
        "accent": "#AFFE85", 
        "muted": "#9AA3B2",
        "panel_alt": "#101521",
        "highlight": "#6FFF00",
        "file_bg": "#0C1116",
        "text": "#E6EEF3",
        "separator": "#3A404A"
    },
    "preview": {
        "max_image_dim": 1024,
        "text_preview_lines": 400
    },
    "sidebar": ["Home", "Desktop", "Documents", "Downloads", "Trash", "Pictures", "Music", "Videos"]
}

def load_config():
    if not APP_DIR.exists():
        try:
            APP_DIR.mkdir(parents=True, exist_ok=True)
        except Exception:
            print(f"Warning: Could not create config directory {APP_DIR}. Using default settings.")
            return DEFAULT_CONFIG.copy()

    if not CONFIG_FILE.exists():
        with open(CONFIG_FILE, "w", encoding="utf-8") as fh:
            json.dump(DEFAULT_CONFIG, fh, indent=4)
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as fh:
            cfg = json.load(fh)
        for k, v in DEFAULT_CONFIG.items():
            if k not in cfg:
                cfg[k] = v
            elif isinstance(v, dict):
                for kk, vv in v.items():
                    if kk not in cfg[k]:
                        cfg[k][kk] = vv
            elif k == "sidebar":
                for item in DEFAULT_CONFIG["sidebar"]:
                    if item not in cfg["sidebar"]:
                         cfg["sidebar"].append(item)
        return cfg
    except Exception:
        return DEFAULT_CONFIG.copy()

def stylesheet_from_config(cfg: dict) -> str:
    c = cfg["colors"]
    fam = cfg.get("font_family", "Roboto Mono")
    size = cfg.get("font_size_pt", 10)
    
    accent_color = QColor(c['accent'])
    
    luma = accent_color.lightness() / 255.0 

    contrasting_text_color = "#070707" if luma > 0.5 else c['text']
    
    return f"""
    QWidget {{
        background-color: {c['background']};
        color: {c['text']};
        font-family: "{fam}";
        font-size: {size}pt;
    }}
    
    QTreeView, QListWidget {{
        background-color: {c['panel']};
        alternate-background-color: {c['panel_alt']};
        color: {c['text']};
        border: 1px solid {c['separator']};
        border-radius: 4px;
        outline: none;
    }}
    
    QTreeView {{
        selection-background-color: {c['accent']};

        selection-color: {contrasting_text_color};
    }}
    
    QTreeView::item:selected {{
        color: {contrasting_text_color};
        /* Ensure background is covered by the QTreeView rule above */
        background-color: {c['accent']};
    }}
    
    QTreeView::item {{
        padding: 6px 4px;
        min-height: 40px;
    }}
    QTreeView::branch {{
        background: {c['panel']};
    }}
    
    QListWidget {{
        border: none;
        border-right: 1px solid {c['separator']};
        background-color: {c['panel_alt']};
    }}
    QListWidget::item {{
        height: 40px;
        border-bottom: 1px dashed {c['separator']};
        padding: 8px 10px;
    }}
    QListWidget::item:selected {{
        color: {c['highlight']};
        background-color: {c['background']}90;
        border-left: 3px solid {c['highlight']}; 
        margin-left: -1px;
    }}

    QLineEdit {{
        background-color: {c['file_bg']};
        border: 1px solid {c['muted']};
        padding: 6px;
        border-radius: 4px;
        color: {c['text']};
    }}
    QPushButton {{
        background-color: {c['accent']}30; 
        border: 1px solid {c['accent']};
        color: {c['highlight']};
        padding: 6px 10px;
        border-radius: 3px;
    }}

    QToolBar {{
        background: {c['panel_alt']};
        border-bottom: 1px solid {c['separator']};
        spacing: 6px;
        padding: 4px;
    }}
    QToolBar QAction, QToolButton {{
        padding: 4px;
        margin: 2px;
        border-radius: 2px;
    }}
    QToolBar QToolButton:hover {{
        background: {c['accent']}40;
    }}

    QStatusBar {{
        background-color: {c['panel_alt']};
        color: {c['muted']};
        padding: 4px;
        border-top: 1px solid {c['separator']};
    }}
    QLabel#headerLabel {{
        color: {c['highlight']};
        font-weight: bold;
        padding-bottom: 4px;
    }}
    QSplitter::handle {{
        background-color: {c['separator']};
        width: 3px;
    }}
    """

class PropertiesDialog(QDialog):
    def __init__(self, path: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Properties")
        self.path = path
        self.resize(460, 300)

        layout = QFormLayout(self)
        p = Path(path)
        layout.addRow("Name:", QLabel(p.name))
        layout.addRow("Path:", QLabel(str(p.absolute()))) 
        
        try:
            statr = p.stat()
            layout.addRow("Size:", QLabel(f"{statr.st_size:,} bytes" if p.is_file() else "-")) 
            layout.addRow("Type:", QLabel("Directory" if p.is_dir() else "File"))
            layout.addRow("Permissions:", QLabel(self._perm_string(statr.st_mode)))
            layout.addRow("Modified:", QLabel(datetime.fromtimestamp(statr.st_mtime).strftime("%Y-%m-%d %H:%M:%S")))
            layout.addRow("Created:", QLabel(datetime.fromtimestamp(statr.st_ctime).strftime("%Y-%m-%d %H:%M:%S")))
        except Exception as e:
            layout.addRow("Info:", QLabel(f"Failed to read file status: {type(e).__name__}"))

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        btns.accepted.connect(self.accept)
        layout.addWidget(btns)

    def _perm_string(self, mode):
        is_dir = 'd' if stat.S_ISDIR(mode) else '-'
        perms_str = []
        for i in range(9):
            if i % 3 == 0:
                perms_str.append('r' if (mode >> (8-i) & 1) else '-')
            elif i % 3 == 1:
                perms_str.append('w' if (mode >> (8-i) & 1) else '-')
            else:
                perms_str.append('x' if (mode >> (8-i) & 1) else '-')
        return is_dir + "".join(perms_str)

class FileManagerWindow(QMainWindow):
    def __init__(self, config):
        super().__init__()
        self.cfg = config
        self.setWindowTitle("Cypher File Manager")
        self.resize(1100, 700)
        self.clipboard_buffer = []
        self.current_root = QDir.homePath()
        self.style = QApplication.instance().style()
        self._trash_path = str(Path.home() / '.local' / 'share' / 'Trash' / 'files')

        self.setStyleSheet(stylesheet_from_config(self.cfg))

        self.model = QFileSystemModel()
        self.model.setRootPath(QDir.homePath())
        self.model.setReadOnly(False)
        self.model.setResolveSymlinks(True) 
        self.model.setFilter(QDir.Filter.AllEntries | QDir.Filter.AllDirs | QDir.Filter.NoDotAndDotDot) 

        self.proxy = QSortFilterProxyModel()
        self.proxy.setSourceModel(self.model)
        
        self.tree = QTreeView()
        self.tree.setModel(self.proxy)
        self.tree.setRootIndex(self.proxy.mapFromSource(self.model.index(QDir.homePath())))
        self.tree.setSortingEnabled(True)
        self.tree.sortByColumn(0, Qt.SortOrder.AscendingOrder) 
        self.tree.setAlternatingRowColors(True)
        self.tree.setSelectionMode(self.tree.SelectionMode.ExtendedSelection)
        self.tree.doubleClicked.connect(self.on_double_click)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.on_context_menu)
        self.tree.setExpandsOnDoubleClick(False)
        self.tree.setIconSize(QSize(32, 32)) 
        self.tree.header().setStretchLastSection(True) 
        self.tree.setColumnWidth(0, 300) 
        self.tree.setColumnHidden(1, True)
        self.tree.setColumnHidden(2, True)
        self.tree.setColumnHidden(3, True)

        self.sidebar = QListWidget()
        self.sidebar.setIconSize(QSize(24, 24))
        self.sidebar.setUniformItemSizes(True)
        for item_name in self.cfg.get("sidebar", DEFAULT_CONFIG["sidebar"]):
            list_item = QListWidgetItem(item_name)
            list_item.setIcon(self._get_sidebar_icon(item_name))
            self.sidebar.addItem(list_item)
        self.sidebar.itemClicked.connect(self.on_sidebar_click)
        self.sidebar.setFixedWidth(180)

        self.preview = QWidget()
        pv_layout = QVBoxLayout(self.preview)
        self.preview_label = QLabel("Preview")
        self.preview_label.setObjectName("headerLabel")
        self.preview_label.setFixedHeight(26)
        pv_layout.addWidget(self.preview_label)
        
        self.preview_area = QLabel()
        self.preview_area.setWordWrap(True)
        self.preview_area.setMinimumWidth(300)
        self.preview_area.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft) 
        pv_layout.addWidget(self.preview_area)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.hide()
        pv_layout.addWidget(self.preview_text)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search (type then press Enter)")
        self.search_bar.returnPressed.connect(self.on_search)

        toolbar = QToolBar()
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)

        new_folder_act = QAction(self.style.standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton), "New Folder", self)
        new_folder_act.triggered.connect(self.create_folder)
        toolbar.addAction(new_folder_act)

        refresh_act = QAction(self.style.standardIcon(QStyle.StandardPixmap.SP_BrowserReload), "Refresh", self)
        refresh_act.triggered.connect(self.refresh)
        refresh_act.setShortcut(QKeySequence("F5")) 
        toolbar.addAction(refresh_act)

        up_act = QAction(self.style.standardIcon(QStyle.StandardPixmap.SP_FileDialogToParent), "Up", self)
        up_act.triggered.connect(self.go_up)
        toolbar.addAction(up_act)

        open_act = QAction(self.style.standardIcon(QStyle.StandardPixmap.SP_ArrowRight), "Open", self)
        open_act.triggered.connect(self.open_selected)
        toolbar.addAction(open_act)
        
        toolbar.addSeparator()

        copy_act = QAction(self.style.standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton), "Copy", self)
        copy_act.setShortcut(QKeySequence.StandardKey.Copy)
        copy_act.triggered.connect(self.copy_selected)
        toolbar.addAction(copy_act)

        cut_act = QAction(self.style.standardIcon(QStyle.StandardPixmap.SP_TitleBarMinButton), "Cut", self)
        cut_act.setShortcut(QKeySequence.StandardKey.Cut)
        cut_act.triggered.connect(self.cut_selected)
        toolbar.addAction(cut_act)

        paste_act = QAction(self.style.standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView), "Paste", self)
        paste_act.setShortcut(QKeySequence.StandardKey.Paste)
        paste_act.triggered.connect(self.paste_clipboard)
        toolbar.addAction(paste_act)

        delete_act = QAction(self.style.standardIcon(QStyle.StandardPixmap.SP_DialogCloseButton), "Delete / Move to Trash", self)
        delete_act.setShortcut(QKeySequence.StandardKey.Delete)
        delete_act.triggered.connect(self.delete_selected)
        toolbar.addAction(delete_act)
        
        toolbar.addSeparator()

        properties_act = QAction(self.style.standardIcon(QStyle.StandardPixmap.SP_FileDialogInfoView), "Properties", self)
        properties_act.triggered.connect(self.show_properties)
        toolbar.addAction(properties_act)

        toolbar.addSeparator()
        toolbar.addWidget(self.search_bar)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        splitter = QSplitter()
        splitter.setHandleWidth(3)
        
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(self.sidebar)
        splitter.addWidget(left_widget)

        middle_widget = QWidget()
        middle_layout = QVBoxLayout(middle_widget)
        middle_layout.setContentsMargins(0, 0, 0, 0)
        middle_layout.addWidget(self.tree)
        splitter.addWidget(middle_widget)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(6, 6, 6, 6)
        right_layout.addWidget(self.preview)
        splitter.addWidget(right_widget)

        splitter.setSizes([180, 500, 300]) 

        main_layout.addWidget(splitter)

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.update_status(QDir.homePath())

        self.preview_area.setText("Select a file or folder to preview.")
        self.tree.selectionModel().selectionChanged.connect(self.on_selection_changed)

    def _get_sidebar_icon(self, name):
        style = self.style
        pixmap_class = QStyle.StandardPixmap
        ICON_NAME_FALLBACKS = {
            "Home": ["SP_DirHomeIcon", "SP_DirIcon"],
            "Documents": ["SP_DirOpenIcon", "SP_DirIcon"],
            "Downloads": ["SP_ArrowDown", "SP_DirIcon"],
            "Desktop": ["SP_DesktopIcon", "SP_DirIcon"],
            "Pictures": ["SP_MediaPhoto", "SP_DirImages", "SP_MediaViewButton", "SP_DirIcon"],
            "Music": ["SP_MediaPlay", "SP_DirIcon"],
            "Videos": ["SP_MediaMovie", "SP_MediaVideo", "SP_DirIcon"],
            "Trash": ["SP_TrashIcon", "SP_DialogDiscardButton", "SP_DirIcon"]
        }
        
        names_to_try = ICON_NAME_FALLBACKS.get(name, ["SP_DirIcon"])

        for name_str in names_to_try:
            icon_enum = getattr(pixmap_class, name_str, None)
            
            if icon_enum is not None:
                try:
                    return style.standardIcon(icon_enum)
                except AttributeError:
                    continue
        
        return style.standardIcon(pixmap_class.SP_DirIcon)

    def on_sidebar_click(self, item):
        name = item.text()
        path = self.path_for_sidebar(name)
        if path and Path(path).exists():
            self.set_root(path)

    def path_for_sidebar(self, name):
        home = Path.home() 
        trash_path = Path(self._trash_path) 
        mapping = {
            "Home": home,
            "Documents": home / "Documents",
            "Downloads": home / "Downloads",
            "Desktop": home / "Desktop",
            "Pictures": home / "Pictures",
            "Music": home / "Music",
            "Videos": home / "Videos",
            "Trash": trash_path
        }
        if name == "Trash":
            if not trash_path.exists():
                try:
                    trash_path.mkdir(parents=True, exist_ok=True)
                    (home / '.local' / 'share' / 'Trash' / 'info').mkdir(parents=True, exist_ok=True)
                except Exception:
                    QMessageBox.warning(self, "Error", "Could not create standard Trash directory.")
                    return str(home)
        return str(mapping.get(name, home)) 

    def set_root(self, path):
        if not Path(path).exists() or not Path(path).is_dir():
            QMessageBox.warning(self, "Folder Error", f"Cannot open: '{path}' is not a valid directory.")
            return
        self.current_root = path
        self.model.setRootPath(path)
        src_idx = self.model.index(path)
        proxy_idx = self.proxy.mapFromSource(src_idx)
        self.tree.setRootIndex(proxy_idx)
        self.update_status(path)

    def update_status(self, path):
        try:
            count = len(list(Path(path).iterdir())) 
        except Exception:
            count = 0
        self.status.showMessage(f"{path} — {count} items")

    def refresh(self):
        self.model.setRootPath(self.current_root)
        self.tree.setRootIndex(self.proxy.mapFromSource(self.model.index(self.current_root)))
        self.update_status(self.current_root)

    def go_up(self):
        parent = str(Path(self.current_root).parent) 
        if parent != self.current_root: 
            self.set_root(parent)

    def on_double_click(self, proxy_index):
        source_index = self.proxy.mapToSource(proxy_index)
        path = self.model.filePath(source_index)
        self._open_path(path) 

    def on_search(self):
        txt = self.search_bar.text().strip()
        if not txt:
            self.model.setNameFilters([]) 
            self.model.setFilter(QDir.Filter.AllEntries | QDir.Filter.AllDirs | QDir.Filter.NoDotAndDotDot)
            self.status.showMessage(f"Filter cleared.", 2000)
            return
        filter_pattern = f"*{txt}*"
        self.model.setFilter(QDir.Filter.AllEntries | QDir.Filter.AllDirs) 
        self.model.setNameFilters([filter_pattern])
        root_index = self.tree.rootIndex()
        match_index = None
        for row in range(self.proxy.rowCount(root_index)):
            proxy_index = self.proxy.index(row, 0, root_index)
            source_index = self.proxy.mapToSource(proxy_index)
            file_name = self.model.fileName(source_index)
            if txt.lower() in file_name.lower():
                match_index = proxy_index
                break
        if match_index:
             self.tree.setCurrentIndex(match_index)
             self.tree.scrollTo(match_index, self.tree.ScrollHint.EnsureVisible)
             self.status.showMessage(f"Found and scrolled to '{self.model.fileName(self.proxy.mapToSource(match_index))}'", 3000)
        else:
            self.status.showMessage(f"No items found matching '{txt}'", 3000)

    def on_selection_changed(self, selected, deselected):
        sel = self.tree.selectionModel().selectedIndexes()
        if not sel:
            self.preview_area.show()
            self.preview_text.hide()
            self.preview_area.setText("Select a file or folder to preview.")
            return
        proxy_index = sel[0]
        source_index = self.proxy.mapToSource(proxy_index)
        path = self.model.filePath(source_index)
        self._preview_path(path)

    def _preview_path(self, path):
        self.preview_text.hide()
        self.preview_area.show()
        p = Path(path)
        if p.is_dir():
            try:
                item_count = len(list(p.iterdir()))
            except Exception:
                item_count = "N/A"
            self.preview_area.setText(f"Directory: {p.name}\nPath: {str(p.absolute())}\n\nContains: {item_count} items")
            return
        ext = p.suffix.lower()
        if ext in (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"):
            try:
                pix = QPixmap(str(p))
                max_dim = self.cfg["preview"]["max_image_dim"]
                if pix.width() > max_dim or pix.height() > max_dim:
                    pix = pix.scaled(max_dim, max_dim, Qt.AspectRatioMode.KeepAspectRatio)
                self.preview_area.setPixmap(pix)
                return
            except Exception:
                self.preview_area.setText("Failed to load image file.")
                return
        try:
            with open(p, "r", encoding="utf-8") as fh:
                lines = []
                limit = self.cfg["preview"]["text_preview_lines"]
                for i, line in enumerate(fh):
                    if i >= limit:
                        lines.append("\n[...truncated...]")
                        break
                    lines.append(line.rstrip("\n"))
            text = "\n".join(lines)
            self.preview_area.hide()
            self.preview_text.setPlainText(text)
            self.preview_text.show()
        except UnicodeDecodeError:
            self.preview_area.setText(f"File is binary, corrupted, or uses an unsupported encoding.\n\nPath: {p.name}")
        except Exception as e:
            self.preview_area.setText(f"Could not read file for preview.\n{type(e).__name__}: {e}")

    def on_context_menu(self, pos):
        idx = self.tree.indexAt(pos)
        if not idx.isValid():
            menu = QMenu(self)
            menu.addAction(self.style.standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton), "New Folder", self.create_folder)
            if self.clipboard_buffer:
                menu.addAction(self.style.standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView), "Paste", self.paste_clipboard)
            menu.exec(self.tree.viewport().mapToGlobal(pos))
            return
        
        source_index = self.proxy.mapToSource(idx)
        path = self.model.filePath(source_index)
        menu = QMenu(self)
        
        menu.addAction("Open", lambda: self._open_path(path))
        menu.addAction("Open in Native File Manager", lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(path))))
        menu.addSeparator()
        
        menu.addAction("Copy", lambda: self._copy_to_clipboard([path], is_cut=False))
        menu.addAction("Cut", lambda: self._copy_to_clipboard([path], is_cut=True))
        if self.clipboard_buffer:
             menu.addAction("Paste", self.paste_clipboard)
        menu.addSeparator()
        
        menu.addAction("Rename", lambda: self._rename(path))
        
        trash_path = Path(self._trash_path).absolute()
        is_in_trash = Path(self.current_root).absolute() == trash_path
        
        if is_in_trash:
             menu.addAction("Permanent Delete", lambda: self._permanent_delete([path]))
        elif HAS_SEND2TRASH:
             menu.addAction("Move to Trash", lambda: self._delete([path]))
        else:
             menu.addAction("Delete (Permanent)", lambda: self._delete([path]))
             
        menu.addSeparator()
        menu.addAction("Properties", lambda: self._show_properties(path))
        menu.exec(self.tree.viewport().mapToGlobal(pos))

    def open_selected(self):
        sel = self.tree.selectionModel().selectedIndexes()
        if not sel:
            return
        proxy_index = sel[0] 
        source_index = self.proxy.mapToSource(proxy_index)
        path = self.model.filePath(source_index)
        self._open_path(path)

    def _open_path(self, path):
        if Path(path).is_dir():
            self.set_root(path)
        else:
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def create_folder(self):
        name, ok = QInputDialog.getText(self, "New Folder", "Folder name:")
        if not ok or not name.strip():
            return
        name = name.strip()
        dest = Path(self.current_root) / name
        if any(c in name for c in '/\\:*?"<>|'):
            QMessageBox.warning(self, "Invalid Name", "Folder name contains illegal characters.")
            return
        try:
            dest.mkdir(exist_ok=False)
            self.refresh()
            self.status.showMessage(f"Folder created: {name}", 3000)
        except FileExistsError:
            QMessageBox.warning(self, "Exists", "Folder already exists.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create folder:\n{type(e).__name__}: {e}")

    def _rename(self, path):
        p = Path(path)
        base = p.name
        new_name, ok = QInputDialog.getText(self, "Rename", "New name:", text=base)
        if not ok or not new_name or new_name == base:
            return
        new_path = p.parent / new_name
        try:
            p.rename(new_path) 
            self.refresh()
            self.status.showMessage(f"Renamed to {new_name}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Rename failed: {type(e).__name__}: {e}")

    def delete_selected(self):
        sel = self.tree.selectionModel().selectedIndexes()
        if not sel:
            return
        paths = []
        for proxy_index in sel:
            if proxy_index.column() == 0: 
                source_index = self.proxy.mapToSource(proxy_index)
                paths.append(self.model.filePath(source_index))
        
        trash_path = Path(self._trash_path).absolute()
        is_in_trash = Path(self.current_root).absolute() == trash_path
        
        if is_in_trash:
            self._permanent_delete(paths) 
        else:
            self._delete(paths)
            
    def _permanent_delete(self, paths):
        """Permanently deletes the given paths using os/shutil."""
        if not paths:
            return
        
        names = "\n".join(Path(p).name for p in paths)
        question_text = f"PERMANENTLY DELETE the following {len(paths)} item(s)?\n{names}\n\nTHIS ACTION CANNOT BE UNDONE."
        
        sure = QMessageBox.question(self, "Permanent Delete Confirmation", question_text, 
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if sure != QMessageBox.StandardButton.Yes:
            return
        
        failed = []
        for p in paths:
            try:
                p_path = Path(p)
                if p_path.is_dir():
                    shutil.rmtree(p) 
                else:
                    os.remove(p)
            except Exception as e:
                failed.append((p, str(e)))
        
        self.refresh()
        if failed:
            msg = "\n".join(f"{Path(p).name}: {err}" for p, err in failed)
            QMessageBox.warning(self, "Partial Failure", f"Some items failed to permanently delete:\n{msg}")
        else:
            self.status.showMessage("Permanent Delete complete", 3000)

    def _delete(self, paths):
        """Moves selected paths to trash (if available) or permanently deletes as fallback."""
        if not paths:
            return
        names = "\n".join(Path(p).name for p in paths)
        
        if HAS_SEND2TRASH:
             question_text = f"Move the following {len(paths)} item(s) to Trash?\n{names}"
        else:
             question_text = f"PERMANENTLY DELETE the following {len(paths)} item(s)?\n{names}\n\n(Install 'send2trash' for safer deletion)"
        
        sure = QMessageBox.question(self, "Delete Confirmation", question_text, 
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if sure != QMessageBox.StandardButton.Yes:
            return
            
        failed = []
        for p in paths:
            try:
                if HAS_SEND2TRASH:
                    send2trash(p)
                else:
                    if Path(p).is_dir():
                        shutil.rmtree(p) 
                    else:
                        os.remove(p)
            except Exception as e:
                failed.append((p, str(e)))
        self.refresh()
        if failed:
            msg = "\n".join(f"{Path(p).name}: {err}" for p, err in failed)
            QMessageBox.warning(self, "Partial Failure", f"Some items failed to delete:\n{msg}")
        else:
            self.status.showMessage("Delete complete", 3000)

    def _show_properties(self, path):
        dlg = PropertiesDialog(path, self)
        dlg.exec()

    def show_properties(self):
        sel = self.tree.selectionModel().selectedIndexes()
        if not sel:
            return
        source_index = self.proxy.mapToSource(sel[0])
        path = self.model.filePath(source_index)
        self._show_properties(path)

    def _get_selected_paths(self):
        paths = []
        for proxy_index in self.tree.selectionModel().selectedIndexes():
            if proxy_index.column() == 0: 
                source_index = self.proxy.mapToSource(proxy_index)
                paths.append(self.model.filePath(source_index))
        return paths

    def copy_selected(self):
        paths = self._get_selected_paths()
        if not paths:
            return
        self._copy_to_clipboard(paths, is_cut=False)

    def cut_selected(self):
        paths = self._get_selected_paths()
        if not paths:
            return
        self._copy_to_clipboard(paths, is_cut=True)

    def _copy_to_clipboard(self, paths, is_cut=False):
        self.clipboard_buffer = [(p, is_cut) for p in paths]
        cb = QApplication.clipboard()
        cb.setText("\n".join(paths))
        msg = "Cut" if is_cut else "Copied"
        self.status.showMessage(f"{msg} {len(paths)} item(s)", 3000)

    def paste_clipboard(self):
        if not self.clipboard_buffer:
            QMessageBox.information(self, "Paste", "Clipboard is empty.")
            return
        dest_dir = Path(self.current_root)
        failed = []
        total_items = len(self.clipboard_buffer)
        pd = QProgressDialog("Pasting...", "Abort", 0, total_items, self)
        pd.setWindowModality(Qt.WindowModality.WindowModal) 
        pd.show()
        for i, (src, is_cut) in enumerate(list(self.clipboard_buffer)):
            if pd.wasCanceled():
                break
            src_path = Path(src)
            basename = src_path.name
            dst = dest_dir / basename
            pd.setValue(i + 1)
            pd.setLabelText(f"Pasting: {basename}...")
            try:
                if is_cut:
                    shutil.move(src, dst) 
                else:
                    if src_path.is_dir():
                        shutil.copytree(src, dst) 
                    else:
                        shutil.copy2(src, dst) 
            except Exception as e:
                failed.append((src, str(e)))
        pd.close()
        if is_cut:
            successful_moves = {item[0] for item in self.clipboard_buffer if item[0] not in [f[0] for f in failed]}
            self.clipboard_buffer = [item for item in self.clipboard_buffer if item[0] not in successful_moves]
        self.refresh()
        if failed:
            msg = "\n".join(f"{Path(p).name}: {e}" for p, e in failed)
            QMessageBox.warning(self, "Partial Failure", f"Some items failed to paste:\n{msg}")
        else:
            self.status.showMessage("Paste complete", 3000)

def main():
    cfg = load_config()
    app = QApplication(sys.argv)
    app.setApplicationName("Cypher File Manager")
    fm = FileManagerWindow(cfg)
    fm.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()