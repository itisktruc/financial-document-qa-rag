"""
FinRAG Dashboard - Streamlit Frontend Application
"""

import os
import uuid
from typing import Dict, Any, List, Tuple, Optional

import requests
import streamlit as st

# ==============================================================================
# CẤU HÌNH & HẰNG SỐ
# ==============================================================================
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
TIMEOUT_CHAT = 180
TIMEOUT_UPLOAD = 60

# ==============================================================================
# CUSTOM CSS
# ==============================================================================
def inject_custom_css() -> None:
    st.markdown(
        """
        <style>
            .stApp {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            }

            .main-header {
                font-size: 2.1rem;
                font-weight: 700;
                color: #0F172A;
                margin-bottom: 0.15rem;
            }
            .sub-header {
                font-size: 0.92rem;
                color: #64748B;
                margin-bottom: 1.4rem;
            }

            /* Badge trạng thái FinRAG */
            .status-badge {
                padding: 5px 12px;
                border-radius: 20px;
                font-size: 0.78rem;
                font-weight: 600;
                display: inline-flex;
                align-items: center;
                gap: 6px;
                letter-spacing: 0.01em;
            }
            .status-online {
                background-color: #ECFDF5;
                color: #047857;
                border: 1px solid #A7F3D0;
            }
            .status-connecting {
                background-color: #FFFBEB;
                color: #B45309;
                border: 1px solid #FDE68A;
            }
            .status-offline {
                background-color: #FEF2F2;
                color: #B91C1C;
                border: 1px solid #FECACA;
            }
            .status-dot {
                width: 7px;
                height: 7px;
                border-radius: 50%;
                display: inline-block;
            }
            .dot-online { background-color: #10B981; }
            .dot-connecting { background-color: #F59E0B; }
            .dot-offline { background-color: #EF4444; }

            /* Progress text nhỏ, tinh tế */
            .finrag-step {
                font-size: 0.82rem !important;
                color: #64748B !important;
                margin: 0.15rem 0 !important;
                line-height: 1.4 !important;
            }

            .stExpander {
                border-radius: 8px !important;
                border: 1px solid #E2E8F0 !important;
            }

            /* Làm status box gọn hơn */
            div[data-testid="stStatusWidget"] p {
                font-size: 0.84rem !important;
                color: #475569 !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ==============================================================================
# API CLIENT
# ==============================================================================
class FinRAGBackendService:
    @staticmethod
    def check_health() -> bool:
        try:
            resp = requests.get(f"{BACKEND_URL}/docs", timeout=2)
            return resp.status_code == 200
        except requests.RequestException:
            return False

    @staticmethod
    def upload_document(uploaded_file) -> Tuple[bool, str]:
        try:
            resp = requests.post(
                f"{BACKEND_URL}/documents/upload",
                files={"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")},
                timeout=TIMEOUT_UPLOAD,
            )
            if resp.status_code == 200:
                return True, f"Tải lên thành công: **{uploaded_file.name}**"
            return False, f"Lỗi hệ thống ({resp.status_code}): {resp.text}"
        except requests.RequestException as err:
            return False, f"Không thể kết nối tới máy chủ khi upload: {err}"

    @staticmethod
    def send_chat_query(session_id: str, query: str) -> Tuple[bool, Dict[str, Any]]:
        try:
            resp = requests.post(
                f"{BACKEND_URL}/chat",
                json={"session_id": session_id, "query": query},
                timeout=TIMEOUT_CHAT,
            )
            resp.raise_for_status()
            return True, resp.json()
        except requests.RequestException as err:
            return False, {"error": f"Lỗi truy vấn Backend: {err}"}


# ==============================================================================
# UI COMPONENTS
# ==============================================================================
def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("### Trạng thái")

        is_online = FinRAGBackendService.check_health()
        if is_online:
            st.markdown(
                """
                <span class="status-badge status-online">
                    <span class="status-dot dot-online"></span>
                    FinRAG đã sẵn sàng
                </span>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <span class="status-badge status-connecting">
                    <span class="status-dot dot-connecting"></span>
                    FinRAG đang kết nối…
                </span>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("---")
        st.markdown("### Tài liệu")

        with st.form("upload_form", clear_on_submit=True):
            files = st.file_uploader(
                "Tải báo cáo tài chính (PDF)",
                type=["pdf"],
                accept_multiple_files=True,
                help="Hỗ trợ BCTC Quý, Năm, Bản cáo bạch…",
            )
            submit = st.form_submit_button("Lưu tài liệu", use_container_width=True)

        if submit and files:
            for file in files:
                success, message = FinRAGBackendService.upload_document(file)
                if success:
                    st.success(message)
                else:
                    st.error(message)


def render_citations(citations: List[Dict[str, Any]]) -> None:
    if not citations:
        return

    with st.expander(f"Nguồn trích dẫn ({len(citations)})", expanded=False):
        for item in sorted(citations, key=lambda x: x.get("index", 0)):
            label = item.get("label") or f"[{item.get('index', '?')}]"
            section = item.get("section_path") or item.get("section")
            section_info = ""

            if isinstance(section, list) and section:
                section_info = f" — *{' > '.join(str(s) for s in section)}*"
            elif isinstance(section, str) and section:
                section_info = f" — *{section}*"

            st.markdown(f"• **{label}**{section_info}")


def render_metadata(msg: Dict[str, Any]) -> None:
    intent = msg.get("intent")
    metric_spec = msg.get("metric_spec")
    calculation = msg.get("calculation")

    if intent:
        with st.expander("Phân tích Intent", expanded=False):
            st.json(intent)

    if metric_spec:
        metric_key = next(iter(metric_spec.keys()), "Chi tiết")
        with st.expander(f"Công thức ({metric_key})", expanded=False):
            st.json(metric_spec)

    if calculation:
        with st.expander("Kết quả tính toán", expanded=False):
            st.json(calculation)


# ==============================================================================
# MAIN
# ==============================================================================
def main() -> None:
    st.set_page_config(
        page_title="FinRAG - Financial Intelligence Assistant",
        page_icon="💼",
        layout="wide",
    )

    inject_custom_css()

    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "messages" not in st.session_state:
        st.session_state.messages = []

    render_sidebar()

    st.markdown(
        '<div class="main-header">FinRAG</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="sub-header">Trợ lý AI phân tích báo cáo tài chính & chỉ số doanh nghiệp</div>',
        unsafe_allow_html=True,
    )

    # Chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            render_metadata(msg)
            render_citations(msg.get("citations", []))

    query = st.chat_input("Hỏi về số liệu tài chính… (ví dụ: Doanh thu A32 là bao nhiêu?)")

    if query:
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.write(query)

        with st.chat_message("assistant"):
            answer = ""
            citations = []
            intent = None
            metric_spec = None
            calculation = None

            with st.status("FinRAG đang xử lý…", expanded=True) as status:
                st.markdown(
                    '<p class="finrag-step">Đang phân tích ý định câu hỏi</p>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    '<p class="finrag-step">Đang truy vấn Hybrid Search (Qdrant & MongoDB)</p>',
                    unsafe_allow_html=True,
                )

                success, data = FinRAGBackendService.send_chat_query(
                    st.session_state.session_id, query
                )

                if success:
                    st.markdown(
                        '<p class="finrag-step">Đang tổng hợp câu trả lời</p>',
                        unsafe_allow_html=True,
                    )

                    answer = data.get("answer", "Không tìm thấy nội dung phản hồi phù hợp.")
                    citations = data.get("citations", [])
                    intent = data.get("intent")
                    metric_spec = data.get("metric_spec")
                    calculation = data.get("calculation")

                    status.update(
                        label="FinRAG đã hoàn tất",
                        state="complete",
                        expanded=False,
                    )
                else:
                    status.update(
                        label="FinRAG gặp sự cố",
                        state="error",
                        expanded=True,
                    )
                    answer = data.get("error", "Đã xảy ra lỗi không xác định.")

            st.write(answer)

            message_data = {
                "role": "assistant",
                "content": answer,
                "intent": intent,
                "metric_spec": metric_spec,
                "calculation": calculation,
                "citations": citations,
            }

            render_metadata(message_data)
            render_citations(citations)
            st.session_state.messages.append(message_data)


if __name__ == "__main__":
    main()