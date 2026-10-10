#!/bin/bash
# Double-click me (macOS) or run me (Linux). Starts the Harness Planner XP
# interface in your browser. Needs Python 3.11+.
cd "$(dirname "$0")"
exec python3 -m harness_planner gui
