# Portal-POC_demo｜混合雲企業檔案門戶

以 Python 與 Streamlit 實作的企業檔案管理概念驗證，整合 Google Drive、模擬 NAS 與 Gemini AI。此 repo 是經過敏感資訊清理的作品展示版本，內附文件均為虛構示範資料。

## 主要功能

| 功能 | 說明 | 所需設定 |
| --- | --- | --- |
| 檔案儀表板 | 列出雲端與本機檔案，提供檢視入口 | 本機 NAS 可直接使用；雲端需 Drive 授權 |
| 跨平台檢索 | 檔名／路徑搜尋，以及 AI 語意檢索 | 一般搜尋可直接使用；AI 需自己的 API key |
| 智慧歸檔 | 擷取 PDF、DOCX、TXT 內容，建議檔名與目錄，供使用者確認後歸檔 | AI 需 API key；雲端歸檔另需 Drive 授權 |
| 知識管理問答 | 根據模擬 NAS 文件內容回答問題 | 需自己的 API key |

## 本機執行

使用 Python 3.10 以上版本，在專案目錄執行：

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS / Linux：source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

不設定金鑰也能瀏覽示範檔案並使用一般搜尋。側邊欄提供「請輸入您的 API key」欄位；輸入自己的 Gemini API key 後，才會啟用 AI 功能。金鑰欄位使用密碼顯示，程式不將其寫入 repo。

也可複製 `.env.example` 為 `.env`，填入自己的設定：

```dotenv
GEMINI_API_KEY="請輸入您的API key"
GDRIVE_FOLDER_ID="請輸入您的Google Drive資料夾ID"
GEMINI_MODEL=gemini-3.1-flash-lite
```

範例文字會被視為未設定。模型名稱可改成自己帳號可使用的模型。此版本以 `google-genai` SDK 呼叫 Gemini，每次請求使用目前工作階段的 API key。

## Google Drive 設定（選用）

1. 在自己的 Google Cloud 專案啟用 Google Drive API，完成 OAuth 同意畫面與測試使用者設定。
2. 建立「桌面應用程式」OAuth 用戶端，下載 JSON 並在本機命名為 `client_secret.json`。`client_secret.example.json` 僅展示欄位結構，不包含可使用的憑證。
3. 建立自己的測試資料夾，將資料夾網址最後一段 ID 填入 `.env` 的 `GDRIVE_FOLDER_ID`。
4. 執行 `python test_drive.py`，在自己的電腦完成瀏覽器授權。產生的 `token.json` 僅保存在本機；重新啟動 Streamlit 即可載入授權。
5. 若要驗證上傳，可另執行 `python test_drive.py --upload`；這會將 `hello.txt` 上傳到您設定的資料夾。

PoC 使用完整 Drive 讀寫 scope，請使用自己的測試帳號與資料夾。本版本使用 OAuth，不需要服務帳戶 `credentials.json`。

## 專案結構

```text
app.py                       Streamlit 介面與四個功能頁籤
config.py                    本機環境設定
storage.py                   模擬 NAS 歸檔路徑檢查
test_drive.py                本機 OAuth 授權與選用上傳測試
requirements.txt             已驗證的直接依賴版本
.env.example                 環境設定範例
client_secret.example.json   OAuth 憑證結構範例
mock_storage/nas/            虛構示範文件
```

## 展示範圍與限制

- NAS 使用專案內資料夾模擬，尚未整合真實 NAS 權限系統。
- 「開啟檔案／路徑」操作執行程式所在的電腦；遠端部署時無法開啟訪客電腦的檔案總管。
- AI 語意檢索目前依據檔名與路徑判斷；KM 將本機文件摘要放入提示詞，未使用向量資料庫。PDF 最多讀前三頁、DOCX 前二十段，單文件最多 1,500 字元；掃描型 PDF 未提供 OCR。
- Drive 清單目前最多列出指定資料夾內 50 個檔案，未遞迴或分頁。
- AI 功能會將相關檔名、路徑、問題或文件摘要傳送到 Google Gemini；請使用可供示範的資料。實際 API 請求依自己的帳號額度與計費規則執行。
- 此版本供本機概念驗證，尚未具備正式系統的登入、角色權限、稽核、惡意上傳防護或多使用者隔離。

## 公開版資料處理

此 repo 以清理後的檔案建立獨立 Git 歷史，未帶入來源專案的舊提交、API key、Drive 資料夾 ID、OAuth token、服務帳戶私鑰或企業原始文件。`.gitignore` 排除本機 `.env`、憑證、token 與執行時新增的 NAS 文件；僅保留指定的兩份虛構範例。

## 官方設定參考

- [Google GenAI SDK](https://ai.google.dev/gemini-api/docs/libraries)
- [Gemini SDK 遷移說明](https://ai.google.dev/gemini-api/docs/migrate)
- [Google Drive Python quickstart](https://developers.google.com/workspace/drive/api/quickstart/python)
