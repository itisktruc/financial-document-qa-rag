# [MASTER SYSTEM ARCHITECTURE & AI PROMPT: RAG PIPELINE] — v3 (Final)

> **v2 → v3 changelog:** (1) Làm rõ tuyệt đối GPU chỉ dùng của Google Colab, máy nội bộ CPU-only; (2) Mở rộng bảo mật kết nối Colab (xác thực 2 lớp, giới hạn bề mặt tấn công, exposure window, không log dữ liệu nhạy cảm); (3) Kiểm tra thực tế khả năng cài đặt (wheel) của toàn bộ thư viện đề xuất trên Python 3.14 — xem Phụ lục A; (4) Đây là bản hoàn chỉnh (final) của tài liệu kiến trúc — xem thêm file `WORKFLOW.md` đi kèm để có hướng dẫn from-zero-to-code theo từng bước.

> Các phiên bản trước đã bổ sung: cơ chế phục hồi lỗi (checkpoint/resume), quản lý trạng thái tập trung, throttle Colab, quy ước metadata, chỉ số đo lường chi tiết theo từng giai đoạn, cấu trúc thư mục, checklist setup, và ghi chú tích hợp LangChain.

## I. MỤC TIÊU VÀ QUY MÔ HỆ THỐNG (OBJECTIVES & SCALE)

* **Mục tiêu:** Xây dựng một Data Ingestion Pipeline hoàn chỉnh để xử lý tài liệu, bóc tách thông tin và đưa vào cơ sở dữ liệu Vector phục vụ truy vấn RAG.
* **Quy mô chịu tải:** 1.000 file PDF hỗn hợp (digital + scanned), mỗi file khoảng 1.000 trang (tổng khối lượng: ~1 triệu trang, ước tính ~2-5 triệu chunk sau khi chia mảnh).
* **Đối tượng bóc tách đa phương thức:**
  * Văn bản (Text) và Bảng biểu (Tables).
  * Hình ảnh mang ngữ nghĩa: Biểu đồ (Charts) và Huy hiệu/Logo quảng cáo (ví dụ: hình khiên "Top 1 Việt Nam").
* **Ràng buộc dung lượng (mới):** Không tách vật lý PDF gốc thành 1 triệu file trang lẻ (gây quá tải filesystem). Thay vào đó, dùng **chỉ số trang ảo** (virtual page index: `source_file + page_number`) và đọc trực tiếp qua `fitz.open(path).load_page(n)`. Ước tính dung lượng cần dự trù: ảnh crop tạm thời, cache VLM, DB vector, log — cần ổ đĩa trống tối thiểu gấp 3 lần dung lượng PDF gốc.
* **Đặc điểm ngôn ngữ:** Toàn bộ nội dung tiếng Việt có dấu → toàn bộ model OCR/embedding phải xác nhận hỗ trợ tiếng Việt (`vi`), và mọi text sau trích xuất phải được chuẩn hoá Unicode NFC (xem mục II.5).

## II. RÀNG BUỘC KỸ THUẬT CỐT LÕI (STRICT TECHNICAL CONSTRAINTS)

1. **Ngôn ngữ & Môi trường:** Toàn bộ mã nguồn, tên biến, chú thích viết bằng Tiếng Anh. Tương thích với Python 3.14 **bản chuẩn** (không dùng biến thể free-threaded `python3.14t`).
   * **Kiểm tra tương thích wheel:** đã kiểm tra thực tế toàn bộ thư viện đề xuất trong tài liệu này trên PyPI — **không có thư viện nào thiếu wheel cho Python 3.14 chuẩn** tại thời điểm 26/07/2026. Chi tiết đầy đủ, bao gồm caveats, xem **Phụ lục A** cuối tài liệu. Script `check_env.py` (mục IX) vẫn bắt buộc chạy lại trước khi code vì đây là kết quả tại một thời điểm, hệ sinh thái pip thay đổi liên tục.
   * **Kiểm tra giấy phép (license):** xác nhận điều khoản license hiện hành của `surya-ocr` (đã từng chuyển sang license có điều kiện thương mại) trước khi đưa vào production nội bộ doanh nghiệp.

2. **Zero-Installation (Chỉ dùng thư viện Pip):** Tuyệt đối không cài đặt phần mềm ngoại vi (Tesseract .exe, Redis Server, RabbitMQ, Celery). Mọi công cụ phải là thư viện Python thuần tuý cài qua `pip`.

3. **Kiến trúc Đa luồng Nội tại (Native Concurrency):**
   * Dùng `concurrent.futures.ProcessPoolExecutor` để phân phối tác vụ song song theo số nhân CPU vật lý.
   * **Quản lý bộ nhớ model trong worker (mới):** không load model OCR/embedding nặng bên trong mỗi task riêng lẻ — dùng `initializer=` của `ProcessPoolExecutor` để load model **một lần duy nhất mỗi worker process**, tránh việc N task cùng nạp lại model N lần gây tràn RAM.
   * **Giới hạn số worker gọi song song ra Colab (mới):** vì chỉ có 1 GPU Colab, cần một `Semaphore`/hàng đợi giới hạn số request đồng thời gửi tới endpoint VLM (ví dụ tối đa 2-3 request cùng lúc), tránh nghẽn/lỗi 429.

