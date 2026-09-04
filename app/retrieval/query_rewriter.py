"""
app/retrieval/query_rewriter.py

Viết lại câu hỏi người dùng thành các dạng tìm kiếm tương đương + trích
xuất metadata (ticker/year/report_scope) bằng LLM (gpt-4o-mini) cho nhánh
financial_search của HybridSearchPipeline.

THAY ĐỔI QUAN TRỌNG NHẤT (bản này): hỗ trợ câu hỏi SO SÁNH/TỔNG HỢP NHIỀU
CÔNG TY -- trước đây rewriter chỉ trả về ĐÚNG 1 "ticker"/"year"/"report_scope"
dạng số ít, nên câu hỏi kiểu "So sánh doanh thu FPT năm 2023 với MWG năm
2024" chỉ lọc được data của 1 trong 2 công ty (ticker sau ghi đè ticker
trước). Giờ LLM được yêu cầu ĐỌC KỸ câu hỏi, XÁC ĐỊNH CÓ BAO NHIÊU công ty
đang được hỏi tới, và trả về "entities": list[{ticker, year, report_scope}]
-- MỖI công ty là 1 phần tử riêng, có thể có năm/report_scope KHÁC NHAU
(vd so sánh 2 công ty ở 2 năm khác nhau, hoặc 1 công ty xem báo cáo mẹ còn
công ty kia xem báo cáo hợp nhất). Tầng gọi (HybridSearchPipeline) sẽ chạy
retrieval RIÊNG cho từng entity trong "entities" rồi gộp kết quả lại, thay
vì lọc chung 1 bộ filter duy nhất cho toàn bộ câu hỏi như bản cũ.

Field "ticker"/"year"/"report_scope" (số ít) VẪN được giữ lại ở top-level
kết quả trả về, luôn đồng bộ = entity ĐẦU TIÊN trong "entities" -- để bất
kỳ chỗ nào trong code còn đọc field số ít (chưa kịp cập nhật sang
"entities") vẫn hoạt động bình thường, không bị vỡ.

Các thay đổi khác giữ nguyên như bản trước:
  - ticker KHÔNG còn tra qua TICKER_MAPPING viết tay -- LLM tự đối chiếu
    tên công ty/biệt danh nhắc trong câu hỏi với danh sách ticker THẬT
    đang có trong hệ thống, lấy trực tiếp từ Mongo qua
    known_tickers_prompt_text() (app/services/mongo_client.py).
  - report_scope KHÔNG còn dò bằng keyword rule-based -- LLM tự suy luận
    "parent"/"consolidated"/null trực tiếp từ ngữ nghĩa câu hỏi.
  - Dùng ChatOpenAI (gpt-4o-mini).

CalculationService.extract_intent() (app/calculation/calculation_service.py)
dùng lại đúng known_tickers_prompt_text() này để 2 nhánh financial_search/
calculation không lệch cách chuẩn hoá ticker.
"""

import json
from typing import Any, Dict, List, Optional

from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

from app.config import settings
from app.services.mongo_client import known_tickers_prompt_text


def _clean_ticker(raw: Any) -> Optional[str]:
    if not raw:
        return None
    return str(raw).strip().upper()


def _clean_year(raw: Any) -> Optional[int]:
    try:
        return int(raw) if raw else None
    except (TypeError, ValueError):
        return None


def _clean_scope(raw: Any) -> Optional[str]:
    return raw if raw in ("parent", "consolidated") else None


