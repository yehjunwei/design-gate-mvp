# Design Gate MVP

給團隊使用的 Claude Code plugin，建立 design-first 與 human review 的開發流程。

兩個硬性 gate：

1. Design 核准前禁止修改 production code。
2. Implementation 後須進入 `AWAITING_HUMAN_REVIEW`，由 human 查看 diff 並核准。

## 安裝

```bash
git clone git@github.com:yehjunwei/design-gate-mvp.git
cd design-gate-mvp
./install.sh
```

然後在 Claude Code 執行：

```text
/reload-plugins
```

## 使用方式

在目標 repository 直接開始一個 task（gate 會自動生效）：

```text
/design-gate:start TASK-123 實作一個ABC功能
/design-gate:approve-design TASK-123
# implementation 完成後查看 git diff
/design-gate:approve-implementation TASK-123
```

Gate 預設值內建,不需初始化。若要客製化規則,先執行 `/design-gate:init` 產生 `.design-gate/config.json`。
