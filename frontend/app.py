"""
Streamlit demo frontend cho Financial RAG Chatbot.
Gọi sang backend FastAPI qua BACKEND_URL (set trong docker-compose.yml).
"""

import os
import uuid
import requests
import json
import base64
import streamlit as st
from datetime import datetime, timezone


BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
APP_NAME = "Fragelerator"

COMPANY_OPTIONS = ["Tất cả", "FPT", "TheGioiDiDong", "Vinamilk", "HoaPhat"]
DOC_TYPE_OPTIONS = [
    "Tất cả",
    "Báo cáo tài chính quý",
    "Báo cáo tài chính năm",
    "Bản cáo bạch",
    "Hợp đồng tín dụng",
    "10-K",
    "10-Q",
]
YEAR_OPTIONS = ["Tất cả"] + list(range(2026, 2005, -1))
QUARTER_OPTIONS = ["Tất cả", "Báo cáo năm", 1, 2, 3, 4]

CONV_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
CONV_FILE = os.path.join(CONV_DIR, "conversations.json")
DEFAULT_TITLE = "Cuộc trò chuyện mới"

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def load_conversations() -> dict:
    if not os.path.exists(CONV_FILE):
        return {}
    try:
        with open(CONV_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        # File hỏng/đang ghi dở -- không để cả app crash, coi như chưa có
        # cuộc trò chuyện nào thay vì raise lỗi ra UI.
        return {}
 
 
def save_conversations(conversations: dict) -> None:
    os.makedirs(CONV_DIR, exist_ok=True)
    tmp_path = CONV_FILE + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(conversations, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, CONV_FILE)  # ghi qua file tạm rồi rename -- tránh hỏng file nếu crash giữa chừng khi ghi
 
 
def new_conversation() -> dict:
    conv_id = uuid.uuid4().hex
    now = _now_iso()
    return {
        "id": conv_id,
        "title": DEFAULT_TITLE,
        "created_at": now,
        "updated_at": now,
        "messages": [],
    }
 
 
def make_title_from_query(query: str, max_len: int = 45) -> str:
    """Tự đặt tên cuộc trò chuyện theo câu hỏi đầu tiên, giống ChatGPT/Claude."""
    q = " ".join(query.strip().split())
    return q if len(q) <= max_len else q[: max_len].rstrip() + "…"
 
 
def get_most_recent_id(conversations: dict) -> str:
    return max(conversations, key=lambda cid: conversations[cid].get("updated_at", ""))

def get_image_base64(file_path: str) -> str:
    if not os.path.exists(file_path):
        return ""
    ext = os.path.splitext(file_path)[1].lower().replace(".", "")
    mime_type = "image/webp" if ext == "webp" else "image/png"
    with open(file_path, "rb") as f:
        data = f.read()
    return f"data:{mime_type};base64,{base64.b64encode(data).decode()}"

# Lấy đường dẫn tới 2 icon trong thư mục icons/
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FOLDER_ICON_PATH = os.path.join(BASE_DIR, "icons", "folder.webp")
FILTER_ICON_PATH = os.path.join(BASE_DIR, "icons", "filter.png")
PLUS_ICON_PATH = os.path.join(BASE_DIR, "icons", "plus.png")

plus_icon_b64 = get_image_base64(PLUS_ICON_PATH)
folder_icon_b64 = get_image_base64(FOLDER_ICON_PATH)
filter_icon_b64 = get_image_base64(FILTER_ICON_PATH)

def fetch_documents():
    try:
        resp = requests.get(f"{BACKEND_URL}/documents/", timeout=180)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Không lấy được danh sách tài liệu: {e}")
        return []

def render_citations(citations: list) -> None:
    """Dropdown citation -- MẶC ĐỊNH THU GỌN (expanded=False), chỉ hiện
    danh sách nguồn khi người dùng bấm mũi tên mở ra. citations là
    ChatResponse.citations từ backend, mỗi item đã có sẵn 'index' + 'label'."""
    if not citations:
        return
    with st.expander(f"📎 Nguồn tham khảo ({len(citations)})", expanded=False):
        for c in sorted(citations, key=lambda c: c.get("index", 0)):
            label = c.get("label") or f"[{c.get('index', '?')}]"
            section = c.get("section_path") or c.get("section")
            section_str = ""
            if isinstance(section, list) and section:
                section_str = f" — *Mục: {' > '.join(str(s) for s in section)}*"
            elif isinstance(section, str) and section:
                section_str = f" — *Mục: {section}*"
            st.markdown(f"**{label}**{section_str}")

def render_intent(intent: dict | None) -> None:
    """Dropdown hiện CalculationIntent -- BƯỚC ĐẦU của quy trình Calculation
    (metric_key/ticker/year/quarter LLM trích xuất từ câu hỏi). Set kể cả
    khi metric_key không khớp được gì, nên có thể xuất hiện dù answer báo
    lỗi -- hữu ích để người dùng/dev thấy hệ thống đã hiểu câu hỏi thế nào."""
    if not intent:
        return
    with st.expander("Đầu vào đã trích xuất (Calculation Intent)", expanded=False):
        st.json(intent)

def _as_nonempty_list(plural_value, singular_value=None) -> list:
    """Chuẩn hoá response Calculation mới/cũ về list.

    Backend mới trả metric_specs/calculations; các response hoặc conversation
    cũ chỉ có metric_spec/calculation. Giữ fallback để lịch sử chat cũ vẫn
    render được sau khi nâng cấp frontend.
    """
    if isinstance(plural_value, list) and plural_value:
        return plural_value
    if singular_value:
        return [singular_value]
    return []

def render_metric_specs(metric_specs: list | None, metric_spec: dict | None = None) -> None:
    """Hiện TOÀN BỘ công thức/required_metrics của câu hỏi multi-metric.

    Mỗi phần tử metric_specs có dạng:
      {"roe": {...}}, {"roa": {...}}, ...
    Frontend cũ chỉ đọc metric_spec nên luôn mất các metric từ vị trí thứ 2.
    """
    specs = _as_nonempty_list(metric_specs, metric_spec)
    if not specs:
        return

    if len(specs) == 1:
        metric_key = next(iter(specs[0].keys()), "") if isinstance(specs[0], dict) else ""
        with st.expander(f"Công thức tính toán ({metric_key})", expanded=False):
            st.json(specs[0])
        return

    with st.expander(f"Công thức tính toán ({len(specs)} metrics)", expanded=False):
        for i, spec in enumerate(specs, start=1):
            if not isinstance(spec, dict):
                st.json(spec)
                continue
            metric_key = next(iter(spec.keys()), f"metric_{i}")
            st.markdown(f"**{i}. {metric_key}**")
            st.json(spec)

def render_calculation_outputs(calculations: list | None, calculation: dict | None = None) -> None:
    """Hiện TOÀN BỘ CalculationOutput tính thành công trong câu hỏi.

    Không gán metric_key theo index vì backend hiện chỉ lưu CalculationOutput
    thuần trong `calculations`; nếu một metric trước đó thiếu operand thì thứ tự
    `metric_specs` và `calculations` có thể lệch nhau.
    """
    outputs = _as_nonempty_list(calculations, calculation)
    if not outputs:
        return
    
    with st.expander("Kết quả tính toán (Calculation Output)", expanded=False):
        st.json(calculation)

st.set_page_config(page_title=f"{APP_NAME} | Financial RAG", page_icon="💬", layout="wide")

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@600;800&display=swap');
 
    .frag-logo {{
        font-family: 'Sora', 'Segoe UI', sans-serif;
        font-weight: 800;
        font-size: 2.1rem;
        line-height: 1.15;
        letter-spacing: -0.02em;
        margin: -3.5rem 0 0 0;
        background: linear-gradient(90deg, #FF4B4B 0%, #000000 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }}

    [data-testid="stSidebar"] hr {{
        margin-top: 0rem !important;
        margin-bottom: 0.8rem !important;
    }}

    .frag-tagline {{
        font-family: 'Sora', 'Segoe UI', sans-serif;
        font-size: 0.85rem;
        color: #8a8f98;
        margin-bottom: 0.3rem;
    }}

    /* Bỏ khung/viền cho 2 nút ✏️ và 🗑️ */
    [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] > div:nth-child(2) button,
    [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] > div:nth-child(3) button {{
        border: none !important;
        background: transparent !important;
        box-shadow: none !important;
        padding: 0 !important;
    }}

    .st-key-new_chat_btn button,
    .st-key-new_chat_btn button *,
    .st-key-new_chat_btn button p {{
        font-weight: 800 !important;
        font-size: 15px !important;
        color: #000000 !important;
    }}

    /* Căn giữa chữ và icon */
    .st-key-new_chat_btn button [data-testid="stMarkdownContainer"] p,
    .st-key-new_chat_btn button p {{
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }}

    /* --- CHÈN ICON VÀO TRƯỚC CHỮ --- */
    .st-key-new_chat_btn button [data-testid="stMarkdownContainer"] p::before,
    .st-key-new_chat_btn button p::before {{
        content: "" !important;
        display: inline-block !important;
        width: 18px !important;
        height: 18px !important;
        min-width: 18px !important;
        min-height: 18px !important;
        margin-right: 8px !important;
        background-image: url("{plus_icon_b64}") !important;
        background-size: contain !important;
        background-repeat: no-repeat !important;
        background-position: center !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)
 
if "conversations" not in st.session_state:
    st.session_state.conversations = load_conversations()
 
if "rename_target" not in st.session_state:
    st.session_state.rename_target = None

query_chat_id = st.query_params.get("chat_id")
 
if query_chat_id and query_chat_id in st.session_state.conversations:
    current_id = query_chat_id
elif st.session_state.conversations:
    current_id = get_most_recent_id(st.session_state.conversations)
    st.query_params["chat_id"] = current_id
else:
    _conv = new_conversation()
    st.session_state.conversations[_conv["id"]] = _conv
    save_conversations(st.session_state.conversations)
    current_id = _conv["id"]
    st.query_params["chat_id"] = current_id
 
current_conv = st.session_state.conversations[current_id]

with st.sidebar:
    # Tên chatbot, góc trái trên cùng
    st.markdown(f'<div class="frag-logo">{APP_NAME}</div>', unsafe_allow_html=True)
    st.divider()

    # Nút tạo cuộc trò chuyện mới
    if st.button("Cuộc trò chuyện mới", key="new_chat_btn", use_container_width=True):
        conv = new_conversation()
        st.session_state.conversations[conv["id"]] = conv
        save_conversations(st.session_state.conversations)
        st.query_params["chat_id"] = conv["id"]
        st.session_state.rename_target = None
        st.rerun()
 
    #st.markdown("💬 Lịch sử trò chuyện")
    st.markdown(
    f"<p style='color: #000000; font-weight: bold; font-size: 18px; margin-top: -10px; margin-left: 0px;'>💬 Lịch sử trò chuyện</p>",
    unsafe_allow_html=True
    )
    sorted_convs = sorted(
        st.session_state.conversations.values(),
        key=lambda c: c.get("updated_at", ""),
        reverse=True,
    )
 
    for conv in sorted_convs:
        is_active = conv["id"] == current_id
        title = conv.get("title") or DEFAULT_TITLE
 
        row = st.columns([0.72, 0.14, 0.14])
        if row[0].button(
            title,
            key=f"open_{conv['id']}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
        ):
            st.query_params["chat_id"] = conv["id"]
            st.session_state.rename_target = None
            st.rerun()
 
        if row[1].button("✏️", key=f"rename_{conv['id']}", help="Đổi tên", type="tertiary"):
            st.session_state.rename_target = conv["id"]
            st.rerun()
 
        if row[2].button("🗑️", key=f"delete_{conv['id']}", help="Xoá cuộc trò chuyện", type="tertiary"):
            del st.session_state.conversations[conv["id"]]
            if st.session_state.conversations:
                next_id = get_most_recent_id(st.session_state.conversations)
            else:
                _new = new_conversation()
                st.session_state.conversations[_new["id"]] = _new
                next_id = _new["id"]
            save_conversations(st.session_state.conversations)
            if conv["id"] == current_id:
                st.query_params["chat_id"] = next_id
            st.session_state.rename_target = None
            st.rerun()
 
        # Ô đổi tên inline, chỉ hiện cho đúng conversation đang chọn
        if st.session_state.rename_target == conv["id"]:
            new_title = st.text_input(
                "Tên mới",
                value=conv.get("title", ""),
                key=f"rename_input_{conv['id']}",
                label_visibility="collapsed",
            )
            rcol1, rcol2 = st.columns(2)
            if rcol1.button("Lưu", key=f"save_rename_{conv['id']}", use_container_width=True):
                conv["title"] = new_title.strip() or DEFAULT_TITLE
                conv["updated_at"] = _now_iso()
                save_conversations(st.session_state.conversations)
                st.session_state.rename_target = None
                st.rerun()
            if rcol2.button("Huỷ", key=f"cancel_rename_{conv['id']}", use_container_width=True):
                st.session_state.rename_target = None
                st.rerun()
 
    st.divider()

    # Upload file
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; gap: 10px; margin-top: 15px; margin-bottom: 12px;">
            <img src="{folder_icon_b64}" width="26" height="26" style="object-fit: contain;">
            <span style="font-size: 20px; font-weight: 700;">Tải tài liệu</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
 
    with st.form("upload_form", clear_on_submit=True):
        uploaded_files = st.file_uploader(
            "Tải tệp lên", type=["pdf"], accept_multiple_files=True
        )
        submitted = st.form_submit_button("Lưu")
 
    if submitted:
        if not uploaded_files:
            st.warning("Chưa chọn file nào.")
        else:
            for f in uploaded_files:
                try:
                    resp = requests.post(
                        f"{BACKEND_URL}/documents/upload",
                        files={"file": (f.name, f.getvalue(), "application/pdf")},
                        timeout=60,
                    )
                    if resp.status_code == 200:
                        st.success(f"Đã upload: {f.name}")
                    else:
                        st.error(f"Lỗi upload {f.name}: {resp.status_code} - {resp.text}")
                except requests.exceptions.RequestException as e:
                    st.error(f"Lỗi kết nối khi upload {f.name}: {e}")
 
    st.divider()
 
    # Filter
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; gap: 10px; margin-top: 15px; margin-bottom: 12px;">
            <img src="{filter_icon_b64}" width="26" height="26" style="object-fit: contain;">
            <span style="font-size: 20px; font-weight: 700;">Bộ lọc</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
 
    filter_company = st.selectbox("Công ty, Tập đoàn", COMPANY_OPTIONS)
    filter_doc_type = st.selectbox("Loại tài liệu", DOC_TYPE_OPTIONS)
    filter_year = st.selectbox("Năm", YEAR_OPTIONS)
    filter_quarter = st.selectbox("Quý", QUARTER_OPTIONS)
 
    all_docs = fetch_documents()

    valid_docs = [
        d for d in all_docs
        if d.get("document_id") 
        and d.get("file_name") 
        and str(d.get("document_id")).lower() != "none" 
        and str(d.get("file_name")).lower() != "none"
    ]

    filtered_docs = valid_docs
    if filter_company != "Tất cả":
        filtered_docs = [d for d in filtered_docs if d.get("company") == filter_company]
    if filter_doc_type != "Tất cả":
        filtered_docs = [d for d in filtered_docs if d.get("document_type") == filter_doc_type]
    if filter_year != "Tất cả":
        filtered_docs = [d for d in filtered_docs if d.get("year") == filter_year]
    if filter_quarter != "Tất cả":
        if filter_quarter == "Báo cáo năm":
            filtered_docs = [d for d in filtered_docs if not d.get("quarter")]
        else:
            filtered_docs = [d for d in filtered_docs if d.get("quarter") == filter_quarter]
 
    st.caption(f"📄 {len(filtered_docs)} / {len(valid_docs)} tài liệu phù hợp")
 
    if st.button("🔄 Làm mới danh sách"):
        st.rerun()
 
    if filtered_docs:
        st.dataframe(filtered_docs, use_container_width=True)
    else:
        st.info("Không tìm thấy tài liệu phù hợp.")

    #Xóa tài liệu
    with st.expander("🗑️ Xoá tài liệu", expanded=False):
        # valid_docs được tính lại độc lập ở đây phòng trường hợp expander
        # "Bộ lọc" ở trên chưa từng được mở ra trong lần chạy này.
        _all_docs = fetch_documents()
        _valid_docs = [
            d for d in _all_docs
            if d.get("document_id")
            and d.get("file_name")
            and str(d.get("document_id")).lower() != "none"
            and str(d.get("file_name")).lower() != "none"
        ]
        doc_options = {
            f"{doc.get('file_name', 'Unamed')} ({doc['document_id']})": doc['document_id']
            for doc in _valid_docs if "document_id" in doc
        }
 
        if doc_options:
            selected_label = st.selectbox(
                "Chọn tài liệu cần xóa:",
                options=list(doc_options.keys()),
            )
            if st.button("Xóa tài liệu", type="primary"):
                selected_id = doc_options[selected_label]
                try:
                    response = requests.delete(f"{BACKEND_URL}/documents/{selected_id}")
                    if response.status_code == 200:
                        st.success("Đã xóa tài liệu thành công!")
                        st.rerun()
                    else:
                        st.error(f"Lỗi {response.status_code}: {response.text}")
                except Exception as e:
                    st.error(f"Không thể kết nối đến Backend: {e}")
        else:
            st.info("Chưa có tài liệu nào để xoá.")


st.title(f"💬 Financial RAG Chatbot")
# st.caption(current_conv.get("title", DEFAULT_TITLE))
title_text = current_conv.get("title", DEFAULT_TITLE)
st.markdown(
    f"<p style='color: #000000; font-weight: bold; font-size: 18px; margin-top: -10px; margin-left: 10px;'>Chats: {title_text}</p>",
    unsafe_allow_html=True
)
 
for msg in current_conv["messages"]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        render_intent(msg.get("intent"))
        render_metric_specs(msg.get("metric_spec"))
        render_calculation_outputs(msg.get("calculation"))
        render_citations(msg.get("citations", []))
 
query = st.chat_input("Hỏi về báo cáo tài chính, hợp đồng tín dụng, bản cáo bạch...")
 
if query:
    current_conv["messages"].append({"role": "user", "content": query})
    if current_conv["title"] == DEFAULT_TITLE:
        current_conv["title"] = make_title_from_query(query)
    current_conv["updated_at"] = _now_iso()
    save_conversations(st.session_state.conversations)
 
    with st.chat_message("user"):
        st.write(query)

    with st.chat_message("assistant"):
        citations = []  # giá trị mặc định, đảm bảo luôn tồn tại kể cả khi request lỗi
        intent = None          # bước 1: CalculationIntent -- chỉ có ở nhánh Calculation
        metric_spec = None     # bước 2: công thức/required_metrics
        metric_specs = []      # bước 2: TOÀN BỘ công thức/required_metrics
        calculation = None     # bước 3: CalculationOutput (kết quả cuối)
        calculations = []      # bước 3: TOÀN BỘ CalculationOutput thành công
        try:
            resp = requests.post(
                f"{BACKEND_URL}/chat",
                json={"session_id": current_conv["id"], "query": query},
                timeout=180,
            )
            resp.raise_for_status()
            data = resp.json()
            answer = data.get("answer", "Không nhận được câu trả lời.")
            citations = data.get("citations", [])
            intent = data.get("intent")
            metric_spec = data.get("metric_spec")
            metric_specs = _as_nonempty_list(data.get("metric_specs"), metric_spec)
            calculation = data.get("calculation")
            calculations = _as_nonempty_list(data.get("calculations"), calculation)
        except requests.exceptions.RequestException as e:
            answer = f"Lỗi kết nối tới backend: {e}"

        st.write(answer)
        render_intent(intent)
        render_metric_specs(metric_specs, metric_spec)
        render_calculation_outputs(calculations, calculation)
        render_citations(citations)
    current_conv["messages"].append({
        "role": "assistant",
        "content": answer,
        "intent": intent,
        "metric_spec": metric_spec,          # giữ để đọc bằng frontend cũ
        "metric_specs": metric_specs,        # đầy đủ multi-metric
        "calculation": calculation,          # giữ để đọc bằng frontend cũ
        "calculations": calculations,        # đầy đủ multi-metric
        "citations": citations,
    })
    current_conv["updated_at"] = _now_iso()
    save_conversations(st.session_state.conversations)