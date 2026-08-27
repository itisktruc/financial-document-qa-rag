# test_embedding.py
"""
Script test thủ công: embed các chunk đã tạo (từ test_parse_chunk.py) bằng
BGE-M3 (app/services/embedding_client.py), in rõ model đang chạy CPU hay
GPU, và làm 1 sanity check nhanh bằng cosine similarity (không cần Qdrant):
tự embed vài câu hỏi mẫu rồi xem câu nào gần vector nào nhất, để phát hiện
sớm nếu model chạy sai / load nhầm / vector toàn NaN...

Chạy:
    python test_embedding.py
"""

from __future__ import annotations

import json
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.embedding_client import (
    DENSE_DIM,
    attach_embeddings_to_chunks,
    embed_query,
    get_device_info,
    to_qdrant_points,
)

from app.services.qdrant_service import (
    QDRANT_COLLECTION,
    search_similar_blocks,
    store_in_qdrant,
    count_points,
)

CHUNKS_PATH = "data/processed/FPT/FPT_BCTC_2024_chunks.json"
EMBEDDED_PATH = "data/embedded/FPT/FPT_BCTC_2024_embedded.json"

# Câu hỏi test để soi cosine similarity -- sửa/thêm tuỳ nhu cầu
TEST_QUESTIONS = [
    "Tổng tài sản của FPT năm 2024 là bao nhiêu?",
    "Doanh thu thuần quý gần nhất của FPT tăng bao nhiêu phần trăm?",
]

TOP_K = 3


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def main():
    if not os.path.exists(CHUNKS_PATH):
        print(f"[!] Chưa có file chunks tại: {CHUNKS_PATH}")
        print("    Chạy test_parse_chunk.py trước.")
        return

    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    print(f"[i] Đã load {len(chunks)} chunk từ {CHUNKS_PATH}")

    # ---- Bước 1: kiểm tra device TRƯỚC khi embed hàng loạt ----
    print("\n[*] Đang load model + kiểm tra device...")
    info = get_device_info()
    print(f"[i] cuda_available = {info['cuda_available']}")
    print(f"[i] device đang dùng = {info['configured_device']}"
          + (f" ({info['gpu_name']})" if info["gpu_name"] else ""))
    print(f"[i] fp16 = {info['fp16']}")
    if not info["cuda_available"]:
        print("[!] Đang chạy CPU -- embed sẽ chậm hơn đáng kể so với GPU, kiểm tra lại driver/CUDA nếu máy có GPU.")

    # ---- Bước 2: embed toàn bộ chunk (chỉ text_child/table) ----
    print(f"\n[*] Đang embed {len(chunks)} chunk...")
    t0 = time.time()
    embedded_chunks = attach_embeddings_to_chunks(chunks, return_sparse=False)
    elapsed = time.time() - t0
    print(f"[✓] Embed xong {len(embedded_chunks)} chunk (đã bỏ qua chunk 'parent') trong {elapsed:.1f}s")

    for c in embedded_chunks:
        dim = len(c["dense_vector"])
        if dim != DENSE_DIM:
            print(f"Chunk {c['chunk_id']} có dense_vector {dim} chiều, khác {DENSE_DIM} chiều kỳ vọng")
 
    # ---- Bước 3: build payload đúng chuẩn Qdrant PointStruct ----
    # (company/ticker/year/quarter/document_type được suy ra từ document_id,
    #  xem docstring parse_document_metadata() trong embedding_client.py)
    qdrant_points = to_qdrant_points(embedded_chunks)
    print(f"Build được {len(qdrant_points)}/{len(embedded_chunks)} Qdrant point hợp lệ.")
 
    os.makedirs(os.path.dirname(EMBEDDED_PATH), exist_ok=True)
    with open(EMBEDDED_PATH, "w", encoding="utf-8") as f:
        json.dump(qdrant_points, f, ensure_ascii=False)
    print(f"Đã lưu bản kết quả embedded và dense vector tại: {EMBEDDED_PATH}")
    print("    (file này khá nặng vì mỗi chunk có 1 vector 1024 số thực -- chỉ để debug, không commit vào git)")
 
    # ---- Bước 4: LƯU THẬT vào Qdrant ----
    print(f"\n[*] Đang lưu vào Qdrant (collection='{QDRANT_COLLECTION}')...")
    store_in_qdrant(qdrant_points)
    print(f"[i] Tổng số point hiện có trong collection: {count_points()}")
 
    # ---- Bước 5: sanity check bằng search THẬT trên Qdrant (không phải cosine tay) ----
    print("\n[*] Sanity check bằng Qdrant search thật:")
    for question in TEST_QUESTIONS:
        print("=" * 70)
        print(f"CÂU HỎI: {question}")
        q_vec = embed_query(question)["dense"]
 
        results = search_similar_blocks(q_vec, limit=TOP_K)
        for hit in results:
            payload = hit.payload
            preview = (payload.get("content") or "").strip().replace("\n", " ")[:80]
            print(
                f"    [{hit.score:.3f}] ({payload.get('chunk_type')}, trang {payload.get('page_start')}) "
                f"{payload.get('company')} {payload.get('year')}"
                f"{'Q' + str(payload['quarter']) if payload.get('quarter') else ''} "
                f"| {payload.get('section_path')} | {preview}..."
            )
        print()
 
 
if __name__ == "__main__":
    main()