# Hướng Dẫn Cài Đặt Môi Trường (Environment Setup Guide)

Tài liệu này hướng dẫn chi tiết các bước thiết lập môi trường để chạy dự án Financial Document Intelligence Assistant ở local.

## Bước 1: Clone Repository
Đầu tiên, tải mã nguồn dự án về máy của bạn:
```bash
git clone https://github.com/itisktruc/financial-document-qa-rag.git
cd financial-document-qa-rag
```

## Bước 2: Khởi Tạo Môi Trường Ảo
Để tránh xung đột thư viện với các dự án khác, hãy tạo và kích hoạt môi trường ảo bằng venv:
```bash
python -m venv .venv
```
**Kích hoạt môi trường (Activate):**
* **Mac/Linux:** `source .venv/bin/activate`
* **Windows:** `.venv\Scripts\activate`

## Bước 3: Cài Đặt Thư Viện
Sau khi môi trường ảo đã được kích hoạt, cài đặt tất cả các gói (packages) cần thiết:
```bash
pip install -r requirements.txt
```
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
## Bước 4: Khởi Động Database Bằng Docker
Dự án sử dụng Qdrant và MongoDB chạy trên Docker. Đảm bảo ứng dụng Docker đang mở, sau đó khởi động các container ở chế độ nền:
```bash
docker compose up -d
```
*(Ghi chú: Bạn có thể kiểm tra Qdrant Dashboard tại http://localhost:6333/dashboard)*

## Bước 5: Chạy Test
Cuối cùng, chạy testing framework để đảm bảo toàn bộ mã nguồn và môi trường đang hoạt động bình thường:
```bash
pytest
```
Nếu terminal trả về kết quả màu xanh (passed), môi trường của bạn đã hoàn toàn sẵn sàng!

### **How to create and commit this file:**

**1. Create the `docs/` directory and the file:**
Run these commands in your terminal from the root of your project:
```bash
mkdir docs
touch docs/setup_guide.md