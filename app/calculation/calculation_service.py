"""
app/calculation/calculation_service.py

Quy trình:
  1. LLM (Groq) đọc câu hỏi -> xác định metric_key (khớp METRIC_REGISTRY)
     + ticker/year/quarter (CalculationIntent).
  2. Với từng input field công thức cần, tái sử dụng trực tiếp
     HybridSearchPipeline.RRF_fuse() + .rerank() (lọc theo ticker/năm) để
     lấy context liên quan.
  3. Một LLM THỨ HAI đọc context, trích xuất ĐÚNG 1 con số cho field đó
     (không suy diễn/làm tròn).
  4. compute_metric() (code Python thuần) thực hiện phép TÍNH -- không để
     LLM tự nhẩm, đúng nguyên tắc README.
"""
from __future__ import annotations

import json
import os
from typing import Optional

from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate

from app.config import settings
from app.calculation.metrics import METRIC_FORMULAS, compute_metric_from_operands, FormulaError, get_metric_spec
from app.models.calculation_schema import CalculationIntent, CalculationResponse, OperandDetail, MetricFormulaSpec
from app.generation.citation import format_citation_label, clean_source_filename
from app.services.mongo_client import get_parent_chunk
from app.calculation.calculation_formatter import format_calculation_answer


FIELD_LABELS: dict[str, str] = {
    "gross_profit": "Lợi nhuận gộp",
    "revenue": "Doanh thu thuần",
    "net_income": "Lợi nhuận sau thuế",
    "current_assets": "Tài sản ngắn hạn",
    "current_liabilities": "Nợ ngắn hạn",
    "total_liabilities": "Tổng nợ phải trả",
    "total_equity": "Vốn chủ sở hữu",
    "current_value": "Giá trị kỳ hiện tại",
    "prior_year_value": "Giá trị cùng kỳ năm trước",
    "prior_quarter_value": "Giá trị quý trước",
    "beginning_value": "Giá trị đầu kỳ",
    "ending_value": "Giá trị cuối kỳ",
    "num_years": "Số năm",
    "shareholders_equity_t": "Vốn chủ sở hữu kỳ hiện tại",
    "shareholders_equity_t_minus_1": "Vốn chủ sở hữu kỳ trước",
    "total_assets_t": "Tổng tài sản kỳ hiện tại",
    "total_assets_t_minus_1": "Tổng tài sản kỳ trước",
    "average_shareholders_equity": "Vốn chủ sở hữu bình quân",
    "average_total_assets": "Tổng tài sản bình quân",
}

def _normalize_cid(cid: Any) -> str:
    """Chuẩn hoá chunk_id/parent_id về dạng hex thô không gạch ngang (đồng bộ với MongoDB)."""
    if not cid:
        return ""
    return str(cid).replace("-", "").strip()

def _clean_filename(source_file: str) -> str:
    """Chỉ lấy tên file (không path), khớp docstring của OperandDetail.source."""
    return os.path.basename(str(source_file or "Báo cáo tài chính"))

