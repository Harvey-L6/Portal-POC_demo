import streamlit as st
from google import genai
from config import BASE_DIR, MOCK_NAS, GDRIVE_FOLDER_ID, AI_MODEL_VERSION, GEMINI_API_KEY
from storage import safe_nas_path
from pypdf import PdfReader
from docx import Document
import datetime
import os
import json
import platform
import subprocess

# Google API 相關套件
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaIoBaseUpload

st.set_page_config(page_title="Demo 混合雲企業門戶", layout="wide")

# ==========================================
# 1. 系統環境與 Google Drive 初始化設定
# ==========================================
os.makedirs(MOCK_NAS, exist_ok=True)
GDRIVE_FOLDER_URL = f"https://drive.google.com/drive/folders/{GDRIVE_FOLDER_ID}"

def get_gdrive_service():
    """僅在使用者設定自己的資料夾與授權檔案時建立連線。"""
    token_path = BASE_DIR / "token.json"
    if not GDRIVE_FOLDER_ID or not token_path.exists():
        return None
    try:
        creds = Credentials.from_authorized_user_file(
            str(token_path), ["https://www.googleapis.com/auth/drive"]
        )
        return build("drive", "v3", credentials=creds)
    except Exception:
        st.sidebar.warning("Google Drive 授權無法載入，請重新執行 test_drive.py。")
        return None

gdrive_service = get_gdrive_service()
API_KEY = st.sidebar.text_input(
    "Gemini API key", value=GEMINI_API_KEY, type="password",
    placeholder="請輸入您的 API key",
)
AI_READY = bool(API_KEY.strip()) and not API_KEY.strip().startswith(("請輸入", "YOUR_"))
st.sidebar.caption("未設定 API key 時，仍可使用檔案總覽與一般搜尋。")

def generate_ai_content(prompt):
    """每次請求使用此工作階段的金鑰，不共用全域 API 設定。"""
    if not AI_READY:
        raise ValueError("請輸入您的 API key")
    with genai.Client(api_key=API_KEY.strip()) as client:
        return client.models.generate_content(model=AI_MODEL_VERSION, contents=prompt)

# ==========================================
# 2. 核心 Helper Functions
# ==========================================
def open_local_file(filepath):
    """開啟本機檔案"""
    try:
        if platform.system() == "Windows":
            os.startfile(os.path.normpath(filepath))
        elif platform.system() == "Darwin":
            subprocess.run(["open", filepath])
        else:
            subprocess.run(["xdg-open", filepath])
    except Exception as e:
        st.error(f"無法開啟檔案: {e}")

def open_local_folder(filepath):
    """開啟所在資料夾，並於前景反白選取該檔案"""
    try:
        if platform.system() == "Windows":
            # 使用 /select 參數，可強制將檔案總管喚醒至前景，並反白目標檔案
            subprocess.Popen(f'explorer /select,"{os.path.normpath(filepath)}"')
        elif platform.system() == "Darwin":
            subprocess.run(["open", "-R", filepath])
        else:
            subprocess.run(["xdg-open", os.path.dirname(filepath)])
    except Exception as e:
        st.error(f"無法開啟目錄: {e}")

def list_all_files():
    """取得雲端與地端檔案清單"""
    file_list = []
    if gdrive_service:
        try:
            results = gdrive_service.files().list(
                q=f"'{GDRIVE_FOLDER_ID}' in parents and trashed=false",
                fields="files(id, name, webViewLink, size)",
                pageSize=50
            ).execute()
            for item in results.get('files', []):
                file_list.append({
                    "Platform": "☁️ Google Drive",
                    "FileName": item.get('name'),
                    "Path": f"/GoogleDrive/{item.get('name')}",
                    "FullPath": item.get('id'),
                    "Link": item.get('webViewLink'),
                    "IsCloud": True
                })
        except Exception:
            pass
            
    for root, _, files in os.walk(MOCK_NAS):
        for f in files:
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, MOCK_NAS)
            file_list.append({
                "Platform": "🖥️ 地端 NAS",
                "FileName": f,
                "Path": f"/NAS/{rel_path}",
                "FullPath": full_path,
                "IsCloud": False
            })
    return file_list

