#!/usr/bin/env bash
# Build a standalone Linux binary with PyInstaller.
# Run from WSL (or any Linux host). On Windows:  wsl -d Ubuntu-24.04 bash build_linux.sh
set -euo pipefail

cd "$(dirname "$0")"

PYTHON=${PYTHON:-python3}

echo ">> Creating venv"
$PYTHON -m venv .build-venv
source .build-venv/bin/activate

echo ">> Installing dependencies"
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt pyinstaller

echo ">> Building binary"
pyinstaller --onefile --clean --name amsat_sstv_bot bot.py

echo ">> Result"
ls -lh dist/amsat_sstv_bot
echo "Done. Copy dist/amsat_sstv_bot together with config.json to the target Linux machine."