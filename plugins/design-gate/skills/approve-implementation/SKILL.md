---
name: Approve Implementation
description: Human 查看實際 diff 並完成 review checklist 後，記錄 final implementation approval。
disable-model-invocation: true
allowed-tools: Bash(python3 *)
---

為 task `$ARGUMENTS` 記錄 final implementation approval。

執行：

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/design_gate.py" approve-implementation "$ARGUMENTS"
```

只有 human 明確 invoke 此 Skill 時才能執行。
