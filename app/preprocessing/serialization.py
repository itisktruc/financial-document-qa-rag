from __future__ import annotations

import dataclasses
from enum import Enum
from typing import Any

from .models import Document


def _serialize_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return _serialize_dataclass(value)
    if isinstance(value, (list, tuple)):
        return [_serialize_value(v) for v in value]
    if isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}
    return value


def _serialize_dataclass(obj: Any) -> dict[str, Any]:
    return {
        f.name: _serialize_value(getattr(obj, f.name))
        for f in dataclasses.fields(obj)
    }


def document_to_dict(document: Document, doc_id: str | None = None) -> dict[str, Any]:
    """Serialize a :class:`Document` (pages, blocks, metadata — everything
    it references) into a plain dict suitable for
    ``collection.insert_one`` / ``collection.replace_one``.

    Parameters
    ----------
    doc_id:
        If given, becomes the Mongo ``_id`` field (e.g. the Hugging Face
        repo file path). Using a stable, content-derived id is what makes
        the "already processed?" resume check in ``hf_to_mongo.py`` a plain
        ``find_one({"_id": doc_id})`` lookup.
    """
    data = _serialize_dataclass(document)
    if doc_id is not None:
        data["_id"] = doc_id
    return data
