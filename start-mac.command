#!/bin/zsh
set -e
cd "$(dirname "$0")"
export PATH="$HOME/.local/bin:/opt/homebrew/bin:$PATH"
if ! command -v uv >/dev/null 2>&1; then
  echo "uv를 먼저 설치해 주세요: https://docs.astral.sh/uv/getting-started/installation/"
  read -r
  exit 1
fi
uv run --frozen python main.py
