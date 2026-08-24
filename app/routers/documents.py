import os
import re
import shutil
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.models.document_schema import DocumentMetadata
from app.services.mongo_client import get_documents_collection, get_chunks_collection, get_document, upsert_document
from app.services.qdrant_store import _client as qdrant_client, QDRANT_COLLECTION
from qdrant_client.models import Filter, FieldCondition, MatchValue

router = APIRouter(prefix="/documents", tags=["documents"])

# Anchor theo vị trí file, không phụ thuộc cwd
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
UPLOAD_DIR = os.path.join(_PROJECT_ROOT, "data", "upload", "ungrouped")

ALLOWED_EXT = {".pdf"}


def _safe_filename(filename: str) -> str:
    """Chỉ lấy tên file (chặn path traversal), giữ nguyên dấu tiếng Việt,
    loại ký tự không hợp lệ trên filesystem."""
    name = os.path.basename(filename)
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    return name.strip()


@router.post("/upload", response_model=DocumentMetadata)
async def upload_document(
    file: UploadFile = File(...),
):
    safe_name = _safe_filename(file.filename)
    ext = os.path.splitext(safe_name)[1].lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(400, f"Định dạng {ext} không được hỗ trợ, chỉ nhận PDF.")

    upload_dir = os.path.join(UPLOAD_DIR)
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, safe_name)

    if os.path.exists(file_path):
        raise HTTPException(409, f"File '{safe_name}' đã tồn tại.")

    try:
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(500, f"Lỗi khi lưu file: {e}")

    doc = DocumentMetadata(
        file_name=safe_name,
        file_path=file_path,
    )
    # get_documents_collection().insert_one(doc.model_dump())
    # return doc
    doc_data = doc.model_dump()
    doc_data["_id"] = doc.document_id
    
    get_documents_collection().insert_one(doc_data)
    return doc


@router.get("/")
async def list_documents():
    docs = list(get_documents_collection().find({}))
    for doc in docs:
        if "_id" in doc:
            doc["_id"] = str(doc["_id"])
    return docs

@router.delete("/{document_id}")
async def delete_document(document_id: str):
    doc = get_documents_collection().find_one({"document_id": document_id}) or get_document(document_id)
    if not doc:
        raise HTTPException(404, "Không tìm thấy tài liệu.")
    
    path_to_delete = doc.get("file_path")
    if path_to_delete and os.path.exists(path_to_delete):
        try:
            os.remove(path_to_delete)
        except Exception as e:
            raise HTTPException(500, f"Lỗi khi xóa file vật lý: {e}")

    get_documents_collection().delete_one({"document_id": document_id})
    get_chunks_collection().delete_many({"document_id": document_id})
    try:
        qdrant_client.delete(
            collection_name=QDRANT_COLLECTION,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="doc_id",
                        match=MatchValue(value=document_id)
                    )
                ]
            )
        )
    except Exception as e:
        print(f"Cảnh báo: Không thể xóa vector trong Qdrant: {e}")
    
    return {"message": "Đã xóa tài liệu và dữ liệu liên quan", "document_id": document_id}
