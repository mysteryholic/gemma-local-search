import os
import sqlite3
import sys
from pathlib import Path

import numpy as np

MODEL_ID = "google/embeddinggemma-2"
REVISION = "914f7f89142e33e77833254d9c9b90c3cef7303b"


def data_dir():
    if os.environ.get("GEMMA_DATA_DIR"):
        root = Path(os.environ["GEMMA_DATA_DIR"])
    elif sys.platform == "win32":
        root = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "GemmaLocalSearch"
    elif sys.platform == "darwin":
        root = Path.home() / "Library/Application Support/GemmaLocalSearch"
    else:
        root = Path.home() / ".local/share/GemmaLocalSearch"
    root.mkdir(parents=True, exist_ok=True)
    return root


def chunks(text, size=1000, overlap=150):
    if not 0 <= overlap < size:
        raise ValueError("잘못된 문서 분할 크기입니다.")
    for start in range(0, len(text), size - overlap):
        part = text[start:start + size].strip()
        if part:
            yield part
        if start + size >= len(text):
            break


def read_document(path):
    path = Path(path)
    if path.stat().st_size > 50 * 1024 * 1024:
        raise ValueError("파일당 최대 50MB까지 지원합니다.")
    if path.suffix.lower() == ".pdf":
        from pypdf import PdfReader
        return "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
    if path.suffix.lower() not in {".txt", ".md"}:
        raise ValueError("TXT, Markdown, PDF만 지원합니다.")
    return path.read_text(encoding="utf-8-sig")


class Engine:
    def __init__(self, root=None):
        self.root = Path(root) if root else data_dir()
        self.root.mkdir(parents=True, exist_ok=True)
        self.model = None
        with self.connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS chunks (path TEXT, ordinal INTEGER, text TEXT, vector BLOB, PRIMARY KEY(path, ordinal))")

    def connect(self):
        return sqlite3.connect(self.root / "documents.sqlite3")

    def load(self, download=False):
        if self.model is not None:
            return
        from huggingface_hub import snapshot_download
        from sentence_transformers import SentenceTransformer
        import torch
        location = snapshot_download(MODEL_ID, revision=REVISION,
                                     cache_dir=str(self.root / "models"),
                                     local_files_only=not download)
        # CPU float32 is the common baseline on macOS and Windows; never use float16.
        self.model = SentenceTransformer(location, device="cpu", local_files_only=True,
                                        config_kwargs={"vision_config": None, "audio_config": None},
                                        model_kwargs={"torch_dtype": torch.float32})

    def encode(self, texts, query=False, prompt_name=None):
        self.load()
        vectors = self.model.encode(texts, prompt_name=prompt_name or ("SearchQuery" if query else "Document"),
                                    normalize_embeddings=True, batch_size=8,
                                    show_progress_bar=False, convert_to_numpy=True)
        vectors = np.asarray(vectors, dtype=np.float32)
        if vectors.ndim != 2 or not np.isfinite(vectors).all():
            raise ValueError("유효하지 않은 임베딩입니다.")
        return vectors

    def compare(self, first, second):
        validate_texts([first, second])
        vectors = self.encode([first, second], prompt_name="SentenceSimilarity")
        return float(vectors[0] @ vectors[1])

    def export_embeddings(self, texts):
        validate_texts(texts)
        vectors = self.encode(texts, prompt_name="SentenceSimilarity")
        return {"model": MODEL_ID, "revision": REVISION, "prompt": "SentenceSimilarity",
                "normalized": True, "dimensions": int(vectors.shape[1]),
                "items": [{"text": text, "embedding": vector.tolist()} for text, vector in zip(texts, vectors)]}

    def index(self, paths, progress=lambda message: None):
        failures = []
        for index, path in enumerate(paths):
            progress(f"문서 처리 중 {index + 1}/{len(paths)} · {Path(path).name}")
            try:
                parts = list(chunks(read_document(path)))
                if not parts:
                    raise ValueError("추출 가능한 텍스트가 없습니다. 스캔 PDF는 OCR이 필요합니다.")
                if len(parts) > 2000:
                    raise ValueError("문서가 너무 큽니다. 작은 파일로 나눠 주세요.")
                vectors = self.encode(parts)
                # Replace only after a successful embedding; failed imports preserve the old index.
                with self.connect() as db:
                    key = str(Path(path).resolve())
                    db.execute("DELETE FROM chunks WHERE path = ?", (key,))
                    db.executemany("INSERT INTO chunks VALUES (?, ?, ?, ?)",
                                   [(key, i, part, vector.tobytes()) for i, (part, vector) in enumerate(zip(parts, vectors))])
            except Exception as exc:
                failures.append(f"{Path(path).name}: {exc}")
        return failures

    def documents(self):
        with self.connect() as db:
            return db.execute("SELECT path, COUNT(*) FROM chunks GROUP BY path ORDER BY path").fetchall()

    def remove(self, path):
        with self.connect() as db:
            db.execute("DELETE FROM chunks WHERE path = ?", (path,))

    def search(self, query, limit=10):
        if not query.strip():
            raise ValueError("검색어를 입력하세요.")
        with self.connect() as db:
            rows = db.execute("SELECT path, ordinal, text, vector FROM chunks").fetchall()
        if not rows:
            return []
        query_vector = self.encode([query], query=True)[0]
        # shortcut: exhaustive search keeps this personal library simple; use a vector index for large corpora.
        matrix = np.stack([np.frombuffer(row[3], dtype=np.float32) for row in rows])
        scores = matrix @ query_vector
        order = np.argsort(-scores, kind="stable")[:limit]
        return [(rows[i][0], rows[i][1], rows[i][2], float(scores[i])) for i in order]


def validate_texts(texts):
    if not texts or len(texts) > 100:
        raise ValueError("1~100개 문장을 입력하세요.")
    if any(not text.strip() or len(text) > 4000 for text in texts):
        raise ValueError("각 문장은 공백 없이 1~4,000자여야 합니다.")
