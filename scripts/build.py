"""Run on each target OS: uv run python scripts/build.py."""
import subprocess
import sys
import os
from pathlib import Path

root = Path(__file__).resolve().parents[1]
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtGui import QImage, QPainter
from PySide6.QtCore import Qt

app = QApplication.instance() or QApplication([])
icon = root / "build/icon.png"
icon.parent.mkdir(exist_ok=True)
canvas = QImage(1024, 1024, QImage.Format.Format_ARGB32)
canvas.fill(Qt.GlobalColor.transparent)
painter = QPainter(canvas)
QSvgRenderer(str(root / "gemma_desktop/assets/icon.svg")).render(painter)
painter.end()
assert canvas.save(str(icon))
command = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
           "--windowed", "--onedir", "--name", "GemmaLocalSearch",
           "--icon", str(icon),
           "--add-data", f"{root / 'gemma_desktop/assets'}:gemma_desktop/assets",
           "--collect-all", "sentence_transformers", "--collect-all", "transformers",
           "--collect-all", "tokenizers", "--collect-all", "huggingface_hub",
           "--collect-all", "torchvision",
           "--copy-metadata", "torch", "--copy-metadata", "scikit-learn",
           "--exclude-module", "PySide6.QtWebEngineCore",
           "--exclude-module", "PySide6.QtWebEngineWidgets", "main.py"]
subprocess.run(command, cwd=root, check=True)