4. **Kiểm soát Luồng Dữ liệu (Stream Management):**
   * Quản lý vòng đời thực thi qua Windows CMD. Phân tách log:
     * `sys.stdout` → hoạt động bình thường, định tuyến, tỷ lệ thành công → `> info.log`.
     * `sys.stderr` → trang lỗi định dạng, exception, block OCR điểm thấp → `2> error.log`.
   * **Logging đa tiến trình (mới):** log ghi trực tiếp từ nhiều `ProcessPoolExecutor` worker dễ bị chèn dòng (interleaved). Dùng `logging.handlers.QueueHandler` + một `QueueListener` chạy ở tiến trình chính để gom log an toàn, thay vì mỗi worker `print()` trực tiếp.
   * **Encoding trên Windows CMD (mới):** bắt buộc `chcp 65001` và set biến môi trường `PYTHONIOENCODING=utf-8` trước khi chạy script, để tránh lỗi hiển thị/log tiếng Việt có dấu.

5. **Chuẩn hoá dữ liệu (mới):** Mọi text trích xuất từ PDF phải qua `unicodedata.normalize("NFC", text)` trước khi lưu, vì PDF thường lưu ký tự tổ hợp (NFD) gây sai lệch khi tìm kiếm/embedding.

6. **Quản lý cấu hình (mới):** Toàn bộ ngưỡng (blank-page %, min chars, chunk size, OCR confidence threshold...), đường dẫn, tên model phải khai báo tập trung trong một file `config.yaml`/`config.json`, không hard-code rải rác trong code — thuận tiện chỉnh sửa và audit.

7. **Cơ chế Cập nhật Code cho AI:** Có sẵn script gom toàn bộ thư mục `.py` thành một file `.txt` duy nhất qua điều hướng STDOUT trên CMD, để nạp lại context cho AI khi cần sửa code.

## III. QUẢN LÝ TRẠNG THÁI & PHỤC HỒI LỖI (STATE MANAGEMENT & RECOVERY) — *mục mới*

Vì hệ thống không dùng broker ngoài (Redis/Celery), cần một "bộ nhớ trạng thái" nội bộ để pipeline có thể dừng/chạy lại mà không mất tiến độ, đặc biệt quan trọng với job chạy nhiều giờ/ngày trên 1 triệu trang.

* **Manifest DB:** dùng SQLite (chế độ WAL để cho phép ghi đồng thời từ nhiều process) làm "sổ cái" theo dõi trạng thái từng trang/chunk.
  * Schema tối thiểu: `page_id, source_file, page_number, status (pending|processing|done|failed), stage, ocr_confidence, error_msg, retry_count, updated_at`.
* **Idempotency:** trước khi xử lý một trang/chunk, kiểm tra manifest — nếu đã `done` thì bỏ qua (cho phép chạy lại toàn bộ script an toàn sau khi crash).
* **Retry có giới hạn:** trang lỗi (OCR thấp, Colab timeout) được đánh dấu `failed` với `retry_count`, tự động thử lại tối đa N lần trước khi được đẩy hẳn vào hàng đợi lỗi để xử lý thủ công.
* **Checkpoint theo batch:** commit trạng thái vào manifest DB theo từng batch nhỏ (ví dụ mỗi 100 trang), không chờ đến cuối toàn bộ job.

## IV. CHIẾN LƯỢC GPU & BẢO MẬT KẾT NỐI COLAB (GPU POLICY & COLAB SECURITY)

### IV.1 Nguyên tắc sử dụng GPU (GPU Usage Policy) — *làm rõ, bắt buộc tuân thủ*

* **GPU compute CHỈ và LUÔN LUÔN xảy ra trên Google Colab.** Máy chủ nội bộ (on-premise) không sở hữu, không cài driver/CUDA, và không được phép dùng GPU cho bất kỳ tác vụ nào trong pipeline này, kể cả khi máy nội bộ vô tình có GPU vật lý.
* Áp dụng cụ thể vào từng giai đoạn để tránh mơ hồ khi code:
  | Tác vụ | Chạy ở đâu | Phần cứng |
  |---|---|---|
  | OCR trang scan (Stage 2) | Máy nội bộ | CPU (`surya-ocr`/`easyocr` hỗ trợ chế độ CPU, chậm hơn GPU — cần benchmark thật trong pilot run, mục VII) |
  | VLM caption Chart/Logo (Stage 2) | **Google Colab — DUY NHẤT tác vụ GPU của toàn hệ thống** | GPU Colab (T4 hoặc tương đương) |
  | Embedding chunk → vector (Stage 4) | Máy nội bộ | CPU (`sentence-transformers` chạy CPU; cân nhắc bản ONNX/int8 quantized của `bge-m3` để bù tốc độ) |
  | Vector search / lưu trữ | Máy nội bộ | CPU (LanceDB/ChromaDB đều là embedded DB, không cần GPU) |
* **Cài đặt torch cục bộ:** chỉ cài bản **CPU-only** (`pip install torch --index-url https://download.pytorch.org/whl/cpu`), tuyệt đối không cài bản kèm CUDA trên máy nội bộ — giảm dung lượng cài đặt (~2-3GB thay vì ~6-7GB) và loại bỏ hoàn toàn rủi ro driver/CUDA không tương thích.
* Nếu sau pilot run, tốc độ CPU-only cho OCR/embedding không đạt yêu cầu ở quy mô 1 triệu trang, việc bổ sung GPU nội bộ là **quyết định hạ tầng cần thảo luận lại riêng** — không tự ý bật CUDA trong code để "vá tạm" vì sẽ phá vỡ ràng buộc kiến trúc đã thống nhất.

### IV.2 Bảo mật kết nối Colab (Colab Connection Security) — *mở rộng*

