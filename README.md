# Financial RAG Chatbot

Hệ thống RAG (Retrieval-Augmented Generation) cho phép người dùng đặt câu hỏi bằng ngôn ngữ tự nhiên (tiếng Việt và tiếng Anh) về báo cáo tài chính, hợp đồng tín dụng, bản cáo bạch, tin tức thị trường và các tài liệu quy định — trả lời chính xác kèm trích dẫn nguồn (document, page, section).

## Tính năng chính

- **Table-aware retrieval**: hiểu và truy vấn được số liệu trong bảng (balance sheet, income statement...)
- **Financial calculation**: tính các chỉ số phái sinh (Gross Margin, ROE, YoY Growth...) bằng code, không để LLM tự nhẩm
- **Multi-turn conversation**: hiểu ngữ cảnh hội thoại, xử lý câu hỏi thiếu ngữ cảnh và tham chiếu đại từ
- **Cross-document reasoning**: so sánh số liệu giữa nhiều công ty/tài liệu
- **Traceable citation**: mọi câu trả lời đều kèm nguồn chính xác đến document/page/section
- **Bilingual**: hỗ trợ song song tiếng Việt và tiếng Anh trong cùng một index

## Tech Stack

| Tầng | Công nghệ |
|---|---|
| RAG / Agent Framework | LangChain / LangGraph |
| PDF Parser | Docling + PaddleOCR |
| Vector Database | Qdrant |
| Metadata / Document Store | MongoDB |
| Embedding | BGE-M3 (local) |
| Reranker | BAAI/bge-reranker-base |
| LLM | GPT-4o-mini, Claude, Llama 3 (qua Groq) |
| Financial Calculator | Python function library |
| Evaluation | Ragas |
| Backend | FastAPI |
| Frontend Demo | Streamlit |
| Containerization | Docker / Docker Compose |

## Cấu trúc thư mục

```
financial-rag-chatbot/
│
├── app/                          # Backend FastAPI
│   ├── main.py                    # Entrypoint, khởi tạo FastAPI app
│   ├── config.py                  # Đọc biến môi trường (.env), settings chung
│   │
│   ├── routers/                   # API routes, tách theo domain
│   │   ├── chat.py                 # POST /chat — endpoint chính
│   │   ├── documents.py            # Upload/quản lý tài liệu
│   │   └── health.py               # /health
│   │
│   ├── ingestion/                 # Giai đoạn 1: Data Ingestion Pipeline
│   │   ├── parser.py               # Gọi Docling + PaddleOCR
│   │   ├── chunker.py              # Hierarchical Parent-Child Chunking
│   │   └── metadata_extractor.py   # LLM extract business_metadata
│   │
│   ├── retrieval/                 # Giai đoạn 2-3: Query Understanding + Retrieval
│   │   ├── query_router.py         # Phân loại lookup/calculation/comparison
│   │   ├── query_rewriter.py       # Contextualization cho multi-turn
│   │   ├── hybrid_search.py        # BM25 + dense retrieval qua Qdrant
│   │   └── reranker.py             # bge-reranker-base
│   │
│   ├── calculation/               # Giai đoạn 4: Financial Calculator Tool
│   │   └── metrics.py              # Gross Margin, ROE, YoY Growth...
│   │
│   ├── generation/                # Giai đoạn 5: Generation & Citation
│   │   ├── generator.py            # Gọi LLM sinh câu trả lời
│   │   └── citation.py             # Gắn document/page/section vào answer
│   │
│   ├── models/                    # Pydantic schemas (Document/Chunk/Conversation/Calculation)
│   │   ├── document_schema.py
│   │   ├── chunk_schema.py
│   │   ├── conversation_schema.py
│   │   └── calculation_schema.py
│   │
│   └── services/                  # Client kết nối hạ tầng
│       ├── qdrant_client.py
│       ├── mongo_client.py
│       └── llm_client.py           # Wrapper OpenAI/Anthropic/Groq
│
├── frontend/                     # Streamlit demo
│   └── app.py
│
├── evaluation/                   # Evaluation Pipeline — kết nối benchmark
│   ├── ragas_eval.py
│   ├── citation_validator.py
│   └── benchmark_dataset/         # Q&A + ground truth + citation
│
├── data/
│   ├── raw/                       # PDF gốc
│   └── benchmark/                 # Dataset cho evaluation
│
├── crawler/                      # Thu thập tài liệu, tách riêng khỏi backend chính
│   ├── crawl.py
│   └── requirements-crawler.txt
│
├── tests/                        # Unit test cho từng module
│   ├── test_chunker.py
│   ├── test_calculator.py
│   └── test_retrieval.py
│
├── Dockerfile                     # Build image cho backend
├── Dockerfile.frontend            # Build image cho frontend
├── docker-compose.yml             # Orchestrate toàn bộ hệ thống
├── requirements.txt               # Dependency backend
├── requirements-frontend.txt      # Dependency frontend
├── .env.example                   # Mẫu biến môi trường
├── .dockerignore
├── .gitignore
└── README.md
```

