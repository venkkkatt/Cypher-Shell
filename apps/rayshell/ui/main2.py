import sys
import os
import pty
import select
import signal
import termios
import struct
import fcntl
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, 
                             QHBoxLayout, QWidget, QTextEdit, QLineEdit, 
                             QPushButton, QSplitter, QLabel)
from PyQt5.QtCore import QThread, pyqtSignal, QTimer, Qt
from PyQt5.QtGui import QFont, QTextCursor, QKeyEvent

class CommandProcessor:
    """Handles NLP to command conversion"""
    
    def __init__(self):
        self.command_patterns = {
            'list files': 'ls -la',
            'show directory': 'pwd',
            'list processes': 'ps aux',
            'disk usage': 'df -h',
            'memory usage': 'free -h',
            'network interfaces': 'ifconfig',
            'current directory': 'pwd',
            'change directory': 'cd',
            'create directory': 'mkdir',
            'remove file': 'rm',
            'copy file': 'cp',
            'move file': 'mv',
            'edit file': 'nano',
            'system monitor': 'htop',
            'process monitor': 'top',
            'disk space': 'df -h',
            'memory info': 'cat /proc/meminfo',
        }
    
    def parse_natural_language(self, input_text):
        """Convert natural language to shell commands"""
        input_lower = input_text.lower().strip()
        
        for pattern, command in self.command_patterns.items():
            if pattern in input_lower:
                return self.build_command(pattern, command, input_text)
        
        return None
    
    def build_command(self, pattern, base_command, original_text):
        """Build complete command with parameters"""
        words = original_text.split()
        
        if pattern == 'change directory':
            if len(words) > 2:
                return f"cd {' '.join(words[2:])}"
            return "cd ~"
        elif pattern == 'create directory':
            if len(words) > 2:
                return f"mkdir {' '.join(words[2:])}"
            return None
        elif pattern == 'edit file':
            if len(words) > 2:
                return f"nano {' '.join(words[2:])}"
            return "nano"
        elif pattern == 'remove file':
            if len(words) > 2:
                return f"rm {' '.join(words[2:])}"
            return None
        
        return base_command

class PTYTerminalThread(QThread):
    """Thread that handles the PTY terminal process"""
    
    output_received = pyqtSignal(bytes)
    process_died = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.master_fd = None
        self.child_pid = None
        self.running = True
        
    def run(self):
        """Fork and create PTY terminal"""
        try:
            # Fork the process and create PTY
            self.child_pid, self.master_fd = pty.fork()
            
            if self.child_pid == 0:
                # Child process - this becomes the shell
                os.execvp('/bin/bash', ['/bin/bash'])
            else:
                # Parent process - read from master fd
                self.read_from_terminal()
                
        except OSError as e:
            print(f"PTY fork failed: {e}")
            self.process_died.emit()
    
    def read_from_terminal(self):
        """Continuously read output from the terminal"""
        while self.running:
            try:
                # Use select to check if data is available
                ready, _, _ = select.select([self.master_fd], [], [], 0.1)
                
                if ready:
                    data = os.read(self.master_fd, 1024)
                    if data:
                        self.output_received.emit(data)
                    else:
                        # EOF - process died
                        break
                        
            except (OSError, ValueError):
                # Terminal closed or error occurred
                break
        
        self.process_died.emit()
    
    def write_to_terminal(self, data):
        """Write data to the terminal"""
        if self.master_fd is not None:
            try:
                os.write(self.master_fd, data)
            except (OSError, ValueError):
                pass
    
    def resize_terminal(self, rows, cols):
        """Resize the terminal"""
        if self.master_fd is not None:
            try:
                # Set terminal size using TIOCSWINSZ ioctl
                winsize = struct.pack('HHHH', rows, cols, 0, 0)
                fcntl.ioctl(self.master_fd, termios.TIOCSWINSZ, winsize)
            except (OSError, ValueError):
                pass
    
    def terminate_terminal(self):
        """Terminate the terminal process"""
        self.running = False
        
        if self.child_pid:
            try:
                os.kill(self.child_pid, signal.SIGTERM)
                os.waitpid(self.child_pid, 0)
            except (OSError, ProcessLookupError):
                pass
        
        if self.master_fd:
            try:
                os.close(self.master_fd)
            except OSError:
                pass

