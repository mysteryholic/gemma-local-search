# Third-party components

Gemma Local Search includes Python, Qt for Python (PySide6 / Shiboken6), PyTorch,
torchvision, Transformers, Sentence Transformers, Hugging Face Hub, NumPy,
SciPy, scikit-learn, pypdf, Pillow, and their dependencies.

The `licenses` directory in each release contains installed distribution license
files and `packages.json` with versions and upstream project URLs. Upstream
licenses govern those components independently of the application source.

Qt / PySide6 / Shiboken6 are dynamically linked. Their applicable LGPL/GPL
license texts are included with their distributions; source and corresponding
release tags are available from https://code.qt.io/pyside/pyside-setup.git/ and
https://code.qt.io/qt/. Qt libraries remain separate files in the bundle.
Users may replace those libraries with compatible modified versions and may
reverse engineer the application as needed to debug modifications to LGPL
components. Re-signing a modified macOS bundle may be necessary.

Model weights are not redistributed inside the application. The application
downloads fixed revisions directly from their official repositories:

- https://huggingface.co/google/embeddinggemma-2
- https://huggingface.co/Qwen/Qwen3-0.6B

See those repositories for model licenses and notices.
