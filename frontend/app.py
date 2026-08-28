"""
Streamlit demo frontend cho Financial RAG Chatbot.
Gọi sang backend FastAPI qua BACKEND_URL (set trong docker-compose.yml).
"""

import os
import uuid
import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

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
    with st.expander("Đầu vào đã trích xuất (CalculationIntent)", expanded=False):
        st.json(intent)

def render_metric_spec(metric_spec: dict | None) -> None:
    """Dropdown hiện cấu trúc JSON của công thức đang dùng (formula/steps +
    required_metrics) -- CHỈ xuất hiện ở câu trả lời thuộc nhánh
    Calculation (backend chỉ set metric_spec khi đó, xem app/main.py).
    Mục đích: cho người dùng thấy rõ hệ thống tính bằng công thức nào và
    cần những số liệu thô nào, không phải LLM tự bịa ra kết quả."""
    if not metric_spec:
        return
    metric_key = next(iter(metric_spec.keys()), "")
    with st.expander(f"Công thức tính toán ({metric_key})", expanded=False):
        st.json(metric_spec)

def render_calculation_output(calculation: dict | None) -> None:
    """Dropdown hiện CalculationOutput -- BƯỚC CUỐI của quy trình
    Calculation: formula ĐÃ THAY SỐ, từng operand kèm nguồn/trang, và result.
    Chỉ có giá trị khi tính THÀNH CÔNG (thiếu dữ liệu/lỗi công thức thì
    backend trả calculation=None, dropdown này sẽ không hiện)."""
    if not calculation:
        return
    with st.expander("Kết quả tính toán (CalculationOutput)", expanded=False):
        st.json(calculation)

st.set_page_config(page_title="Financial RAG Chatbot", page_icon="💬", layout="wide")

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    # Upload file
    st.subheader("📁 Tải tài liệu")
 
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
 
    # Filter: công ty / loại tài liệu / năm / quý cho các file đã upload
    st.subheader("🔎 Bộ lọc")
 
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
    # Tạo danh sách ánh xạ: "Tên file (ID)" -> document_id
    doc_options = {
        f"{doc.get('file_name', 'Unamed')} ({doc['document_id']})": doc['document_id']
        for doc in valid_docs if "document_id" in doc
    }

    if doc_options:
        st.sidebar.markdown("---")
        st.sidebar.subheader("🗑️ Xóa tài liệu")
    
    # UI: Menu chọn tài liệu
    selected_label = st.sidebar.selectbox(
        "Chọn tài liệu cần xóa:",
        options=list(doc_options.keys())
    )
    
    # UI: Nút bấm xác nhận xóa
    if st.sidebar.button("Xóa tài liệu", type="primary"):
        selected_id = doc_options[selected_label]
        
        try:
            # 2. Gửi yêu cầu DELETE xuống Backend
            response = requests.delete(f"{BACKEND_URL}/documents/{selected_id}")
            
            # 3. Đồng bộ giao diện khi thành công
            if response.status_code == 200:
                st.sidebar.success("Đã xóa tài liệu thành công!")
                st.rerun()  # Tự động reload để xóa file khỏi bảng hiển thị
            else:
                st.sidebar.error(f"Lỗi {response.status_code}: {response.text}")
        except Exception as e:
            st.sidebar.error(f"Không thể kết nối đến Backend: {e}")


st.title("💬 Financial RAG Chatbot")
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        render_intent(msg.get("intent"))
        render_metric_spec(msg.get("metric_spec"))
        render_calculation_output(msg.get("calculation"))
        render_citations(msg.get("citations", []))

query = st.chat_input("Hỏi về báo cáo tài chính, hợp đồng tín dụng, bản cáo bạch...")

if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.write(query)

    with st.chat_message("assistant"):
        citations = []  # giá trị mặc định, đảm bảo luôn tồn tại kể cả khi request lỗi
        intent = None          # bước 1: CalculationIntent -- chỉ có ở nhánh Calculation
        metric_spec = None     # bước 2: công thức/required_metrics
        calculation = None     # bước 3: CalculationOutput (kết quả cuối)
        try:
            resp = requests.post(
                f"{BACKEND_URL}/chat",
                json={"session_id": st.session_state.session_id, "query": query},
                timeout=180,
            )
            resp.raise_for_status()
            data = resp.json()
            answer = data.get("answer", "Không nhận được câu trả lời.")
            citations = data.get("citations", [])
            intent = data.get("intent")
            metric_spec = data.get("metric_spec")
            calculation = data.get("calculation")
        except requests.exceptions.RequestException as e:
            answer = f"Lỗi kết nối tới backend: {e}"

        st.write(answer)
        render_intent(intent)
        render_metric_spec(metric_spec)
        render_calculation_output(calculation)
        render_citations(citations)
        st.session_state.messages.append({
            "role": "assistant", 
            "content": answer, 
            "intent": intent,
            "metric_spec": metric_spec,
            "calculation": calculation,
            "citations": citations})