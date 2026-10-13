import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QEventLoop, QTimer
from gemma_desktop.app import Window
from gemma_desktop.core import Engine


def test_window_results_are_plain_text(tmp_path):
    app = QApplication.instance() or QApplication([])
    window = Window(Engine(tmp_path))
    window.searched([("/tmp/example.txt", 0, "<script>plain text</script>", 0.8)])
    assert window.results.count() == 1
    assert "<script>plain text</script>" in window.preview.toPlainText()
    window.searched([])
    assert not window.preview.toPlainText()
    window.close()


def test_background_job_restores_controls(tmp_path):
    app = QApplication.instance() or QApplication([])
    window = Window(Engine(tmp_path))
    results = []
    window.run_job(lambda progress: 42, results.append)
    assert not window.send_button.isEnabled()
    loop = QEventLoop()
    window.job.finished.connect(loop.quit)
    QTimer.singleShot(5000, loop.quit)
    loop.exec()
    app.processEvents()
    assert results == [42]
    assert window.job is None
    assert window.send_button.isEnabled()
    window.close()
