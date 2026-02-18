#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXTERNAL_DIR="$ROOT_DIR/external/frontier-evals"
SRC_DIR="$EXTERNAL_DIR/project/evmbench"
DST_DIR="$ROOT_DIR/datasets/evmbench"

mkdir -p "$ROOT_DIR/external" "$ROOT_DIR/datasets"

if [[ ! -d "$EXTERNAL_DIR/.git" ]]; then
  echo "[fetch] cloning openai/frontier-evals"
  git clone --depth 1 https://github.com/openai/frontier-evals.git "$EXTERNAL_DIR"
else
  echo "[fetch] updating openai/frontier-evals"
  git -C "$EXTERNAL_DIR" pull --ff-only
fi

if [[ ! -d "$SRC_DIR" ]]; then
  echo "[fetch] expected source path not found: $SRC_DIR" >&2
  exit 1
fi

if command -v rsync >/dev/null 2>&1; then
  rsync -a --delete "$SRC_DIR/" "$DST_DIR/"
else
  rm -rf "$DST_DIR"
  mkdir -p "$DST_DIR"
  cp -R "$SRC_DIR/." "$DST_DIR/"
fi

echo "[fetch] evmbench copied to $DST_DIR"