* **Quy tắc On-premise:** Toàn bộ file gốc, text trích xuất, và Vector DB nằm trên máy chủ nội bộ. Embedding chạy nội bộ.
* **Tận dụng GPU Colab (Zero-Storage):**
  * Colab chỉ dùng làm API Server xử lý ảnh nặng (VLM), không có vai trò nào khác.
  * **Luồng hoạt động:** Máy nội bộ cắt vùng ảnh (Chart/Logo) → gửi HTTP POST (payload ảnh) tới endpoint Colab (FastAPI + Ngrok) → Colab dùng GPU dịch ảnh thành mô tả văn bản → trả JSON về máy nội bộ.
  * **Không lưu trữ:** không upload lên Google Drive; Colab chỉ xử lý trên RAM, không ghi ảnh ra đĩa của Colab dưới bất kỳ hình thức nào (kể cả cache tạm).
* **Checklist bảo mật bắt buộc:**
  * **Xác thực 2 lớp:** (1) Bearer token ngẫu nhiên (≥32 ký tự, sinh lại mỗi lần khởi động Colab session, ví dụ bằng `secrets.token_urlsafe(32)`), (2) header bí mật tuỳ biến (VD `X-Pipeline-Secret`) — endpoint từ chối mọi request thiếu 1 trong 2, giảm rủi ro bị bot quét URL Ngrok công khai dò trúng.
  * **Thu hẹp bề mặt tấn công:** FastAPI trên Colab chỉ mở đúng 2 route cần thiết — `POST /caption` (xử lý ảnh) và `GET /ping` (health-check). Tắt hẳn Swagger UI/docs công khai (`FastAPI(docs_url=None, redoc_url=None)`), không để lộ danh sách endpoint cho người ngoài.
  * **Validate payload nghiêm ngặt:** giới hạn `Content-Type` (chỉ `image/png`, `image/jpeg`), giới hạn kích thước file (VD tối đa 5MB/ảnh), từ chối payload không đúng định dạng ngay ở tầng nhận request — tránh bị lợi dụng gửi payload cỡ lớn gây quá tải GPU/RAM Colab.
  * **Rate limiting phía Colab:** giới hạn số request/giây kể cả khi chỉ có máy nội bộ gọi vào, để chặn trường hợp lỗi logic ở client gây spam ngoài ý muốn làm sập session Colab.
  * **Thu hẹp cửa sổ tiếp xúc (exposure window):** chỉ mở tunnel Ngrok đúng trong khung thời gian chạy batch; chủ động dừng notebook/tunnel ngay khi batch hoàn tất, không để endpoint treo mở qua đêm hoặc nhiều ngày.
  * **Không log dữ liệu nhạy cảm phía Colab:** output cell của notebook chỉ nên in `request_id`, `timestamp`, `status_code` — KHÔNG print toàn bộ base64 ảnh hoặc nội dung mô tả ra output, vì nội dung notebook có thể vô tình bị lưu/chia sẻ (`.ipynb` chứa cả output cell).
  * **Xác nhận kênh truyền mã hoá:** URL do Ngrok cấp phải luôn bắt đầu bằng `https://`; script phía local nên chủ động kiểm tra và từ chối gửi payload nếu URL đọc từ `colab_endpoint.json` không phải HTTPS.
  * **Không log token/URL dạng plaintext lâu dài:** token và URL Colab chỉ lưu trong `config/colab_endpoint.json` (không commit vào git, thêm vào `.gitignore`), không in ra `info.log`/`error.log` dưới dạng đọc được.
  * **Khám phá URL Ngrok động:** Ngrok free đổi URL mỗi lần khởi động lại Colab — máy local đọc lại `colab_endpoint.json` mỗi khi bắt đầu batch, thay vì hard-code URL.
  * **Vòng đời phiên Colab:** phiên Colab tự ngắt khi idle hoặc sau ~12-24h. Cần: (1) health-check định kỳ tới Colab qua `/ping`, (2) khi mất kết nối, các trang chờ VLM được đánh dấu `pending_vlm` trong manifest thay vì làm job dừng hẳn, tiếp tục xử lý phần text/table không phụ thuộc VLM.
  * **Nén/resize ảnh trước khi gửi:** resize về tối đa 1024px cạnh dài, nén JPEG chất lượng vừa phải, vừa giảm băng thông vừa giảm bề mặt dữ liệu truyền đi.
  * **Timeout & retry cho HTTP request:** timeout rõ ràng (VD 30s) và retry có backoff khi gọi Colab thất bại.
  * **Kiểm tra VRAM model VLM:** xác nhận model VLM (PaliGemma hoặc tương đương) và mức lượng tử hoá (quantization) phù hợp với GPU miễn phí của Colab (thường T4 ~15GB VRAM).

## V. QUY TRÌNH 4 GIAI ĐOẠN CHI TIẾT (THE 4-STAGE WORKFLOW)

### Giai đoạn 1: Tiếp nhận & Phân luồng Cấp độ Trang (Ingestion & Routing)

* **Cách hoạt động:** Duyệt từng trang PDF gốc qua chỉ số ảo (không tách file vật lý — xem mục I).
* **Định tuyến (Routing) — thuật toán cụ thể (mới):**
  * **Lọc trang trắng:** render trang thành bitmap độ phân giải thấp, tính tỷ lệ pixel trắng/tổng pixel; nếu > 98% → huỷ.
  * **Phát hiện lỗi font:** tính tỷ lệ ký tự thay thế (`�`, ký tự không in được) trên tổng ký tự trích xuất được; nếu vượt ngưỡng cấu hình → coi là lỗi font, chuyển sang `SCANNED_QUEUE`.
  * **Phân nhánh:** nếu số ký tự hợp lệ > 50 (ngưỡng đọc từ `config.yaml`) và không lỗi font → `DIGITAL_QUEUE`; nếu là ảnh scan hoặc ảnh bọc text → `SCANNED_QUEUE`.
