from gemma_desktop.core import Engine

if __name__ == "__main__":
    engine = Engine()
    engine.load(download=True)
    vectors = engine.encode(["모델 실행 확인"])
    print(f"모델 다운로드 및 실행 완료: {vectors.shape}")
