import sys
import json
from pathlib import Path

from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtWidgets import (QApplication, QFileDialog, QHBoxLayout, QLabel,
                               QLineEdit, QListWidget, QListWidgetItem, QMainWindow,
                               QMessageBox, QProgressBar, QPushButton, QSplitter,
                               QTextEdit, QVBoxLayout, QWidget, QTabWidget, QCheckBox)

from gemma_desktop.core import Engine
from gemma_desktop.chat import Chat


class Job(QThread):
    result = Signal(object)
    error = Signal(str)
    progress = Signal(str)

    def __init__(self, function, parent):
        super().__init__(parent)
        self.function = function

    def run(self):
        try:
            self.result.emit(self.function(self.progress.emit))
        except Exception as exc:
            self.error.emit(str(exc))


class Window(QMainWindow):
    def __init__(self, engine=None):
        super().__init__()
        self.engine = engine or Engine()
        self.chat = Chat(self.engine)
        self.history = []
        self.embedding_data = None
        self.job = None
        self.setWindowTitle("Gemma · 내 문서 검색")
        self.resize(1100, 760)
        base = QWidget()
        layout = QVBoxLayout(base)
        layout.setContentsMargins(28, 24, 28, 24)
        title = QLabel("Gemma  /  내 문서 검색")
        title.setStyleSheet("font-size: 26px; font-weight: 700")
        layout.addWidget(title)
        layout.addWidget(QLabel("EmbeddingGemma 2 · 문장을 이해하는 로컬 검색"))
        layout.addWidget(QLabel("TXT · Markdown · 텍스트 PDF | 최초 모델 다운로드 후 오프라인 사용"))
        toolbar = QHBoxLayout()
        self.prepare = QPushButton("모델 다운로드 / 준비")
        self.add = QPushButton("문서 추가")
        self.remove = QPushButton("선택 문서 제외")
        for button in (self.prepare, self.add, self.remove):
            toolbar.addWidget(button)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        row = QHBoxLayout()
        self.query = QLineEdit()
        self.query.setPlaceholderText("예: 출장 경비는 어떻게 정산하나요?")
        self.search_button = QPushButton("의미 검색")
        row.addWidget(self.query)
        row.addWidget(self.search_button)
        layout.addLayout(row)
        splitter = QSplitter()
        self.docs = QListWidget()
        self.docs.setMinimumWidth(220)
        self.results = QListWidget()
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setPlaceholderText("문서를 추가하고 검색하면 관련 내용을 확인할 수 있습니다.")
        right = QSplitter(Qt.Orientation.Vertical)
        right.addWidget(self.results)
        right.addWidget(self.preview)
        splitter.addWidget(self.docs)
        splitter.addWidget(right)
        splitter.setStretchFactor(1, 3)
        layout.addWidget(splitter, 1)
        self.status = QLabel("모델을 준비한 뒤 문서를 추가하세요. 문서 내용은 외부로 전송하지 않습니다.")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.hide()
        layout.addWidget(self.progress)
        tabs = QTabWidget()
        tabs.addTab(base, "문서 검색")
        tabs.addTab(self.embedding_tab(), "유사도 · 임베딩")
        tabs.addTab(self.chat_tab(), "로컬 챗봇")
        shell = QWidget()
        outer = QVBoxLayout(shell)
        outer.addWidget(tabs)
        outer.addWidget(self.status)
        outer.addWidget(self.progress)
        self.setCentralWidget(shell)
        self.prepare.clicked.connect(lambda: self.run_job(lambda p: self.engine.load(download=True), self.model_ready))
        self.add.clicked.connect(self.add_documents)
        self.remove.clicked.connect(self.remove_document)
        self.search_button.clicked.connect(self.search)
        self.query.returnPressed.connect(self.search)
        self.results.currentItemChanged.connect(self.show_result)
        self.refresh()

    def embedding_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("두 문장의 의미 유사도를 비교하거나 문장별 벡터를 JSON으로 저장합니다."))
        self.first = QTextEdit()
        self.first.setPlaceholderText("첫 번째 문장 (최대 4,000자)")
        self.second = QTextEdit()
        self.second.setPlaceholderText("두 번째 문장 (최대 4,000자)")
        layout.addWidget(self.first)
        layout.addWidget(self.second)
        self.compare_button = QPushButton("문장 유사도 비교")
        self.compare_button.clicked.connect(self.compare)
        layout.addWidget(self.compare_button)
        self.similarity = QLabel("코사인 유사도: −1 ~ 1 · 높을수록 의미가 유사합니다.")
        layout.addWidget(self.similarity)
        self.sentences = QTextEdit()
        self.sentences.setPlaceholderText("임베딩할 문장을 한 줄에 하나씩 입력하세요 (최대 100개).")
        layout.addWidget(self.sentences)
        self.embed_button = QPushButton("임베딩 계산")
        self.export_button = QPushButton("JSON으로 저장")
        self.export_button.setEnabled(False)
        self.embed_button.clicked.connect(self.embed)
        self.export_button.clicked.connect(self.export)
        layout.addWidget(self.embed_button)
        layout.addWidget(self.export_button)
        return widget

    def compare(self):
        first, second = self.first.toPlainText(), self.second.toPlainText()
        self.run_job(lambda p: self.engine.compare(first, second),
                     lambda value: self.compared(value))

    def compared(self, value):
        self.similarity.setText(f"코사인 유사도: {value:.4f} (정답 확률이 아닙니다)")
        self.status.setText("문장 유사도 비교 완료")

    def embed(self):
        texts = [line.strip() for line in self.sentences.toPlainText().splitlines() if line.strip()]
        self.run_job(lambda p: self.engine.export_embeddings(texts), self.embedded)

    def embedded(self, data):
        self.embedding_data = data
        self.status.setText(f"{len(data['items'])}개 문장 · {data['dimensions']}차원 임베딩 준비 완료. JSON으로 저장하세요.")

    def export(self):
        if self.embedding_data is None:
            return
        path, _ = QFileDialog.getSaveFileName(self, "임베딩 저장", "embeddings.json", "JSON (*.json)")
        if path:
            from PySide6.QtCore import QSaveFile, QIODevice
            output = QSaveFile(path)
            payload = json.dumps(self.embedding_data, ensure_ascii=False, indent=2).encode("utf-8")
            if not output.open(QIODevice.OpenModeFlag.WriteOnly):
                self.failed(output.errorString())
            elif output.write(payload) != len(payload) or not output.commit():
                self.failed(output.errorString())
            else:
                self.status.setText(f"임베딩 저장 완료 · {path}")

    def chat_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("Qwen3 0.6B · 로컬 답변 생성 / EmbeddingGemma 2 · 문서 검색"))
        layout.addWidget(QLabel("소형 모델의 답변은 부정확할 수 있습니다. 문서 참고 결과와 원문을 함께 확인하세요."))
        self.chat_prepare = QPushButton("챗봇 모델 다운로드 / 준비")
        self.chat_prepare.clicked.connect(lambda: self.run_job(lambda p: self.chat.load(download=True),
                                         lambda _: self.status.setText("챗봇 모델 준비 완료")))
        layout.addWidget(self.chat_prepare)
        self.grounded = QCheckBox("내 문서 참고 (검색 결과를 답변에 활용)")
        self.grounded.setChecked(True)
        layout.addWidget(self.grounded)
        self.transcript = QTextEdit()
        self.transcript.setReadOnly(True)
        layout.addWidget(self.transcript)
        self.question = QLineEdit()
        self.question.setMaxLength(2000)
        self.question.setPlaceholderText("질문을 입력하세요")
        layout.addWidget(self.question)
        self.send_button = QPushButton("질문 보내기")
        self.send_button.clicked.connect(self.ask)
        self.question.returnPressed.connect(self.ask)
        layout.addWidget(self.send_button)
        self.clear_chat = QPushButton("대화 지우기")
        self.clear_chat.clicked.connect(self.reset_chat)
        layout.addWidget(self.clear_chat)
        return widget

    def reset_chat(self):
        self.history.clear()
        self.transcript.clear()

    def ask(self):
        if self.job is not None:
            return
        question = self.question.text().strip()
        if question:
            history = list(self.history)
            grounded = self.grounded.isChecked()
            self.run_job(lambda p: self.chat.reply(question, history, grounded),
                         lambda result: self.answered(question, result))

    def answered(self, question, result):
        answer, sources = result
        self.history.extend([{"role": "user", "content": question}, {"role": "assistant", "content": answer}])
        self.history = self.history[-4:]
        text = f"나: {question}\n\nGemma 앱: {answer}"
        if sources:
            text += "\n\n참고한 검색 결과 (답변 정확성을 보증하지 않습니다):\n"
            text += "\n".join(f"[{i + 1}] {path} · 구간 {ordinal + 1}\n{content[:600]}"
                              for i, (path, ordinal, content, _) in enumerate(sources))
        self.transcript.setPlainText(self.transcript.toPlainText() + text + "\n\n────────\n\n")
        self.question.clear()
        self.status.setText("답변 생성 완료 · 대화는 앱 종료 시 사라집니다.")

    def refresh(self):
        self.docs.clear()
        for path, count in self.engine.documents():
            item = QListWidgetItem(f"{Path(path).name}\n{count}개 구간")
            item.setData(Qt.ItemDataRole.UserRole, path)
            item.setToolTip(path)
            self.docs.addItem(item)

    def run_job(self, function, done):
        if self.job is not None:
            return
        self.set_busy(True)
        self.status.setText("처리 중입니다. 최초 모델 다운로드는 시간이 걸릴 수 있습니다.")
        self.job = Job(function, self)
        self.job.progress.connect(self.status.setText)
        self.job.result.connect(done)
        self.job.error.connect(self.failed)
        self.job.finished.connect(self.job_finished)
        self.job.start()

    def set_busy(self, busy):
        for widget in (self.prepare, self.add, self.remove, self.search_button, self.query):
            widget.setEnabled(not busy)
        for widget in (self.compare_button, self.embed_button, self.chat_prepare, self.send_button,
                       self.clear_chat, self.question, self.grounded):
            widget.setEnabled(not busy)
        self.export_button.setEnabled(not busy and self.embedding_data is not None)
        self.progress.setVisible(busy)

    def job_finished(self):
        self.job.deleteLater()
        self.job = None
        self.set_busy(False)

    def model_ready(self, _):
        self.status.setText("모델 준비 완료 · CPU / float32 · 오프라인 검색 가능")

    def failed(self, error):
        self.status.setText("작업 실패 · 모델 다운로드 상태와 파일을 확인하세요.")
        QMessageBox.warning(self, "작업 실패", error)

    def add_documents(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "문서 선택", "", "문서 (*.txt *.md *.pdf)")
        if paths:
            self.run_job(lambda progress: self.engine.index(paths, progress), self.indexed)

    def indexed(self, failures):
        self.refresh()
        self.results.clear()
        self.preview.clear()
        self.status.setText(f"문서 처리 완료 · {self.docs.count()}개 문서 · 실패 {len(failures)}개")
        if failures:
            QMessageBox.warning(self, "일부 문서를 추가하지 못했습니다", "\n".join(failures))

    def remove_document(self):
        item = self.docs.currentItem()
        if item:
            self.engine.remove(item.data(Qt.ItemDataRole.UserRole))
            self.refresh()
            self.results.clear()
            self.preview.clear()
            self.status.setText("검색 목록에서 제외했습니다. 원본 파일은 유지됩니다.")

    def search(self):
        query = self.query.text().strip()
        if query:
            self.run_job(lambda p: self.engine.search(query), self.searched)

    def searched(self, rows):
        self.results.clear()
        self.preview.clear()
        for path, ordinal, text, score in rows:
            item = QListWidgetItem(f"{Path(path).name} · 구간 {ordinal + 1} · 유사도 {score:.3f}\n{text[:100].replace(chr(10), ' ')}")
            item.setData(Qt.ItemDataRole.UserRole, f"{path}\n구간 {ordinal + 1} · 코사인 유사도 {score:.3f}\n\n{text}")
            self.results.addItem(item)
        self.status.setText(f"검색 완료 · 상위 {len(rows)}개 구간 · 유사도는 정답 확률이 아닙니다.")
        if rows:
            self.results.setCurrentRow(0)

    def show_result(self, current, previous=None):
        self.preview.setPlainText(current.data(Qt.ItemDataRole.UserRole) if current else "")

    def closeEvent(self, event):
        if self.job is not None:
            self.status.setText("진행 중인 작업이 완료된 뒤 종료해 주세요.")
            event.ignore()
        else:
            event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = Window()
    window.show()
    sys.exit(app.exec())
