import numpy as np
import pytest

from gemma_desktop.chat import Chat, messages_for
from gemma_desktop.core import Engine


class Embeddings:
    def encode(self, texts, **kwargs):
        assert kwargs["prompt_name"] == "SentenceSimilarity"
        return np.array([[1., 0.] for _ in texts], dtype=np.float32)


def test_compare_and_export(tmp_path):
    engine = Engine(tmp_path)
    engine.model = Embeddings()
    assert engine.compare("고양이", "고양이") == 1.0
    data = engine.export_embeddings(["한글"])
    assert data["items"] == [{"text": "한글", "embedding": [1., 0.]}]
    assert data["dimensions"] == 2
    with pytest.raises(ValueError):
        engine.compare("", "a")
    with pytest.raises(ValueError):
        engine.export_embeddings(["a"] * 101)


def test_chat_context_and_empty_library(tmp_path):
    history = [{"role": "user", "content": str(i)} for i in range(8)]
    messages = messages_for("질문", history, [("/tmp/a.txt", 0, "본문", 0.5)], True)
    assert len(messages) == 6
    assert "untrusted data" in messages[0]["content"]
    assert "[1] a.txt\n본문" in messages[-1]["content"]
    chat = Chat(Engine(tmp_path))
    answer, sources = chat.reply("질문", [], True)
    assert "문서가 없습니다" in answer
    assert sources == []
    assert chat.model is None
    with pytest.raises(ValueError):
        chat.reply(" " , [], False)
