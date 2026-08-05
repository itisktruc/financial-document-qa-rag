"""
Worker process cho PP-StructureV3 - chạy bằng interpreter của venv riêng
(/opt/venv-paddle), tách khỏi venv chính (torch/vietocr) để tránh xung đột
thư viện native CUDA dùng chung (nvidia-nccl-cu12...) giữa paddle và torch
(xem lịch sử: lỗi "undefined symbol: ncclCommResume" khi 2 framework chung 1
process/site-packages).

VAI TRÒ (theo yêu cầu): PPStructureV3 ở đây CHỈ dùng để PHÁT HIỆN layout/bảng
(bounding box) - KHÔNG dùng kết quả nhận diện chữ (rec_texts) của paddle. Venv
chính sẽ tự cắt ảnh theo bbox và nhận diện lại bằng vietocr (chính xác hơn cho
tiếng Việt có dấu, xem ghi chú OCR_DPI ở parser.py).

GIAO THỨC (line-delimited JSON qua stdin/stdout):
- Khởi động xong (model load xong, tốn thời gian) -> in {"ready": true}
- Nhận vào 1 dòng: {"npy_path": "<file .npy chứa ảnh trang, lossless>", "id": "<uuid do cha sinh ra>"}
- Trả ra 1 dòng (LUÔN kèm "id" giống hệt request tương ứng, để process cha có
  thể phát hiện và bỏ qua nếu vô tình đọc nhầm kết quả của 1 request khác):
    {
      "id": "<uuid giống request>",
      "text_boxes": [
        {
          "bbox": [x0,y0,x1,y1],
          "quad": [[x,y],[x,y],[x,y],[x,y]]  // 4 góc THẬT (ưu tiên dt_polys,
                                              // xem _coerce_quad) - venv chính
                                              // dùng để crop kiểu deepdoc
                                              // (perspective transform)
        }, ...
      ],   // chữ NGOÀI bảng
      "tables": [
        {
          "bbox": [x0,y0,x1,y1],                       // vị trí bảng trên trang
          "pred_html": "<table>...</table>",           // khung cấu trúc (rowspan/colspan) do paddle suy luận
          "cells": [{"bbox": [x0,y0,x1,y1]}, ...]      // GIẢ ĐỊNH: cùng thứ tự thẻ <td>/<th> trong pred_html
        }, ...
      ]
    }
  hoặc {"id": "...", "error": "..."} nếu trang lỗi hoàn toàn
- File .npy đầu vào được WORKER tự xoá ngay sau khi đọc xong vào RAM (không
  chờ process cha dọn dẹp) - tránh tranh chấp về thời điểm ai xoá file giữa 2
  process (xem chi tiết ở phần "BẢO VỆ KÊNH GIAO TIẾP STDOUT" phía dưới).
- Nhận "__QUIT__" -> thoát vòng lặp, kết thúc process

LƯU Ý QUAN TRỌNG VỀ TÊN FIELD:
Tên field (`layout_det_res`, `overall_ocr_res`, `table_res_list`,
`cell_box_list`, `rec_boxes`, `dt_polys`...) dựa theo tài liệu/mã nguồn
paddleocr 3.7.x tại thời điểm viết. Các field này đã đổi tên/cấu trúc qua các
bản paddleocr khác nhau trước đây -> code CỐ TÌNH truy cập rất thủ công
(defensive, .get() + try/except từng phần) để 1 field bị thiếu/đổi tên không
làm crash cả trang - nhưng bạn NÊN chạy thử trên 1 trang scan thật, in
`res.json` ra xem cấu trúc thực tế có khớp không (mình không có môi trường
paddle để test trực tiếp).
"""
import json
import os
import sys

import numpy as np

