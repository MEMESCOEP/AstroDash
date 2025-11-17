#!/bin/bash
set -euo pipefail

BUILD_DIR="$(pwd)/bin/"
EXE_NAME="Game.bin"

echo ">>> Creating Linux executable \"$BUILD_DIR$EXE_NAME\"..."
mkdir -p "$BUILD_DIR"
nuitka \
    --standalone \
    --onefile \
    --no-pyi-file \
    --clang \
    --lto=yes \
    --jobs="$(nproc)" \
    --python-flag=-O \
    --output-file="$EXE_NAME" \
    --output-dir="$BUILD_DIR" \
    --assume-yes-for-downloads \
    Game.py
