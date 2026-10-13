import numpy as np
import pytest

from gemma_desktop.core import Engine, chunks, read_document


class FakeModel:
    def encode(self, texts, **kwargs):
        vectors = np.array([[1., 0.] if "고양이" in text else [0., 1.] for text in texts], dtype=np.float32)
        return vectors


def test_chunk_boundaries():
    assert list(chunks("abcdefghij", 6, 2)) == ["abcdef", "efghij"]
    assert list(chunks("   ")) == []
    with pytest.raises(ValueError):
        list(chunks("a", 1, 1))


def test_index_search_replace_remove_and_persistence(tmp_path):
    engine = Engine(tmp_path / "data")
    engine.model = FakeModel()
    cat = tmp_path / "cat.txt"
    dog = tmp_path / "dog.md"
    cat.write_text("고양이 사료", encoding="utf-8")
    dog.write_text("강아지 산책", encoding="utf-8")
    assert engine.index([cat, dog]) == []
    assert engine.search("고양이")[0][0] == str(cat.resolve())
    cat.write_text("새 고양이 문서", encoding="utf-8")
    assert engine.index([cat]) == []
    assert len(engine.documents()) == 2
    assert engine.search("고양이")[0][2] == "새 고양이 문서"
    cat.write_text("", encoding="utf-8")
    assert len(engine.index([cat])) == 1
    assert engine.search("고양이")[0][2] == "새 고양이 문서"
    reopened = Engine(tmp_path / "data")
    assert len(reopened.documents()) == 2
    reopened.remove(str(cat.resolve()))
    assert cat.exists()
    assert len(reopened.documents()) == 1


def test_empty_and_invalid(tmp_path):
    engine = Engine(tmp_path)
    assert engine.search("검색") == []
    with pytest.raises(ValueError):
        engine.search(" ")
    unsupported = tmp_path / "test.bin"
    unsupported.write_bytes(b"test")
    with pytest.raises(ValueError):
        read_document(unsupported)