class QueryRewriter:
    def __init__(self):
        self.llm = ChatOpenAI(
            model_name="gpt-4o-mini",
            temperature=0,
            openai_api_key=settings.OPENAI_API_KEY,
        )
        self.prompt = PromptTemplate(
            template="""Bạn là chuyên gia phân tích truy vấn tài chính.

DANH SÁCH MÃ CỔ PHIẾU (TICKER) HIỆN CÓ TRONG HỆ THỐNG (đối chiếu tên công
ty/ngân hàng/biệt danh/tên viết tắt/tên không dấu trong câu hỏi với danh
sách này để trả về ĐÚNG ticker viết hoa tương ứng, kể cả khi người dùng gõ
khác hẳn tên chính thức):
{known_tickers}

Nhiệm vụ của bạn:

1. ĐỌC KỸ câu hỏi và xác định CÓ BAO NHIÊU công ty/ngân hàng đang được hỏi
   tới, câu hỏi có thể chỉ nói về 1 công ty (tra cứu thông thường), HOẶC
   nhắc tới TỪ 2 CÔNG TY TRỞ LÊN (so sánh, tổng hợp thông tin cần lấy từ
   NHIỀU tài liệu/công ty khác nhau để trả lời đầy đủ). Một số dấu hiệu
   câu hỏi nhiều công ty: "so sánh", "giữa X và Y", liệt kê nhiều tên công
   ty/ticker cách nhau bằng dấu phẩy/"và"/"với", "công ty nào ... hơn",
   "X so với Y". Ví dụ:
     - "Doanh thu FPT năm 2023" -> 1 công ty (FPT).
     - "So sánh doanh thu FPT năm 2023 với MWG năm 2024" -> 2 công ty
       (FPT/2023 và MWG/2024 -- MỖI công ty giữ ĐÚNG năm được hỏi cho
       riêng nó, KHÔNG dùng chung 1 năm cho cả 2).
     - "Lợi nhuận của FPT, MWG và VNM năm 2024 công ty nào cao nhất?" -> 3
       công ty (FPT, MWG, VNM), cùng năm 2024.
     - "Tổng tài sản công ty mẹ FPT so với báo cáo hợp nhất của FPT" -> 2
       phần tử CÙNG ticker FPT nhưng report_scope KHÁC NHAU ("parent" và
       "consolidated").

2. Với MỖI công ty xác định được ở bước 1, tạo 1 phần tử trong mảng
   "entities", gồm:
   - "ticker": mã cổ phiếu viết hoa, đối chiếu danh sách ticker thật ở
     trên. Nếu công ty được hỏi không có trong danh sách, vẫn suy đoán mã
     ticker hợp lý (viết hoa) thay vì trả null, TRỪ khi không xác định
     được công ty nào cả.
   - "year": năm dạng số CỦA RIÊNG công ty đó, hoặc null nếu câu hỏi không
     nêu rõ năm cho công ty đó.
   - "report_scope": "parent" nếu hỏi về công ty mẹ/báo cáo riêng lẻ
     (không hợp nhất công ty con); "consolidated" nếu hỏi về báo cáo hợp
     nhất/toàn hệ thống/toàn ngân hàng; null nếu câu hỏi không phân biệt
     rõ phạm vi báo cáo cho công ty đó.
   Mảng "entities" LUÔN có ÍT NHẤT 1 phần tử (kể cả câu hỏi chỉ về 1 công
   ty, hoặc không xác định được công ty nào -- khi đó trả 1 phần tử với
   "ticker": null).

3. Tạo 3 câu hỏi tương đương (rewritten_queries) bằng tiếng Việt để hỗ trợ
   tìm kiếm ngữ nghĩa tốt hơn. Nếu câu hỏi gốc so sánh nhiều công ty, MỖI
   câu viết lại vẫn phải giữ đầy đủ TÊN/NĂM của TẤT CẢ công ty liên quan
   (không được chỉ viết lại theo 1 công ty rồi bỏ sót công ty còn lại).

Trả về DUY NHẤT 1 JSON object, không thêm giải thích, đúng cấu trúc:
{{
    "entities": [
        {{"ticker": "MÃ_CỔ_PHIẾU" hoặc null, "year": <năm dạng số> hoặc null, "report_scope": "parent" | "consolidated" | null}}
    ],
    "rewritten_queries": ["câu 1", "câu 2", "câu 3"]
}}

Câu hỏi của người dùng: {query}
JSON Output:""",
            input_variables=["query", "known_tickers"],
        )

    @staticmethod
    def _safe_json(raw: str) -> Dict[str, Any]:
        try:
            start_idx = raw.find("{")
            end_idx = raw.rfind("}") + 1
            return json.loads(raw[start_idx:end_idx])
        except Exception:
            return {}

    def rewrite_and_extract_metadata(self, query: str) -> Dict[str, Any]:
        """Viết lại câu hỏi thành các dạng tìm kiếm khác nhau + trích xuất
        DANH SÁCH công ty cần truy vấn (ticker/year/report_scope MỖI công
        ty), bằng gpt-4o-mini, đối chiếu với danh sách ticker thật đang có
        trong hệ thống.

        Trả về:
            {
                "entities": list[{"ticker", "year", "report_scope"}],  # >= 1 phần tử
                "ticker": <giống entities[0]["ticker"]>,   # tương thích ngược
                "year": <giống entities[0]["year"]>,       # tương thích ngược
                "report_scope": <giống entities[0]["report_scope"]>,  # tương thích ngược
                "rewritten_queries": list[str],
            }
        """
        chain = self.prompt | self.llm
        raw = chain.invoke({
            "query": query,
            "known_tickers": known_tickers_prompt_text(),
        }).content.strip()

        data = self._safe_json(raw)
        if not data:
            print(f"[QueryRewriter] Không parse được JSON từ LLM, raw: {raw!r} -- fallback về query gốc.")
            empty_entity = {"ticker": None, "year": None, "report_scope": None}
            return {
                "entities": [empty_entity],
                "ticker": None,
                "year": None,
                "report_scope": None,
                "rewritten_queries": [query],
            }

        entities: List[Dict[str, Any]] = []
        raw_entities = data.get("entities")
        if isinstance(raw_entities, list):
            for item in raw_entities:
                if not isinstance(item, dict):
                    continue
                entities.append({
                    "ticker": _clean_ticker(item.get("ticker")),
                    "year": _clean_year(item.get("year")),
                    "report_scope": _clean_scope(item.get("report_scope")),
                })

        if not entities:
            # LLM lỡ trả format cũ (ticker/year/report_scope số ít, không có
            # "entities") -- fallback dựng 1 entity từ field số ít, vẫn
            # tương thích thay vì mất trắng kết quả.
            print(f"[QueryRewriter] Không có 'entities' hợp lệ trong JSON, raw: {raw!r} -- "
                  "fallback đọc field ticker/year/report_scope số ít.")
            entities = [{
                "ticker": _clean_ticker(data.get("ticker")),
                "year": _clean_year(data.get("year")),
                "report_scope": _clean_scope(data.get("report_scope")),
            }]

        rewritten_queries = data.get("rewritten_queries")
        if not isinstance(rewritten_queries, list) or not rewritten_queries:
            rewritten_queries = [query]

        first = entities[0]
        if len(entities) > 1:
            tickers_preview = [e.get("ticker") for e in entities]
            print(f"[QueryRewriter] Câu hỏi nhiều công ty ({len(entities)}): {tickers_preview}")

        return {
            "entities": entities,
            "ticker": first.get("ticker"),
            "year": first.get("year"),
            "report_scope": first.get("report_scope"),
            "rewritten_queries": rewritten_queries,
        }