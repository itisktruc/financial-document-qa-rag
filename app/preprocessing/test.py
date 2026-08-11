from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

# Cho phép import preprocessing khi chạy từ bất kỳ đâu
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from preprocessing.pipeline import DocumentPreprocessingPipeline, PipelineConfig
from preprocessing.serialization import document_to_dict

TEST_DIR = Path(__file__).resolve().parent / "test"


def process_one(pipeline: DocumentPreprocessingPipeline, txt_path: Path, out_path: Path) -> None:
    print(f"\n=== Processing: {txt_path.name} ===")
    doc = pipeline.process_file(txt_path)

    print(f"  pages   : {len(doc.pages)}")
    print(f"  blocks  : {len(doc.blocks)}")
    print(f"  company : {doc.metadata.company_name!r}")
    print(f"  year    : {doc.metadata.report_year}")
    if doc.quality is not None:
        print(f"  risk    : {doc.quality.overall_risk}")

    payload = document_to_dict(doc, doc_id=txt_path.name)
    # Không export raw pages (giống hf_to_mongo)
    payload.pop("pages", None)

    out_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"  wrote   : {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--file",
        default=None,
        help="Tên file .txt trong test/ (mặc định: xử lý tất cả *.txt)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Đường dẫn JSON output (chỉ khi --file; mặc định: test/<stem>.json)",
    )
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args()

    logging.basicConfig(
        level=args.log_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stdout,
    )

    pipeline = DocumentPreprocessingPipeline(config=PipelineConfig())

    if args.file:
        txt_path = TEST_DIR / args.file
        if not txt_path.exists():
            # Cho phép truyền path tuyệt đối / tương đối ngoài test/
            txt_path = Path(args.file)
        if not txt_path.exists():
            print(f"ERROR: không tìm thấy file: {args.file}", file=sys.stderr)
            sys.exit(1)
        out_path = (
            Path(args.output)
            if args.output
            else TEST_DIR / f"{txt_path.stem}.json"
        )
        process_one(pipeline, txt_path, out_path)
    else:
        txt_files = sorted(TEST_DIR.glob("*.txt"))
        if not txt_files:
            print(f"Không có file .txt nào trong {TEST_DIR}")
            print("Hãy bỏ file OCR .txt vào folder test/ rồi chạy lại.")
            sys.exit(0)
        for txt_path in txt_files:
            out_path = TEST_DIR / f"{txt_path.stem}.json"
            process_one(pipeline, txt_path, out_path)

    print("\nDone.")


if __name__ == "__main__":
    main()