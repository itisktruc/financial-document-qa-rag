import os
import json
from pathlib import Path
from pypdf import PdfReader

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, RapidOcrOptions
from docling.datamodel.accelerator_options import AcceleratorOptions, AcceleratorDevice

def analyze_pdf_structure(pdf_path: str) -> tuple[str, int]:
    try:
        reader = PdfReader(pdf_path)
        scanned_pages_count = 0
        for page in reader.pages:
            text = page.extract_text() or ""
            has_images = len(page.images) > 0
            if len(text.strip()) < 30 and has_images:
                scanned_pages_count += 1
        all_sample_text = "".join((p.extract_text() or "") for p in reader.pages[:3])
        if scanned_pages_count > 0 or len(all_sample_text.strip()) < 100:
            return "Scanned PDF", len(reader.pages)
        return "Digital PDF", len(reader.pages)
    except Exception as e:
        print(f"Error analyzing PDF: {e}")
        return "Scanned PDF", 0


def process_document(pdf_path: str, output_dir: str = "../../data/processed", chunk_size: int = 3):
    path = Path(pdf_path)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    print(f"Processing PDF: {pdf_path}")
    pdf_type, total_pages = analyze_pdf_structure(pdf_path)
    print(f"PDF Type: {pdf_type}, Total Pages: {total_pages}")

    md_file_path = out_path / f"{path.stem}.md"
    json_file_path = out_path / f"{path.stem}.json"

    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_table_structure = True
    pipeline_options.do_picture_classification = False

    pipeline_options.accelerator_options = AcceleratorOptions(
        num_threads=1,
        device=AcceleratorDevice.CPU
    )

    if pdf_type == "Scanned PDF":
        print("Using RapidOCR with memory optimizations...")
        pipeline_options.do_ocr = True
        pipeline_options.ocr_options = RapidOcrOptions(
            lang=["vi"],
            force_full_page_ocr=False
        )
    else:
        pipeline_options.do_ocr = False

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    all_markdown = []
    all_json_chunks = []

    for start in range(0, total_pages, chunk_size):
        end = min(start + chunk_size, total_pages)
        print(f"Processing pages {start+1} to {end}...")

        result = converter.convert(
            pdf_path, 
            page_range=(start + 1, end)
        )
        doc = result.document

        all_markdown.append(doc.export_to_markdown())
        all_json_chunks.append(doc.export_to_dict())

        print(f"Chunk {start//chunk_size + 1} completed")

    # Save results
    with open(md_file_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(all_markdown))
    print(f"\nMarkdown saved to: {md_file_path}")

    with open(json_file_path, "w", encoding="utf-8") as f:
        json.dump(all_json_chunks, f, ensure_ascii=False, indent=2)
    print(f"\nJSON saved to: {json_file_path}")


if __name__ == "__main__":
    current_dir = Path(__file__).resolve().parent
    pdf_file = (current_dir / "../../data/raw/FPT/FPT_BCTC_2023.pdf").resolve()
    output_dir = (current_dir / "../../data/processed").resolve()

    if pdf_file.exists():
        process_document(pdf_path=str(pdf_file), output_dir=str(output_dir), chunk_size=3)
    else:
        print(f"[!] PDF not found: {pdf_file}")