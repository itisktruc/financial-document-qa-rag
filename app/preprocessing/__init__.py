"""
preprocessing
=============

A modular, production-ready preprocessing pipeline for OCR'd Vietnamese
annual financial reports (audited financial statements). Parses raw
``===== PAGE X =====``-delimited OCR text into a structured
:class:`~preprocessing.models.Document` of typed, page-tracked, HTML-table
-preserving :class:`~preprocessing.models.Block` objects — ready for
hierarchical chunking and citation in a RAG pipeline (LangChain,
LlamaIndex, Haystack, or a custom retriever).

Typical usage
-------------

    from preprocessing import DocumentPreprocessingPipeline

    pipeline = DocumentPreprocessingPipeline()
    document = pipeline.process_file("annual_report_2024.txt")

    for block in document.blocks:
        print(block.block_type, block.section, block.page_start)

    for table in document.tables():
        print(table.html)  # exact original HTML, never modified

    if document.quality is not None:
        print(document.quality.overall_risk, document.quality.notes)

See ``preprocessing/pipeline.py`` for configuration and
``preprocessing/models.py`` for the full output schema.
"""

from .block_detector import BlockDetector
from .cleaner import CleaningConfig, CleaningStats, OCRCleaner
from .diacritic_corrector import (
    DiacriticCorrector,
    DiacriticCorrectorConfig,
    DiacriticStats,
)
from .header_footer import HeaderFooterDetector, HeaderFooterResult
from .heading_detector import HeadingCandidate, HeadingDetector
from .metadata import MetadataExtractor
from .models import (
    Block,
    BlockType,
    Document,
    DocumentMetadata,
    HeadingBlock,
    ListBlock,
    Page,
    ParagraphBlock,
    SignatureBlock,
    TableBlock,
    UnknownBlock,
)
from .parser import PageParser, PageParsingError
from .pipeline import DocumentPreprocessingPipeline, PipelineConfig
from .quality import QualityScorecard, build_scorecard

__all__ = [
    "BlockDetector",
    "CleaningConfig",
    "CleaningStats",
    "OCRCleaner",
    "DiacriticCorrector",
    "DiacriticCorrectorConfig",
    "DiacriticStats",
    "HeaderFooterDetector",
    "HeaderFooterResult",
    "HeadingCandidate",
    "HeadingDetector",
    "MetadataExtractor",
    "Block",
    "BlockType",
    "Document",
    "DocumentMetadata",
    "HeadingBlock",
    "ListBlock",
    "Page",
    "ParagraphBlock",
    "SignatureBlock",
    "TableBlock",
    "UnknownBlock",
    "PageParser",
    "PageParsingError",
    "DocumentPreprocessingPipeline",
    "PipelineConfig",
    "QualityScorecard",
    "build_scorecard",
]

__version__ = "0.2.0"