* **Trạng thái:** mỗi kết quả routing được ghi ngay vào Manifest DB (mục III) trước khi chuyển sang Stage 2.
* **Thư viện đề xuất:** PyMuPDF (fitz) hoặc pdfplumber.
* **Chỉ số đo lường (mở rộng):**
  | Chỉ số | Công thức / Cách đo | Mục tiêu | Nguồn dữ liệu |
  |---|---|---|---|
  | Routing Accuracy | (Số trang được gán đúng nhãn / Tổng số trang lấy mẫu) × 100% | ≥ 95% | Lấy mẫu ngẫu nhiên 200-500 trang, gán nhãn thủ công (ground-truth) để so sánh |
  | Blank-page False Positive Rate | Số trang có nội dung nhưng bị coi là trắng / Tổng số trang bị loại | < 1% | Kiểm tra thủ công tập trang bị loại |
  | Font-error Detection Rate | Số trang phát hiện lỗi font đúng / Tổng số trang thực sự lỗi font | ≥ 90% | So với tập mẫu đã biết lỗi |
  | Throughput | Số trang route được / giây (theo batch) | Ghi log theo batch để phát hiện nghẽn | `info.log` |
  | Queue Balance | Tỷ lệ DIGITAL_QUEUE : SCANNED_QUEUE | So sánh với ước lượng ban đầu để phát hiện bất thường (VD: routing logic bị lỗi khiến toàn bộ rơi vào 1 queue) | Manifest DB |

### Giai đoạn 2: Bóc tách Đa phương thức (Multimodal Extraction)

* **Text & Bảng:**
  * Trang Digital: trích text trực tiếp bằng fitz/pdfplumber.
  * Trang Scanned: OpenCV tiền xử lý (nhị phân hoá, xoay thẳng) → mô hình OCR thuần Python để lấy chữ. **Chạy trên CPU nội bộ** (đúng mục IV.1 — GPU chỉ dành riêng cho VLM trên Colab); cấu hình OCR engine ở chế độ CPU tường minh (VD `easyocr.Reader(['vi','en'], gpu=False)`) để tránh code vô tình tự bật GPU nếu máy có sẵn card đồ hoạ.
  * **Tái tạo cấu trúc bảng (mới, cụ thể hơn):** OCR thuần không đủ để dựng lưới bảng — cần thêm bước phát hiện đường kẻ/bảng (line detection bằng OpenCV, hoặc thư viện thuần Python như `img2table`) trước khi OCR từng ô riêng lẻ.
* **Biểu đồ & Huy hiệu:**
  * **Trích ảnh (mới, ưu tiên phương án chính xác hơn):** ưu tiên dùng `page.get_images()` của PyMuPDF để lấy trực tiếp ảnh raster nhúng trong PDF, thay vì chỉ dò contour bằng OpenCV trên ảnh render (dễ nhầm ảnh trang trí/nền).
  * **Lọc & khử trùng lặp (mới):** tính perceptual hash cho mỗi ảnh crop; nếu hash đã tồn tại trong cache (ví dụ logo lặp lại hàng nghìn lần) → dùng lại mô tả VLM cũ, không gọi API lại — tiết kiệm chi phí/độ trễ đáng kể.
  * Máy local gửi ảnh chưa có trong cache lên Colab (đã throttle theo Semaphore, mục II.3) → VLM (PaliGemma) trả text mô tả → gắn vào đúng vị trí.
* **Thư viện đề xuất (Local):** opencv-python-headless, surya-ocr hoặc easyocr (đã kiểm tra license), img2table.
* **Thư viện đề xuất (Colab):** fastapi, pyngrok, transformers, torch.
* **Chỉ số đo lường (mở rộng):**
  | Chỉ số | Công thức / Cách đo | Mục tiêu | Nguồn dữ liệu |
  |---|---|---|---|
  | OCR Confidence trung bình | Trung bình `confidence` do OCR engine trả về trên toàn bộ trang scan | ≥ 80%; < 80% → ghi tên trang ra STDERR + `status=failed` trong manifest | Manifest DB |
  | Character Error Rate (CER) | So sánh text OCR với ground-truth (tập mẫu 50-100 trang gán nhãn tay) | < 5% | Đo bằng thư viện tính edit-distance (VD `jiwer`) |
  | Colab API Success Rate | (Số request thành công / Tổng số request) × 100% | ≥ 98%; log riêng lỗi timeout vs lỗi 4xx/5xx | `error.log` |
  | Colab API Latency (p50/p95) | Thời gian phản hồi trung bình/95th percentile | Theo dõi để phát hiện nghẽn khi nhiều worker gọi song song | `info.log` |
  | Cache-hit Rate ảnh trùng lặp | (Số ảnh dùng lại từ cache / Tổng số ảnh crop) × 100% | Càng cao càng tốt (logo/watermark lặp lại nên > 50%) | Cache store (perceptual hash) |
  | Table Structure Preservation | (Số bảng tái tạo đúng số hàng/cột / Tổng số bảng lấy mẫu) × 100% | ≥ 85% | So sánh thủ công với bảng gốc trên tập mẫu |
  | Image Classification Precision | Tỷ lệ ảnh được gửi lên VLM thực sự là Chart/Logo (không phải ảnh trang trí/nhiễu) | ≥ 90% | Lấy mẫu kiểm tra thủ công |

### Giai đoạn 3: Cấu trúc hoá Markdown & Chia mảnh (Formatting & Semantic Chunking)