class CalculationService:
    def __init__(self, search_pipeline):
        """search_pipeline: instance HybridSearchPipeline đã khởi tạo sẵn
        trong app/main.py (dùng lại luôn RRF_fuse/rerank/_qdrant_filter,
        không tạo pipeline riêng)."""
        self.search_pipeline = search_pipeline
        self.intent_llm = ChatGroq(temperature=0, model_name="openai/gpt-oss-120b",
                                    groq_api_key=settings.GROQ_API_KEY)
        self.extract_llm = ChatGroq(temperature=0, model_name="openai/gpt-oss-120b",
                                     groq_api_key=settings.GROQ_API_KEY)

        self.intent_prompt = PromptTemplate(
            template="""Bạn là chuyên gia phân tích tài chính. Nhiệm vụ: đọc câu hỏi của người
dùng và xác định ĐÚNG 1 chỉ số tài chính (metric_key) người dùng muốn tính,
cùng công ty (ticker)/năm/quý liên quan.

DANH SÁCH CHỈ SỐ HỖ TRỢ (chỉ được chọn 1 trong các key sau, không tự bịa key mới):
{metric_list}

Trả về DUY NHẤT 1 JSON object, không thêm giải thích, đúng cấu trúc sau:
{{
    "metric_key": "<1 trong các key trên, hoặc null nếu không xác định được>",
    "ticker": "<mã cổ phiếu viết hoa, hoặc null>",
    "year": <năm dạng số, hoặc null>,
    "quarter": <quý 1-4 dạng số, hoặc null>,
    "compare_year": <năm dùng để so sánh YoY/CAGR nếu có, hoặc null>,
    "compare_quarter": <quý dùng để so sánh QoQ nếu có, hoặc null>
}}

Câu hỏi: {query}
JSON Output:""",
            input_variables=["query", "metric_list"],
        )

    def _metric_list_text(self) -> str:
        return "\n".join(
            f"- {key}: {spec.name_vi} (aliases: {', '.join(spec.aliases)})"
            for key, spec in METRIC_FORMULAS.items()
        )

    @staticmethod
    def _safe_json(raw: str) -> Optional[dict]:
        try:
            start, end = raw.find("{"), raw.rfind("}") + 1
            return json.loads(raw[start:end])
        except Exception:
            return None

    def extract_intent(self, query: str) -> CalculationIntent:
        chain = self.intent_prompt | self.intent_llm
        raw = chain.invoke({"query": query, "metric_list": self._metric_list_text()}).content.strip()
        data = self._safe_json(raw) or {}
        intent = CalculationIntent(
            metric_key=data.get("metric_key"),
            ticker=(data.get("ticker") or None),
            year=data.get("year"),
            quarter=data.get("quarter"),
            compare_year=data.get("compare_year"),
            compare_quarter=data.get("compare_quarter"),
            raw_query=query,
        )
        print(f"[Calculation] Intent trích được: metric={intent.metric_key}, ticker={intent.ticker}, "
              f"year={intent.year}, quarter={intent.quarter}")
        return intent

    def _fetch_operand(self, field: str, intent: CalculationIntent, period_label: str) -> tuple[Optional[OperandDetail], list[dict]]:
        field_label = FIELD_LABELS.get(field, field)
        search_query = f"{field_label} {period_label}".strip()

        metadata_filter = {"ticker": intent.ticker, "year": intent.year}
        print(f"[Calculation] Đang tra cứu '{field_label}' | filter ticker={intent.ticker}, year={intent.year}")

        RRF_ids, content_lookup = self.search_pipeline.RRF_fuse([search_query], metadata_filter=metadata_filter)
        top_ids = self.search_pipeline.rerank(search_query, RRF_ids, content_lookup, top_k=5)
        print(f"[Calculation] '{field_label}': còn lại {len(RRF_ids)} chunk sau RRF, giữ được {len(top_ids)} sau rerank")

        contexts, seen_parents = [], set()
        for cid in top_ids:
            norm_cid = _normalize_cid(cid)
            info = content_lookup.get(norm_cid, {})
            parent_id = _normalize_cid(info.get("parent_id")) or norm_cid
            if parent_id in seen_parents:
                continue
            seen_parents.add(parent_id)
            parent_doc = get_parent_chunk(parent_id)
            if parent_doc:
                text_content = parent_doc.get("text") or parent_doc.get("content", "")
                citation_info = {
                    "doc_id": parent_doc.get("doc_id"),
                    "source_file": parent_doc.get("source_file"),
                    "page_start": parent_doc.get("page_start"),
                    "page_end": parent_doc.get("page_end"),
                    "section": parent_doc.get("section") or parent_doc.get("heading"),
                    "ticker": parent_doc.get("ticker"),
                    "year": parent_doc.get("year"),
                }
            else:
                text_content = info.get("content", "")
                citation_info = {"doc_id": norm_cid, "source_file": "Báo cáo tài chính"}
            if text_content:
                contexts.append({"content": text_content, "citation": citation_info})

        if not contexts:
            print(f"[Calculation] '{field_label}': không tìm thấy ngữ cảnh nào phù hợp, bỏ qua field này.")
            return None, []

        numbered_blocks, citations = [], []
        for i, ctx in enumerate(contexts, start=1):
            citation = dict(ctx.get("citation", {}))
            citation["index"] = i
            citation["label"] = format_citation_label(citation, i)
            citations.append(citation)
            numbered_blocks.append(f"[{i}]\n{ctx['content']}")
        joined_context = "\n\n".join(numbered_blocks)

        extract_prompt = f"""Bạn là chuyên gia trích xuất số liệu tài chính. Dựa vào các đoạn ngữ
    cảnh được đánh số [1], [2]... dưới đây (trích từ báo cáo tài chính), hãy tìm ĐÚNG 1 con số
    cho chỉ tiêu: "{field_label}"{f" ({period_label})" if period_label else ""}.

    Yêu cầu:
    - Chỉ lấy số liệu CÓ TRONG ngữ cảnh, không suy diễn, không tự tính.
    - Đơn vị trả về LUÔN quy đổi ra đồng (VND) -- nếu ngữ cảnh ghi "triệu đồng"/"tỷ đồng",
    nhân tương ứng 1,000,000 / 1,000,000,000.
    - Nếu không tìm thấy số liệu phù hợp, trả "value": null.

    --- NGỮ CẢNH ---
    {joined_context}
    ---

    Chỉ trả về DUY NHẤT 1 JSON object, không thêm giải thích, đúng cấu trúc:
    {{"value": <số hoặc null>, "source_index": <n tương ứng [n] đã dùng, hoặc null>, "table": "<tên bảng/mục nếu có, hoặc null>"}}
    JSON Output:"""
        raw = self.extract_llm.invoke(extract_prompt).content.strip()
        data = self._safe_json(raw) or {}

        value = data.get("value")
        if value is None:
            print(f"[Calculation] '{field_label}': LLM trích xuất trả về null (không tìm thấy số liệu trong ngữ cảnh).")
            return None, citations
        try:
            value = float(value)
        except (TypeError, ValueError):
            print(f"[Calculation] '{field_label}': Giá trị trích xuất không hợp lệ ({value!r}), bỏ qua field này.")
            return None, citations

        source_index = data.get("source_index")
        if isinstance(source_index, int) and 1 <= source_index <= len(citations):
            chosen = citations[source_index - 1]
        else:
            chosen = citations[0] if citations else {}
        operand = OperandDetail(
            value=value,
            source=_clean_filename(chosen.get("source_file")),
            page=chosen.get("page_start"),
            table=data.get("table") or chosen.get("section"),
        )
        print(f"[Calculation] '{field_label}': giá trị trích được = {value} (nguồn: {operand.source}, trang {operand.page})")
        return operand, citations


    def calculate(self, query: str) -> CalculationResponse:
        print(f"[Calculation] Bắt đầu xử lý câu hỏi loại calculation: {query!r}")
        intent = self.extract_intent(query)

        intent_json = intent.model_dump()
        spec = get_metric_spec(intent.metric_key)
        if spec is None:
            print(f"[Calculation] Không khớp được metric_key nào trong registry (intent.metric_key={intent.metric_key!r}).")
            return CalculationResponse(
                answer=("Mình chưa xác định được chính xác chỉ số tài chính bạn muốn tính. "
                        "Bạn có thể hỏi lại rõ hơn, ví dụ: 'Tính ROE của FPT năm 2024' nhé."),
                result=None, citations=[],
                intent=intent_json,
            )
        metric_spec_json = spec.display_json(intent.metric_key)
        print(f"[Calculation] Công thức sẽ dùng: {metric_spec_json}")

        period_label = ""
        if intent.quarter and intent.year:
            period_label = f"quý {intent.quarter} năm {intent.year}"
        elif intent.year:
            period_label = f"năm {intent.year}"

        operands: dict[str, OperandDetail] = {}
        all_citations, missing_fields = [], []        
        for field in spec.required_metrics:
            operand, used_citations = self._fetch_operand(field, intent, period_label)
            if operand is None:
                missing_fields.append(FIELD_LABELS.get(field, field))
                continue
            operands[field] = operand
            all_citations.extend(used_citations)

        if missing_fields:
            print(f"[Calculation] Thiếu operand: {missing_fields}, không đủ dữ liệu để tính {spec.name_vi}.")
            ticker_part = f"cho {intent.ticker} " if intent.ticker else ""
            return CalculationResponse(
                answer=(f"Không tìm đủ dữ liệu trong hệ thống để tính {spec.name_vi} "
                        f"{ticker_part}{period_label}. Thiếu: {', '.join(missing_fields)}."),
                result=None, citations=all_citations,
                metric_spec=metric_spec_json,
                intent=intent_json,
            )

        deduped_citations, seen_labels = [], set()
        for c in all_citations:
            key = (c.get("doc_id"), c.get("page_start"))
            if key in seen_labels:
                continue
            seen_labels.add(key)
            deduped_citations.append(c)
        for i, c in enumerate(deduped_citations, start=1):
            c["index"] = i
            c["label"] = format_citation_label(c, i)

        try:
            output = compute_metric_from_operands(intent.metric_key, operands)
        except FormulaError as e:
            return CalculationResponse(
                answer=f"Không thể tính {spec.name_vi}: {e}",
                calculation=None, citations=deduped_citations,
                metric_spec=metric_spec_json,
                intent=intent_json,
            )
        print(f"[Calculation] Kết quả {spec.name_vi} = {output.result} {spec.unit} "
              f"(công thức: {output.formula})")

        answer = format_calculation_answer(
        metric_label=spec.name_vi,
        period_label=period_label,
        ticker=intent.ticker,
        output=output,
        spec=spec,
        field_labels=FIELD_LABELS,
        )

        return CalculationResponse(answer=answer, calculation=output, citations=deduped_citations, metric_spec=metric_spec_json, intent=intent_json)