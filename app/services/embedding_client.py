"""
app/services/embedding_client.py

Wrapper cho BGE-M3 (BAAI) -- embedding model dùng ở 2 chỗ:
  - Ingestion: embed chunk.embedding_text (text_child/table) trước khi
    upsert vào Qdrant.
  - Retrieval: embed câu hỏi (sau khi qua query_rewriter) để search.

Dùng thư viện FlagEmbedding (chính chủ BAAI) thay vì sentence-transformers,
vì FlagEmbedding xuất được CẢ dense lẫn sparse (lexical weights) trong 1 lần
encode -- cần cho app/retrieval/hybrid_search.py sau này (dense + sparse qua
named vectors của Qdrant), khỏi phải chạy riêng 1 BM25 engine khác.

BGE-M3 hỗ trợ tối đa 8192 token/input, đa ngôn ngữ (có tiếng Việt), dense
vector 1024 chiều cố định.

QUAN TRỌNG: BGE-M3 (khác bge-large-en/zh v1.5) KHÔNG cần instruction prefix
(vd "Represent this sentence for searching relevant passages:") cho câu
query -- theo khuyến nghị chính thức của BAAI. Thêm prefix vào sẽ làm giảm
chất lượng thay vì tăng, nên embed_query() ở đây KHÔNG thêm prefix.
"""

from __future__ import annotations

import os
import re
import sys
import uuid
from functools import lru_cache
from typing import Optional


# ---------------------------------------------------------------------------
# Ép UTF-8 cho stdout/stderr ngay khi import (cùng lý do đã áp dụng ở
# app/ingestion/parser.py -- một số môi trường mặc định locale ASCII khiến
# log tiếng Việt crash giữa chừng).
# ---------------------------------------------------------------------------

def _ensure_utf8_stdio() -> None:
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is not None and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


_ensure_utf8_stdio()


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

EMBEDDING_MODEL_ID = os.getenv("EMBEDDING_MODEL_ID", "BAAI/bge-m3")
EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE")  # để trống -> tự dò cuda/cpu
EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "12"))
EMBEDDING_MAX_LENGTH = int(os.getenv("EMBEDDING_MAX_LENGTH", "8192"))
EMBEDDING_USE_FP16 = os.getenv("EMBEDDING_USE_FP16", "auto")  # "auto" | "true" | "false"

DENSE_DIM = 1024  # cố định theo kiến trúc BGE-M3, dùng khi tạo collection Qdrant sau này


# ---------------------------------------------------------------------------
# Load model (lazy singleton -- load 1 lần/process, giống pattern đã dùng
# cho Qwen3-VL ở parser.py trước khi đổi sang gọi HTTP)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _load_model():
    import torch
    from FlagEmbedding import BGEM3FlagModel

    device = EMBEDDING_DEVICE or ("cuda" if torch.cuda.is_available() else "cpu")

    if EMBEDDING_USE_FP16 == "auto":
        use_fp16 = device.startswith("cuda")
    else:
        use_fp16 = EMBEDDING_USE_FP16.lower() == "true"

    print(f"[embedding_client] Đang load {EMBEDDING_MODEL_ID} | device={device} | fp16={use_fp16}")
    model = BGEM3FlagModel(EMBEDDING_MODEL_ID, use_fp16=use_fp16, device=device)

    if torch.cuda.is_available():
        print(f"[embedding_client] CUDA khả dụng -- GPU: {torch.cuda.get_device_name(0)}")
    else:
        print("[embedding_client] CUDA KHÔNG khả dụng -- đang chạy CPU (sẽ chậm hơn nhiều).")

    return model


def get_device_info() -> dict:
    """
    Kiểm tra CHẮC CHẮN model đang chạy CPU hay GPU, thay vì đoán qua log --
    gọi hàm này (vd trong test_embedding.py) để in ra rõ ràng, tránh lặp lại
    tình huống phải đoán 'file đã chạy GPU chưa' như ở bước OCR trước đó.
    """
    import torch

    _load_model()  # đảm bảo model đã load (và đã in log device ở trên)
    return {
        "cuda_available": torch.cuda.is_available(),
        "configured_device": EMBEDDING_DEVICE or ("cuda" if torch.cuda.is_available() else "cpu"),
        "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "fp16": (EMBEDDING_USE_FP16 == "auto" and torch.cuda.is_available()) or EMBEDDING_USE_FP16.lower() == "true",
    }


def _to_native(vec) -> list:
    """numpy array / float32 -> list[float] Python thuần, JSON-serializable
    và không bắt nơi gọi (vd qdrant_client) phải phụ thuộc numpy."""
    return [float(x) for x in vec]


