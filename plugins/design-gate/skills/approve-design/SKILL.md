---
name: Approve Design
description: Human 已 review design document 後，用來記錄明確 design approval。
disable-model-invocation: true
allowed-tools: Bash(python3 *)
---

為 task `$ARGUMENTS` 記錄 design approval。

執行：

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/design_gate.py" approve-design "$ARGUMENTS"
```

Approval 成功後，摘要 approved scope，然後進入 implementation。

不得擴張 scope。