# ==========================================================================
# BẢO VỆ KÊNH GIAO TIẾP STDOUT (FIX MỚI - xem thêm phần GIAO THỨC ở trên)
# ==========================================================================
# VẤN ĐỀ ĐÃ QUAN SÁT ĐƯỢC: paddle/paddleocr (và các thư viện nó phụ thuộc như
# tqdm) đôi khi in thẳng ra STDOUT (không phải stderr) - progress bar, banner
# license, cảnh báo cấu hình, log lúc load model hoặc lúc predict()... Vì kênh
# IPC ở đây dùng CHÍNH stdout để truyền JSON kết quả, BẤT KỲ dòng "lạc" nào in
# ra stdout cũng sẽ bị parser.py (process cha) hiểu nhầm là JSON kết quả của
# request hiện tại:
#   - Nếu dòng đó không phải JSON hợp lệ -> lỗi "Expecting value..." khi cha
#     cố json.loads() nó.
#   - Nếu cha "nuốt" nhầm dòng rác đó thay vì dòng JSON thật, dòng JSON thật
#     (kết quả ĐÚNG của trang hiện tại) vẫn còn nằm trong hàng đợi, chờ bị đọc
#     NHẦM ở lần gọi kế tiếp (trang sau) -> mọi trang từ đó trở đi bị LỆCH 1
#     NHỊP vĩnh viễn, cha luôn nhận kết quả của trang trước đó. Khi cha xoá
#     file .npy ngay sau khi "tưởng" đã nhận đủ kết quả cho trang hiện tại,
#     trong khi worker (đang xử lý chậm hơn 1 nhịp) chưa kịp đọc đúng file đó
#     -> chính là nguồn gốc chuỗi lỗi "No such file or directory" lặp lại ở
#     rất nhiều trang liên tiếp.
#
# CÁCH SỬA: giữ lại 1 file descriptor RIÊNG (_REAL_STDOUT) trỏ thẳng tới stdout
# thật ban đầu (dup lại TRƯỚC khi import paddleocr) - CHỈ dùng fd này để gửi
# JSON giao thức qua hàm _protocol_write(). Sau đó, dup2 fd 1 (stdout) đè lên
# fd 2 (stderr) và gán sys.stdout = sys.stderr, để BẤT KỲ print()/log nào từ
# paddle (kể cả in từ tầng C/C++ vốn ghi thẳng vào fd 1, không qua sys.stdout
# của Python) cũng chảy vào stderr thay vì làm bẩn kênh JSON.
_REAL_STDOUT_FD = os.dup(1)
_real_stdout = os.fdopen(_REAL_STDOUT_FD, "w", buffering=1, encoding="utf-8")
os.dup2(2, 1)
sys.stdout = sys.stderr


def _protocol_write(obj: dict) -> None:
    """Ghi 1 dòng JSON ra kênh giao thức THẬT - KHÔNG dùng print()/sys.stdout
    thường (đã bị redirect sang stderr ở trên) để tránh mọi thứ khác vô tình
    lẫn vào kênh này."""
    _real_stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    _real_stdout.flush()


# Import SAU khi đã redirect stdout, phòng trường hợp bản thân việc import
# paddleocr cũng in banner/log ra stdout.
from paddleocr import PPStructureV3

OCR_DEVICE = os.getenv("OCR_DEVICE", "gpu:0")
CPU_THREADS = int(os.getenv("OCR_CPU_THREADS", os.cpu_count() or 4))


def _build_structure_engine() -> PPStructureV3:
    common_kwargs = dict(
        lang="vi",
        device=OCR_DEVICE,
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=True,
        use_table_recognition=True,
        use_formula_recognition=False,
        use_chart_recognition=False,
        use_seal_recognition=False,
    )
    if not OCR_DEVICE.startswith("cpu"):
        return PPStructureV3(**common_kwargs)
    try:
        return PPStructureV3(enable_mkldnn=True, cpu_threads=CPU_THREADS, **common_kwargs)
    except TypeError:
        return PPStructureV3(**common_kwargs)


