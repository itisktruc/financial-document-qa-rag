from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class DocumentStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class DocumentMetadata(BaseModel):
    document_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    file_name: str
    company: Optional[str] = None
    document_type: Optional[str] = None   # BCTC_Nam, BCTC_Quy, ...
    year: Optional[int] = None
    quarter: Optional[int] = None
    language: str = "vi"
    status: DocumentStatus = DocumentStatus.UPLOADED
    file_path: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)