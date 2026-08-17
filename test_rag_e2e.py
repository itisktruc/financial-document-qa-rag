"""
test_rag_e2e.py

Script kiểm tra toàn bộ luồng RAG End-to-End:
Query -> Routing -> Hybrid Search (BM25 + Qdrant Dense) -> RRF Fusion -> CrossEncoder Rerank -> MongoDB Parent Expansion -> Generation + Citations.
"""

from __future__ import annotations
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.retrieval.hybrid_search import HybridSearchPipeline
from app.retrieval.rag_pipeline import RAGController
from app.generation.answer_generator import AnswerGenerator

TEST_QUERIES = [
    "Xin chào bạn là ai?",
    "EBITDA là gì?",
    "Tổng tài sản của FPT năm 2024 là bao nhiêu?",
    "Doanh thu thuần năm 2024 của FPT đạt bao nhiêu và tăng trưởng thế nào?"
]

def main():
    print("==================================================")
    print("[*] KHỞI TẠO HỆ THỐNG RAG END-TO-END FOR TESTING")
    print("==================================================")
    
    pipeline = HybridSearchPipeline()
    controller = RAGController(pipeline=pipeline, top_k=5)
    generator = AnswerGenerator()
    
    print("\n[✓] Khởi tạo hệ thống thành công!\n")

    for q in TEST_QUERIES:
        print("=" * 80)
        print(f"❓ CÂU HỎI TEST: '{q}'")
        print("=" * 80)
        
        search_res = controller.execute_search(q)
        
        if search_res.get("is_chitchat"):
            print("👉 Phân loại: CHITCHAT")
            print("💬 Trả lời: Đây là câu hỏi giao tiếp thông thường.")
            continue
            
        if search_res.get("is_definition"):
            print("👉 Phân loại: TERM_DEFINITION")
            ans = generator.generate_definition(q)
            print(f"💬 Trả lời giải thích:\n{ans}")
            continue
            
        context_items = search_res.get("context_items", [])
        contexts = search_res.get("context", [])
        retrieved_input = context_items if context_items else contexts
        
        print(f"👉 Phân loại: FINANCIAL_SEARCH")
        print(f"🔍 Số lượng ngữ cảnh retrieved: {len(retrieved_input)}")
        
        gen_res = generator.generate(q, retrieved_input)
        
        print("\n🤖 CÂU TRẢ LỜI SINH BỞI LLM:")
        print(gen_res.get("answer"))
        
        print("\n📚 TRÍCH DẪN NGUỒN (CITATIONS):")
        citations = gen_res.get("citations", [])
        if citations:
            for c in citations:
                print(f"   [{c.get('id')}] {c.get('ticker')} {c.get('year')} | Page {c.get('page_start')} | {c.get('section_path')}")
                print(f"       Trích đoạn: {c.get('snippet')}")
        else:
            print("   (Không có trích dẫn)")
        print("\n")

if __name__ == "__main__":
    main()
