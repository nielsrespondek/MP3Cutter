#!/bin/bash
# Startet Hook-Cutter unabhaengig davon, von wo aus dieses Skript aufgerufen wird.
cd "$(dirname "$(readlink -f "$0")")"
python3 app.py
