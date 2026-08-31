"""
generate_ragas_testset.py

Sinh bộ testset tổng hợp (synthetic testset) bằng Ragas, dùng TRỰC TIẾP các
chunk đã ingest sẵn trong MongoDB (collection "chunked_documents_2025", xem
app/ingestion/chunker.py) thay vì để Ragas tự split lại tài liệu từ đầu --
đúng theo hướng dẫn "Using Pre-chunked Data" của Ragas
(generator.generate_with_chunks()).

Điểm khác biệt so với ví dụ trong docs Ragas: dự án này KHÔNG gọi thẳng
OpenAI mà gọi qua OmniRoute -- một gateway lộ ra bề mặt tương thích OpenAI
tại `{baseURL}/v1` (xem tài liệu "OpenCode Integration" của OmniRoute:
mọi request đi qua `/v1/chat/completions` theo đúng OpenAI surface). Vì
vậy vẫn dùng thẳng `openai.OpenAI` client như ví dụ prechunked_data của
Ragas docs, chỉ đổi `base_url`/`api_key` trỏ về OmniRoute -- không cần sửa
gì trong logic Ragas.

    Theo tài liệu OmniRoute (OpenCode Integration):
    - base_url chuẩn: "http://<host>:<port>/v1" (local mặc định cổng
      20128 -> "http://localhost:20128/v1"). OmniRoute tự dedupe nếu bạn
      lỡ truyền thừa "/v1" ở cuối OMNIROUTE_BASE_URL (xem
      `_normalize_omniroute_base_url()` bên dưới, mô phỏng lại đúng cách
      OmniRoute tự chuẩn hoá URL cho OpenCode).
    - api_key: nếu OmniRoute đang chạy với REQUIRE_API_KEY=false (mặc định
      khi chạy local) thì dùng literal "sk_omniroute"; nếu
      REQUIRE_API_KEY=true thì phải lấy API key thật từ Dashboard -> API
      Manager của OmniRoute.
    - model id: OmniRoute route theo tên combo/model đã cấu hình (vd
      "claude-sonnet-4-5-thinking", "gemini-3-flash", hoặc "auto" để dùng
      Auto-Combo -- OmniRoute tự chọn model tốt nhất). Đặt đúng tên model
      LLM sinh câu hỏi vào biến OMNIROUTE_LLM_MODEL bên dưới.

EMBEDDING: theo yêu cầu, phần embedding (dùng để build quan hệ giữa các
chunk qua CosineSimilarityBuilder/OverlapScoreBuilder -- xem docs Ragas
"Using Pre-chunked Data") KHÔNG gọi qua OmniRoute mà dùng thẳng model
BGE-M3 ĐÃ CHẠY LOCAL SẴN trong app/services/embedding_client.py (cùng model
dùng để embed chunk lúc ingest vào Qdrant, xem embed_texts()/embed_query()).
Điều này còn giúp testset "cùng không gian embedding" với retrieval thật
của hệ thống -- không tốn thêm API call nào ra ngoài chỉ cho bước sinh
testset. Ragas chấp nhận bất kỳ object nào implement interface
`langchain_core.embeddings.Embeddings` (embed_documents/embed_query) qua
`ragas.embeddings.LangchainEmbeddingsWrapper` -- xem
`build_local_bge_m3_embeddings()` bên dưới.

Cách chạy:
    export OMNIROUTE_BASE_URL="http://localhost:20128"              # hoặc host OmniRoute thật, có/không /v1 đều được
    export OMNIROUTE_API_KEY="sk_omniroute"                         # hoặc key thật nếu REQUIRE_API_KEY=true
    export OMNIROUTE_LLM_MODEL="claude-sonnet-4-5-thinking"         # hoặc "auto" để dùng Auto-Combo
    export MONGO_URI="mongodb://admin:changeme@localhost:27017"     # khớp README/docker-compose

    # Chạy TỪ THƯ MỤC GỐC của repo (nơi có thư mục app/) -- script cần
    # import được app.services.embedding_client để dùng BGE-M3 local.
    python generate_ragas_testset.py --testset-size 20 --out data/evaluation/ragas_testset.csv

    # Chỉ lấy chunk của 1 ticker/năm cụ thể (khớp field ticker/year trong
    # chunked_documents_2025.chunks[], xem app/ingestion/chunker.py):
    python generate_ragas_testset.py --ticker BVB --year 2025 --testset-size 10

    # Nếu vì lý do nào đó muốn quay lại dùng embedding qua OmniRoute thay vì
    # BGE-M3 local (cần OmniRoute expose /v1/embeddings):
    python generate_ragas_testset.py --embedding-backend omniroute

Phụ thuộc (cài thêm nếu chưa có):
    pip install ragas langchain-core openai pymongo pandas --break-system-packages
    # BGE-M3 local (đã có sẵn nếu bạn từng chạy app/services/embedding_client.py):
    pip install FlagEmbedding torch --break-system-packages
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Optional/heavy deps -- fail fast với thông báo rõ ràng thay vì traceback
# khó hiểu, cùng phong cách với evaluation/ragas_eval.py đã có trong repo.
# ---------------------------------------------------------------------------

def _require(module_name: str, pip_name: Optional[str] = None):
    try:
        return __import__(module_name)
    except ImportError:
        pip_name = pip_name or module_name
        print(
            f"[FATAL] Thiếu thư viện '{module_name}'. Cài bằng:\n"
            f"    pip install {pip_name} --break-system-packages",
            file=sys.stderr,
        )
        sys.exit(1)


_require("pymongo")
_require("openai")
_require("ragas")
_require("langchain_core")

from pymongo import MongoClient  # noqa: E402
from openai import OpenAI  # noqa: E402
from langchain_core.documents import Document  # noqa: E402
from langchain_core.embeddings import Embeddings  # noqa: E402
from ragas.testset.synthesizers.generate import TestsetGenerator  # noqa: E402
from ragas.llms import llm_factory  # noqa: E402
from ragas.embeddings import OpenAIEmbeddings  # noqa: E402

try:
    from ragas.embeddings import LangchainEmbeddingsWrapper  # noqa: E402
except ImportError:
    LangchainEmbeddingsWrapper = None  # dò lại + báo lỗi rõ ràng lúc dùng, xem build_local_bge_m3_embeddings()

# Cho phép chạy script từ bất kỳ đâu trong repo (không chỉ đúng thư mục gốc)
# -- cần thiết để import được app.services.embedding_client (BGE-M3 local),
# giống pattern sys.path.insert() mà test_embedding.py/test_chunking.py
# trong repo đã dùng.
_PROJECT_ROOT = str(Path(__file__).resolve().parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:changeme@mongodb:27017")
MONGO_DB = os.getenv("MONGO_DB", "financial_rag")
# Đúng tên collection chunker.py thật sự ghi vào (xem app/ingestion/chunker.py
# DESTINATION_COLLECTION và app/services/mongo_client.get_chunks_collection()).
CHUNKS_COLLECTION = os.getenv("MONGO_CHUNKS_COLLECTION", "chunked_documents_2025")

# Chỉ những chunk_type này mới có nội dung "đọc được trực tiếp" phù hợp làm
# 1 node cho Ragas -- khớp _RETRIEVABLE_CHUNK_TYPES trong
# app/services/embedding_client.py (bỏ "parent" vì chỉ dùng để mở rộng ngữ
# cảnh, không phải đơn vị nội dung độc lập).
RETRIEVABLE_CHUNK_TYPES = {"child", "text_child", "table"}

# "sk_omniroute" = placeholder literal OmniRoute chấp nhận khi chạy local
# với REQUIRE_API_KEY=false (mặc định). Nếu server bật REQUIRE_API_KEY=true,
# set OMNIROUTE_API_KEY thành API key thật lấy từ Dashboard -> API Manager.
OMNIROUTE_API_KEY = os.getenv("OMNIROUTE_API_KEY", "sk_omniroute")
OMNIROUTE_BASE_URL_RAW = os.getenv("OMNIROUTE_BASE_URL", "http://localhost:20128")
# "auto" = Auto-Combo của OmniRoute (tự chọn model tốt nhất đang khả dụng),
# đặt tên model/combo cụ thể (vd "claude-sonnet-4-5-thinking") nếu muốn cố định.
OMNIROUTE_LLM_MODEL = os.getenv("OMNIROUTE_LLM_MODEL", "auto")
# Chỉ dùng khi --embedding-backend=omniroute (mặc định KHÔNG dùng -- xem
# build_local_bge_m3_embeddings() bên dưới, mặc định dùng BGE-M3 local).
OMNIROUTE_EMBEDDING_MODEL = os.getenv("OMNIROUTE_EMBEDDING_MODEL", "text-embedding-3-small")


def _normalize_omniroute_base_url(raw: str) -> str:
    """
    Mô phỏng đúng quy tắc chuẩn hoá URL mà OmniRoute áp dụng cho OpenCode
    (xem bảng "URL normalisation" trong docs OpenCode Integration): dù
    người dùng truyền có/không có "/v1", có/không có "/" thừa ở cuối, kết
    quả luôn là đúng 1 "/v1" ở cuối -- tránh lỗi 404 do double-suffix
    "/v1/v1/..." (lỗi phổ biến nhất theo docs OmniRoute).
    """
    normalized = raw.rstrip("/")
    while normalized.endswith("/v1"):
        normalized = normalized[: -len("/v1")].rstrip("/")
    return f"{normalized}/v1"


OMNIROUTE_BASE_URL = _normalize_omniroute_base_url(OMNIROUTE_BASE_URL_RAW)


# ---------------------------------------------------------------------------
# Bước 1: đọc chunk từ MongoDB -> list[langchain Document]
# ---------------------------------------------------------------------------

def fetch_chunks_as_documents(
    ticker: Optional[str] = None,
    year: Optional[int] = None,
    limit: Optional[int] = None,
) -> list[Document]:
    """
    Đọc trực tiếp các chunk đã ingest trong MongoDB (mỗi document Mongo
    chứa 1 mảng `chunks`, xem chunk_document()/process() trong
    app/ingestion/chunker.py) và chuyển thành langchain Document -- đúng
    input mà Ragas.generate_with_chunks() cần (page_content + metadata).

    Chỉ giữ chunk_type trong RETRIEVABLE_CHUNK_TYPES: "parent" bị loại vì nó
    là bản gộp của các child/table bên dưới, giữ lại sẽ làm Ragas thấy nội
    dung trùng lặp nhiều lần trong cùng 1 testset.
    """
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client[MONGO_DB]
    col = db[CHUNKS_COLLECTION]

    mongo_query: dict[str, Any] = {}
    if ticker:
        mongo_query["ticker"] = ticker.upper()
    if year:
        mongo_query["year"] = int(year)

    print(f"[*] Đang đọc chunk từ Mongo: db='{MONGO_DB}', collection='{CHUNKS_COLLECTION}', filter={mongo_query}")
    file_docs = list(col.find(mongo_query))
    print(f"[i] Tìm thấy {len(file_docs)} file khớp filter")

    documents: list[Document] = []
    for file_doc in file_docs:
        for chunk in file_doc.get("chunks", []):
            if chunk.get("chunk_type") not in RETRIEVABLE_CHUNK_TYPES:
                continue
            text = (chunk.get("text") or chunk.get("content") or "").strip()
            if not text:
                continue

            metadata = {
                "chunk_id": chunk.get("_id") or chunk.get("chunk_id"),
                "doc_id": chunk.get("doc_id"),
                "parent_id": chunk.get("parent_id"),
                "company": chunk.get("company"),
                "ticker": chunk.get("ticker"),
                "year": chunk.get("year"),
                "source_file": chunk.get("source_file"),
                "section": chunk.get("section"),
                "subsection": chunk.get("subsection"),
                "heading_path": chunk.get("heading_path") or [],
                "page_start": chunk.get("page_start"),
                "page_end": chunk.get("page_end"),
                "block_type": chunk.get("block_type"),
            }
            # Ragas không cần field None -- dọn bớt cho gọn payload/metadata
            metadata = {k: v for k, v in metadata.items() if v not in (None, [], "")}

            documents.append(Document(page_content=text, metadata=metadata))

            if limit and len(documents) >= limit:
                print(f"[i] Đã đạt --limit={limit} chunk, dừng đọc thêm.")
                client.close()
                return documents

    client.close()
    print(f"[✓] Chuẩn bị được {len(documents)} chunk hợp lệ (chunk_type in {sorted(RETRIEVABLE_CHUNK_TYPES)})")
    if not documents:
        print(
            "[!] KHÔNG có chunk nào khớp filter -- kiểm tra lại MONGO_URI/MONGO_DB/"
            "MONGO_CHUNKS_COLLECTION, hoặc bỏ --ticker/--year để lấy toàn bộ."
        )
    return documents


# ---------------------------------------------------------------------------
# Bước 2: build client Omniroute (OpenAI-compatible) cho Ragas
# ---------------------------------------------------------------------------

def build_omniroute_client() -> OpenAI:
    """
    OmniRoute lộ ra bề mặt tương thích OpenAI tại `{baseURL}/v1`
    (`/v1/chat/completions`) -- nên chỉ cần dùng thẳng `openai.OpenAI`
    client với base_url trỏ về OmniRoute, đúng cách Ragas docs minh hoạ
    cho pre-chunked data (`OpenAI(api_key=...)` rồi truyền vào
    `llm_factory(..., client=client)`). Client này dùng để sinh CÂU HỎI/
    ĐÁP ÁN (LLM) -- phần embedding mặc định KHÔNG đi qua client này, xem
    build_local_bge_m3_embeddings().

    Auth: OmniRoute (client OpenAI SDK) luôn gửi `Authorization: Bearer
    <apiKey>` -- không có xử lý đặc biệt kiểu Anthropic `x-api-key` ở nhánh
    OpenAI surface này, nên chỉ cần set đúng OMNIROUTE_API_KEY là đủ (xem
    bảng "Authentication modes" trong docs OmniRoute).
    """
    print(f"[*] Khởi tạo client OmniRoute: base_url={OMNIROUTE_BASE_URL}, llm_model={OMNIROUTE_LLM_MODEL}")
    return OpenAI(api_key=OMNIROUTE_API_KEY, base_url=OMNIROUTE_BASE_URL)


def build_local_bge_m3_embeddings():
    """
    Wrap BGE-M3 local (app/services/embedding_client.py -- ĐÚNG model đang
    dùng để embed chunk lúc ingest vào Qdrant) thành 1 object khớp
    interface `langchain_core.embeddings.Embeddings` (embed_documents,
    embed_query), rồi bọc thêm 1 lớp `LangchainEmbeddingsWrapper` của Ragas
    để TestsetGenerator dùng được -- Ragas không quan tâm embedding đến từ
    OpenAI hay đâu, miễn implement đúng interface này.

    Model chỉ load thật sự (torch/FlagEmbedding, có thể tốn vài giây - vài
    chục giây nếu chạy CPU) ở LẦN GỌI ĐẦU TIÊN, nhờ @lru_cache trong
    _load_model() của embedding_client.py -- các lần sau (embed_query lẫn
    embed_documents) đều tái sử dụng đúng 1 model instance đã load.
    """
    if LangchainEmbeddingsWrapper is None:
        print(
            "[FATAL] Bản ragas đang cài không có ragas.embeddings.LangchainEmbeddingsWrapper. "
            "Nâng cấp ragas (pip install -U ragas --break-system-packages) hoặc dùng "
            "--embedding-backend omniroute thay thế.",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        from app.services.embedding_client import embed_texts, embed_query, get_device_info
    except ImportError as e:
        print(
            f"[FATAL] Không import được app.services.embedding_client ({e}). "
            "Chạy script này từ thư mục gốc của repo (nơi có thư mục app/), "
            "và cài đủ dependency BGE-M3: pip install FlagEmbedding torch --break-system-packages",
            file=sys.stderr,
        )
        sys.exit(1)

    class _BGEM3LocalEmbeddings(Embeddings):
        """Adapter mỏng -- KHÔNG tự implement lại logic embed, chỉ gọi lại
        đúng embed_texts()/embed_query() đã có sẵn trong embedding_client.py
        để đảm bảo cùng 1 model/1 cấu hình (max_length, fp16...) với
        pipeline ingestion thật."""

        def embed_documents(self, texts: list[str]) -> list[list[float]]:
            if not texts:
                return []
            return embed_texts(list(texts))["dense"]

        def embed_query(self, text: str) -> list[float]:
            return embed_query(text)["dense"]

    info = get_device_info()
    print(f"[*] Dùng BGE-M3 local cho embedding (device={info['configured_device']}, fp16={info['fp16']})")
    return LangchainEmbeddingsWrapper(_BGEM3LocalEmbeddings())


# ---------------------------------------------------------------------------
# Bước 3: sinh testset bằng Ragas (generate_with_chunks -- bỏ qua bước split
# nội bộ của Ragas vì mình đã có chunk sẵn từ pipeline ingestion thật)
# ---------------------------------------------------------------------------

def generate_testset(documents: list[Document], testset_size: int, embedding_backend: str = "bge-m3"):
    client = build_omniroute_client()  # LLM sinh câu hỏi/answer -- luôn qua OmniRoute

    if embedding_backend == "bge-m3":
        embedding_model = build_local_bge_m3_embeddings()
    else:
        print(f"[*] Dùng embedding qua OmniRoute (model={OMNIROUTE_EMBEDDING_MODEL}) -- "
              "yêu cầu OmniRoute có expose /v1/embeddings cho model này.")
        embedding_model = OpenAIEmbeddings(client=client, model=OMNIROUTE_EMBEDDING_MODEL)

    generator = TestsetGenerator(
        llm=llm_factory(OMNIROUTE_LLM_MODEL, client=client),
        embedding_model=embedding_model,
    )

    print(f"[*] Đang sinh testset (testset_size={testset_size}) từ {len(documents)} chunk...")
    testset = generator.generate_with_chunks(chunks=documents, testset_size=testset_size)
    print("[✓] Sinh testset xong.")
    return testset


# ---------------------------------------------------------------------------
# Bước 4: xuất kết quả -- vừa ra CSV thô của Ragas, vừa convert sang đúng
# format ragas_test_dataset.json đã dùng sẵn trong repo (question/contexts/
# ground_truth/evolution_type) để cắm thẳng vào evaluation/ragas_eval.py,
# evaluation/generation_eval.py mà không cần sửa gì thêm.
# ---------------------------------------------------------------------------

def _first_present(row: dict, *candidates: str):
    for c in candidates:
        if c in row and row[c] not in (None, ""):
            return row[c]
    return None


def export_results(testset, out_csv: Path, out_json: Path) -> None:
    df = testset.to_pandas()

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False)
    print(f"[✓] Đã lưu CSV thô (định dạng gốc của Ragas) tại: {out_csv}")

    # Ragas đổi tên cột giữa các bản (question/contexts/ground_truth ở bản
    # cũ  vs  user_input/reference_contexts/reference ở bản mới) -- dò cả 2
    # để convert an toàn thay vì hard-code 1 bộ tên cột.
    records = df.to_dict(orient="records")
    converted = []
    for r in records:
        question = _first_present(r, "user_input", "question")
        ground_truth = _first_present(r, "reference", "ground_truth")
        contexts = _first_present(r, "reference_contexts", "contexts") or []
        if isinstance(contexts, str):
            # 1 số bản Ragas lưu contexts dưới dạng chuỗi đã json.dumps sẵn
            try:
                contexts = json.loads(contexts)
            except Exception:
                contexts = [contexts]
        evolution_type = _first_present(r, "synthesizer_name", "evolution_type") or "unknown"

        converted.append({
            "question": question,
            "contexts": contexts,
            "ground_truth": ground_truth,
            "evolution_type": evolution_type,
        })

    out_json.parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(converted, f, ensure_ascii=False, indent=2)
    print(f"[✓] Đã lưu bản convert khớp format ragas_test_dataset.json tại: {out_json}")
    print(f"    (dùng trực tiếp cho evaluation/ragas_eval.py --dataset {out_json})")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sinh synthetic testset bằng Ragas từ chunk đã ingest trong MongoDB, dùng Omniroute thay OpenAI."
    )
    parser.add_argument("--ticker", type=str, default=None, help="Chỉ lấy chunk của 1 ticker (vd BVB, BID, VCB...).")
    parser.add_argument("--year", type=int, default=None, help="Chỉ lấy chunk của 1 năm (vd 2025).")
    parser.add_argument("--limit", type=int, default=None, help="Giới hạn số chunk đọc từ Mongo (để test nhanh).")
    parser.add_argument("--testset-size", type=int, default=20, help="Số câu hỏi Ragas sẽ sinh ra.")
    parser.add_argument(
        "--embedding-backend", choices=["bge-m3", "omniroute"], default="bge-m3",
        help="Embedding dùng để build quan hệ giữa các chunk. 'bge-m3' (mặc định) "
             "dùng BGE-M3 local có sẵn trong app/services/embedding_client.py -- "
             "không tốn API call, đồng bộ với embedding dùng lúc retrieval thật. "
             "'omniroute' gọi qua OmniRoute (cần OmniRoute expose /v1/embeddings).",
    )
    parser.add_argument(
        "--out", type=Path, default=Path("data/evaluation/ragas_testset.csv"),
        help="Đường dẫn file CSV xuất ra (bản gốc của Ragas).",
    )
    parser.add_argument(
        "--out-json", type=Path, default=None,
        help="Đường dẫn file JSON xuất ra (đã convert khớp format ragas_test_dataset.json). "
             "Mặc định = --out nhưng đổi đuôi thành .json.",
    )
    args = parser.parse_args()

    out_json = args.out_json or args.out.with_suffix(".json")

    documents = fetch_chunks_as_documents(ticker=args.ticker, year=args.year, limit=args.limit)
    if not documents:
        sys.exit(1)

    testset = generate_testset(documents, testset_size=args.testset_size, embedding_backend=args.embedding_backend)
    export_results(testset, out_csv=args.out, out_json=out_json)


if __name__ == "__main__":
    main()