def extract_text(file_obj, filename):
    """擷取文件摘要內文"""
    text = ""
    try:
        if filename.endswith(".pdf"):
            reader = PdfReader(file_obj)
            for page in reader.pages[:3]:
                text += page.extract_text() or ""
        elif filename.endswith(".docx"):
            doc = Document(file_obj)
            text = "\n".join([p.text for p in doc.paragraphs[:20]])
        elif filename.endswith(".txt"):
            text = file_obj.read().decode("utf-8")
    except Exception:
        pass
    if hasattr(file_obj, 'seek'):
        file_obj.seek(0)
    return text[:1500]

def extract_text_from_local(filepath):
    """讀取本地實體檔案內文 (供 KM 知識庫使用)"""
    with open(filepath, 'rb') as f:
        return extract_text(f, filepath)

# ==========================================
# 3. 網頁 UI 與 系統頁籤
# ==========================================
st.title("Demo 混合雲企業檔案門戶 (Enterprise Portal)")
st.caption(f"整合 Google Drive 與 NAS 儲存服務 ｜ 語言模型：{AI_MODEL_VERSION}")
st.caption("公開示範版｜內附虛構文件；本機檔案操作適用於在自己的電腦執行。")

# 側邊欄狀態指示
if not gdrive_service:
    st.sidebar.error("連線狀態：未授權 Google Drive")
else:
    st.sidebar.success("連線狀態：Google Drive API 已連線")
st.sidebar.info(f"AI 引擎：{AI_MODEL_VERSION}")

# 系統頁籤配置
tab1, tab2, tab3, tab4 = st.tabs(["檔案儀表板", "跨平台檢索", "智慧歸檔系統", "知識管理問答 (KM)"])

# --- TAB 1: 檔案儀表板 ---
with tab1:
    st.subheader("雲地混合檔案總覽")
    files = list_all_files()
    if not files:
        st.info("目前儲存庫尚無檔案記錄。")
    else:
        for file in files:
            col1, col2, col3, col4 = st.columns([2, 3, 2, 3])
            with col1:
                st.markdown(f"**{file['Platform']}**")
            with col2:
                st.text(file['FileName'])
            with col3:
                st.caption(file['Path'])
            with col4:
                if file['IsCloud']:
                    st.link_button("🌐 線上檢視", url=file['Link'])
                    st.link_button("📁 開啟雲端目錄", url=GDRIVE_FOLDER_URL)
                else:
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("⚙️ 開啟檔案", key=f"f_{file['FullPath']}"):
                            open_local_file(file['FullPath'])
                    with c2:
                        if st.button("📁 開啟路徑", key=f"p_{file['FullPath']}"):
                            open_local_folder(file['FullPath'])
            st.divider()

