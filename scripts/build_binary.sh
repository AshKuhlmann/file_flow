#!/usr/bin/env bash
set -e
pyinstaller sorter/cli.py --onefile -n "file-sorter" --log-level WARN
mkdir -p dist
mv dist/file-sorter* dist/

