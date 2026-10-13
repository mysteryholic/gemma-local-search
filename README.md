# Gemma · 내 문서 검색

Google의 [EmbeddingGemma 2](https://huggingface.co/google/embeddinggemma-2)를 로컬에서 실행하는 macOS / Windows 데스크톱 앱입니다. 문서 검색, 문장 유사도 비교·임베딩 추출, 로컬 챗봇을 제공합니다. EmbeddingGemma 2가 검색과 임베딩을 담당하고, [Qwen3 0.6B](https://huggingface.co/Qwen/Qwen3-0.6B)가 대화 답변을 생성합니다.

## 실행

일반 사용자는 [GitHub Releases](https://github.com/mysteryholic/gemma-local-search/releases/latest)에서 운영체제에 맞는 앱을 받습니다. 배포 앱에는 Python이 포함되어 있으므로 Python이나 uv를 별도로 설치하지 않아도 됩니다.

- **Apple Silicon Mac**: DMG를 열고 앱을 Applications 폴더로 드래그합니다.
- **Windows x64**: ZIP 전체를 풀고 `GemmaLocalSearch/GemmaLocalSearch.exe`를 실행합니다.
- 첫 실행 후 각 탭에서 모델을 다운로드하세요. 모델 파일은 앱에 포함하지 않습니다.

배포 앱은 Apple Developer ID / Windows 인증서 서명이 없는 초기 버전입니다. 운영체제가 실행을 차단하거나 게시자를 확인할 수 없다고 표시할 수 있습니다. 조직의 보안 정책에 따라 실행이 제한될 수 있습니다. 아래는 소스에서 실행하는 방법입니다.

Python 3.12와 [uv](https://docs.astral.sh/uv/getting-started/installation/)를 사용합니다. uv가 Python을 준비할 수 있습니다.

```sh
uv sync --frozen --python 3.12
uv run python main.py
```

macOS에서는 `start-mac.command`, Windows에서는 `start-windows.bat`를 실행할 수도 있습니다. 처음에는 인터넷 연결이 필요합니다.

1. **모델 다운로드 / 준비**를 누릅니다. 공식 모델의 고정 리비전을 다운로드합니다.
2. **문서 추가**에서 TXT, MD, PDF를 선택합니다.
3. 검색어를 입력하고 **의미 검색**을 누릅니다.
4. 결과를 선택하면 파일 경로와 관련 구간을 확인할 수 있습니다.

**유사도 · 임베딩** 탭에서는 두 문장을 비교하거나 한 줄당 한 문장씩 입력하여 정규화된 768차원 벡터를 계산하고 JSON으로 저장합니다. JSON에는 모델 ID, 고정 리비전, 프롬프트 종류, 원문도 포함됩니다.

**로컬 챗봇** 탭에서는 별도로 **챗봇 모델 다운로드 / 준비**를 누른 뒤 질문합니다. **내 문서 참고**를 켜면 검색한 상위 3개 구간을 활용하고 참고 원문을 답변 아래 표시합니다. 끄면 일반 대화를 합니다. 최근 2회 대화를 문맥으로 사용하며 대화는 디스크에 저장하지 않습니다. 소형 모델이므로 한국어 품질과 사실 정확성에 한계가 있습니다. 참고 문서가 있어도 답변이 틀릴 수 있으므로 원문을 확인하세요.

다운로드한 모델과 검색 DB는 재사용됩니다. 이후 문서 임베딩과 검색은 오프라인으로 처리합니다. 문서 내용은 서버로 전송하지 않습니다. 모델 다운로드 시에는 Hugging Face에 접속합니다. 전체 체크포인트를 내려받고 텍스트 인코더만 메모리에 로드합니다. CPU float32를 사용하므로 GPU가 없어도 실행 가능하지만 속도는 하드웨어에 따라 다릅니다.

## 저장 위치

- macOS: `~/Library/Application Support/GemmaLocalSearch`
- Windows: `%LOCALAPPDATA%\GemmaLocalSearch`
- 별도 경로: `GEMMA_DATA_DIR` 환경변수

DB에는 문서의 추출 텍스트와 벡터가 평문으로 저장됩니다. **선택 문서 제외**는 검색 DB에서만 삭제하며 원본 파일은 삭제하지 않습니다. 같은 경로를 다시 추가하면 성공한 경우에만 기존 색인을 교체합니다.

## 앱 빌드

```sh
uv run python scripts/build.py
```

각 운영체제에서 따로 빌드해야 합니다. macOS에서는 `dist/GemmaLocalSearch.app`, Windows에서는 `dist/GemmaLocalSearch/GemmaLocalSearch.exe`와 함께 배포할 폴더가 생성됩니다. Windows 실행 파일만 따로 복사하지 마세요. `uv run python scripts/package.py`로 배포 파일과 SHA-256 체크섬을 생성합니다. 모델은 앱에 포함하지 않으며 각 PC에서 최초 다운로드합니다. `.github/workflows/build.yml`은 macOS ARM64와 Windows x64에서 테스트, 빌드, 패키지 라이브러리 검증 후 배포 파일을 생성합니다. macOS Intel 빌드는 Intel Mac에서 별도로 수행해야 합니다.

빌드 결과는 서명·공증하지 않습니다. 공개 배포 시 운영체제별 코드 서명과 종속 라이브러리 라이선스 고지를 준비해야 합니다.

## 검증

```sh
uv run pytest
uv run python -m scripts.download_model
uv run python -m scripts.check_model
```

단위 테스트는 문서 교체/실패 시 보존, 검색 순위, 영속 저장, 삭제, 유사도·벡터 내보내기, 챗봇 문맥, UI 결과 표시를 검사합니다. 실제 모델 다운로드와 추론은 두 번째 명령으로, 오프라인 한국어 검색은 세 번째 명령으로 확인합니다. 빌드한 실행 파일도 `--check-model` 인수로 검색 검증을 실행할 수 있습니다.

## 범위

텍스트 중심의 첫 버전입니다. 이미지·음성·영상과 OCR은 포함하지 않습니다. UTF-8 텍스트, 파일당 50MB / 2,000구간까지 받습니다. 스캔 PDF는 먼저 OCR이 필요합니다. 검색은 전체 벡터를 메모리에 읽는 방식으로 개인 문서 모음에 적합합니다. 원본 변경은 자동 감지하지 않으며 다시 추가해야 합니다. 검색 유사도는 정답 확률이 아닙니다. 두 모델을 함께 쓰면 수 GB의 메모리와 다운로드 공간이 필요합니다. GPU 가속은 현재 적용하지 않았습니다.