# --- TAB 2: 跨平台檢索 ---
with tab2:
    st.subheader("檔案搜尋引擎")
    
    search_mode = st.radio("檢索模式：", ["一般字串比對", "AI 語意檢索"], horizontal=True)
    query = st.text_input("輸入檢索關鍵字：")
    search_button = st.button("執行搜尋", type="primary", disabled="AI" in search_mode and not AI_READY)
    
    if search_button and query:
        files = list_all_files()
        
        # 一般字串比對
        if "一般" in search_mode:
            st.info(f"搜尋中： {query}")
            results = [f for f in files if query.lower() in f['FileName'].lower() or query.lower() in f['Path'].lower()]
            if not results:
                st.warning("查無符合條件的檔案。")
            else:
                st.success(f"搜尋結果：共 {len(results)} 筆檔案符合")
                for f in results:
                    col_card, col_action = st.columns([5, 2])
                    with col_card:
                        st.markdown(f"**📄 {f['FileName']}**")
                        st.caption(f"儲存位置: {f['Platform']} | 路徑: {f['Path']}")
                    with col_action:
                        if f['IsCloud']:
                            st.link_button("🌐 線上檢視", url=f['Link'])
                            st.link_button("📁 開啟目錄", url=GDRIVE_FOLDER_URL)
                        else:
                            c1, c2 = st.columns(2)
                            with c1:
                                if st.button("⚙️ 開啟檔案", key=f"n_f_{f['FullPath']}"):
                                    open_local_file(f['FullPath'])
                            with c2:
                                if st.button("📁 開啟路徑", key=f"n_p_{f['FullPath']}"):
                                    open_local_folder(f['FullPath'])
                    st.divider()

        # AI 語意檢索
        else:
            with st.spinner("系統分析中，請稍候..."):

                search_prompt = f"""
                你是企業搜尋助手。請依據【搜尋需求】從【資料庫】挑選最相關的檔案。
                【搜尋需求】: {query}
                【資料庫】: {json.dumps([{'filename': f['FileName'], 'platform': f['Platform'], 'path': f['Path']} for f in files], ensure_ascii=False)}
                請輸出 JSON 格式陣列，需包含以下鍵值: filename, platform, relevance_score, match_reason
                """
                try:
                    response = generate_ai_content(search_prompt)
                    search_results = json.loads(response.text.replace("```json", "").replace("```", "").strip())
                    st.success(f"語意分析完成：共判定 {len(search_results)} 筆高度相關文件")
                    
                    for idx, res in enumerate(search_results):
                        matched_file = next((f for f in files if f['FileName'] == res.get('filename')), None)
                        col_card, col_action = st.columns([5, 2])
                        
                        with col_card:
                            st.markdown(f"**📄 {res.get('filename')}** (關聯度: {res.get('relevance_score')})")
                            st.caption(f"儲存位置: {res.get('platform')}")
                            st.info(f"系統判定依據：{res.get('match_reason')}")
                            
                        with col_action:
                            if matched_file:
                                if matched_file['IsCloud']:
                                    st.link_button("🌐 線上檢視", url=matched_file['Link'])
                                    st.link_button("📁 開啟目錄", url=GDRIVE_FOLDER_URL)
                                else:
                                    c1, c2 = st.columns(2)
                                    with c1:
                                        if st.button("⚙️ 開啟檔案", key=f"s_f_{matched_file['FullPath']}_{idx}"):
                                            open_local_file(matched_file['FullPath'])
                                    with c2:
                                        if st.button("📁 開啟路徑", key=f"s_p_{matched_file['FullPath']}_{idx}"):
                                            open_local_folder(matched_file['FullPath'])
                        st.divider()
                except Exception as e:
                    st.error(f"分析失敗（{type(e).__name__}），請檢查 API key、模型設定與服務額度。")

