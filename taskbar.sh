#!/bin/bash
PYTHON="$PWD/venv/bin/python"
MAIN="$PWD/shell/ui/taskbar/main.py"

find shell -name '*.py' | entr -r "$PYTHON" "$MAIN"