class TerminalEmulator(QTextEdit):
    """Advanced terminal emulator with PTY support"""
    
    def __init__(self):
        super().__init__()
        self.setup_terminal()
        self.setup_pty()
        
    def setup_terminal(self):
        """Setup terminal appearance and behavior"""
        # Use a monospace font
        font = QFont("Consolas", 10)
        font.setFixedPitch(True)
        self.setFont(font)
        
        # Terminal colors and styling
        self.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: none;
                selection-background-color: #404040;
            }
        """)
        
        # Calculate character dimensions for terminal sizing
        fm = self.fontMetrics()
        self.char_width = fm.averageCharWidth()
        self.char_height = fm.height()
        
        # Terminal state
        self.cursor_position = 0
        self.current_line = ""
        
    def setup_pty(self):
        """Setup PTY terminal thread"""
        self.pty_thread = PTYTerminalThread()
        self.pty_thread.output_received.connect(self.handle_terminal_output)
        self.pty_thread.process_died.connect(self.handle_process_died)
        self.pty_thread.start()
        
        # Set initial terminal size
        self.resize_terminal()
    
    def handle_terminal_output(self, data):
        """Handle output from PTY terminal"""
        try:
            # Decode terminal output (handles ANSI escape sequences)
            output = data.decode('utf-8', errors='replace')
            
            # Move cursor to end and insert text
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.End)
            cursor.insertText(output)
            self.setTextCursor(cursor)
            
            # Auto-scroll to bottom
            self.ensureCursorVisible()
            
        except Exception as e:
            print(f"Error handling terminal output: {e}")
    
    def handle_process_died(self):
        """Handle when terminal process dies"""
        self.append("\n[Process completed]")
        
    def keyPressEvent(self, event):
        """Handle key presses and send to terminal"""
        # Get the key and any modifiers
        key = event.key()
        text = event.text()
        modifiers = event.modifiers()
        
        # Handle special keys
        if key == Qt.Key_Return or key == Qt.Key_Enter:
            self.pty_thread.write_to_terminal(b'\r')
        elif key == Qt.Key_Backspace:
            self.pty_thread.write_to_terminal(b'\x7f')  # Delete character
        elif key == Qt.Key_Tab:
            self.pty_thread.write_to_terminal(b'\t')
        elif key == Qt.Key_Up:
            self.pty_thread.write_to_terminal(b'\x1b[A')  # Up arrow
        elif key == Qt.Key_Down:
            self.pty_thread.write_to_terminal(b'\x1b[B')  # Down arrow
        elif key == Qt.Key_Left:
            self.pty_thread.write_to_terminal(b'\x1b[D')  # Left arrow
        elif key == Qt.Key_Right:
            self.pty_thread.write_to_terminal(b'\x1b[C')  # Right arrow
        elif key == Qt.Key_Home:
            self.pty_thread.write_to_terminal(b'\x1b[H')
        elif key == Qt.Key_End:
            self.pty_thread.write_to_terminal(b'\x1b[F')
        elif key == Qt.Key_PageUp:
            self.pty_thread.write_to_terminal(b'\x1b[5~')
        elif key == Qt.Key_PageDown:
            self.pty_thread.write_to_terminal(b'\x1b[6~')
        elif modifiers & Qt.ControlModifier:
            # Handle Ctrl+key combinations
            if key == Qt.Key_C:
                self.pty_thread.write_to_terminal(b'\x03')  # Ctrl+C
            elif key == Qt.Key_D:
                self.pty_thread.write_to_terminal(b'\x04')  # Ctrl+D
            elif key == Qt.Key_Z:
                self.pty_thread.write_to_terminal(b'\x1a')  # Ctrl+Z
            elif key == Qt.Key_L:
                self.pty_thread.write_to_terminal(b'\x0c')  # Ctrl+L
        elif text:
            # Regular character input
            self.pty_thread.write_to_terminal(text.encode('utf-8'))
        
        # Don't call parent keyPressEvent to prevent default text editing
    
    def execute_command(self, command):
        """Execute a command in the terminal"""
        if command.strip():
            self.pty_thread.write_to_terminal((command + '\r').encode('utf-8'))
    
    def resize_terminal(self):
        """Calculate and set terminal size based on widget dimensions"""
        if hasattr(self, 'pty_thread') and self.pty_thread.master_fd:
            # Calculate rows and columns based on widget size
            width = self.viewport().width()
            height = self.viewport().height()
            
            cols = max(80, width // self.char_width)
            rows = max(24, height // self.char_height)
            
            self.pty_thread.resize_terminal(rows, cols)
    
    def resizeEvent(self, event):
        """Handle widget resize events"""
        super().resizeEvent(event)
        self.resize_terminal()
    
    def closeEvent(self, event):
        """Clean up when closing"""
        if hasattr(self, 'pty_thread'):
            self.pty_thread.terminate_terminal()
            self.pty_thread.wait()
        event.accept()

class ChatWidget(QTextEdit):
    """Chat interface for conversational AI"""
    
    def __init__(self):
        super().__init__()
        self.setFont(QFont("Arial", 10))
        self.setReadOnly(True)
        self.setStyleSheet("""
            QTextEdit {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
            }
        """)
    
    def add_message(self, sender, message, is_user=True):
        """Add a message to the chat"""
        color = "#007acc" if is_user else "#666666"
        self.append(f'<span style="color: {color}; font-weight: bold;">{sender}:</span> {message}')
        
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.setTextCursor(cursor)

class SmartTerminal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.command_processor = CommandProcessor()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Smart Terminal with LLM - PTY Edition")
        self.setGeometry(100, 100, 1400, 900)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # Create splitter for terminal and chat
        splitter = QSplitter(Qt.Horizontal)
        
        # Terminal section
        terminal_widget = QWidget()
        terminal_layout = QVBoxLayout(terminal_widget)
        
        terminal_layout.addWidget(QLabel("Terminal (PTY) - Supports htop, nano, vim, etc."))
        self.terminal = TerminalEmulator()
        terminal_layout.addWidget(self.terminal)
        
        # Chat section
        chat_widget = QWidget()
        chat_layout = QVBoxLayout(chat_widget)
        
        chat_layout.addWidget(QLabel("AI Assistant"))
        self.chat = ChatWidget()
        chat_layout.addWidget(self.chat)
        
        splitter.addWidget(terminal_widget)
        splitter.addWidget(chat_widget)
        splitter.setSizes([800, 600])
        
        main_layout.addWidget(splitter)
        
        # Input section
        input_layout = QHBoxLayout()
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Enter command or chat message (try 'system monitor' or 'edit file test.txt')...")
        self.input_field.returnPressed.connect(self.process_input)
        
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.process_input)
        
        self.mode_button = QPushButton("Auto Mode")
        self.mode_button.setCheckable(True)
        self.mode_button.setChecked(True)
        self.mode_button.clicked.connect(self.toggle_mode)
        
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_button)
        input_layout.addWidget(self.mode_button)
        
        main_layout.addLayout(input_layout)
        
        # Initial chat message
        self.chat.add_message("Assistant", 
            "Hello! I can help with commands and chat. Try:\n"
            "• 'system monitor' (launches htop)\n"
            "• 'edit file myfile.txt' (opens nano)\n"
            "• 'list processes'\n"
            "• Or just type directly in the terminal!", False)
    
    def toggle_mode(self):
        if self.mode_button.isChecked():
            self.mode_button.setText("Auto Mode")
        else:
            self.mode_button.setText("Manual Mode")
    
    def process_input(self):
        user_input = self.input_field.text().strip()
        if not user_input:
            return
            
        self.input_field.clear()
        
        if self.mode_button.isChecked():
            self.auto_process_input(user_input)
        else:
            self.terminal.execute_command(user_input)
    
    def auto_process_input(self, user_input):
        command = self.command_processor.parse_natural_language(user_input)
        
        if command:
            self.chat.add_message("You", f"Executing: {command}", True)
            self.terminal.execute_command(command)
        else:
            self.handle_chat_message(user_input)
    
    def handle_chat_message(self, message):
        self.chat.add_message("You", message, True)
        
        responses = {
            "hello": "Hello! The terminal now supports interactive programs like htop, nano, and vim!",
            "help": "You can run any terminal command, including interactive ones like:\n• htop (system monitor)\n• nano filename (text editor)\n• vim filename (vim editor)\n• top (process monitor)",
            "what can you do": "I can execute any terminal command through natural language. The terminal uses PTY so it supports full-screen interactive programs!"
        }
        
        response = responses.get(message.lower(), 
                               "I can help with terminal commands. Try 'system monitor' or 'edit file' or type directly in the terminal!")
        
        QTimer.singleShot(500, lambda: self.chat.add_message("Assistant", response, False))
    
    def closeEvent(self, event):
        """Ensure terminal process is cleaned up"""
        if hasattr(self, 'terminal'):
            self.terminal.closeEvent(event)
        event.accept()

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    terminal = SmartTerminal()
    terminal.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()