# ---------------------------------------------------------------------------
# Embed text thô
# ---------------------------------------------------------------------------

def embed_texts(
    texts: list[str],
    batch_size: int = EMBEDDING_BATCH_SIZE,
    max_length: int = EMBEDDING_MAX_LENGTH,
    return_sparse: bool = False,
) -> dict:
    """
    Embed 1 danh sách text (thường là chunk['embedding_text']).

    Trả về:
        {
            "dense":  list[list[float]]        # 1 vector 1024-dim / text
            "sparse": list[dict[str,float]] | None   # token_id(str) -> weight, chỉ có nếu return_sparse=True
        }
    """
    if not texts:
        return {"dense": [], "sparse": [] if return_sparse else None}

    model = _load_model()
    output = model.encode(
        texts,
        batch_size=batch_size,
        max_length=max_length,
        return_dense=True,
        return_sparse=return_sparse,
        return_colbert_vecs=False,
    )

    dense = [_to_native(v) for v in output["dense_vecs"]]

    sparse = None
    if return_sparse:
        # lexical_weights: list[dict[int/token_id, float]] -> ép key str để JSON-serializable/Qdrant payload
        sparse = [{str(k): float(v) for k, v in lw.items()} for lw in output["lexical_weights"]]

    return {"dense": dense, "sparse": sparse}


def embed_query(query: str, return_sparse: bool = False) -> dict:
    """Embed 1 câu hỏi (thường là 1 trong các rewritten_queries từ
    query_rewriter). KHÔNG thêm instruction prefix -- xem ghi chú đầu file."""
    result = embed_texts([query], batch_size=1, return_sparse=return_sparse)
    return {
        "dense": result["dense"][0],
        "sparse": result["sparse"][0] if return_sparse else None,
    }


# ---------------------------------------------------------------------------
# Embed trực tiếp từ output của chunker.py
# ---------------------------------------------------------------------------

_RETRIEVABLE_CHUNK_TYPES = {"text_child", "table"}


def attach_embeddings_to_chunks(
    chunks: list[dict],
    batch_size: int = EMBEDDING_BATCH_SIZE,
    return_sparse: bool = False,
    include_parent: bool = False,
) -> list[dict]:
    """
    Nhận list chunk dict (từ Chunk.to_dict() trong chunker.py), trả về list
    MỚI (không sửa in-place) có thêm field 'dense_vector' (+ 'sparse_vector'
    nếu return_sparse=True).

    MẶC ĐỊNH BỎ QUA chunk type="parent": parent chỉ dùng để mở rộng ngữ cảnh
    sau khi tìm được text_child/table match (đọc từ Mongo bằng parent_id),
    KHÔNG bao giờ được search trực tiếp bằng vector -- embed parent vừa tốn
    compute vô ích vừa có thể vượt quá 8192 token với section rất dài. Đặt
    include_parent=True chỉ khi có lý do cụ thể cần vector cho parent.
    """
    targets = [c for c in chunks if include_parent or c.get("chunk_type") in _RETRIEVABLE_CHUNK_TYPES]
    skipped = len(chunks) - len(targets)
    if skipped:
        print(f"[embedding_client] Bỏ qua {skipped} chunk type='parent' (không cần embed).")

    texts = [c.get("embedding_text") or c.get("content") or "" for c in targets]
    result = embed_texts(texts, batch_size=batch_size, return_sparse=return_sparse)

    out = []
    for i, c in enumerate(targets):
        new_c = dict(c)
        new_c["dense_vector"] = result["dense"][i]
        if return_sparse:
            new_c["sparse_vector"] = result["sparse"][i]
        out.append(new_c)
    return out

COMPANY_TICKER_MAP = {
    "FPT": "CTCP FPT",
    "HPG": "CTCP Tập đoàn Hòa Phát",
    "MWG": "CTCP Đầu tư Thế Giới Di Động",
    "VNM": "CTCP Sữa Việt Nam",
}
 
_TICKER_RE = re.compile(r"^([A-Z]{2,5})_")
_YEAR_RE = re.compile(r"(20\d{2})")
_QUARTER_RE = re.compile(r"Q([1-4])", re.IGNORECASE)
_ANNUAL_REPORT_RE = re.compile(r"BCTN|_AR_", re.IGNORECASE)
_FINANCIAL_STATEMENT_RE = re.compile(r"BCTC|CFS|PCFS", re.IGNORECASE)
_TICKER_ALIASES = {
    "baovietbank": "BVB", "bao viet bank": "BVB",
    "bidv": "BID",
    "agribank": "AGR",
}
_COMPANY_NAME_TO_TICKER = {v.lower(): k for k, v in COMPANY_TICKER_MAP.items()}