# --- TAB 3: 智慧歸檔系統 ---
with tab3:
    st.subheader("文件上傳與系統分析歸檔")
    SYSTEM_PROMPT = """
    你是一位企業文件管理系統 AI。請閱讀文件摘要，並輸出標準化 JSON 格式：
    1. "suggested_filename": 建議標準化檔名 (格式: 日期_文件類別_主題_版本.副檔名)
    2. "target_platform": "Google Drive" 或 "NAS" (報價/合約/一般文件建議雲端；SOP/技術規格建議地端)
    3. "suggested_subpath": 建議分類子目錄
    4. "summary": 文件摘要重點 (100字內)
    """
    
    uploaded_file = st.file_uploader("請選擇或拖曳檔案進行上傳", type=["pdf", "docx", "txt"])
    
    if uploaded_file:
        if st.button("執行文件分析", type="primary", disabled=not AI_READY):
            with st.spinner("讀取文件內容與分析中..."):

                file_text = extract_text(uploaded_file, uploaded_file.name)
                prompt = f"{SYSTEM_PROMPT}\n\n【原始檔名】: {uploaded_file.name}\n【執行日期】: {datetime.date.today().strftime('%Y%m%d')}\n【文件內文摘要】:\n{file_text}"
                try:
                    response = generate_ai_content(prompt)
                    st.session_state['ai_draft'] = response.text
                    st.session_state['up_file'] = uploaded_file
                except Exception as e:
                    st.error(f"分析失敗（{type(e).__name__}），請檢查 API key、模型設定與服務額度。")

    if 'ai_draft' in st.session_state:
        st.success("分析完成，請確認或調整以下歸檔資訊：")
        try:
            draft_data = json.loads(st.session_state['ai_draft'].replace("```json", "").replace("```", "").strip())
        except:
            draft_data = {"suggested_filename": st.session_state['up_file'].name, "target_platform": "NAS", "suggested_subpath": "General"}
            
        with st.form("archive_form"):
            col_a, col_b = st.columns(2)
            with col_a:
                edit_name = st.text_input("檔案名稱", value=draft_data.get("suggested_filename", ""))
                edit_path = st.text_input("分類目錄 (子路徑)", value=draft_data.get("suggested_subpath", ""))
            with col_b:
                platform_index = 0 if "Google" in draft_data.get("target_platform", "") else 1
                edit_platform = st.selectbox("儲存平台", ["Google Drive", "NAS"], index=platform_index)
                st.info(f"**文件摘要：**\n{draft_data.get('summary', '無內容摘要')}")
                
            submitted = st.form_submit_button("確認歸檔")
            
            if submitted:
                file_obj = st.session_state['up_file']
                file_obj.seek(0)
                try:
                    if edit_platform == "Google Drive":
                        if gdrive_service:
                            media = MediaIoBaseUpload(file_obj, mimetype='application/octet-stream', resumable=True)
                            file_metadata = {'name': edit_name, 'parents': [GDRIVE_FOLDER_ID]}
                            g_file = gdrive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
                            st.success(f"檔案已成功歸檔至 Google Drive (ID: {g_file.get('id')})")
                        else:
                            st.error("Google API 連線失敗，無法寫入。")
                    else:
                        final_path = safe_nas_path(MOCK_NAS, edit_path, edit_name)
                        os.makedirs(final_path.parent, exist_ok=True)
                        with open(final_path, "wb") as f:
                            f.write(file_obj.read())
                        st.success(f"檔案已成功歸檔至 NAS 目錄：{final_path}")
                    
                    if edit_platform == "NAS" or gdrive_service:
                        del st.session_state['ai_draft']
                except Exception as e:
                    st.error(f"寫入過程發生異常: {e}")

# --- TAB 4: 知識管理問答 (KM) ---
with tab4:
    st.subheader("知識管理問答系統")
    st.info("請輸入業務相關問題，系統將自動檢索內部知識庫(NAS)提供解答。")
    
    km_query = st.text_input("請輸入您的提問：")
    if st.button("產生解答", type="primary", disabled=not AI_READY) and km_query:
        with st.spinner("知識庫檢索與生成中..."):
            docs_context = ""
            for root, _, files in os.walk(MOCK_NAS):
                for f in files:
                    full_path = os.path.join(root, f)
                    content = extract_text_from_local(full_path)
                    docs_context += f"\n\n--- 來源檔案：{f} ---\n{content}"
            
            if not docs_context.strip():
                st.warning("目前知識庫內無相關文件紀錄，請先完成文件歸檔。")
            else:

                km_prompt = f"""
                你是企業內部的知識庫顧問。請根據以下【內部文獻】，專業、客觀地回答使用者的【問題】。
                若文獻中無相關資訊，請回覆「內部文件中目前無此資訊」。
                
                【問題】: {km_query}
                
                【內部文獻】:
                {docs_context}
                """
                try:
                    res = generate_ai_content(km_prompt)
                    st.success("系統解答：")
                    st.markdown(res.text)
                except Exception as e:
                    st.error(f"生成失敗（{type(e).__name__}），請檢查 API key、模型設定與服務額度。")
