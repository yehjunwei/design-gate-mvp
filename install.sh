#!/usr/bin/env bash
set -euo pipefail

MARKETPLACE_NAME="${DESIGN_GATE_MARKETPLACE_NAME:-team-engineering-standards}"
PLUGIN_NAME="design-gate"
SOURCE="${1:-}"

if ! command -v claude >/dev/null 2>&1; then
  echo "ERROR: 找不到 Claude Code CLI。" >&2
  exit 1
fi

if [[ -z "$SOURCE" ]]; then
  # script 所在目錄即 marketplace 時直接用它
  HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  if [[ -f "$HERE/.claude-plugin/marketplace.json" ]]; then
    SOURCE="$HERE"
  fi
fi

if [[ -z "$SOURCE" ]]; then
  echo "Usage: ./install.sh <github-owner/repo | git-url | local-path>" >&2
  exit 2
fi

echo "Adding marketplace: $SOURCE"
claude plugin marketplace add "$SOURCE"

echo "Installing plugin: ${PLUGIN_NAME}@${MARKETPLACE_NAME}"
claude plugin install "${PLUGIN_NAME}@${MARKETPLACE_NAME}"

# Dev mode: 把 cache 內的複製品換成指向 repo 的 symlink,改 code 即時生效。
# 只有本地路徑安裝才適用;github/git-url 安裝沒有本地 plugin 目錄,自動跳過。
PLUGIN_SRC="$SOURCE/plugins/${PLUGIN_NAME}"
if [[ -d "$PLUGIN_SRC" ]]; then
  INSTALL_PATH="$(python3 - "$PLUGIN_NAME" "$MARKETPLACE_NAME" <<'PY'
import json, os, sys
name, mkt = sys.argv[1], sys.argv[2]
p = os.path.expanduser("~/.claude/plugins/installed_plugins.json")
print(json.load(open(p))["plugins"][f"{name}@{mkt}"][0]["installPath"])
PY
)"
  if [[ -n "$INSTALL_PATH" ]]; then
    rm -rf "$INSTALL_PATH"
    mkdir -p "$(dirname "$INSTALL_PATH")"
    ln -s "$PLUGIN_SRC" "$INSTALL_PATH"
    echo "Dev symlink: $INSTALL_PATH -> $PLUGIN_SRC"
  fi
fi

cat <<'EOF'

Design Gate 安裝完成。

重新載入 plugin：
  /reload-plugins

每個 repository 第一次使用時：
  python3 "${CLAUDE_PLUGIN_ROOT}/scripts/design_gate.py" init

開始任務：
  /design-gate:design-gate TASK-123 <需求>
EOF