* **Ráp lại trật tự đọc (mới, cụ thể hơn):** đối chiếu toạ độ (X, Y) của các khối — với layout nhiều cột, trước tiên cụm các khối theo dải toạ độ X (column clustering), sau đó mới sort theo Y trong từng cột; sort trực tiếp theo Y sẽ trộn lẫn nội dung nếu trang có ≥2 cột.
* Chuyển đổi thành Markdown (`## Tiêu đề`, `| Cột 1 | Cột 2 |`).
* **Chia mảnh (Chunking):**
  * Tìm Heading (`#`) hoặc đoạn văn (`\n\n`) để cắt chunk ngữ nghĩa (~500-1000 tokens).
  * **Tokenizer (mới):** đếm token bằng đúng tokenizer của model embedding (`bge-m3`), không ước lượng bằng số ký tự, để chunk khớp thực tế giới hạn của model.
  * **Overlap (mới):** thêm overlap ~10-15% giữa các chunk liền kề để tránh mất ngữ cảnh ở ranh giới câu.
  * **Chunk vắt qua trang (mới):** nếu một đoạn văn bị cắt ngang bởi ranh giới trang, cần logic nối lại (dựa vào việc câu cuối trang N không kết thúc bằng dấu câu) trước khi chunk.
* **Thư viện đề xuất:** Regex (re), `langchain-text-splitters` (xem mục X — ghi chú tích hợp LangChain).
* **Chỉ số đo lường (mở rộng):**
  | Chỉ số | Công thức / Cách đo | Mục tiêu | Nguồn dữ liệu |
  |---|---|---|---|
  | Markdown Validation Rate | (Số chunk parse thành công bằng markdown linter / Tổng số chunk) × 100% | ≥ 99% | Parse thử bằng thư viện markdown (VD `markdown-it-py`) |
  | Reading-order Accuracy | (Số trang có thứ tự đọc đúng / Tổng số trang lấy mẫu, đặc biệt trang nhiều cột) × 100% | ≥ 90% trên tập mẫu multi-column | Kiểm tra thủ công |
  | Chunk Size Compliance | Tỷ lệ chunk nằm trong khoảng token cấu hình (VD 500-1000) | ≥ 95%; chunk lệch ngưỡng → cảnh báo ra STDERR | Log thống kê phân phối token/chunk |
  | Sentence/Table Integrity | Tỷ lệ chunk KHÔNG bị cắt giữa câu hoặc vỡ cấu trúc bảng | ≥ 95% | Kiểm tra bằng regex phát hiện câu dở dang + kiểm tra thủ công |
  | Overlap Consistency | Tỷ lệ chunk liền kề có overlap đúng theo cấu hình (10-15%) | 100% theo thiết kế; log lệch nếu có | Kiểm tra tự động khi build chunk |
  | Cross-page Merge Rate | Số đoạn văn bị cắt ngang trang được nối lại thành công / Tổng số trường hợp phát hiện | ≥ 90% | Log riêng các case merge |

### Giai đoạn 4: Vector hoá Cục bộ & Lưu trữ (Local Vectorization & DB)

* **Cách hoạt động:** Chunk ngữ nghĩa → model nhúng nội bộ → Vector → lưu vào Vector DB nhúng (embedded, không cần server).
* **Bổ sung (mới):**
  * **Phần cứng embedding — đã chốt theo mục IV.1:** chạy CPU-only trên máy nội bộ (GPU chỉ dành riêng cho VLM trên Colab, không dùng cho embedding). Với ước tính 2-5 triệu chunk, embedding CPU-only bằng `bge-m3` (568M tham số) sẽ chậm hơn đáng kể so với GPU — **bắt buộc** đo tốc độ thực tế trong pilot run (mục VII) và ưu tiên dùng bản ONNX/int8 quantized của `bge-m3` (qua `sentence-transformers` + `optimum`/`onnxruntime`, đã xác nhận có wheel Python 3.14 ở Phụ lục A) để bù tốc độ, thay vì đề xuất "cân nhắc GPU" như bản trước.
  * **Chọn Vector DB theo quy mô:** ở mức hàng triệu vector, **LanceDB** (columnar, tối ưu disk-based ANN) thường phù hợp hơn ChromaDB về khả năng mở rộng; chốt lựa chọn dựa trên benchmark thử nghiệm quy mô nhỏ trước.
  * **Schema metadata cho mỗi vector (mới, xem mục VI):** bắt buộc lưu kèm metadata để phục vụ trích dẫn nguồn khi trả lời RAG và lọc truy vấn.
  * **Idempotency khi embedding:** tính hash nội dung chunk (`chunk_hash`); nếu hash đã tồn tại trong DB → bỏ qua, tránh embed trùng khi chạy lại pipeline.
* **Thư viện đề xuất:** sentence-transformers (`BAAI/bge-m3`), chromadb hoặc lancedb (tương thích LangChain VectorStore — xem mục X).
* **Chỉ số đo lường (mở rộng):**
  | Chỉ số | Công thức / Cách đo | Mục tiêu | Nguồn dữ liệu |
  |---|---|---|---|
  | Embedding Latency (chunk/giây) | Tổng số chunk embed được / tổng thời gian | Ghi log theo batch để tối ưu batch size | `info.log` |
  | Index Success Rate | (Số vector ghi thành công vào DB / Tổng số chunk) × 100% | ≥ 99.5% | Manifest DB / log DB |
  | Dedup Hit Rate | Tỷ lệ chunk bị bỏ qua vì trùng `chunk_hash` đã tồn tại | Theo dõi để phát hiện bất thường (VD nếu quá cao → có thể lỗi hash logic) | Log Stage 4 |
  | Retrieval Quality (sample eval) | Recall@k trên bộ câu hỏi mẫu tự tạo (VD 30-50 câu hỏi với đáp án biết trước nằm ở trang nào) | Recall@5 ≥ 80% | Test script truy vấn thử sau khi index xong |
  | Metadata Completeness | Tỷ lệ vector có đầy đủ trường bắt buộc (mục VI) | 100% | Kiểm tra schema khi insert |
  | Storage Growth Rate | Dung lượng DB tăng theo số file đã xử lý | Theo dõi để dự báo dung lượng tổng khi hoàn tất 1.000 file | Log định kỳ |