def _coerce_bbox(coord) -> list:
    """
    Chấp nhận cả 2 dạng toạ độ mà các field khác nhau của PP-StructureV3 hay
    trả về: [x0,y0,x1,y1] (axis-aligned) hoặc [[x,y]x4] (tứ giác 4 điểm, như
    dt_polys). Luôn quy về axis-aligned [x0,y0,x1,y1] (float thường, không phải
    numpy) để đơn giản hoá việc cắt ảnh ở venv chính và để json.dumps không vỡ
    vì numpy int16/float32.
    """
    arr = np.asarray(coord, dtype=float)
    if arr.ndim == 1 and arr.shape[0] == 4:
        return [float(arr[0]), float(arr[1]), float(arr[2]), float(arr[3])]
    if arr.ndim == 2:
        x0, y0 = float(arr[:, 0].min()), float(arr[:, 1].min())
        x1, y1 = float(arr[:, 0].max()), float(arr[:, 1].max())
        return [x0, y0, x1, y1]
    raise ValueError(f"Không nhận dạng được định dạng bbox: {coord!r}")


def _coerce_quad(coord) -> list:
    """
    GHÉP CROP KIỂU DEEPDOC: khác với `_coerce_bbox` (luôn làm phẳng về axis-
    aligned [x0,y0,x1,y1]), hàm này GIỮ LẠI toạ độ 4 điểm góc gốc (quad) khi
    có thể - đây chính là phần "duỗi thẳng theo góc nghiêng" mà crop kiểu
    deepdoc (get_rotate_crop_image - perspective transform) cần, mà crop bbox
    trục X-Y thô không có.

    - Nếu coord vốn đã là quad [[x,y]]x4 (vd dt_polys - polygon THẬT do
      detector trả ra, có thể hơi nghiêng) -> giữ nguyên, chỉ ép kiểu.
    - Nếu coord vốn chỉ là bbox axis-aligned [x0,y0,x1,y1] (vd rec_boxes,
      hoặc cell_box_list của bảng) -> suy ra 4 góc hình chữ nhật tương ứng
      (thứ tự TL, TR, BR, BL). Lúc này crop kiểu deepdoc ở venv chính sẽ TỰ
      SUY BIẾN về giống hệt crop bbox thẳng như code cũ (không có gì để
      "duỗi") - không mất thông tin, không cần nhánh xử lý riêng ở đây.
    """
    arr = np.asarray(coord, dtype=float)
    if arr.ndim == 2 and arr.shape[0] == 4 and arr.shape[1] == 2:
        return arr.tolist()
    if arr.ndim == 1 and arr.shape[0] == 4:
        x0, y0, x1, y1 = arr.tolist()
        return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]
    raise ValueError(f"Không nhận dạng được định dạng quad: {coord!r}")