def _guess_ticker_from_text(*texts: str) -> Optional[str]:
    for t in texts:
        if not t:
            continue
        low = t.lower()
        for alias, ticker in _TICKER_ALIASES.items():
            if alias in low:
                return ticker
        for name, ticker in _COMPANY_NAME_TO_TICKER.items():
            if name in low:
                return ticker
    return None
 
 
def parse_document_metadata(document_id: str, source_file: str = "", ticker_hint: Optional[str] = None) -> dict:
    """
    Suy company/ticker/year/quarter/document_type từ document_id (vd
    'FPT_BCTC_Q1_2024') hoặc source_file. Trả None cho field không đoán
    được thay vì đoán bừa.
    """
    basis = document_id or source_file or ""
 
    ticker_match = _TICKER_RE.match(basis)
    ticker = ticker_match.group(1) if ticker_match else ticker_hint
    if not ticker:
        ticker = _guess_ticker_from_text(basis, company_hint or "")
        
    year_match = _YEAR_RE.search(basis)
    year = int(year_match.group(1)) if year_match else None
 
    quarter_match = _QUARTER_RE.search(basis)
    quarter = int(quarter_match.group(1)) if quarter_match else None
 
    if quarter:
        document_type = "BCTC_Quy"
    elif _ANNUAL_REPORT_RE.search(basis):
        # "BCTN"/"AR" (annual/thường niên) không nằm trong enum của
        # data/metadata_schema.json (chỉ có BCTC_Nam/BCTC_Quy/...) -- gắn
        # nhãn riêng để không đánh tráo với báo cáo tài chính năm thật.
        document_type = "BCTN"
    elif _FINANCIAL_STATEMENT_RE.search(basis):
        document_type = "BCTC_Nam"
    else:
        document_type = None
 
    return {
        "ticker": ticker,
        "company": COMPANY_TICKER_MAP.get(ticker, ticker),
        "year": year,
        "quarter": quarter,
        "document_type": document_type,
    }
 
 
# ---------------------------------------------------------------------------
# Build payload sẵn sàng cho Qdrant (PointStruct kwargs) từ output của
# attach_embeddings_to_chunks()
# ---------------------------------------------------------------------------
 
def to_qdrant_points(embedded_chunks: list[dict]) -> list[dict]:
 def to_qdrant_points(embedded_chunks: list[dict]) -> list[dict]:
    points: list[dict] = []
    skipped: list[tuple[str, str]] = []

    for c in embedded_chunks:
        raw_id = str(c.get("chunk_id") or c.get("_id", "")).strip()
        try:
            point_id = str(uuid.UUID(hex=raw_id))
        except Exception:
            skipped.append((raw_id or "<empty>", "chunk_id không phải UUID hex hợp lệ"))
            continue

        vector = c.get("dense_vector")
        if not vector:
            skipped.append((raw_id, "thiếu dense_vector"))
            continue

        # chunker.py (pipeline hiện tại -> chunked_documents_2025) trả về
        # field PHẲNG: doc_id/ticker/company/year/source_file/text -- KHÔNG
        # có "document_id" hay "metadata" lồng nhau như code cũ giả định.
        # Đó là lý do ticker luôn ra None trong Qdrant payload trước đây.
        doc_id = c.get("doc_id") or c.get("document_id") or ""
        source_file = c.get("source_file") or ""
        raw_ticker = c.get("ticker")
        raw_company = c.get("company")

        doc_meta = parse_document_metadata(
            doc_id, source_file, ticker_hint=raw_ticker, company_hint=raw_company
        )

        payload = {
            "document_id": doc_id,
            "company": raw_company or doc_meta["company"],
            "ticker": raw_ticker or doc_meta["ticker"],
            "year": c.get("year") or doc_meta["year"],
            "quarter": doc_meta["quarter"],
            "document_type": doc_meta["document_type"],
            "source_file": source_file,
            "chunk_type": c.get("chunk_type"),
            "parent_id": c.get("parent_id"),
            "section_path": c.get("heading_path") or c.get("section_path", []),
            "page_start": c.get("page_start"),
            "page_end": c.get("page_end"),
            "token_count": c.get("token_count"),
            "content": c.get("text") or c.get("content"),  # chunker.py dùng "text", không phải "content"
            "order_index": c.get("order_index"),
        }
        points.append({"id": point_id, "vector": vector, "payload": payload})

    if skipped:
        print(f"[embedding_client] Bỏ qua {len(skipped)} chunk khi build Qdrant points:")
        for cid, reason in skipped[:10]:
            print(f"    - {cid}: {reason}")
    return points