## VI. QUY ƯỚC ĐỊNH DANH & METADATA (NAMING & METADATA SCHEMA) — *mục mới*

Cần thiết để truy vết nguồn (traceability) và trích dẫn chính xác khi RAG trả lời.

| Trường | Mô tả |
|---|---|
| `doc_id` | Định danh file PDF gốc |
| `page_id` | `doc_id` + số trang |
| `chunk_id` | `page_id` + thứ tự chunk trong trang |
| `chunk_type` | `text` \| `table` \| `image_caption` |
| `section_heading` | Heading gần nhất phía trên chunk (nếu có) |
| `ocr_confidence` | Điểm tin cậy OCR (nếu chunk đến từ trang scan) |
| `chunk_hash` | Hash nội dung, dùng để dedup |
| `source_bbox` | Toạ độ (x0, y0, x1, y1) trên trang gốc, phục vụ highlight khi trả lời |

## VII. KIỂM THỬ & TRIỂN KHAI (TESTING & ROLLOUT) — *mục mới*

* **Pilot run bắt buộc:** chạy thử toàn bộ pipeline với 5-10 file trước khi scale lên 1.000 file, để phát hiện lỗi cấu hình/model và ước lượng thời gian, chi phí Colab thực tế.
* **Giám sát tài nguyên:** theo dõi CPU/RAM của từng worker process khi xử lý file 1.000 trang, tránh OOM khi nhiều worker cùng load model song song.
* **Ước lượng tiến độ (ETA):** với job chạy nhiều ngày, cần log tiến độ định kỳ (số trang đã xử lý / tổng số, tốc độ trung bình) để theo dõi qua `info.log`.

## VIII. CẤU TRÚC THƯ MỤC DỰ ÁN (PROJECT FOLDER STRUCTURE) — *mục mới*

```
rag_pipeline/
│
├── config/
│   ├── config.yaml                # Toàn bộ ngưỡng, đường dẫn, tên model (mục II.6)
│   └── colab_endpoint.json        # URL Ngrok hiện hành + token xác thực (mục IV)
│
├── data/
│   ├── raw_pdfs/                  # 1.000 file PDF gốc (read-only, không sửa)
│   ├── cache/
│   │   ├── image_hash_cache/      # Cache mô tả VLM theo perceptual hash (mục V.2)
│   │   └── crops_tmp/             # Ảnh crop tạm thời (dọn dẹp định kỳ)
│   ├── markdown_output/           # Kết quả Stage 3 theo từng doc_id/page_id
│   └── vector_db/                 # LanceDB/ChromaDB (persist local)
│
├── state/
│   └── manifest.sqlite            # Manifest DB (mục III) — KHÔNG được xoá giữa các lần chạy
│
├── logs/
│   ├── info.log
│   └── error.log
│
├── src/
│   ├── stage1_routing/
│   │   ├── page_router.py
│   │   └── blank_font_detector.py
│   ├── stage2_extraction/
│   │   ├── text_table_extractor.py
│   │   ├── image_extractor.py     # dùng page.get_images()
│   │   ├── vlm_client.py          # gọi Colab qua HTTP
│   │   └── ocr_engine.py
│   ├── stage3_chunking/
│   │   ├── layout_reorder.py      # column clustering theo X,Y
│   │   ├── markdown_builder.py
│   │   └── semantic_chunker.py    # có thể wrap langchain-text-splitters
│   ├── stage4_vectorization/
│   │   ├── embedder.py
│   │   └── vector_store.py
│   ├── common/
│   │   ├── manifest_db.py         # CRUD cho manifest.sqlite
│   │   ├── logging_setup.py       # QueueHandler/QueueListener (mục II.4)
│   │   └── config_loader.py
│   └── run_pipeline.py            # entry point, dùng ProcessPoolExecutor
│
├── colab_server/
│   └── vlm_api.py                 # FastAPI + Ngrok, chạy trên Colab notebook
│
├── scripts/
│   ├── check_env.py               # kiểm tra tương thích thư viện (mục II.1)
│   ├── dump_source_to_txt.cmd     # gom .py → .txt cho AI (mục II.7)
│   └── pilot_run.cmd              # chạy thử 5-10 file (mục VII)
│
├── tests/
│   ├── sample_pages/              # tập trang mẫu đã gán nhãn (ground-truth) cho đo lường
│   └── eval_queries.json          # bộ câu hỏi mẫu để đo Retrieval Quality (mục V, Stage 4)
│
├── requirements.txt
└── README.md
```

## IX. SETUP & CHUẨN BỊ TRƯỚC KHI CODE (PRE-CODING SETUP CHECKLIST) — *mục mới*

Thực hiện tuần tự trước khi viết bất kỳ dòng code xử lý pipeline nào:

