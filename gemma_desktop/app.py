import sys
import json
from html import escape
from pathlib import Path

from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import QIcon, QTextCursor
from PySide6.QtWidgets import (QApplication, QFileDialog, QHBoxLayout, QLabel,
                               QLineEdit, QListWidget, QListWidgetItem, QMainWindow,
                               QMessageBox, QProgressBar, QPushButton, QSplitter,
                               QTextEdit, QVBoxLayout, QWidget, QStackedWidget, QCheckBox)

from gemma_desktop.core import Engine
from gemma_desktop.chat import Chat
from gemma_desktop.theme import apply_theme, label, card


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
        self.setWindowTitle("Gemma")
        self.setWindowIcon(QIcon(str(Path(__file__).resolve().parent / "assets/icon.svg")))
        self.resize(1200, 820)
        self.setMinimumSize(980, 720)
        shell = QWidget()
        shell.setObjectName("shell")
        outer = QHBoxLayout(shell)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(218)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(18, 32, 18, 24)
        side.setSpacing(8)
        brand_row = QHBoxLayout()
        mark = label("G", "mark")
        mark.setFixedSize(44, 44)
        mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand_row.addWidget(mark)
        brand_row.addWidget(label("Gemma", "brand"))
        brand_row.addStretch()
        side.addLayout(brand_row)
        side.addSpacing(6)
        side.addWidget(label("나만의 로컬 AI 공간", "muted"))
        side.addSpacing(36)
        side.addWidget(label("WORKSPACE", "eyebrow"))
        side.addSpacing(5)
        self.pages = QStackedWidget()
        self.nav_buttons = []
        for index, title in enumerate(("문서 검색", "유사도 · 임베딩", "로컬 챗봇")):
            button = QPushButton(title)
            button.setProperty("role", "nav")
            button.setCheckable(True)
            button.setAutoExclusive(True)
            button.clicked.connect(lambda checked=False, page=index: self.pages.setCurrentIndex(page))
            side.addWidget(button)
            self.nav_buttons.append(button)
        self.nav_buttons[0].setChecked(True)
        side.addStretch()
        side.addWidget(label("●  내 기기에서 처리", "badge"))
        side.addSpacing(8)
        side.addWidget(label("문서와 대화는 이 기기에.\n다운로드 후 오프라인으로.", "muted"))
        side.addSpacing(14)
        side.addWidget(label("GEMMA LOCAL  /  0.1", "eyebrow"))
        outer.addWidget(sidebar)
        content = QVBoxLayout()
        content.setContentsMargins(30, 28, 30, 16)
        content.setSpacing(14)
        self.pages.addWidget(self.search_page())
        self.pages.addWidget(self.embedding_tab())
        self.pages.addWidget(self.chat_tab())
        content.addWidget(self.pages, 1)
        self.status = label("시작하려면 모델을 준비하고 문서를 추가하세요.", "muted")
        content.addWidget(self.status)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setTextVisible(False)
        self.progress.hide()
        content.addWidget(self.progress)
        outer.addLayout(content, 1)
        self.setCentralWidget(shell)
        self.prepare.clicked.connect(lambda: self.run_job(lambda p: self.engine.load(download=True), self.model_ready))
        self.add.clicked.connect(self.add_documents)
        self.remove.clicked.connect(self.remove_document)
        self.search_button.clicked.connect(self.search)
        self.query.returnPressed.connect(self.search)
        self.results.currentItemChanged.connect(self.show_result)
        self.refresh()

    def page(self, eyebrow, title, subtitle):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        layout.addWidget(label(eyebrow, "eyebrow"))
        layout.addWidget(label(title, "title"))
        layout.addWidget(label(subtitle, "subtitle"))
        layout.addSpacing(6)
        return widget, layout

    def search_page(self):
        widget, layout = self.page("YOUR LIBRARY", "내 문서 검색", "정확한 단어가 떠오르지 않아도, 의미로 찾아보세요.")
        toolbar = QHBoxLayout()
        toolbar.addWidget(label("TXT · Markdown · PDF", "muted"))
        toolbar.addStretch()
        self.prepare = QPushButton("모델 준비")
        self.prepare.setToolTip("EmbeddingGemma 2 다운로드 및 로딩")
        self.add = QPushButton("＋ 문서 추가")
        self.add.setProperty("role", "primary")
        toolbar.addWidget(self.prepare)
        toolbar.addWidget(self.add)
        layout.addLayout(toolbar)
        row = QHBoxLayout()
        row.setSpacing(10)
        self.query = QLineEdit()
        self.query.setObjectName("search")
        self.query.setPlaceholderText("어떤 내용을 찾고 있나요?")
        self.query.setAccessibleName("문서 검색어")
        self.search_button = QPushButton("검색")
        self.search_button.setProperty("role", "primary")
        self.search_button.setMinimumHeight(34)
        row.addWidget(self.query)
        row.addWidget(self.search_button)
        layout.addLayout(row)
        splitter = QSplitter()
        library, library_layout = card()
        library.setMinimumWidth(205)
        library.setMaximumWidth(300)
        heading = QHBoxLayout()
        heading.addWidget(label("내 라이브러리", "section"))
        self.document_count = label("0", "muted")
        heading.addWidget(self.document_count)
        heading.addStretch()
        library_layout.addLayout(heading)
        self.docs = QListWidget()
        self.docs.setAccessibleName("추가한 문서 목록")
        self.docs.setWordWrap(True)
        library_layout.addWidget(self.docs, 1)
        self.library_empty = label("아직 문서가 없어요.\n문서를 추가하면 여기에 모입니다.", "muted")
        library_layout.addWidget(self.library_empty)
        self.remove = QPushButton("선택 문서 제외")
        self.remove.setProperty("role", "quiet")
        library_layout.addWidget(self.remove)
        splitter.addWidget(library)
        self.result_stack = QStackedWidget()
        empty, empty_layout = card()
        empty_layout.addStretch()
        icon = label("⌕", "empty-mark")
        icon.setFixedSize(76, 76)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(icon, 0, Qt.AlignmentFlag.AlignHCenter)
        self.empty_title = label("문서 속에서 발견하는 답", "section")
        self.empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(self.empty_title)
        self.empty_description = label("문서를 추가하고 궁금한 내용을 물어보세요.\n관련된 구간과 원문을 함께 보여드릴게요.", "muted")
        self.empty_description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(self.empty_description)
        empty_layout.addSpacing(12)
        example = label("예: 출장 경비는 어떻게 정산하나요?", "muted")
        example.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(example)
        empty_layout.addStretch()
        self.result_stack.addWidget(empty)
        right = QSplitter(Qt.Orientation.Vertical)
        results_card, results_layout = card()
        results_layout.addWidget(label("관련 내용", "section"))
        self.results = QListWidget()
        self.results.setObjectName("results")
        self.results.setWordWrap(True)
        self.results.setAccessibleName("문서 검색 결과")
        results_layout.addWidget(self.results)
        reading_card, reading_layout = card()
        reading_layout.addWidget(label("원문 미리보기", "section"))
        self.preview = QTextEdit()
        self.preview.setObjectName("reading")
        self.preview.setReadOnly(True)
        reading_layout.addWidget(self.preview)
        right.addWidget(results_card)
        right.addWidget(reading_card)
        self.result_stack.addWidget(right)
        splitter.addWidget(self.result_stack)
        splitter.setStretchFactor(1, 3)
        splitter.setSizes([235, 650])
        layout.addWidget(splitter, 1)
        return widget

    def embedding_tab(self):
        widget, layout = self.page("EXPLORE MEANING", "문장 사이의 거리", "비슷한 의미를 발견하고, 텍스트를 숫자로 표현해 보세요.")
        compare_card, compare_layout = card()
        compare_layout.addWidget(label("문장 유사도", "section"))
        fields = QHBoxLayout()
        self.first = QTextEdit()
        self.first.setPlaceholderText("첫 번째 문장을 입력하세요.")
        self.first.setAccessibleName("비교할 첫 번째 문장")
        self.second = QTextEdit()
        self.second.setPlaceholderText("두 번째 문장을 입력하세요.")
        self.second.setAccessibleName("비교할 두 번째 문장")
        self.first.setMaximumHeight(125)
        self.second.setMaximumHeight(125)
        fields.addWidget(self.first)
        fields.addWidget(self.second)
        compare_layout.addLayout(fields)
        actions = QHBoxLayout()
        self.similarity = label("두 문장은 얼마나 닮았을까요?", "muted")
        actions.addWidget(self.similarity, 1)
        self.compare_button = QPushButton("유사도 비교")
        self.compare_button.setProperty("role", "primary")
        self.compare_button.clicked.connect(self.compare)
        actions.addWidget(self.compare_button)
        compare_layout.addLayout(actions)
        layout.addWidget(compare_card)
        export_card, export_layout = card()
        export_layout.addWidget(label("임베딩 내보내기", "section"))
        export_layout.addWidget(label("한 줄에 한 문장씩 · 최대 100개 · 문장당 4,000자", "muted"))
        self.sentences = QTextEdit()
        self.sentences.setPlaceholderText("오늘의 아이디어를 적어보세요.\n각 문장을 벡터로 변환해 드립니다.")
        self.sentences.setAccessibleName("임베딩할 문장 목록")
        export_layout.addWidget(self.sentences, 1)
        actions = QHBoxLayout()
        actions.addWidget(label("768차원 · JSON", "muted"))
        actions.addStretch()
        self.embed_button = QPushButton("임베딩 계산")
        self.embed_button.setProperty("role", "primary")
        self.export_button = QPushButton("JSON 저장")
        self.export_button.setEnabled(False)
        self.embed_button.clicked.connect(self.embed)
        self.export_button.clicked.connect(self.export)
        actions.addWidget(self.embed_button)
        actions.addWidget(self.export_button)
        export_layout.addLayout(actions)
        layout.addWidget(export_card, 1)
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
        widget, layout = self.page("A LITTLE HELP", "생각을 나누는 공간", "내 문서를 함께 읽고, 궁금한 것들을 편하게 물어보세요.")
        toolbar = QHBoxLayout()
        self.grounded = QCheckBox("내 문서 참고")
        self.grounded.setChecked(True)
        toolbar.addWidget(self.grounded)
        toolbar.addStretch()
        self.clear_chat = QPushButton("새 대화")
        self.clear_chat.setProperty("role", "quiet")
        self.clear_chat.clicked.connect(self.reset_chat)
        toolbar.addWidget(self.clear_chat)
        self.chat_prepare = QPushButton("챗봇 모델 준비")
        self.chat_prepare.clicked.connect(lambda: self.run_job(lambda p: self.chat.load(download=True),
                                         lambda _: self.status.setText("챗봇 모델 준비 완료")))
        toolbar.addWidget(self.chat_prepare)
        layout.addLayout(toolbar)
        conversation, conversation_layout = card()
        self.transcript = QTextEdit()
        self.transcript.setObjectName("conversation")
        self.transcript.setReadOnly(True)
        self.transcript.setPlaceholderText("무엇을 도와드릴까요?\n\n문서에 담긴 내용을 질문하거나, 아이디어를 함께 정리해 보세요.\n일반 대화를 하려면 ‘내 문서 참고’를 해제하세요.")
        self.transcript.setAccessibleName("대화 내용")
        conversation_layout.addWidget(self.transcript)
        layout.addWidget(conversation, 1)
        composer = QHBoxLayout()
        self.question = QLineEdit()
        self.question.setObjectName("search")
        self.question.setMaxLength(2000)
        self.question.setPlaceholderText("메시지를 입력하세요…")
        self.question.setAccessibleName("챗봇에게 보낼 메시지")
        composer.addWidget(self.question)
        self.send_button = QPushButton("보내기 ↑")
        self.send_button.setProperty("role", "primary")
        self.send_button.setMinimumHeight(34)
        self.send_button.clicked.connect(self.ask)
        self.question.returnPressed.connect(self.ask)
        composer.addWidget(self.send_button)
        layout.addLayout(composer)
        layout.addWidget(label("Qwen3 0.6B · 답변이 부정확할 수 있으니 참고 원문을 확인하세요.", "muted"))
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
        text = ('<p style="color:#737780;font-size:11px">나</p>'
                f'<table width="100%" cellpadding="14" bgcolor="#edf5ff"><tr><td>{escape(question)}</td></tr></table>'
                '<p style="color:#0071e3;font-size:11px"><b>GEMMA</b></p>'
                f'<p>{escape(answer).replace(chr(10), "<br>")}</p>')
        if sources:
            text += '<p style="color:#737780;font-size:11px">참고한 문서 · 답변과 원문을 함께 확인하세요.</p>'
            text += "".join(f'<p style="color:#737780;font-size:12px">[{i + 1}] {escape(path)} · 구간 {ordinal + 1}<br>{escape(content[:600])}</p>'
                            for i, (path, ordinal, content, _) in enumerate(sources))
        cursor = self.transcript.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertHtml(text + '<p><br></p>')
        self.transcript.setTextCursor(cursor)
        self.transcript.ensureCursorVisible()
        self.question.clear()
        self.status.setText("답변 생성 완료 · 대화는 앱 종료 시 사라집니다.")

    def refresh(self):
        self.docs.clear()
        for path, count in self.engine.documents():
            item = QListWidgetItem(f"{Path(path).name}\n{count}개 구간")
            item.setData(Qt.ItemDataRole.UserRole, path)
            item.setToolTip(path)
            self.docs.addItem(item)
        self.document_count.setText(str(self.docs.count()))
        self.library_empty.setVisible(self.docs.count() == 0)

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
        self.status.setText("모델 준비 완료 · 오프라인으로 문서를 검색할 수 있어요.")

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
        self.result_stack.setCurrentIndex(0)
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
            self.result_stack.setCurrentIndex(0)
            self.status.setText("검색 목록에서 제외했습니다. 원본 파일은 유지됩니다.")

    def search(self):
        query = self.query.text().strip()
        if query:
            self.run_job(lambda p: self.engine.search(query), self.searched)

    def searched(self, rows):
        self.results.clear()
        self.preview.clear()
        self.result_stack.setCurrentIndex(0)
        for path, ordinal, text, score in rows:
            item = QListWidgetItem(f"{Path(path).name} · 구간 {ordinal + 1} · 유사도 {score:.3f}\n{text[:100].replace(chr(10), ' ')}")
            item.setData(Qt.ItemDataRole.UserRole, f"{path}\n구간 {ordinal + 1} · 코사인 유사도 {score:.3f}\n\n{text}")
            self.results.addItem(item)
        self.status.setText(f"검색 완료 · 상위 {len(rows)}개 구간 · 유사도는 정답 확률이 아닙니다.")
        if rows:
            self.result_stack.setCurrentIndex(1)
            self.results.setCurrentRow(0)
        else:
            self.empty_title.setText("검색 결과가 없습니다")
            self.empty_description.setText("문서를 추가한 뒤 다시 검색해 보세요.")

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
    apply_theme(app)
    window = Window()
    window.show()
    sys.exit(app.exec())
