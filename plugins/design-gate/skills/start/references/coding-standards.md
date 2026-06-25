# Coding Best Practices

這些規則的目的，是提高可讀性、可測試性與長期維護性，而不是追求形式上的完美。

## 1. Scope discipline

- 只實作 approved design 中定義的內容。
- 不順便做無關 cleanup、rename、formatting、dependency upgrade 或 feature。
- 發現值得改善但不在 scope 的問題時，記錄成 follow-up，不要混入本次 change。
- Material deviation 必須先更新 design 再實作。

## 2. Single Responsibility

- 每個 function 執行一個 coherent operation。
- 每個 class 負責一個清楚 capability 或 policy。
- 每個 module 聚合高度相關的 responsibility。
- 分離 orchestration、domain logic、persistence、transport 與 presentation。
- 避免把不相關邏輯塞進 `Manager`、`Helper`、`Utils` 類型。

## 3. Function size

- Function 預設不超過 40 行有效邏輯。
- 以 responsibility 拆分，不是依行數任意切割。
- 優先使用 early return，避免過深 nesting。
- 避免大量 boolean parameter 控制不同流程。
- Parameter 過多且構成同一概念時，考慮 value object。
- 合理例外必須在 approved design 中記錄。

## 4. Reuse

新增 implementation 前，先搜尋：

- domain rule
- validator
- parser
- adapter
- serializer
- error type
- test fixture
- utility function
- repository convention

Reuse 判斷順序：

1. 有語意完全一致的既有 implementation：直接 reuse。
2. 既有 abstraction 可在不破壞 cohesion 下擴充：擴充。
3. 至少兩個真實 caller 共用同一 business rule：抽取 shared logic。
4. 找不到合適 reuse point：新增小而專注的 implementation。
5. 不為 hypothetical future requirement 建立 speculative abstraction。

不要只因為程式碼長得相似就強迫共用；真正應共用的是相同的 semantics 與 reason to change。

## 5. Readability

- Identifier 使用 intention-revealing name。
- 優先直白 control flow，不追求 clever one-liner。
- Comment 說明 why、constraint 或 trade-off，不重述明顯 code。
- 不留下 commented-out code。
- Public interface 保持最小。
- 避免 premature optimization。

## 6. Error and state

- 在 system boundary 驗證 external input。
- 不吞掉 exception。
- Error contract 要明確且一致。
- 避免 hidden global state。
- Retry、timeout、idempotency、transaction、concurrency 行為在 relevant 時必須說清楚。

## 7. Tests

- 測 externally observable behavior 與重要 invariant。
- 包含 normal、boundary、failure、regression cases。
- 測試應 deterministic。
- 不過度依賴 private implementation detail。
- Bug fix 原則上加入 regression test。
- 不弱化 assertion 或 skip test 來配合錯誤 behavior。

## 8. Security and operations

- 不記錄 secret 或敏感 payload。
- 使用 parameterized query 與安全的 process invocation。
- 遵循 least privilege。
- External call 應有合理 timeout。
- 保留必要 error、log、metric 與 observability。