1. **Tạo virtual environment riêng cho dự án** (`python -m venv venv`), tránh xung đột với các dự án Python khác trên cùng máy.
2. **Nâng cấp pip trước tiên:** `python -m pip install --upgrade pip` — bắt buộc để pip nhận diện đúng tag `cp314` và các wheel `abi3` tương thích ngược (xem Phụ lục A).
3. **Cài `torch` bản CPU-only tường minh** (mục IV.1): `pip install torch --index-url https://download.pytorch.org/whl/cpu` — không để pip tự chọn bản kèm CUDA.
4. **Chạy `scripts/check_env.py`** để xác nhận toàn bộ thư viện trong `requirements.txt` cài đặt và import được trên Python 3.14 (đối chiếu với Phụ lục A). Nếu có thư viện lỗi → quyết định fallback trước khi code tiếp.
5. **Khởi tạo `config/config.yaml`** với toàn bộ ngưỡng mặc định (blank-page %, min chars, OCR confidence threshold, chunk size/overlap, batch size...) — không để trống, có giá trị khởi điểm hợp lý.
6. **Khởi tạo `state/manifest.sqlite`** với schema đã định nghĩa ở mục III, bật chế độ WAL (`PRAGMA journal_mode=WAL;`).
7. **Thiết lập `logging_setup.py`** với `QueueHandler`/`QueueListener` trước khi viết bất kỳ worker nào, để mọi module sau này log đúng chuẩn ngay từ đầu.
8. **Chuẩn bị Colab notebook (`colab_server/vlm_api.py`) theo checklist bảo mật mục IV.2:**
   * Cài `fastapi`, `pyngrok`, `transformers`, `torch` (bản GPU, chỉ trên Colab) trên Colab.
   * Sinh bearer token + secret header, tắt `/docs`, giới hạn kích thước/định dạng payload, thiết lập endpoint health-check (`/ping`).
   * Xác nhận model VLM (PaliGemma hoặc tương đương) chạy được trong giới hạn VRAM của GPU Colab miễn phí.
   * Test gọi thử 1 ảnh từ máy local → Colab → nhận JSON trả về, xác nhận URL là HTTPS, trước khi tích hợp vào pipeline chính.
   * Thêm `config/colab_endpoint.json` vào `.gitignore` ngay từ commit đầu tiên.
9. **Chuẩn bị tập dữ liệu kiểm thử (`tests/`):**
   * Gán nhãn tay 200-500 trang mẫu (đa dạng: digital, scanned, có bảng, có ảnh/logo, multi-column) để dùng cho các chỉ số đo lường ở mục V.
   * Soạn bộ `eval_queries.json` (30-50 câu hỏi + vị trí đáp án biết trước) để đo Retrieval Quality ở Stage 4.
10. **Chạy `scripts/pilot_run.cmd`** với 5-10 file PDF thật để kiểm tra toàn bộ luồng end-to-end (Stage 1 → 4) trước khi scale lên 1.000 file, đúng theo mục VII.
11. **Xác nhận môi trường Windows CMD:** set `chcp 65001`, `PYTHONIOENCODING=utf-8`, kiểm tra ghi log tiếng Việt không bị lỗi trước khi chạy batch lớn.

> Thứ tự thực hiện chi tiết hơn (kèm code mẫu, "definition of done" từng bước) xem file **`WORKFLOW.md`** đi kèm.

## X. GHI CHÚ TÍCH HỢP LANGCHAIN (LANGCHAIN INTEGRATION NOTES, NẾU CẦN) — *mục mới*

Tài liệu gốc chỉ đề cập `langchain-text-splitters` cho Stage 3. Nếu định mở rộng dùng LangChain nhiều hơn ở các bước sau (ví dụ dựng RAG chain để trả lời truy vấn), cần lưu ý:

* **Phạm vi sử dụng hiện tại:** chỉ dùng module `langchain-text-splitters` (nhẹ, không kéo theo toàn bộ framework LangChain) cho việc chia mảnh theo Heading/đoạn văn ở Stage 3 — phù hợp với yêu cầu "chunk ngữ nghĩa 500-1000 token" đã mô tả. Có thể thay bằng `RecursiveCharacterTextSplitter` hoặc `MarkdownHeaderTextSplitter` tuỳ theo cấu trúc Markdown đã dựng ở Stage 3.
* **Nếu mở rộng sang LangChain đầy đủ (retrieval/chain) ở giai đoạn sau:**
  * **Tương thích Vector DB:** cả `ChromaDB` và `LanceDB` đều có wrapper `VectorStore` chính thức trong LangChain (`langchain-chroma`, `langchain-community` cho LanceDB) — nên thiết kế schema metadata ở mục VI sao cho tương thích trực tiếp với interface `Document(page_content, metadata)` của LangChain, tránh phải viết lại tầng chuyển đổi sau này.
  * **Embedding wrapper:** nếu dùng `sentence-transformers` trực tiếp ở Stage 4 (không qua LangChain) nhưng sau này muốn dùng LangChain retriever, cần đảm bảo có thể wrap lại bằng `HuggingFaceEmbeddings` mà không phải embed lại toàn bộ dữ liệu — tức là lưu đúng vector số thực (không lưu qua định dạng riêng khó tái sử dụng).
  * **Metadata filter:** LangChain retriever hỗ trợ filter theo metadata — nên đảm bảo các trường ở mục VI (`doc_id`, `page_id`, `chunk_type`...) được lưu ở dạng phẳng (flat key-value), tránh nested object phức tạp, để tương thích filter query của cả Chroma/LanceDB qua LangChain.
  * **Không bắt buộc phải cài toàn bộ LangChain ngay từ đầu** — theo nguyên tắc Zero-Installation/tối giản dependency (mục II.2), chỉ thêm các package con cần thiết (`langchain-text-splitters`, và sau này `langchain-core`, `langchain-chroma`...) khi thực sự triển khai bước dùng đến, tránh cài đặt dư thừa gây rủi ro xung đột version trên Python 3.14 (mục II.1).
* **Khuyến nghị:** giữ Stage 1-4 độc lập với LangChain càng nhiều càng tốt (chỉ dùng ở Stage 3 chunking); phần "RAG query/chain" nên tách thành module riêng (`src/rag_chain/`, chưa có trong cấu trúc mục VIII) khi bắt đầu triển khai, không trộn vào pipeline ingestion để tránh phụ thuộc chéo không cần thiết.

