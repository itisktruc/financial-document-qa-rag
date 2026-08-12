"""
app/models/chunk_schema.py

Pydantic schema cho document lưu trong Mongo collection "chunks". Khớp 1-1
với dataclass Chunk trong app/ingestion/chunker.py (field cho field), CHỈ
thêm:
  - id (alias "_id"): dùng chunk_id làm khoá chính Mongo luôn, thay vì để
    Mongo tự sinh ObjectId -- tra cứu ngược theo chunk_id (vd sau khi Qdrant
    trả top-k id) là lookup trực tiếp trên _id, không cần index phụ.
  - embedded: cờ runtime cho bước embedding/Qdrant sẽ làm sau -- thêm sẵn ở
    đây để không phải migrate schema khi cắm bước đó vào.

Tách schema Mongo ra khỏi dataclass nội bộ của chunker để 2 bên tiến hoá độc
lập: đổi cấu trúc _Block/thuật toán chunk không bắt buộc đổi luôn schema đã
lưu trong DB, và ngược lại đổi schema DB (vd thêm field) không đụng vào
logic chunking.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class ChunkType(str, Enum):
    PARENT = "parent"
    TEXT_CHILD = "text_child"
    TABLE = "table"


class ChunkDocument(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="_id", description="= chunk_id sinh bởi chunker (uuid4 hex)")
    document_id: str
    chunk_type: ChunkType
    content: str
    embedding_text: str
    parent_id: Optional[str] = None
    section_path: list[str] = Field(default_factory=list)
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    token_count: int
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Chưa dùng ở giai đoạn chunking hiện tại -- bước embedding sau này sẽ
    # query {"embedded": False} để biết chunk nào cần embed + upsert Qdrant,
    # rồi set lại True. Tránh phải quét lại toàn bộ chunk mỗi lần chạy job.
    embedded: bool = False

    @classmethod
    def from_chunk_dict(cls, d: dict) -> "ChunkDocument":
        """d = output của Chunk.to_dict() trong app/ingestion/chunker.py
        (chunk_type ở đây đã là string do to_dict() tự convert enum)."""
        payload = {k: v for k, v in d.items() if k != "chunk_id"}
        return cls(_id=d["chunk_id"], **payload)

    def to_mongo(self) -> dict:
        """Convert tường minh enum -> string thay vì dựa vào việc ChunkType
        kế thừa str (đúng về mặt kỹ thuật nhưng dễ vỡ nếu sau này đổi cách
        định nghĩa enum) -- ưu tiên rõ ràng hơn là dựa vào chi tiết ngầm."""
        d = self.model_dump(by_alias=True)
        d["chunk_type"] = self.chunk_type.value
        return d