## Yêu cầu hệ thống

- Docker & Docker Compose
- Python 3.11+ (nếu chạy local không qua Docker)
- (Tùy chọn) GPU + `nvidia-container-toolkit` nếu xử lý nhiều PDF scan qua PaddleOCR

## Setup

### 1. Clone repo và cấu hình biến môi trường

```bash
git clone <repo-url>
cd financial-rag-chatbot
cp .env.example .env
```

Mở `.env` và điền các API key cần dùng:

```
OPENAI_API_KEY=          # GPT-4o-mini: metadata extraction, query rewriting, Ragas eval
ANTHROPIC_API_KEY=       # Claude: generation chính (nếu dùng thay OpenAI)
GROQ_API_KEY=            # Llama 3 qua Groq: route câu hỏi đơn giản
HF_TOKEN=                # chỉ cần nếu model embedding gated trên HuggingFace
MONGO_USER=admin
MONGO_PASSWORD=changeme
```

> Ở giai đoạn chưa tích hợp LLM, có thể để trống giá trị các key — chỉ cần file `.env` tồn tại để `docker compose` không báo lỗi.

### 2. Chạy toàn bộ hệ thống bằng Docker Compose

```bash
docker compose up --build
```

Sau khi chạy xong, truy cập:

| Service | URL |
|---|---|
| Backend API docs | http://localhost:8000/docs |
| Backend health check | http://localhost:8000/health |
| Frontend (Streamlit) | http://localhost:8501 |
| Qdrant dashboard | http://localhost:6333/dashboard |

Chỉ chạy riêng hạ tầng database (khi backend/frontend chưa sẵn sàng):

```bash
docker compose up qdrant mongodb
```

Dừng hệ thống (giữ lại dữ liệu Qdrant/MongoDB):

```bash
docker compose down
```

Dừng và xoá luôn dữ liệu (ĐỪNG LÀM):

```bash
docker compose down -v
```

Muốn bật lại:
```bash
docker compose up -d
```

### 3. Setup local không dùng Docker (cho việc phát triển/debug)

```bash
python3 -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows

pip install -r requirements.txt
``

Nếu gặp lỗi khi cài đặt `antlr4-python3-runtime` (lỗi liên quan đến `bin/pygrun`), hãy chạy các lệnh sau để cài đặt thủ công:

1. Tải gói cài đặt:
   ```powershell
   pip download antlr4-python3-runtime==4.9.3
   ```
2. Giải nén
   ```powershell
   tar -xvzf antlr4-python3-runtime-4.9.3.tar.gz
   ```  
3. Vào thư mục antlr4-python3-runtime-4.9.3, mở file setup.py và xóa/comment dòng scripts=['bin/pygrun'],.
4. Chạy lệnh cài đặt cục bộ:
   ```powershell
   pip install .
   ```
5. Quay lại thư mục gốc dự án và tiếp tục cài đặt các thư viện khác:
   ```powershell
   cd ..
   pip install -r requirements.txt
   ```

uvicorn app.main:app --reload --port 8000
```

Chạy frontend (terminal khác):

```bash
pip install -r requirements-frontend.txt
streamlit run frontend/app.py
```

> Lưu ý: khi chạy local không qua Docker, cần tự khởi động Qdrant và MongoDB (có thể dùng `docker compose up qdrant mongodb` song song), và set biến môi trường `QDRANT_HOST=localhost`, `MONGO_URI=mongodb://localhost:27017` thay vì tên service như trong Docker network.

### 4. Chạy crawler (thu thập tài liệu, tách riêng)

```bash
python3 -m venv venv_crawler
source venv_crawler/bin/activate
pip install -r crawler/requirements-crawler.txt

python crawler/crawl.py
```

### 5. Chạy test

```bash
pip install pytest
pytest tests/
```

### 6. Chạy evaluation (Ragas)

```bash
python evaluation/ragas_eval.py
```
## Ghi chú phát triển

- Mỗi thành viên nên tự tạo API key riêng (OpenAI/Anthropic/Groq) thay vì dùng chung — dễ theo dõi chi phí và tránh lộ key khi commit nhầm.

## Team

| Thành viên | Phụ trách |
|---|---|
| An | — |
| Kiệt | — |
| Trúc | — |
| Tú | — |
| Ngọc | — |