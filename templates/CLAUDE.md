# 專案規則

@AGENTS.md

<!-- 上面這行會載入通用的後設認知規則。把 AGENTS.md 一起複製到專案根目錄。
     已安裝 metacognitive-harness plugin 的話，可以刪掉這行，改用 plugin 的 skill。 -->

## 已知陷阱

工具行為和預期不同時，在這裡加一行（R10）。寫成下次可以照做的規則，不要寫成事件紀錄。
以下是實際專案累積的範例，留下適用的，刪掉不適用的。

- 透過遠端工具寫入使用者電腦的檔案後，一定要讀回確認；曾發生回報成功但檔案沒更新。
- 瀏覽器自動化：導航後先截圖一次，頁面才會完整渲染，之後再跑 JavaScript。
- Google Maps 儲存按鈕在第一次儲存後會從「儲存」變成「已儲存」，判斷時兩種都要接受。
- Claude Docs：更新前先讀取文件拿區塊 ID，不要用建立時的骨架 ID。
- Windows `.bat`：log 寫到不重複的檔名（`logs\deploy-%RANDOM%.txt`），逾時自動關閉，不要用 `pause`。
- Cloudflare Workers：`assets.run_worker_first` 只列 API 路由（`/api/*`、`/ws/*`）；不要手動加 `/host` 這類頁面路由，靜態資源會自己處理。
- Cloudflare 連接器不能部署 Worker；要用 `wrangler deploy` 或 GitHub 連動的 Workers Builds。
