"""Run on each target OS: uv run python scripts/build.py."""
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
command = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
           "--windowed", "--onedir", "--name", "GemmaLocalSearch",
           "--collect-all", "sentence_transformers", "--collect-all", "transformers",
           "--collect-all", "tokenizers", "--collect-all", "huggingface_hub",
           "--collect-all", "torchvision",
           "--copy-metadata", "torch", "--copy-metadata", "scikit-learn",
           "--exclude-module", "PySide6.QtWebEngineCore",
           "--exclude-module", "PySide6.QtWebEngineWidgets", "main.py"]
subprocess.run(command, cwd=root, check=True)
