# AI Meeting Room （人工智能會議室）

讓多個 AI 模型在會議中協作討論的終端應用程式。你提出議題，由 AI 規劃助手設計與會者（例如產品經理、工程師、設計師），接著這些 AI 參與者會根據各自的角色和性格即時討論，並自動產生會議記錄。

## 安裝

### 1. 安裝 Python

需要 Python 3.11 以上版本。如果你的電腦還沒有安裝 Python：

1. 前往 https://www.python.org/downloads/
2. 下載最新版本的 Python 安裝程式
3. 執行安裝程式，**務必勾選「Add Python to PATH」**
4. 安裝完成後，開啟終端機確認安裝成功：

```
python --version
```

> 上方灰色區塊中的文字是要在**終端機**中輸入的指令。
> Windows 使用者請開啟「命令提示字元」或「PowerShell」（按 Win+R，輸入 `cmd` 或 `powershell`，按 Enter）。
> macOS 使用者請開啟「終端機」應用程式。

如果安裝時忘記勾選「Add Python to PATH」，可以重新執行安裝程式，選擇「Modify」，然後勾選「Add Python to environment variables」。或者解除安裝後重新安裝，這次記得勾選。

### 2. 下載程式碼

先在終端機中用 `cd` 指令切換到你想存放程式碼的路徑，例如：

```
cd C:\Users\你的使用者名稱\Desktop
```

將「你的使用者名稱」替換為你的使用者名稱。

然後下載程式碼：

```
git clone https://github.com/Richard-Wong-1999/ai_meeting_room.git
cd ai_meeting_room
```

如果你沒有安裝 git，也可以在 GitHub 頁面點擊綠色的「Code」按鈕，選擇「Download ZIP」，解壓縮到你想要的位置，再用終端機進入該資料夾。

### 3. 安裝程式及相依套件

在終端機中確認你位於專案資料夾內，然後執行：

```
pip install .
```

這會自動安裝程式所需的所有相依套件（Textual、OpenAI SDK、Pydantic、PyYAML、python-dotenv）。

### 4. 取得 Poe API Key

本程式透過 Poe API 呼叫各家 LLM（GPT、Claude、Gemini 等），因此需要一組 Poe API key。

取得方式：

1. 前往 https://poe.com/ 並登入（如果沒有帳號需要先註冊）
2. 登入後前往 https://poe.com/api_key
3. 點擊「Generate API Key」產生一組 key
4. 複製產生的 key（格式類似 `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`）

> 注意：本程式透過 Poe API 呼叫 AI 模型，每次呼叫會消耗 Poe 點數。使用前需要先在 https://poe.com/settings 購買點數。

### 5. 設定 API Key

在專案根目錄建立一個名為 `.env` 的檔案（注意檔名以點開頭），內容如下：

```
POE_API_KEY=貼上你的key
```

將「貼上你的key」替換為你在上一步複製的 API key，不需要加引號。

## 啟動

在終端機中進入專案資料夾，然後執行：

```
python -m src
```

> 如果出現「'python' is not recognized」之類的錯誤，請改用 `py -m src`。
> 這取決於你的系統環境，兩者功能相同。

程式會顯示啟動畫面，接著進入主選單。

## 使用流程

### 主選單

```
============================================================
  AI 會議室
============================================================

主選單：
  1 - 新會議
  2 - 載入會議
  3 - 管理會議記錄
  4 - 模型設定
  5 - 會議設定
  v - 檢視目前設定
  q - 離開
```

輸入對應的數字或字母後按 Enter 執行。

### 開始新會議

選擇 `1` 後進入參與者設計階段：

1. 輸入會議標題
2. 用自然語言向 AI 規劃助手描述你的需求（例如「我要討論產品策略，需要產品經理、技術負責人和設計師」）
3. AI 會建議 2-6 個參與者，包含角色、性格和使用的模型
4. 你可以繼續對話調整設計（例如「把技術負責人的模型換成 claude-opus-4.6」、「再加一個市場分析師」）
5. 滿意後輸入 `/start` 確認並開始會議

參與者設計階段的指令：
- `/start` — 確認設計並開始會議
- `/back` — 返回主選單
- `/quit` — 離開程式

### 會議進行中

會議介面分為三個區域：
- **左側** — 聊天面板，顯示所有對話
- **右側** — 會議記錄面板，自動產生每輪摘要
- **底部** — 輸入框

你輸入訊息後，主持人會詢問所有 AI 是否想發言，想發言的 AI 會按優先順序依次回應。每輪結束後自動產生摘要。

會議中的快捷鍵：
- `Ctrl+S` — 手動儲存會議
- `Ctrl+Q` — 離開會議（自動儲存）

> 注意：如果在 AI 發言途中按 `Ctrl+Q`，當輪對話會被中斷，已完成發言的部分會被儲存。之後重新載入這場會議時，會從新的一輪對話開始，被中斷的那輪對話不會繼續。

### 載入會議

選擇 `2` 可以載入之前儲存的會議，繼續討論。

### 管理會議記錄

選擇 `3` 可以檢視和刪除已儲存的會議。

### 模型設定

選擇 `4` 可以設定：
- **規劃助手模型** — 用於參與者設計的 AI（預設：gemini-3-pro）
- **會議記錄模型** — 用於產生會議摘要（預設：gpt-4o）
- **可用模型清單** — 會議參與者能使用的模型，可新增、移除或重設為預設值

### 會議設定

選擇 `5` 可以調整：
- **每輪最大回合數**（1-50，預設：10）— 單輪中 AI 回應的最大次數
- **相關性逾時**（5-120 秒，預設：20）— 等待 AI 決定是否要發言的時間
- **回應逾時**（10-300 秒，預設：90）— 等待 AI 產生完整回應的時間

所有設定會自動儲存，下次啟動時自動載入。

## 新增模型

程式內建了常用的模型（見下方清單），如果你想使用其他 Poe API 支援的模型：

1. 在主選單選擇 `4`（模型設定）
2. 選擇 `3`（管理可用模型）
3. 選擇 `a`（新增模型）
4. 輸入模型名稱，名稱必須與 Poe API 中的名稱完全一致（例如 `gemini-2-flash`）

Poe API 支援的完整模型列表見 https://poe.com/api/models 。

## 內建模型

以下是預設可用的模型（皆透過 Poe API 呼叫）：

| 廠商 | 模型 |
|------|------|
| OpenAI | gpt-5.2, gpt-4o, gpt-4o-search, o3, o4-mini |
| Anthropic | claude-opus-4.6, claude-sonnet-4.5, claude-haiku-4.5 |
| Google | gemini-3-pro, gemini-3-flash |
| xAI | grok-4 |
| 其他 | deepseek-r1, llama-4-maverick-t, qwen3-max |

## 資料儲存位置

| 項目 | 路徑 |
|------|------|
| 偏好設定 | `~/.ai_meeting_room/preferences.yaml` |
| 會議記錄 | `~/.ai_meeting_room/conversations/*.yaml` |

> `~` 代表你的使用者主目錄。Windows 上通常是 `C:\Users\你的使用者名稱`。

## 技術細節

- [Textual](https://github.com/Textualize/textual) — 終端 UI 框架
- [OpenAI SDK](https://github.com/openai/openai-python) — 透過 Poe 相容 API 呼叫各家模型
- [Pydantic](https://github.com/pydantic/pydantic) — 資料驗證
- [PyYAML](https://github.com/yaml/pyyaml) — 設定檔處理
- [python-dotenv](https://github.com/theskumar/python-dotenv) — 環境變數管理
