# Agent Harness 後設認知工作流

讓 Agent 在每一步都知道自己做了什麼、確定到什麼程度、哪裡可能錯，**並且不讓小任務被流程拖慢**。
安裝後 Agent 就能直接照著做：規則寫成「何時 → 做什麼 → 完成條件」，關鍵規則由 hook 自動執行，不靠 Agent 記得。

## 安裝

**Claude Code（plugin）**

```
/plugin install metacognitive-harness --marketplace jeffery8910/agent-harness-metacognition
```

舊版 Claude Code 分兩步：

```
/plugin marketplace add jeffery8910/agent-harness-metacognition
/plugin install metacognitive-harness@jeffery-harness
```

> 這個 repo 是私人的，安裝的電腦需要能用 git 存取它（例如已登入 `gh`）。

要啟用部署前的帳號檢查，在專案的 `.claude/settings.json` 加上：

```json
{ "env": { "EXPECTED_CF_EMAIL": "你的 Cloudflare 帳號" } }
```

**其他 Agent（Codex、Cursor、Gemini CLI 等）**

把 [AGENTS.md](AGENTS.md) 複製到專案根目錄。Claude Code 不用 plugin 的話，再複製 [templates/CLAUDE.md](templates/CLAUDE.md)，它會用 `@AGENTS.md` 載入規則。

## 裝了之後會發生什麼

| 元件 | 什麼時候作用 | 做什麼 |
|---|---|---|
| `metacognitive-workflow` skill | 會改檔案、多步驟、部署、發布、交付報告時 | 依任務規模套用 R1–R11 工作迴圈 |
| `verify_write.py` hook | 每次 Write／Edit／MultiEdit 之後 | 讀回檔案比對，沒寫進去就告訴 Agent 不要回報完成 |
| `preflight_deploy.py` hook | 執行 `wrangler deploy` 之前 | 帳號不是 `EXPECTED_CF_EMAIL` 就擋下 |
| `reviewer` agent | 高風險成果交付前 | 只看成果和原始資料的獨立審查 |

## 為什麼 Agent 會願意採用

- **依規模套用**：問答和唯讀查詢只用一條規則（回報分級），不會為了流程而流程。
- **由 hook 執行，不靠記憶**：寫入後讀回、部署前檢查帳號都是自動的，不佔 Agent 的注意力。
- **完成條件明確**：每條規則都寫了怎樣算做完，Agent 不用猜。
- **有停損點**：同一個做法最多重試 2 次，避免卡在迴圈。

## 規則一覽

`界定範圍 → 前置檢查 → 執行 → 驗證 → 回報 → 沉澱`

| 規則 | 一句話 |
|---|---|
| R1 界定範圍 | 開工前寫下目標、排除項目、完成條件、輸出格式 |
| R2 前置檢查 | 不可逆動作前確認身分、環境、目標，不符就停 |
| R3 動作後驗證 | 不相信工具回報的成功；寫檔讀回、部署讀線上版本 |
| R4 外部來源判定 | 成功由測試、CI、線上 API 判定，不是自己宣告 |
| R5 分支與 PR | 不直接推主分支，不自己合併 |
| R6 留下痕跡 | 任務清單、不重複的 log 檔名、腳本自己結束 |
| R7 獨立審查 | 高風險成果交給 reviewer，不給它你的結論 |
| R8 回報分級 | 已驗證（附來源）／推論（附依據）／未驗證（怎麼補） |
| R9 選擇理由 | 一句話寫出候選方案和取捨 |
| R10 沉澱經驗 | 踩坑就在 CLAUDE.md「已知陷阱」加一行規則 |
| R11 主動更正 | 說錯了就明說哪句錯、改成什麼 |

完整規則在 [AGENTS.md](AGENTS.md)（和 skill 內容相同，測試會檢查兩者一致）。

## 規則的依據與案例

每條規則都來自實際專案（SolveMate、猜歌搶答、揪團日曆、資安報導寫作）踩過的坑。給人看的說明在 `docs/`，依性質分四類：

| 類別 | 回答的問題 | 文件 | 對應規則 |
|---|---|---|---|
| 認知監控 | 我有多確定？哪些沒驗證？ | [01-cognition.md](docs/01-cognition.md) | R8、R9 |
| 行動控制 | 動手前擋什麼？動手後怎麼確認？ | [02-action.md](docs/02-action.md) | R1、R2、R3、R6 |
| 架構設計 | 誰有權判定？錯了怎麼回頭？ | [03-architecture.md](docs/03-architecture.md) | R4、R5、R7 |
| 學習反思 | 踩過的坑怎麼不再踩？ | [04-learning.md](docs/04-learning.md) | R7、R10、R11 |

快速版：[docs/checklist.md](docs/checklist.md)。

## 範例

- [examples/evidence-report/](examples/evidence-report/)：R8 的 JSON 格式和檢查器。派子 Agent 做研究時，要求它照這個格式回報，再用 `python3 check_evidence.py report.json` 檢查。
- [examples/server-authority/judge.mjs](examples/server-authority/judge.mjs)：R4 的最小示範。同一組搶答，用客戶端時間和伺服器時間判定會得到不同結果。

## 結構

```
.claude-plugin/        plugin 與 marketplace 設定
skills/                metacognitive-workflow skill 與回報範本
agents/reviewer.md     獨立審查 agent
hooks/                 寫入後讀回、部署前檢查
AGENTS.md              通用規則（給其他 Agent）
templates/CLAUDE.md    含「已知陷阱」的專案範本
docs/                  規則依據與案例（給人看）
examples/              可執行範例
tests/run_tests.py     自動測試
```

## 測試

```bash
python3 tests/run_tests.py      # 需要 Python 3.9+、Node.js 18+，不需安裝套件
claude plugin validate .        # 驗證 plugin 結構
```

> hook 會自動使用電腦上的 `python3` 或 `python`。Windows 上如果 `python3` 只是 Microsoft Store 的捷徑，請到「設定 → 應用程式 → 應用程式執行別名」把它關掉。
