# INSTALL-SYMLINK：install.sh 開發模式 symlink

## Complexity

L1 — 對 `install.sh` 的局部修改,不改變 plugin runtime behavior,只改變本地安裝後的檔案佈局。

## Problem / Goal / Non-goal

- **Problem**:`claude plugin install` 會把 plugin **複製**到 `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`。在 repo 修改 code 後 cache 不會更新,每次都要重裝才能測。
- **Goal**:本地路徑安裝時,讓 cache 內的 plugin 指向 repo,改 code 即時生效。
- **Non-goal**:
  - 不改 github / git-url 安裝行為(那種沒有本地 plugin 目錄)。
  - 不手動編輯 `installed_plugins.json` / `known_marketplaces.json`(交給 CLI 登記)。
  - 不新增 flag、不做 production / dev 模式切換。

## Existing behavior

`install.sh` 現況:
1. 檢查 `claude` CLI 存在。
2. 推導 `SOURCE`(預設為 script 所在 repo 根目錄)。
3. `claude plugin marketplace add "$SOURCE"`。
4. `claude plugin install "design-gate@team-engineering-standards"` → 複製到 cache 並登記。

`marketplace.json` 中 plugin source 為 `./plugins/design-gate`,故 repo 內 plugin 目錄為 `$SOURCE/plugins/design-gate`。

## Proposed change

在 `claude plugin install` 之後新增一段:若 `$SOURCE/plugins/design-gate` 是本地目錄,則
1. 從 `installed_plugins.json` 讀出該 plugin 的 `installPath`(CLI 剛登記的 cache 路徑)。
2. `rm -rf` 掉 cache 內的複製品。
3. 建立 symlink:`installPath -> $SOURCE/plugins/design-gate`。

CLI 仍負責 marketplace / installed_plugins 登記,我們只把「複製品」換成「symlink」,登記保持有效。

非本地安裝(github/git-url)因為 `$SOURCE/plugins/design-gate` 不存在,自動跳過,行為不變。

## Data flow

`installed_plugins.json["plugins"]["design-gate@team-engineering-standards"][0]["installPath"]` 是唯一的真實來源,用 `python3` 讀(此 plugin 本來就依賴 python3,不引入新相依)。

## Error flow

- `installPath` 讀不到(key 不存在 / JSON 壞)→ python 拋例外,`set -e` 中止安裝並顯示錯誤,不會留下半套狀態。
- 非本地安裝 → `[[ -d ]]` 為 false,整段跳過。

## Files to modify

- `install.sh`(僅在 install 步驟後插入一段,約 18 行 shell)。

## Reuse

沿用既有 `SOURCE`、`PLUGIN_NAME`、`MARKETPLACE_NAME` 變數;沿用 CLI 的登記機制,不重造。

## Function length

純 shell 線性腳本,無 function,不涉 40 行 function 上限。

## Test strategy

手動驗證(無自動測試框架):
1. 跑 `./install.sh` → 確認 `installPath` 是 symlink(`ls -l` 指向 repo)。
2. 改 repo 內 skill 檔 → `/reload-plugins` → 確認改動即時生效,無需重裝。
3. 模擬非本地安裝路徑時該段跳過(`$SOURCE/plugins/design-gate` 不存在則不建立 symlink)。

## Minimal viable solution

如上;不加 dev/prod flag、不加 idempotent 檢查(symlink 已存在時 `rm -rf` + 重建即可)。

## Risk / Open question

- Risk:`rm -rf "$INSTALL_PATH"` 作用於 CLI 剛產生的 cache 路徑;若 `installPath` 讀成空字串會誤刪 → 已用 `[[ -n "$INSTALL_PATH" ]]` 防護。
- Open question:無。