def _bbox_center_inside(bbox, container_bbox) -> bool:
    cx, cy = (bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2
    x0, y0, x1, y1 = container_bbox
    return x0 <= cx <= x1 and y0 <= cy <= y1


def _extract_structure(res) -> dict:
    data = res.json.get("res", res) if hasattr(res, "json") else res

    # ---- chữ rời rạc trên toàn trang (bao gồm cả chữ nằm trong bảng) ----
    # GHÉP CROP KIỂU DEEPDOC: đổi thứ tự ưu tiên so với trước - lấy dt_polys
    # (polygon THẬT do detector trả ra, có thể hơi nghiêng) TRƯỚC rec_boxes
    # (đã bị paddle làm phẳng về axis-aligned rectangle). Vì venv chính không
    # dùng rec_texts của paddle (tự nhận diện lại bằng vietocr), cái ta cần là
    # toạ độ CÀNG SÁT VỚI GÓC NGHIÊNG THẬT càng tốt để crop kiểu deepdoc
    # (get_rotate_crop_image - xem parser.py) phát huy tác dụng "duỗi thẳng"
    # dòng chữ; rec_boxes chỉ giữ vai trò fallback nếu dt_polys không có.
    all_text_boxes = []
    all_text_quads = []
    try:
        overall = data.get("overall_ocr_res", {}) or {}
        dt_polys = overall.get("dt_polys")
        rec_boxes = overall.get("rec_boxes")
        if dt_polys is not None and len(dt_polys) > 0:
            coords = dt_polys
        elif rec_boxes is not None and len(rec_boxes) > 0:
            coords = rec_boxes
        else:
            coords = []
        all_text_boxes = [_coerce_bbox(c) for c in coords]
        all_text_quads = [_coerce_quad(c) for c in coords]
    except Exception:
        all_text_boxes = []
        all_text_quads = []

    # ---- bảng: bbox tổng + khung HTML (rowspan/colspan) + bbox từng cell ----
    tables = []
    table_bboxes = []
    try:
        for tbl in data.get("table_res_list", []) or []:
            cell_boxes = [_coerce_bbox(c) for c in (tbl.get("cell_box_list") or [])]
            pred_html = tbl.get("pred_html", "") or ""
            if cell_boxes:
                table_bbox = [
                    min(c[0] for c in cell_boxes), min(c[1] for c in cell_boxes),
                    max(c[2] for c in cell_boxes), max(c[3] for c in cell_boxes),
                ]
            else:
                table_bbox = [0.0, 0.0, 0.0, 0.0]
            tables.append({
                "bbox": table_bbox,
                "pred_html": pred_html,
                "cells": [{"bbox": c} for c in cell_boxes],
            })
            table_bboxes.append(table_bbox)
    except Exception:
        tables = []
        table_bboxes = []

    # ---- loại text box rơi vào bên trong 1 bảng (nội dung bảng ghép riêng
    # qua "cells" ở trên, tránh lặp lại trong đoạn văn thường) ----
    # LƯU Ý: zip bbox+quad ở đây để giữ chúng ĐI CÙNG NHAU qua bước lọc -
    # tránh lệch chỉ số nếu chỉ lọc all_text_boxes rồi tra all_text_quads
    # riêng (2 danh sách gốc luôn cùng độ dài vì cùng build từ 1 `coords`).
    text_box_quad_pairs = [
        (b, q) for b, q in zip(all_text_boxes, all_text_quads)
        if not any(_bbox_center_inside(b, t) for t in table_bboxes)
    ]

    return {
        # "quad": 4 điểm góc (xem _coerce_quad) - venv chính (parser.py) dùng
        # để crop kiểu deepdoc (perspective transform) thay vì crop bbox trục
        # X-Y thô. Luôn có mặt (không None) nhờ _coerce_quad tự suy ra hình
        # chữ nhật khi nguồn vốn chỉ là bbox axis-aligned.
        "text_boxes": [{"bbox": b, "quad": q} for b, q in text_box_quad_pairs],
        "tables": tables,
    }


def _structure_page(engine: PPStructureV3, image: np.ndarray) -> dict:
    try:
        results = list(engine.predict(image))
    except Exception as e:
        return {"error": f"predict lỗi: {e}"}
    if not results:
        return {"text_boxes": [], "tables": []}
    try:
        return _extract_structure(results[0])
    except Exception as e:
        return {"error": f"parse kết quả lỗi: {e}"}


def main() -> None:
    engine = _build_structure_engine()
    _protocol_write({"ready": True})

    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue
        if line == "__QUIT__":
            break

        req_id = None
        try:
            req = json.loads(line)
            req_id = req.get("id")
            npy_path = req["npy_path"]
            image = np.load(npy_path)
            # Xoá file input NGAY sau khi đã đọc xong vào RAM - không đợi
            # process cha (parser.py) dọn dẹp, để loại bỏ hoàn toàn tranh
            # chấp về THỜI ĐIỂM ai xoá file trước/sau (nguồn gốc lỗi "No such
            # file or directory" nếu cha xoá file trước khi worker kịp đọc do
            # hàng đợi kết quả bị lệch nhịp).
            try:
                os.remove(npy_path)
            except OSError:
                pass
            result = _structure_page(engine, image)
        except Exception as e:
            result = {"error": f"worker IPC error: {e}"}

        result["id"] = req_id
        _protocol_write(result)


if __name__ == "__main__":
    main()