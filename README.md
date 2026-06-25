# Design Gate MVP

給團隊使用的 Claude Code plugin，建立 design-first 與 human review 的開發流程。

兩個硬性 gate：

1. Design 核准前禁止修改 production code。
2. Implementation 後須進入 `AWAITING_HUMAN_REVIEW`，由 human 查看 diff 並核准。

## 安裝

```bash
git clone git@github.com:yehjunwei/design-gate-mvp.git
cd design-gate-mvp
./install.sh "$PWD"
```

然後在 Claude Code 執行：

```text
/reload-plugins
```

## 使用方式

在目標 repository 初始化：

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/design_gate.py" init
```

開始一個 task：

```text
/design-gate:design-gate TASK-123 implement vehicle cache invalidation
/design-gate:approve-design TASK-123
# implementation 完成後查看 git diff
/design-gate:approve-implementation TASK-123
```

## 設定

`.design-gate/config.json` 預設 function 不超過 40 行（warning-only，不 hard block）。建議 commit `config.json` 與 `docs/designs/`，將 `state.json` 加入 `.gitignore`。
