# Human Review Checklist

Reviewer 必須查看實際 diff，而不是只看 Claude summary。

- [ ] 我查看了 `git diff`
- [ ] Implementation 符合 approved design
- [ ] 沒有 unrelated change
- [ ] Function 符合 Single Responsibility
- [ ] 超過 40 行的 function 已拆分，或有 approved exception
- [ ] 已考慮 reuse 既有 function / class / module
- [ ] 沒有 speculative abstraction
- [ ] Public API、data flow、state ownership 與 error behavior 正確
- [ ] Tests 包含必要 normal、boundary、failure、regression coverage
- [ ] 沒有 weak assertion、skip test 或隱藏 failure
- [ ] Formatter、linter、type checker、build 與 tests 已通過，或 failure 已明確接受

Final approval：

`/design-gate:approve-implementation <task-id>`
