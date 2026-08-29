# RAG Hỏi - Đáp Tài Liệu Tài Chính (Financial Document QA RAG)

Kho lưu trữ này chứa hệ thống hỏi - đáp tài liệu tài chính được xây dựng trên đường ống (pipeline) RAG (Retrieval-Augmented Generation). Ứng dụng được thiết kế để tiếp nhận các tệp PDF tài chính, truy xuất các đoạn văn bản liên quan, trả lời các câu hỏi bằng ngôn ngữ tự nhiên dựa trên tài liệu nguồn, và tính toán một số chỉ số tài chính tiêu chuẩn từ dữ liệu trích xuất.

Hệ thống phục vụ cho các quy trình phân tích tài chính tập trung vào tài liệu như:

* Trả lời câu hỏi về báo cáo tài chính hàng năm hoặc hàng quý
* Tra cứu thuật ngữ và định nghĩa trong thuật ngữ tài chính
* Tính toán các chỉ số tài chính từ dữ liệu được trích xuất
* Xem lại các tài liệu nguồn đã tải lên với câu trả lời đi kèm trích dẫn (citations)

## Điểm nổi bật

* Quy trình tải lên PDF và đánh chỉ mục tài liệu qua FastAPI
* Đường ống truy xuất kết hợp (hybrid retrieval) sử dụng BM25 + tìm kiếm vector + hợp nhất xếp hạng nghịch đảo (RRF) + xếp hạng lại (reranking)
* Bộ lọc thông minh nhận biết mã cổ phiếu (ticker) và năm dành riêng cho truy vấn tài chính
* Định tuyến đa lớp cho trò chuyện chung (chitchat), tra cứu định nghĩa, tính toán và tìm kiếm tài chính tiêu chuẩn
* Tạo câu hỏi - đáp bám sát nguồn dữ liệu có kèm trích dẫn
* Dịch vụ tính toán cho các chỉ số dựa trên công thức như biên lợi nhuận gộp, ROE, ROI và các chỉ số tương tự
* Giao diện thử nghiệm (demo) bằng Streamlit
* Môi trường chạy cục bộ dựa trên Docker với MongoDB và Qdrant

## Công nghệ sử dụng (Tech stack)

* **Backend:** FastAPI
* **Frontend:** Streamlit
* **Vector database:** Qdrant
* **Metadata/Document store:** MongoDB
* **Embedding model:** BGE-M3 thông qua FlagEmbedding
* **Search stack:** BM25 + Truy xuất vector + Reranking
* **Tích hợp LLM:** OpenAI và Groq (thông qua LangChain)
* **Xử lý/Trích xuất:** Các công cụ xử lý tài liệu và kịch bản OCR chuyên dụng cho PDF tài chính
* **Đóng gói container:** Docker Compose

## Cấu trúc thư mục

```text
financial-document-qa-rag/
├── app/
│   ├── calculation/
│   │   ├── calculation_formatter.py
│   │   ├── calculation_service.py
│   │   └── metrics.py
│   ├── generation/
│   │   ├── answer_generator.py
│   │   ├── citation.py
│   │   └── generator.py
│   ├── ingestion/
│   │   ├── chunker.py
│   │   ├── chunker_local.py
│   │   ├── metadata_extractor.py
│   │   ├── parser.py
│   │   ├── parser_local.py
│   │   └── server.py
│   ├── models/
│   │   ├── calculation_schema.py
│   │   ├── chunk_schema.py
│   │   ├── conversation_schema.py
│   │   └── document_schema.py
│   ├── retrieval/
│   │   ├── glossary.py
│   │   ├── hybrid_search.py
│   │   ├── query_rewriter.py
│   │   ├── query_router.py
│   │   ├── rag_pipeline.py
│   │   └── reranker.py
│   ├── routers/
│   │   ├── chat.py
│   │   ├── documents.py
│   │   └── health.py
│   ├── services/
│   │   ├── embedding_client.py
│   │   ├── llm_client.py
│   │   ├── mongo_client.py
│   │   ├── mongo_store.py
│   │   └── qdrant_store.py
│   ├── config.py
│   └── main.py
├── crawler/
│   ├── config.py
│   └── crawl.py
├── data/
│   ├── raw/
│   └── upload/
├── docs/
│   ├── project_structure.md
│   └── setup_guide.md
├── frontend/
│   └── app.py
├── tests/
│   ├── test_chunking.py
│   └── test_parser.py
├── .env.example
├── Dockerfile
├── Dockerfile.frontend
├── docker-compose.yml
├── requirements.txt
├── requirements-frontend.txt
├── README.md
├── chunking.py
├── mongo_test.py
├── render_review_html.py
├── test_chunking.py
├── test_embedding.py
├── test_ocr.py
├── test_ocr_colab.py
├── test_ocr_vast.py
└── test_parse_chunk.py

```

## Cách thức hoạt động

Dự án triển khai quy trình hỏi - đáp tài chính gồm các bước:

