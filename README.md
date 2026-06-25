# Design Gate MVP

一套給團隊使用的 Claude Code plugin，建立低摩擦的 design-first 與 human review 開發流程。

## MVP 原則

第一版只把兩件事做成硬性 gate：

1. Design 尚未核准前，禁止修改 production code。
2. Implementation 後必須進入 `AWAITING_HUMAN_REVIEW`，由 human 查看實際 diff 並明確核准。

以下規則會由 Skill 與 checker 強烈提醒，但 MVP 不會因 parser 誤判直接中止工作：

- Function 預設不超過 40 行有效邏輯。
- Single Responsibility。
- 優先 reuse 語意相同的既有 implementation。
- 不做 approved design 以外的 change。
- 不弱化 test 或隱藏 failure。

這樣可以先建立習慣，不會一開始就讓團隊覺得流程過重。

## 結構

```text
.claude-plugin/marketplace.json
plugins/design-gate/
  .claude-plugin/plugin.json
  hooks/hooks.json
  skills/
    design-gate/
    approve-design/
    approve-implementation/
  scripts/design_gate.py
install.sh
```

## 發佈前修改

請先替換：

- `Your Engineering Team`
- marketplace name（需要時）
- repository URL

建議放到公司內部 GitHub / GitLab repository。

## 一鍵安裝

公開 GitHub repository：

```bash
curl -fsSL https://raw.githubusercontent.com/YOUR_ORG/design-gate/main/install.sh \
  | bash -s -- YOUR_ORG/design-gate
```

Private repository 建議先 clone：

```bash
git clone git@github.com:YOUR_ORG/design-gate.git
cd design-gate
./install.sh "$PWD"
```

底層執行：

```bash
claude plugin marketplace add <source>
claude plugin install design-gate@team-engineering-standards
```

## Project 初始化

在目標 repository 執行：

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/design_gate.py" init
```

會建立：

```text
.design-gate/config.json
.design-gate/state.json
docs/designs/
```

建議 commit：

```text
.design-gate/config.json
docs/designs/
```

建議加入 `.gitignore`：

```gitignore
.design-gate/state.json
```

## 使用方式

開始一個 code-changing task：

```text
/design-gate:design-gate TASK-123 implement vehicle cache invalidation
```

Review design 後：

```text
/design-gate:approve-design TASK-123
```

Implementation 完成後，查看：

```bash
git status --short
git diff
```

完成 human review：

```text
/design-gate:approve-implementation TASK-123
```

## 40 行規則

預設設定：

```json
{
  "max_function_lines": 40,
  "function_length_mode": "warn"
}
```

MVP 採 warning-only，原因是：

- Python 可以用 AST 較準確分析。
- Java、Kotlin、C++、TypeScript 等語言若不引入完整 parser，只能 heuristic。
- 若直接 hard block，容易因 false positive 造成團隊反感。

後續可依 repository 技術棧接入：

- ESLint
- Detekt
- Checkstyle / PMD
- Ruff
- Clang-Tidy
- golangci-lint

等團隊習慣工作流後，再把特定語言的規則改成 CI hard gate。

## 建議 rollout

### 第 1–2 週

- 只要求 L2/L3 使用完整 design。
- L1 使用 lightweight design。
- 40 行規則 warning-only。
- 收集大家覺得最卡的地方。

### 第 3–4 週

- 調整 design template。
- 將高頻例外寫入規則。
- 對主要語言接入正式 linter。

### 穩定後

- Pull request required review。
- Branch protection。
- CODEOWNERS。
- CI 驗證 design document 與 tests。
- 視情況把 function length 轉為 hard gate。

Plugin 控制 Claude 行為；真正的交付治理仍應由 PR、CI 與 branch protection 負責。
