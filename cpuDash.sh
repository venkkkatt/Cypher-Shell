#!/bin/bash

PYTHON="$PWD/venv/bin/python"
MAIN="$PWD/shell/ui/dashboard/main.py"
QT_QPA_PLATFORM=xcb
QT_WM_CLASS=dashboard

sleep 1 &&
find shell -name '*.py' | entr -r "$PYTHON" "$MAIN"
