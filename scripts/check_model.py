"""Offline integration check with the downloaded real model."""
import tempfile
from pathlib import Path

from gemma_desktop.core import Engine


def main():
    loaded = Engine()
    loaded.load()
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        engine = Engine(root / "data")
        engine.model = loaded.model
        travel = root / "travel.txt"
        food = root / "food.txt"
        travel.write_text("출장 경비 정산: 교통비 영수증을 첨부하여 재무팀에 제출하세요.", encoding="utf-8")
        food.write_text("김치찌개 조리법: 김치와 돼지고기를 냄비에 넣고 끓입니다.", encoding="utf-8")
        assert engine.index([travel, food]) == []
        result = engine.search("출장 교통비를 돌려받으려면 어떻게 해야 하나요?")
        assert result[0][0] == str(travel.resolve()), result
        print(f"REAL_MODEL_OFFLINE_SEARCH_OK score={result[0][3]:.4f}")


if __name__ == "__main__":
    main()