1. **Tải tài liệu lên (Document upload):** Backend FastAPI tiếp nhận tệp PDF qua endpoint `/documents/upload`. Tệp được lưu tại `data/upload/ungrouped` và thông tin lưu trữ (metadata) được thêm vào MongoDB.
2. **Xử lý và chia đoạn (Ingestion & chunking):** Tài liệu được phân tích và chia thành các đoạn văn bản (chunks) tài chính nhỏ hơn. Mỗi đoạn được bổ sung thông tin như mã cổ phiếu, năm, quý và tên tệp nguồn.
3. **Tạo embedding và lưu trữ:** Các đoạn văn bản được nhúng bằng mô hình BGE-M3. Vector được ghi vào Qdrant, còn metadata được giữ ở MongoDB.
4. **Phân tích truy vấn và truy xuất:** Router phân loại yêu cầu (tìm kiếm tài chính, tra định nghĩa, tính toán, trò chuyện). Hệ thống thực hiện viết lại truy vấn, trích xuất metadata và tìm kiếm kết hợp (BM25 + vector search + reranking).
5. **Tạo câu trả lời:** Ngữ cảnh phù hợp được chuyển đến LLM kèm ràng buộc về trích dẫn nguồn. Câu trả lời cuối cùng chứa các tham chiếu trực tiếp tới đoạn tài liệu nguồn.
6. **Chế độ tính toán (Calculation mode):** Đối với câu hỏi về chỉ số, hệ thống xác định công thức, trích xuất số liệu từ tài liệu và tính toán trực tiếp bằng Python thay vì để LLM tự suy đoán số liệu.

## Yêu cầu tiên quyết

* Python 3.11 trở lên
* Docker và Docker Compose
* API Key của các nhà cung cấp LLM cloud (OpenAI, Groq) để chạy tính năng tạo câu trả lời và tính toán
* Card đồ họa GPU (tùy chọn) cho các tác vụ OCR nặng và mô hình nhúng lớn

## Cấu hình môi trường

Tạo tệp `.env` tại thư mục gốc của dự án với các biến môi trường mẫu:

```env
OPENAI_API_KEY=your_openai_key
GROQ_API_KEY=your_groq_key
MONGO_USER=admin
MONGO_PASSWORD=changeme
MONGO_URI=mongodb://admin:changeme@localhost:27017
MONGO_DB=financial_rag
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
QDRANT_HOST=localhost
QDRANT_PORT=6333
EMBEDDING_MODEL_ID=BAAI/bge-m3

```

*Lưu ý:*

* Khi chạy bằng Docker Compose, backend sẽ tự động kết nối tới các dịch vụ `mongodb` và `qdrant` thông qua tên dịch vụ nội bộ.
* Nếu chạy backend trực tiếp không qua Docker, hãy trỏ `MONGO_URI` và `QDRANT_URL` về địa chỉ dịch vụ cục bộ của bạn.
* Việc tải mô hình lần đầu (BGE-M3, OCR) có thể mất vài phút.

## Hướng dẫn chạy nhanh với Docker

Tại thư mục gốc của dự án, chạy lệnh:

```bash
docker compose up --build

```

Sau khi khởi chạy hoàn tất, các cổng dịch vụ cục bộ bao gồm:

* **Backend API:** http://localhost:8000
* **API Docs (Swagger):** http://localhost:8000/docs
* **Health check:** http://localhost:8000/health
* **Frontend (Streamlit):** http://localhost:8501
* **Qdrant Dashboard:** http://localhost:6333/dashboard
* **MongoDB:** localhost:27017

Dừng các dịch vụ và giữ lại dữ liệu:

```bash
docker compose down

```

Xóa toàn bộ container và dữ liệu đã lưu (thao tác này sẽ xóa sạch dữ liệu):

```bash
docker compose down -v

```

## Hướng dẫn cài đặt cho môi trường phát triển (Local Development)

1. **Tạo và kích hoạt môi trường ảo:**
```bash
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

```


2. **Cài đặt thư viện:**
```bash
pip install -r requirements.txt

```


3. **Khởi chạy cơ sở dữ liệu qua Docker:**
```bash
docker compose up -d qdrant mongodb

```


4. **Khởi chạy Backend:**
```bash
uvicorn app.main:app --reload --port 8000

```


5. **Khởi chạy Frontend trong terminal mới:**
```bash
pip install -r requirements-frontend.txt
streamlit run frontend/app.py

```


6. **Chạy kiểm thử (Tests):**
```bash
pytest tests

```



## Sử dụng API

### Kiểm tra trạng thái (Health check)

```bash
curl http://localhost:8000/health

```

### Tải lên tệp PDF

```bash
curl -X POST "http://localhost:8000/documents/upload" \
  -F "file=@/duong/dan/toi/baocao.pdf"

```

### Gửi câu hỏi

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "demo-session",
    "query": "Doanh thu của A32 2025 là bao nhiêu?"
  }'

```

## Lưu ý

* Đây là dự án thử nghiệm/nghiên cứu về hệ thống QA tài liệu tài chính, không phải là ứng dụng SaaS thương mại sẵn sàng cho sản xuất ngay lập tức.
* Trong lần khởi chạy đầu tiên, hệ thống cần thời gian để tải trọng số mô hình và các phụ thuộc OCR.
* Các tệp kịch bản ở thư mục gốc (`test_ocr.py`, `test_embedding.py`, `mongo_test.py`,...) là công cụ hỗ trợ phát triển, không phải luồng chính của ứng dụng.
* Công cụ thu thập dữ liệu trong thư mục `crawler/` chạy độc lập và không bắt buộc cho quy trình hỏi - đáp thông thường.