## PHỤ LỤC A — KIỂM TRA WHEEL PYTHON 3.14 CHO TOÀN BỘ THƯ VIỆN ĐỀ XUẤT

*Kiểm tra thực tế qua PyPI JSON API ngày 26/07/2026. Phương pháp: đối chiếu danh sách file wheel của phiên bản mới nhất mỗi package với tag `cp314`, và tag `abi3` (tương thích ngược nhờ Stable ABI của CPython).*

| Thư viện | Loại wheel tìm thấy | Kết luận cho Python 3.14 chuẩn |
|---|---|---|
| `torch` | `cp314`/`cp314t`, đủ macOS/Linux/Windows | ✅ An toàn — hỗ trợ chính thức từ bản 2.10 |
| `numpy` | `cp314`/`cp314t`, đủ mọi platform | ✅ An toàn |
| `pillow` | `cp314`/`cp314t`, đủ mọi platform | ✅ An toàn |
| `opencv-python-headless` | `cp37-abi3` (tương thích ngược) | ✅ An toàn qua abi3 |
| `sentence-transformers` | `py3-none-any` (pure Python) | ✅ An toàn |
| `chromadb` | `cp39-abi3` | ✅ An toàn qua abi3 |
| `lancedb` | `cp39-abi3`, **không có sdist** | ✅ An toàn qua abi3, nhưng phụ thuộc 100% vào wheel dựng sẵn (không build được từ source nếu thiếu platform) |
| `easyocr` | `py3-none-any` | ✅ An toàn (deps `torch`/`opencv`/`scikit-image`/`shapely`/`pyclipper` đã kiểm tra riêng — đều ổn) |
| `surya-ocr` | `py3-none-any` | ✅ An toàn |
| `img2table` | `cp314` riêng biệt, đủ platform | ✅ An toàn |
| `pymupdf` (fitz) | `cp310-abi3` cho bản chuẩn | ✅ An toàn cho Python 3.14 chuẩn. Chỉ có 1 wheel `cp314t` (free-threaded, manylinux x86_64) — **không đủ cho free-threaded trên mọi platform** |
| `pdfplumber` | `py3-none-any` | ✅ An toàn |
| `fastapi` | `py3-none-any` | ✅ An toàn |
| `uvicorn` | `py3-none-any` | ✅ An toàn |
| `pyngrok` | `py3-none-any` | ✅ An toàn |
| `transformers` | `py3-none-any` (deps `tokenizers`/`safetensors` là `cp310-abi3` — đã kiểm tra, ổn) | ✅ An toàn |
| `langchain-text-splitters` | `py3-none-any` | ✅ An toàn |
| `pydantic-core` (dep của FastAPI) | `cp314`/`cp314t`, đủ mọi platform | ✅ An toàn |
| `scikit-image`, `shapely`, `pyclipper`, `onnxruntime` | `cp314`/`cp314t`, đủ mọi platform chính | ✅ An toàn |

**Kết luận chung:** tại thời điểm kiểm tra, **không có thư viện nào trong danh sách đề xuất của tài liệu này thiếu wheel cho Python 3.14 bản chuẩn** — toàn bộ cài được bằng `pip install` thông thường, không cần build từ source, không cần Visual C++ Build Tools trên Windows.

**Lưu ý quan trọng (caveats) — đọc kỹ trước khi tin tưởng hoàn toàn vào bảng trên:**
1. **Chỉ áp dụng cho Python 3.14 bản chuẩn.** Biến thể **free-threaded** (`python3.14t`, no-GIL, thử nghiệm) có độ phủ wheel kém hơn nhiều (VD PyMuPDF chỉ có 1 wheel free-threaded cho 1 platform) → **khuyến nghị dùng bản chuẩn**, không dùng `python3.14t` cho dự án này.
2. **Wheel `abi3` cần pip đủ mới** để nhận diện đúng tag Python 3.14 — đã thêm bước `pip install --upgrade pip` vào đầu mục IX.
3. **Đây là kết quả tại một thời điểm (snapshot 26/07/2026).** Hệ sinh thái PyPI cập nhật liên tục; bảng này không thay thế việc chạy `scripts/check_env.py` thực tế ngay trước khi bắt đầu code.
4. **Chưa quét toàn bộ cây dependency**, chỉ các gói chính + một số gói phụ có rủi ro cao (C/Rust extension). `check_env.py` nên chạy `pip install -r requirements.txt --dry-run` để xác nhận 100% trước khi code thật.
5. **`lancedb` không có sdist** — nếu Google thay đổi cấu trúc release hoặc một platform bị rút wheel, sẽ không có phương án build từ source; nên khoá version cụ thể trong `requirements.txt` (`lancedb==0.34.0`) thay vì để trống.
6. **Đã xác nhận riêng cho `win_amd64`** (vì hệ thống chạy trên Windows CMD — mục II.4): kiểm tra trực tiếp từng file wheel của `numpy`, `opencv-python-headless`, `pymupdf`, `onnxruntime`, `scipy`, `shapely`, `pyclipper`, `scikit-image`, `pillow`, `torch`, `chromadb`, `lancedb`, `tokenizers`, `safetensors`, `pydantic-core`, `img2table` — **toàn bộ đều có wheel `win_amd64` cho Python 3.14 bản chuẩn** (qua tag `cp314-cp314-win_amd64` trực tiếp hoặc `abi3-win_amd64`). Không có gói nào chỉ có wheel cho Linux/macOS mà thiếu Windows.
