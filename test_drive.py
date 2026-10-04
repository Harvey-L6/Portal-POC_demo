"""本機 Google Drive OAuth 授權；加上 --upload 才會上傳示範檔案。"""
import argparse
import json
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload
from config import BASE_DIR, GDRIVE_FOLDER_ID

# 此 PoC 會列出既有資料夾，因此使用完整 Drive scope。
SCOPES = ["https://www.googleapis.com/auth/drive"]

def authenticate():
    token_path = BASE_DIR / "token.json"
    client_path = BASE_DIR / "client_secret.json"
    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not client_path.exists():
                raise ValueError("請先放入自己的桌面應用程式 OAuth 憑證 client_secret.json。")
            data = json.loads(client_path.read_text(encoding="utf-8"))
            installed = data.get("installed", {})
            if not installed.get("client_id") or any(
                str(installed.get(field, "")).startswith(("請輸入", "YOUR_"))
                for field in ("client_id", "client_secret")
            ):
                raise ValueError("client_secret.json 仍是設定範例，請換成自己的 OAuth 憑證。")
            flow = InstalledAppFlow.from_client_secrets_file(str(client_path), SCOPES)
            creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json(), encoding="utf-8")
        token_path.chmod(0o600)
    return creds

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upload", action="store_true", help="授權後上傳 hello.txt 至您設定的資料夾")
    args = parser.parse_args()
    if not GDRIVE_FOLDER_ID:
        parser.error("請先在 .env 設定自己的 GDRIVE_FOLDER_ID。")
    try:
        creds = authenticate()
        print("授權完成，token.json 已保存在本機。可重新啟動 Streamlit。")
        if args.upload:
            service = build("drive", "v3", credentials=creds)
            media = MediaFileUpload(str(BASE_DIR / "hello.txt"), mimetype="text/plain")
            service.files().create(
                body={"name": "Portal_Demo_OAuth_測試上傳.txt", "parents": [GDRIVE_FOLDER_ID]},
                media_body=media, fields="id",
            ).execute()
            print("示範文件已上傳至您設定的 Google Drive 資料夾。")
    except Exception as exc:
        # 不把可能含有憑證內容的底層錯誤訊息輸出到紀錄。
        print(f"授權或上傳失敗（{type(exc).__name__}），請檢查本機設定與 OAuth 授權。")
        raise SystemExit(1) from None

if __name__ == "__main__":
    main()
