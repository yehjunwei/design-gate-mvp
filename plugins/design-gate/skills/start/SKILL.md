---
name: Design Gate
description: >
  當使用者要求 implementation、feature development、bug fix、refactoring、
  migration、integration、optimization、code change、實作、新增功能、修正、
  修改、重構或移除程式碼時，使用這個 Skill。先釐清需求與既有設計，
  產生 design document，取得明確 human approval 後才開始 coding；
  完成後要求 human review 實際 diff。
effort: high
---

# Design Gate

這是一套低摩擦的 design-first 開發流程。

目標不是製造文件或增加官僚程序，而是避免：

- 還沒理解需求就開始 coding
- Claude 自行補完未確認的 requirement
- implementation 超出原本 scope
- function 過長、責任混雜
- 重複實作既有邏輯
- 工程師只看 Claude summary，沒有 review 實際 diff

請閱讀：

- `${CLAUDE_SKILL_DIR}/references/design-template.md`
- `${CLAUDE_SKILL_DIR}/references/coding-standards.md`
- `${CLAUDE_SKILL_DIR}/references/review-checklist.md`

## Workflow

狀態依序為：

`DISCOVERY -> DESIGN -> DESIGN_APPROVED -> IMPLEMENTATION -> AWAITING_HUMAN_REVIEW -> COMPLETED`

不得跳過狀態，也不得自行假設 human approval 已經發生。

## 1. DISCOVERY

開始 coding 前：

1. 用簡短文字重述問題、目標與限制。
2. 閱讀相關 production code、test、interface、configuration 與 documentation。
3. 找出既有可 reuse 的 function、class、module、pattern 與 test fixture。
4. 區分：
   - 已確認事實
   - assumption
   - open question
   - non-goal
5. 只詢問真正會影響設計的問題，通常每輪 2–4 題。
6. 小改動不需要長篇討論；只要把關鍵決策說清楚。

### Complexity

- `L0`：comment、typo、formatting、documentation-only，不改變 runtime behavior。
- `L1`：局部 bug fix、小型內部修改。
- `L2`：新功能、public API、class responsibility 或 data flow 改變。
- `L3`：跨 service、persistence、security、concurrency 或 architecture 改變。

`L1` 可以使用 lightweight design；`L2/L3` 使用完整 design。

## 2. DESIGN

建立：

`docs/designs/<task-id>-<feature-name>.md`

Design document 至少要說明：

- problem、goal、non-goal
- existing behavior
- reuse candidates
- proposed class/function responsibility
- data flow 與 error flow
- 預計修改的 files
- test strategy
- 最小可行方案
- risk 與 open question

### Function design

每個 function 應只有一個清楚責任。

預設每個 function 不超過 **40 行有效邏輯**：

- 不計空白行
- 不計 comment-only line
- 不計 function signature
- 不應為了湊行數而機械式切割
- 應依照 coherent responsibility 拆分

若單一 function 確實超過 40 行更清楚，必須在 design document 寫明原因，並讓 human 一起核准。

### Design approval

完成 design 後停止，不得開始修改 production code。

請要求 human 明確執行：

`/design-gate:approve-design <task-id>`

以下文字不得當成正式 approval：

- 繼續
- 看起來可以
- 沒問題
- go ahead
- proceed

## 3. IMPLEMENTATION

取得 approval 後才開始 coding。

實作時遵守：

1. 只做 approved design 中描述的內容。
2. 不做未在 design 內的 cleanup、rename、dependency upgrade、generalization 或新功能。
3. 優先 reuse 語意相同的既有 function、class、module 或 pattern。
4. 不為了表面消除重複而錯誤抽象不同概念。
5. function、class、module 都維持 Single Responsibility。
6. function 預設不超過 40 行有效邏輯。
7. orchestration、domain logic、I/O side effect 儘量分離。
8. public API、error contract 與 backward compatibility 必須符合 design。
9. 加入 design 中定義的 normal、boundary、failure 與 regression tests。
10. 不得刪除、skip 或弱化 test 來讓錯誤 implementation 通過。
11. 不得隱藏 lint、type-check、build 或 test failure。

如果 implementation 發現 design 必須重大改變：

1. 停止 coding。
2. 更新 design document。
3. 說明 deviation 與原因。
4. 回到 `DESIGN`。
5. 重新取得 approval。

## 4. HUMAN REVIEW

Implementation 完成後：

1. 執行適用的 formatter、linter、type checker、build 與 tests。
2. 執行：
   `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/design_gate.py" check`
3. 顯示：
   - `git status --short`
   - changed files
   - diff summary
   - tests 與 commands executed
   - warning / failure
   - deviations from design
   - known limitations
4. 將狀態設為 `AWAITING_HUMAN_REVIEW`。
5. 明確要求 human 查看實際 `git diff`。
6. Human review 完成後執行：

`/design-gate:approve-implementation <task-id>`

在此之前不得宣稱 task 已完成。

## 語言規則

- 與使用者對話：繁體中文
- Design document：繁體中文
- 程式碼 identifier：英文
- Code comment：遵循 repository 現有慣例；無慣例時使用英文
- Commit message：遵循 repository 現有慣例
- Status、command、JSON key、file path：保留英文
