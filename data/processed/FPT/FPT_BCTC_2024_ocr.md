## Trang 1

> ⚠️ **LỖI OCR ở trang này:** OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 437, in cached_files
    hf_hub_download(
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1013, in hf_hub_download
    return _hf_hub_download_to_cache_dir(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1088, in _hf_hub_download_to_cache_dir
    (url_to_download, etag, commit_hash, expected_size, xet_file_data, head_call_error) = _get_metadata_or_catch_error(
                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1707, in _get_metadata_or_catch_error
    metadata = get_hf_file_metadata(
               ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1615, in get_hf_file_metadata
    response = _httpx_follow_relative_redirects_with_backoff(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 719, in _httpx_follow_relative_redirects_with_backoff
    response = http_backoff(
               ^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 596, in http_backoff
    return next(
           ^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 504, in _http_backoff_base
    response = client.request(method=method, url=url, **kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 812, in request
    request = self.build_request(
              ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 367, in build_request
    headers = self._merge_headers(headers)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 430, in _merge_headers
    merged_headers.update(headers)
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 275, in update
    headers = Headers(headers)
              ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 156, in __init__
    bytes_value = _normalize_header_value(v, encoding)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 82, in _normalize_header_value
    return value.encode(encoding or "ascii")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/app/app/ingestion/parser.py", line 257, in _parse_with_qwen_vlm
    pages_markdown[page_num] = _ocr_page_with_qwen(pil_image)
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 212, in _ocr_page_with_qwen
    model, processor = _load_qwen_model()
                       ^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 186, in _load_qwen_model
    model = Qwen3VLForConditionalGeneration.from_pretrained(QWEN_MODEL_ID, **kwargs)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/modeling_utils.py", line 4286, in from_pretrained
    _adapter_model_path, pretrained_model_name_or_path, adapter_kwargs = maybe_load_adapters(
                                                                         ^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/integrations/peft.py", line 672, in maybe_load_adapters
    resolved_config_file = cached_file(
                           ^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 293, in cached_file
    file = cached_files(path_or_repo_id=path_or_repo_id, filenames=[filename], **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 488, in cached_files
    raise OSError(f"{e}") from e
OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)


*(trang rỗng / OCR không trả về nội dung)*

---

## Trang 2

> ⚠️ **LỖI OCR ở trang này:** OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 437, in cached_files
    hf_hub_download(
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1013, in hf_hub_download
    return _hf_hub_download_to_cache_dir(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1088, in _hf_hub_download_to_cache_dir
    (url_to_download, etag, commit_hash, expected_size, xet_file_data, head_call_error) = _get_metadata_or_catch_error(
                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1707, in _get_metadata_or_catch_error
    metadata = get_hf_file_metadata(
               ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1615, in get_hf_file_metadata
    response = _httpx_follow_relative_redirects_with_backoff(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 719, in _httpx_follow_relative_redirects_with_backoff
    response = http_backoff(
               ^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 596, in http_backoff
    return next(
           ^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 504, in _http_backoff_base
    response = client.request(method=method, url=url, **kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 812, in request
    request = self.build_request(
              ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 367, in build_request
    headers = self._merge_headers(headers)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 430, in _merge_headers
    merged_headers.update(headers)
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 275, in update
    headers = Headers(headers)
              ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 156, in __init__
    bytes_value = _normalize_header_value(v, encoding)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 82, in _normalize_header_value
    return value.encode(encoding or "ascii")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/app/app/ingestion/parser.py", line 257, in _parse_with_qwen_vlm
    pages_markdown[page_num] = _ocr_page_with_qwen(pil_image)
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 212, in _ocr_page_with_qwen
    model, processor = _load_qwen_model()
                       ^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 186, in _load_qwen_model
    model = Qwen3VLForConditionalGeneration.from_pretrained(QWEN_MODEL_ID, **kwargs)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/modeling_utils.py", line 4286, in from_pretrained
    _adapter_model_path, pretrained_model_name_or_path, adapter_kwargs = maybe_load_adapters(
                                                                         ^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/integrations/peft.py", line 672, in maybe_load_adapters
    resolved_config_file = cached_file(
                           ^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 293, in cached_file
    file = cached_files(path_or_repo_id=path_or_repo_id, filenames=[filename], **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 488, in cached_files
    raise OSError(f"{e}") from e
OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)


*(trang rỗng / OCR không trả về nội dung)*

---

## Trang 3

> ⚠️ **LỖI OCR ở trang này:** OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 437, in cached_files
    hf_hub_download(
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1013, in hf_hub_download
    return _hf_hub_download_to_cache_dir(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1088, in _hf_hub_download_to_cache_dir
    (url_to_download, etag, commit_hash, expected_size, xet_file_data, head_call_error) = _get_metadata_or_catch_error(
                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1707, in _get_metadata_or_catch_error
    metadata = get_hf_file_metadata(
               ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1615, in get_hf_file_metadata
    response = _httpx_follow_relative_redirects_with_backoff(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 719, in _httpx_follow_relative_redirects_with_backoff
    response = http_backoff(
               ^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 596, in http_backoff
    return next(
           ^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 504, in _http_backoff_base
    response = client.request(method=method, url=url, **kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 812, in request
    request = self.build_request(
              ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 367, in build_request
    headers = self._merge_headers(headers)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 430, in _merge_headers
    merged_headers.update(headers)
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 275, in update
    headers = Headers(headers)
              ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 156, in __init__
    bytes_value = _normalize_header_value(v, encoding)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 82, in _normalize_header_value
    return value.encode(encoding or "ascii")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/app/app/ingestion/parser.py", line 257, in _parse_with_qwen_vlm
    pages_markdown[page_num] = _ocr_page_with_qwen(pil_image)
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 212, in _ocr_page_with_qwen
    model, processor = _load_qwen_model()
                       ^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 186, in _load_qwen_model
    model = Qwen3VLForConditionalGeneration.from_pretrained(QWEN_MODEL_ID, **kwargs)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/modeling_utils.py", line 4286, in from_pretrained
    _adapter_model_path, pretrained_model_name_or_path, adapter_kwargs = maybe_load_adapters(
                                                                         ^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/integrations/peft.py", line 672, in maybe_load_adapters
    resolved_config_file = cached_file(
                           ^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 293, in cached_file
    file = cached_files(path_or_repo_id=path_or_repo_id, filenames=[filename], **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 488, in cached_files
    raise OSError(f"{e}") from e
OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)


*(trang rỗng / OCR không trả về nội dung)*

---

## Trang 4

> ⚠️ **LỖI OCR ở trang này:** OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 437, in cached_files
    hf_hub_download(
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1013, in hf_hub_download
    return _hf_hub_download_to_cache_dir(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1088, in _hf_hub_download_to_cache_dir
    (url_to_download, etag, commit_hash, expected_size, xet_file_data, head_call_error) = _get_metadata_or_catch_error(
                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1707, in _get_metadata_or_catch_error
    metadata = get_hf_file_metadata(
               ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1615, in get_hf_file_metadata
    response = _httpx_follow_relative_redirects_with_backoff(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 719, in _httpx_follow_relative_redirects_with_backoff
    response = http_backoff(
               ^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 596, in http_backoff
    return next(
           ^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 504, in _http_backoff_base
    response = client.request(method=method, url=url, **kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 812, in request
    request = self.build_request(
              ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 367, in build_request
    headers = self._merge_headers(headers)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 430, in _merge_headers
    merged_headers.update(headers)
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 275, in update
    headers = Headers(headers)
              ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 156, in __init__
    bytes_value = _normalize_header_value(v, encoding)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 82, in _normalize_header_value
    return value.encode(encoding or "ascii")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/app/app/ingestion/parser.py", line 257, in _parse_with_qwen_vlm
    pages_markdown[page_num] = _ocr_page_with_qwen(pil_image)
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 212, in _ocr_page_with_qwen
    model, processor = _load_qwen_model()
                       ^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 186, in _load_qwen_model
    model = Qwen3VLForConditionalGeneration.from_pretrained(QWEN_MODEL_ID, **kwargs)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/modeling_utils.py", line 4286, in from_pretrained
    _adapter_model_path, pretrained_model_name_or_path, adapter_kwargs = maybe_load_adapters(
                                                                         ^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/integrations/peft.py", line 672, in maybe_load_adapters
    resolved_config_file = cached_file(
                           ^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 293, in cached_file
    file = cached_files(path_or_repo_id=path_or_repo_id, filenames=[filename], **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 488, in cached_files
    raise OSError(f"{e}") from e
OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)


*(trang rỗng / OCR không trả về nội dung)*

---

## Trang 5

> ⚠️ **LỖI OCR ở trang này:** OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 437, in cached_files
    hf_hub_download(
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1013, in hf_hub_download
    return _hf_hub_download_to_cache_dir(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1088, in _hf_hub_download_to_cache_dir
    (url_to_download, etag, commit_hash, expected_size, xet_file_data, head_call_error) = _get_metadata_or_catch_error(
                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1707, in _get_metadata_or_catch_error
    metadata = get_hf_file_metadata(
               ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1615, in get_hf_file_metadata
    response = _httpx_follow_relative_redirects_with_backoff(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 719, in _httpx_follow_relative_redirects_with_backoff
    response = http_backoff(
               ^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 596, in http_backoff
    return next(
           ^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 504, in _http_backoff_base
    response = client.request(method=method, url=url, **kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 812, in request
    request = self.build_request(
              ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 367, in build_request
    headers = self._merge_headers(headers)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 430, in _merge_headers
    merged_headers.update(headers)
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 275, in update
    headers = Headers(headers)
              ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 156, in __init__
    bytes_value = _normalize_header_value(v, encoding)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 82, in _normalize_header_value
    return value.encode(encoding or "ascii")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/app/app/ingestion/parser.py", line 257, in _parse_with_qwen_vlm
    pages_markdown[page_num] = _ocr_page_with_qwen(pil_image)
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 212, in _ocr_page_with_qwen
    model, processor = _load_qwen_model()
                       ^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 186, in _load_qwen_model
    model = Qwen3VLForConditionalGeneration.from_pretrained(QWEN_MODEL_ID, **kwargs)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/modeling_utils.py", line 4286, in from_pretrained
    _adapter_model_path, pretrained_model_name_or_path, adapter_kwargs = maybe_load_adapters(
                                                                         ^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/integrations/peft.py", line 672, in maybe_load_adapters
    resolved_config_file = cached_file(
                           ^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 293, in cached_file
    file = cached_files(path_or_repo_id=path_or_repo_id, filenames=[filename], **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 488, in cached_files
    raise OSError(f"{e}") from e
OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)


*(trang rỗng / OCR không trả về nội dung)*

---

## Trang 6

> ⚠️ **LỖI OCR ở trang này:** OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 437, in cached_files
    hf_hub_download(
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1013, in hf_hub_download
    return _hf_hub_download_to_cache_dir(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1088, in _hf_hub_download_to_cache_dir
    (url_to_download, etag, commit_hash, expected_size, xet_file_data, head_call_error) = _get_metadata_or_catch_error(
                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1707, in _get_metadata_or_catch_error
    metadata = get_hf_file_metadata(
               ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1615, in get_hf_file_metadata
    response = _httpx_follow_relative_redirects_with_backoff(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 719, in _httpx_follow_relative_redirects_with_backoff
    response = http_backoff(
               ^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 596, in http_backoff
    return next(
           ^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 504, in _http_backoff_base
    response = client.request(method=method, url=url, **kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 812, in request
    request = self.build_request(
              ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 367, in build_request
    headers = self._merge_headers(headers)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 430, in _merge_headers
    merged_headers.update(headers)
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 275, in update
    headers = Headers(headers)
              ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 156, in __init__
    bytes_value = _normalize_header_value(v, encoding)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 82, in _normalize_header_value
    return value.encode(encoding or "ascii")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/app/app/ingestion/parser.py", line 257, in _parse_with_qwen_vlm
    pages_markdown[page_num] = _ocr_page_with_qwen(pil_image)
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 212, in _ocr_page_with_qwen
    model, processor = _load_qwen_model()
                       ^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 186, in _load_qwen_model
    model = Qwen3VLForConditionalGeneration.from_pretrained(QWEN_MODEL_ID, **kwargs)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/modeling_utils.py", line 4286, in from_pretrained
    _adapter_model_path, pretrained_model_name_or_path, adapter_kwargs = maybe_load_adapters(
                                                                         ^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/integrations/peft.py", line 672, in maybe_load_adapters
    resolved_config_file = cached_file(
                           ^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 293, in cached_file
    file = cached_files(path_or_repo_id=path_or_repo_id, filenames=[filename], **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 488, in cached_files
    raise OSError(f"{e}") from e
OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)


*(trang rỗng / OCR không trả về nội dung)*

---

## Trang 7

> ⚠️ **LỖI OCR ở trang này:** OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 437, in cached_files
    hf_hub_download(
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1013, in hf_hub_download
    return _hf_hub_download_to_cache_dir(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1088, in _hf_hub_download_to_cache_dir
    (url_to_download, etag, commit_hash, expected_size, xet_file_data, head_call_error) = _get_metadata_or_catch_error(
                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1707, in _get_metadata_or_catch_error
    metadata = get_hf_file_metadata(
               ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1615, in get_hf_file_metadata
    response = _httpx_follow_relative_redirects_with_backoff(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 719, in _httpx_follow_relative_redirects_with_backoff
    response = http_backoff(
               ^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 596, in http_backoff
    return next(
           ^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 504, in _http_backoff_base
    response = client.request(method=method, url=url, **kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 812, in request
    request = self.build_request(
              ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 367, in build_request
    headers = self._merge_headers(headers)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 430, in _merge_headers
    merged_headers.update(headers)
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 275, in update
    headers = Headers(headers)
              ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 156, in __init__
    bytes_value = _normalize_header_value(v, encoding)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 82, in _normalize_header_value
    return value.encode(encoding or "ascii")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/app/app/ingestion/parser.py", line 257, in _parse_with_qwen_vlm
    pages_markdown[page_num] = _ocr_page_with_qwen(pil_image)
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 212, in _ocr_page_with_qwen
    model, processor = _load_qwen_model()
                       ^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 186, in _load_qwen_model
    model = Qwen3VLForConditionalGeneration.from_pretrained(QWEN_MODEL_ID, **kwargs)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/modeling_utils.py", line 4286, in from_pretrained
    _adapter_model_path, pretrained_model_name_or_path, adapter_kwargs = maybe_load_adapters(
                                                                         ^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/integrations/peft.py", line 672, in maybe_load_adapters
    resolved_config_file = cached_file(
                           ^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 293, in cached_file
    file = cached_files(path_or_repo_id=path_or_repo_id, filenames=[filename], **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 488, in cached_files
    raise OSError(f"{e}") from e
OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)


*(trang rỗng / OCR không trả về nội dung)*

---

## Trang 8

> ⚠️ **LỖI OCR ở trang này:** OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 437, in cached_files
    hf_hub_download(
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1013, in hf_hub_download
    return _hf_hub_download_to_cache_dir(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1088, in _hf_hub_download_to_cache_dir
    (url_to_download, etag, commit_hash, expected_size, xet_file_data, head_call_error) = _get_metadata_or_catch_error(
                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1707, in _get_metadata_or_catch_error
    metadata = get_hf_file_metadata(
               ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1615, in get_hf_file_metadata
    response = _httpx_follow_relative_redirects_with_backoff(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 719, in _httpx_follow_relative_redirects_with_backoff
    response = http_backoff(
               ^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 596, in http_backoff
    return next(
           ^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 504, in _http_backoff_base
    response = client.request(method=method, url=url, **kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 812, in request
    request = self.build_request(
              ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 367, in build_request
    headers = self._merge_headers(headers)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 430, in _merge_headers
    merged_headers.update(headers)
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 275, in update
    headers = Headers(headers)
              ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 156, in __init__
    bytes_value = _normalize_header_value(v, encoding)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 82, in _normalize_header_value
    return value.encode(encoding or "ascii")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/app/app/ingestion/parser.py", line 257, in _parse_with_qwen_vlm
    pages_markdown[page_num] = _ocr_page_with_qwen(pil_image)
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 212, in _ocr_page_with_qwen
    model, processor = _load_qwen_model()
                       ^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 186, in _load_qwen_model
    model = Qwen3VLForConditionalGeneration.from_pretrained(QWEN_MODEL_ID, **kwargs)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/modeling_utils.py", line 4286, in from_pretrained
    _adapter_model_path, pretrained_model_name_or_path, adapter_kwargs = maybe_load_adapters(
                                                                         ^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/integrations/peft.py", line 672, in maybe_load_adapters
    resolved_config_file = cached_file(
                           ^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 293, in cached_file
    file = cached_files(path_or_repo_id=path_or_repo_id, filenames=[filename], **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 488, in cached_files
    raise OSError(f"{e}") from e
OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)


*(trang rỗng / OCR không trả về nội dung)*

---

## Trang 9

> ⚠️ **LỖI OCR ở trang này:** OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 437, in cached_files
    hf_hub_download(
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1013, in hf_hub_download
    return _hf_hub_download_to_cache_dir(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1088, in _hf_hub_download_to_cache_dir
    (url_to_download, etag, commit_hash, expected_size, xet_file_data, head_call_error) = _get_metadata_or_catch_error(
                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1707, in _get_metadata_or_catch_error
    metadata = get_hf_file_metadata(
               ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1615, in get_hf_file_metadata
    response = _httpx_follow_relative_redirects_with_backoff(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 719, in _httpx_follow_relative_redirects_with_backoff
    response = http_backoff(
               ^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 596, in http_backoff
    return next(
           ^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 504, in _http_backoff_base
    response = client.request(method=method, url=url, **kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 812, in request
    request = self.build_request(
              ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 367, in build_request
    headers = self._merge_headers(headers)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 430, in _merge_headers
    merged_headers.update(headers)
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 275, in update
    headers = Headers(headers)
              ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 156, in __init__
    bytes_value = _normalize_header_value(v, encoding)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 82, in _normalize_header_value
    return value.encode(encoding or "ascii")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/app/app/ingestion/parser.py", line 257, in _parse_with_qwen_vlm
    pages_markdown[page_num] = _ocr_page_with_qwen(pil_image)
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 212, in _ocr_page_with_qwen
    model, processor = _load_qwen_model()
                       ^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 186, in _load_qwen_model
    model = Qwen3VLForConditionalGeneration.from_pretrained(QWEN_MODEL_ID, **kwargs)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/modeling_utils.py", line 4286, in from_pretrained
    _adapter_model_path, pretrained_model_name_or_path, adapter_kwargs = maybe_load_adapters(
                                                                         ^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/integrations/peft.py", line 672, in maybe_load_adapters
    resolved_config_file = cached_file(
                           ^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 293, in cached_file
    file = cached_files(path_or_repo_id=path_or_repo_id, filenames=[filename], **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 488, in cached_files
    raise OSError(f"{e}") from e
OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)


*(trang rỗng / OCR không trả về nội dung)*

---

## Trang 10

> ⚠️ **LỖI OCR ở trang này:** OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 437, in cached_files
    hf_hub_download(
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1013, in hf_hub_download
    return _hf_hub_download_to_cache_dir(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1088, in _hf_hub_download_to_cache_dir
    (url_to_download, etag, commit_hash, expected_size, xet_file_data, head_call_error) = _get_metadata_or_catch_error(
                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1707, in _get_metadata_or_catch_error
    metadata = get_hf_file_metadata(
               ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1615, in get_hf_file_metadata
    response = _httpx_follow_relative_redirects_with_backoff(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 719, in _httpx_follow_relative_redirects_with_backoff
    response = http_backoff(
               ^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 596, in http_backoff
    return next(
           ^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 504, in _http_backoff_base
    response = client.request(method=method, url=url, **kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 812, in request
    request = self.build_request(
              ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 367, in build_request
    headers = self._merge_headers(headers)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 430, in _merge_headers
    merged_headers.update(headers)
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 275, in update
    headers = Headers(headers)
              ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 156, in __init__
    bytes_value = _normalize_header_value(v, encoding)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 82, in _normalize_header_value
    return value.encode(encoding or "ascii")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/app/app/ingestion/parser.py", line 257, in _parse_with_qwen_vlm
    pages_markdown[page_num] = _ocr_page_with_qwen(pil_image)
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 212, in _ocr_page_with_qwen
    model, processor = _load_qwen_model()
                       ^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 186, in _load_qwen_model
    model = Qwen3VLForConditionalGeneration.from_pretrained(QWEN_MODEL_ID, **kwargs)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/modeling_utils.py", line 4286, in from_pretrained
    _adapter_model_path, pretrained_model_name_or_path, adapter_kwargs = maybe_load_adapters(
                                                                         ^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/integrations/peft.py", line 672, in maybe_load_adapters
    resolved_config_file = cached_file(
                           ^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 293, in cached_file
    file = cached_files(path_or_repo_id=path_or_repo_id, filenames=[filename], **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 488, in cached_files
    raise OSError(f"{e}") from e
OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)


*(trang rỗng / OCR không trả về nội dung)*

---

## Trang 11

> ⚠️ **LỖI OCR ở trang này:** OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 437, in cached_files
    hf_hub_download(
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1013, in hf_hub_download
    return _hf_hub_download_to_cache_dir(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1088, in _hf_hub_download_to_cache_dir
    (url_to_download, etag, commit_hash, expected_size, xet_file_data, head_call_error) = _get_metadata_or_catch_error(
                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1707, in _get_metadata_or_catch_error
    metadata = get_hf_file_metadata(
               ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1615, in get_hf_file_metadata
    response = _httpx_follow_relative_redirects_with_backoff(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 719, in _httpx_follow_relative_redirects_with_backoff
    response = http_backoff(
               ^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 596, in http_backoff
    return next(
           ^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 504, in _http_backoff_base
    response = client.request(method=method, url=url, **kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 812, in request
    request = self.build_request(
              ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 367, in build_request
    headers = self._merge_headers(headers)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 430, in _merge_headers
    merged_headers.update(headers)
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 275, in update
    headers = Headers(headers)
              ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 156, in __init__
    bytes_value = _normalize_header_value(v, encoding)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 82, in _normalize_header_value
    return value.encode(encoding or "ascii")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/app/app/ingestion/parser.py", line 257, in _parse_with_qwen_vlm
    pages_markdown[page_num] = _ocr_page_with_qwen(pil_image)
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 212, in _ocr_page_with_qwen
    model, processor = _load_qwen_model()
                       ^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 186, in _load_qwen_model
    model = Qwen3VLForConditionalGeneration.from_pretrained(QWEN_MODEL_ID, **kwargs)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/modeling_utils.py", line 4286, in from_pretrained
    _adapter_model_path, pretrained_model_name_or_path, adapter_kwargs = maybe_load_adapters(
                                                                         ^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/integrations/peft.py", line 672, in maybe_load_adapters
    resolved_config_file = cached_file(
                           ^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 293, in cached_file
    file = cached_files(path_or_repo_id=path_or_repo_id, filenames=[filename], **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 488, in cached_files
    raise OSError(f"{e}") from e
OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)


*(trang rỗng / OCR không trả về nội dung)*

---

## Trang 12

> ⚠️ **LỖI OCR ở trang này:** OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 437, in cached_files
    hf_hub_download(
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1013, in hf_hub_download
    return _hf_hub_download_to_cache_dir(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1088, in _hf_hub_download_to_cache_dir
    (url_to_download, etag, commit_hash, expected_size, xet_file_data, head_call_error) = _get_metadata_or_catch_error(
                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1707, in _get_metadata_or_catch_error
    metadata = get_hf_file_metadata(
               ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1615, in get_hf_file_metadata
    response = _httpx_follow_relative_redirects_with_backoff(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 719, in _httpx_follow_relative_redirects_with_backoff
    response = http_backoff(
               ^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 596, in http_backoff
    return next(
           ^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 504, in _http_backoff_base
    response = client.request(method=method, url=url, **kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 812, in request
    request = self.build_request(
              ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 367, in build_request
    headers = self._merge_headers(headers)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 430, in _merge_headers
    merged_headers.update(headers)
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 275, in update
    headers = Headers(headers)
              ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 156, in __init__
    bytes_value = _normalize_header_value(v, encoding)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 82, in _normalize_header_value
    return value.encode(encoding or "ascii")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/app/app/ingestion/parser.py", line 257, in _parse_with_qwen_vlm
    pages_markdown[page_num] = _ocr_page_with_qwen(pil_image)
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 212, in _ocr_page_with_qwen
    model, processor = _load_qwen_model()
                       ^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 186, in _load_qwen_model
    model = Qwen3VLForConditionalGeneration.from_pretrained(QWEN_MODEL_ID, **kwargs)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/modeling_utils.py", line 4286, in from_pretrained
    _adapter_model_path, pretrained_model_name_or_path, adapter_kwargs = maybe_load_adapters(
                                                                         ^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/integrations/peft.py", line 672, in maybe_load_adapters
    resolved_config_file = cached_file(
                           ^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 293, in cached_file
    file = cached_files(path_or_repo_id=path_or_repo_id, filenames=[filename], **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 488, in cached_files
    raise OSError(f"{e}") from e
OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)


*(trang rỗng / OCR không trả về nội dung)*

---

## Trang 13

> ⚠️ **LỖI OCR ở trang này:** OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 437, in cached_files
    hf_hub_download(
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1013, in hf_hub_download
    return _hf_hub_download_to_cache_dir(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1088, in _hf_hub_download_to_cache_dir
    (url_to_download, etag, commit_hash, expected_size, xet_file_data, head_call_error) = _get_metadata_or_catch_error(
                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1707, in _get_metadata_or_catch_error
    metadata = get_hf_file_metadata(
               ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1615, in get_hf_file_metadata
    response = _httpx_follow_relative_redirects_with_backoff(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 719, in _httpx_follow_relative_redirects_with_backoff
    response = http_backoff(
               ^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 596, in http_backoff
    return next(
           ^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 504, in _http_backoff_base
    response = client.request(method=method, url=url, **kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 812, in request
    request = self.build_request(
              ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 367, in build_request
    headers = self._merge_headers(headers)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 430, in _merge_headers
    merged_headers.update(headers)
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 275, in update
    headers = Headers(headers)
              ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 156, in __init__
    bytes_value = _normalize_header_value(v, encoding)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 82, in _normalize_header_value
    return value.encode(encoding or "ascii")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/app/app/ingestion/parser.py", line 257, in _parse_with_qwen_vlm
    pages_markdown[page_num] = _ocr_page_with_qwen(pil_image)
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 212, in _ocr_page_with_qwen
    model, processor = _load_qwen_model()
                       ^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 186, in _load_qwen_model
    model = Qwen3VLForConditionalGeneration.from_pretrained(QWEN_MODEL_ID, **kwargs)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/modeling_utils.py", line 4286, in from_pretrained
    _adapter_model_path, pretrained_model_name_or_path, adapter_kwargs = maybe_load_adapters(
                                                                         ^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/integrations/peft.py", line 672, in maybe_load_adapters
    resolved_config_file = cached_file(
                           ^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 293, in cached_file
    file = cached_files(path_or_repo_id=path_or_repo_id, filenames=[filename], **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 488, in cached_files
    raise OSError(f"{e}") from e
OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)


*(trang rỗng / OCR không trả về nội dung)*

---

## Trang 14

> ⚠️ **LỖI OCR ở trang này:** OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 437, in cached_files
    hf_hub_download(
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1013, in hf_hub_download
    return _hf_hub_download_to_cache_dir(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1088, in _hf_hub_download_to_cache_dir
    (url_to_download, etag, commit_hash, expected_size, xet_file_data, head_call_error) = _get_metadata_or_catch_error(
                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1707, in _get_metadata_or_catch_error
    metadata = get_hf_file_metadata(
               ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1615, in get_hf_file_metadata
    response = _httpx_follow_relative_redirects_with_backoff(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 719, in _httpx_follow_relative_redirects_with_backoff
    response = http_backoff(
               ^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 596, in http_backoff
    return next(
           ^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 504, in _http_backoff_base
    response = client.request(method=method, url=url, **kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 812, in request
    request = self.build_request(
              ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 367, in build_request
    headers = self._merge_headers(headers)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 430, in _merge_headers
    merged_headers.update(headers)
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 275, in update
    headers = Headers(headers)
              ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 156, in __init__
    bytes_value = _normalize_header_value(v, encoding)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 82, in _normalize_header_value
    return value.encode(encoding or "ascii")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/app/app/ingestion/parser.py", line 257, in _parse_with_qwen_vlm
    pages_markdown[page_num] = _ocr_page_with_qwen(pil_image)
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 212, in _ocr_page_with_qwen
    model, processor = _load_qwen_model()
                       ^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 186, in _load_qwen_model
    model = Qwen3VLForConditionalGeneration.from_pretrained(QWEN_MODEL_ID, **kwargs)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/modeling_utils.py", line 4286, in from_pretrained
    _adapter_model_path, pretrained_model_name_or_path, adapter_kwargs = maybe_load_adapters(
                                                                         ^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/integrations/peft.py", line 672, in maybe_load_adapters
    resolved_config_file = cached_file(
                           ^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 293, in cached_file
    file = cached_files(path_or_repo_id=path_or_repo_id, filenames=[filename], **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 488, in cached_files
    raise OSError(f"{e}") from e
OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)


*(trang rỗng / OCR không trả về nội dung)*

---

## Trang 15

> ⚠️ **LỖI OCR ở trang này:** OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 437, in cached_files
    hf_hub_download(
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1013, in hf_hub_download
    return _hf_hub_download_to_cache_dir(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1088, in _hf_hub_download_to_cache_dir
    (url_to_download, etag, commit_hash, expected_size, xet_file_data, head_call_error) = _get_metadata_or_catch_error(
                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1707, in _get_metadata_or_catch_error
    metadata = get_hf_file_metadata(
               ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1615, in get_hf_file_metadata
    response = _httpx_follow_relative_redirects_with_backoff(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 719, in _httpx_follow_relative_redirects_with_backoff
    response = http_backoff(
               ^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 596, in http_backoff
    return next(
           ^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 504, in _http_backoff_base
    response = client.request(method=method, url=url, **kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 812, in request
    request = self.build_request(
              ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 367, in build_request
    headers = self._merge_headers(headers)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 430, in _merge_headers
    merged_headers.update(headers)
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 275, in update
    headers = Headers(headers)
              ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 156, in __init__
    bytes_value = _normalize_header_value(v, encoding)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 82, in _normalize_header_value
    return value.encode(encoding or "ascii")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/app/app/ingestion/parser.py", line 257, in _parse_with_qwen_vlm
    pages_markdown[page_num] = _ocr_page_with_qwen(pil_image)
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 212, in _ocr_page_with_qwen
    model, processor = _load_qwen_model()
                       ^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 186, in _load_qwen_model
    model = Qwen3VLForConditionalGeneration.from_pretrained(QWEN_MODEL_ID, **kwargs)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/modeling_utils.py", line 4286, in from_pretrained
    _adapter_model_path, pretrained_model_name_or_path, adapter_kwargs = maybe_load_adapters(
                                                                         ^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/integrations/peft.py", line 672, in maybe_load_adapters
    resolved_config_file = cached_file(
                           ^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 293, in cached_file
    file = cached_files(path_or_repo_id=path_or_repo_id, filenames=[filename], **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 488, in cached_files
    raise OSError(f"{e}") from e
OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)


*(trang rỗng / OCR không trả về nội dung)*

---

## Trang 16

> ⚠️ **LỖI OCR ở trang này:** OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 437, in cached_files
    hf_hub_download(
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1013, in hf_hub_download
    return _hf_hub_download_to_cache_dir(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1088, in _hf_hub_download_to_cache_dir
    (url_to_download, etag, commit_hash, expected_size, xet_file_data, head_call_error) = _get_metadata_or_catch_error(
                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1707, in _get_metadata_or_catch_error
    metadata = get_hf_file_metadata(
               ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1615, in get_hf_file_metadata
    response = _httpx_follow_relative_redirects_with_backoff(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 719, in _httpx_follow_relative_redirects_with_backoff
    response = http_backoff(
               ^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 596, in http_backoff
    return next(
           ^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 504, in _http_backoff_base
    response = client.request(method=method, url=url, **kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 812, in request
    request = self.build_request(
              ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 367, in build_request
    headers = self._merge_headers(headers)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 430, in _merge_headers
    merged_headers.update(headers)
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 275, in update
    headers = Headers(headers)
              ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 156, in __init__
    bytes_value = _normalize_header_value(v, encoding)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 82, in _normalize_header_value
    return value.encode(encoding or "ascii")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/app/app/ingestion/parser.py", line 257, in _parse_with_qwen_vlm
    pages_markdown[page_num] = _ocr_page_with_qwen(pil_image)
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 212, in _ocr_page_with_qwen
    model, processor = _load_qwen_model()
                       ^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 186, in _load_qwen_model
    model = Qwen3VLForConditionalGeneration.from_pretrained(QWEN_MODEL_ID, **kwargs)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/modeling_utils.py", line 4286, in from_pretrained
    _adapter_model_path, pretrained_model_name_or_path, adapter_kwargs = maybe_load_adapters(
                                                                         ^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/integrations/peft.py", line 672, in maybe_load_adapters
    resolved_config_file = cached_file(
                           ^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 293, in cached_file
    file = cached_files(path_or_repo_id=path_or_repo_id, filenames=[filename], **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 488, in cached_files
    raise OSError(f"{e}") from e
OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)


*(trang rỗng / OCR không trả về nội dung)*

---

## Trang 17

> ⚠️ **LỖI OCR ở trang này:** OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 437, in cached_files
    hf_hub_download(
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1013, in hf_hub_download
    return _hf_hub_download_to_cache_dir(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1088, in _hf_hub_download_to_cache_dir
    (url_to_download, etag, commit_hash, expected_size, xet_file_data, head_call_error) = _get_metadata_or_catch_error(
                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1707, in _get_metadata_or_catch_error
    metadata = get_hf_file_metadata(
               ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1615, in get_hf_file_metadata
    response = _httpx_follow_relative_redirects_with_backoff(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 719, in _httpx_follow_relative_redirects_with_backoff
    response = http_backoff(
               ^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 596, in http_backoff
    return next(
           ^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 504, in _http_backoff_base
    response = client.request(method=method, url=url, **kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 812, in request
    request = self.build_request(
              ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 367, in build_request
    headers = self._merge_headers(headers)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 430, in _merge_headers
    merged_headers.update(headers)
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 275, in update
    headers = Headers(headers)
              ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 156, in __init__
    bytes_value = _normalize_header_value(v, encoding)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 82, in _normalize_header_value
    return value.encode(encoding or "ascii")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/app/app/ingestion/parser.py", line 257, in _parse_with_qwen_vlm
    pages_markdown[page_num] = _ocr_page_with_qwen(pil_image)
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 212, in _ocr_page_with_qwen
    model, processor = _load_qwen_model()
                       ^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 186, in _load_qwen_model
    model = Qwen3VLForConditionalGeneration.from_pretrained(QWEN_MODEL_ID, **kwargs)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/modeling_utils.py", line 4286, in from_pretrained
    _adapter_model_path, pretrained_model_name_or_path, adapter_kwargs = maybe_load_adapters(
                                                                         ^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/integrations/peft.py", line 672, in maybe_load_adapters
    resolved_config_file = cached_file(
                           ^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 293, in cached_file
    file = cached_files(path_or_repo_id=path_or_repo_id, filenames=[filename], **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 488, in cached_files
    raise OSError(f"{e}") from e
OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)


*(trang rỗng / OCR không trả về nội dung)*

---

## Trang 18

> ⚠️ **LỖI OCR ở trang này:** OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 437, in cached_files
    hf_hub_download(
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1013, in hf_hub_download
    return _hf_hub_download_to_cache_dir(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1088, in _hf_hub_download_to_cache_dir
    (url_to_download, etag, commit_hash, expected_size, xet_file_data, head_call_error) = _get_metadata_or_catch_error(
                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1707, in _get_metadata_or_catch_error
    metadata = get_hf_file_metadata(
               ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1615, in get_hf_file_metadata
    response = _httpx_follow_relative_redirects_with_backoff(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 719, in _httpx_follow_relative_redirects_with_backoff
    response = http_backoff(
               ^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 596, in http_backoff
    return next(
           ^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 504, in _http_backoff_base
    response = client.request(method=method, url=url, **kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 812, in request
    request = self.build_request(
              ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 367, in build_request
    headers = self._merge_headers(headers)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 430, in _merge_headers
    merged_headers.update(headers)
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 275, in update
    headers = Headers(headers)
              ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 156, in __init__
    bytes_value = _normalize_header_value(v, encoding)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 82, in _normalize_header_value
    return value.encode(encoding or "ascii")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/app/app/ingestion/parser.py", line 257, in _parse_with_qwen_vlm
    pages_markdown[page_num] = _ocr_page_with_qwen(pil_image)
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 212, in _ocr_page_with_qwen
    model, processor = _load_qwen_model()
                       ^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 186, in _load_qwen_model
    model = Qwen3VLForConditionalGeneration.from_pretrained(QWEN_MODEL_ID, **kwargs)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/modeling_utils.py", line 4286, in from_pretrained
    _adapter_model_path, pretrained_model_name_or_path, adapter_kwargs = maybe_load_adapters(
                                                                         ^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/integrations/peft.py", line 672, in maybe_load_adapters
    resolved_config_file = cached_file(
                           ^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 293, in cached_file
    file = cached_files(path_or_repo_id=path_or_repo_id, filenames=[filename], **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 488, in cached_files
    raise OSError(f"{e}") from e
OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)


*(trang rỗng / OCR không trả về nội dung)*

---

## Trang 19

> ⚠️ **LỖI OCR ở trang này:** OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 437, in cached_files
    hf_hub_download(
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1013, in hf_hub_download
    return _hf_hub_download_to_cache_dir(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1088, in _hf_hub_download_to_cache_dir
    (url_to_download, etag, commit_hash, expected_size, xet_file_data, head_call_error) = _get_metadata_or_catch_error(
                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1707, in _get_metadata_or_catch_error
    metadata = get_hf_file_metadata(
               ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1615, in get_hf_file_metadata
    response = _httpx_follow_relative_redirects_with_backoff(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 719, in _httpx_follow_relative_redirects_with_backoff
    response = http_backoff(
               ^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 596, in http_backoff
    return next(
           ^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 504, in _http_backoff_base
    response = client.request(method=method, url=url, **kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 812, in request
    request = self.build_request(
              ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 367, in build_request
    headers = self._merge_headers(headers)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 430, in _merge_headers
    merged_headers.update(headers)
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 275, in update
    headers = Headers(headers)
              ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 156, in __init__
    bytes_value = _normalize_header_value(v, encoding)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 82, in _normalize_header_value
    return value.encode(encoding or "ascii")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/app/app/ingestion/parser.py", line 257, in _parse_with_qwen_vlm
    pages_markdown[page_num] = _ocr_page_with_qwen(pil_image)
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 212, in _ocr_page_with_qwen
    model, processor = _load_qwen_model()
                       ^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 186, in _load_qwen_model
    model = Qwen3VLForConditionalGeneration.from_pretrained(QWEN_MODEL_ID, **kwargs)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/modeling_utils.py", line 4286, in from_pretrained
    _adapter_model_path, pretrained_model_name_or_path, adapter_kwargs = maybe_load_adapters(
                                                                         ^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/integrations/peft.py", line 672, in maybe_load_adapters
    resolved_config_file = cached_file(
                           ^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 293, in cached_file
    file = cached_files(path_or_repo_id=path_or_repo_id, filenames=[filename], **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 488, in cached_files
    raise OSError(f"{e}") from e
OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)


*(trang rỗng / OCR không trả về nội dung)*

---

## Trang 20

> ⚠️ **LỖI OCR ở trang này:** OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 437, in cached_files
    hf_hub_download(
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1013, in hf_hub_download
    return _hf_hub_download_to_cache_dir(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1088, in _hf_hub_download_to_cache_dir
    (url_to_download, etag, commit_hash, expected_size, xet_file_data, head_call_error) = _get_metadata_or_catch_error(
                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1707, in _get_metadata_or_catch_error
    metadata = get_hf_file_metadata(
               ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1615, in get_hf_file_metadata
    response = _httpx_follow_relative_redirects_with_backoff(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 719, in _httpx_follow_relative_redirects_with_backoff
    response = http_backoff(
               ^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 596, in http_backoff
    return next(
           ^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 504, in _http_backoff_base
    response = client.request(method=method, url=url, **kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 812, in request
    request = self.build_request(
              ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 367, in build_request
    headers = self._merge_headers(headers)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 430, in _merge_headers
    merged_headers.update(headers)
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 275, in update
    headers = Headers(headers)
              ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 156, in __init__
    bytes_value = _normalize_header_value(v, encoding)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 82, in _normalize_header_value
    return value.encode(encoding or "ascii")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/app/app/ingestion/parser.py", line 257, in _parse_with_qwen_vlm
    pages_markdown[page_num] = _ocr_page_with_qwen(pil_image)
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 212, in _ocr_page_with_qwen
    model, processor = _load_qwen_model()
                       ^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 186, in _load_qwen_model
    model = Qwen3VLForConditionalGeneration.from_pretrained(QWEN_MODEL_ID, **kwargs)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/modeling_utils.py", line 4286, in from_pretrained
    _adapter_model_path, pretrained_model_name_or_path, adapter_kwargs = maybe_load_adapters(
                                                                         ^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/integrations/peft.py", line 672, in maybe_load_adapters
    resolved_config_file = cached_file(
                           ^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 293, in cached_file
    file = cached_files(path_or_repo_id=path_or_repo_id, filenames=[filename], **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 488, in cached_files
    raise OSError(f"{e}") from e
OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)


*(trang rỗng / OCR không trả về nội dung)*

---

## Trang 21

> ⚠️ **LỖI OCR ở trang này:** OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 437, in cached_files
    hf_hub_download(
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1013, in hf_hub_download
    return _hf_hub_download_to_cache_dir(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1088, in _hf_hub_download_to_cache_dir
    (url_to_download, etag, commit_hash, expected_size, xet_file_data, head_call_error) = _get_metadata_or_catch_error(
                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1707, in _get_metadata_or_catch_error
    metadata = get_hf_file_metadata(
               ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1615, in get_hf_file_metadata
    response = _httpx_follow_relative_redirects_with_backoff(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 719, in _httpx_follow_relative_redirects_with_backoff
    response = http_backoff(
               ^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 596, in http_backoff
    return next(
           ^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 504, in _http_backoff_base
    response = client.request(method=method, url=url, **kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 812, in request
    request = self.build_request(
              ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 367, in build_request
    headers = self._merge_headers(headers)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 430, in _merge_headers
    merged_headers.update(headers)
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 275, in update
    headers = Headers(headers)
              ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 156, in __init__
    bytes_value = _normalize_header_value(v, encoding)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 82, in _normalize_header_value
    return value.encode(encoding or "ascii")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/app/app/ingestion/parser.py", line 257, in _parse_with_qwen_vlm
    pages_markdown[page_num] = _ocr_page_with_qwen(pil_image)
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 212, in _ocr_page_with_qwen
    model, processor = _load_qwen_model()
                       ^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 186, in _load_qwen_model
    model = Qwen3VLForConditionalGeneration.from_pretrained(QWEN_MODEL_ID, **kwargs)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/modeling_utils.py", line 4286, in from_pretrained
    _adapter_model_path, pretrained_model_name_or_path, adapter_kwargs = maybe_load_adapters(
                                                                         ^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/integrations/peft.py", line 672, in maybe_load_adapters
    resolved_config_file = cached_file(
                           ^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 293, in cached_file
    file = cached_files(path_or_repo_id=path_or_repo_id, filenames=[filename], **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 488, in cached_files
    raise OSError(f"{e}") from e
OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)


*(trang rỗng / OCR không trả về nội dung)*

---

## Trang 22

> ⚠️ **LỖI OCR ở trang này:** OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 437, in cached_files
    hf_hub_download(
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1013, in hf_hub_download
    return _hf_hub_download_to_cache_dir(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1088, in _hf_hub_download_to_cache_dir
    (url_to_download, etag, commit_hash, expected_size, xet_file_data, head_call_error) = _get_metadata_or_catch_error(
                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1707, in _get_metadata_or_catch_error
    metadata = get_hf_file_metadata(
               ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1615, in get_hf_file_metadata
    response = _httpx_follow_relative_redirects_with_backoff(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 719, in _httpx_follow_relative_redirects_with_backoff
    response = http_backoff(
               ^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 596, in http_backoff
    return next(
           ^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 504, in _http_backoff_base
    response = client.request(method=method, url=url, **kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 812, in request
    request = self.build_request(
              ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 367, in build_request
    headers = self._merge_headers(headers)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 430, in _merge_headers
    merged_headers.update(headers)
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 275, in update
    headers = Headers(headers)
              ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 156, in __init__
    bytes_value = _normalize_header_value(v, encoding)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 82, in _normalize_header_value
    return value.encode(encoding or "ascii")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/app/app/ingestion/parser.py", line 257, in _parse_with_qwen_vlm
    pages_markdown[page_num] = _ocr_page_with_qwen(pil_image)
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 212, in _ocr_page_with_qwen
    model, processor = _load_qwen_model()
                       ^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 186, in _load_qwen_model
    model = Qwen3VLForConditionalGeneration.from_pretrained(QWEN_MODEL_ID, **kwargs)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/modeling_utils.py", line 4286, in from_pretrained
    _adapter_model_path, pretrained_model_name_or_path, adapter_kwargs = maybe_load_adapters(
                                                                         ^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/integrations/peft.py", line 672, in maybe_load_adapters
    resolved_config_file = cached_file(
                           ^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 293, in cached_file
    file = cached_files(path_or_repo_id=path_or_repo_id, filenames=[filename], **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 488, in cached_files
    raise OSError(f"{e}") from e
OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)


*(trang rỗng / OCR không trả về nội dung)*

---

## Trang 23

> ⚠️ **LỖI OCR ở trang này:** OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 437, in cached_files
    hf_hub_download(
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1013, in hf_hub_download
    return _hf_hub_download_to_cache_dir(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1088, in _hf_hub_download_to_cache_dir
    (url_to_download, etag, commit_hash, expected_size, xet_file_data, head_call_error) = _get_metadata_or_catch_error(
                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1707, in _get_metadata_or_catch_error
    metadata = get_hf_file_metadata(
               ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1615, in get_hf_file_metadata
    response = _httpx_follow_relative_redirects_with_backoff(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 719, in _httpx_follow_relative_redirects_with_backoff
    response = http_backoff(
               ^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 596, in http_backoff
    return next(
           ^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 504, in _http_backoff_base
    response = client.request(method=method, url=url, **kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 812, in request
    request = self.build_request(
              ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 367, in build_request
    headers = self._merge_headers(headers)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 430, in _merge_headers
    merged_headers.update(headers)
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 275, in update
    headers = Headers(headers)
              ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 156, in __init__
    bytes_value = _normalize_header_value(v, encoding)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 82, in _normalize_header_value
    return value.encode(encoding or "ascii")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/app/app/ingestion/parser.py", line 257, in _parse_with_qwen_vlm
    pages_markdown[page_num] = _ocr_page_with_qwen(pil_image)
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 212, in _ocr_page_with_qwen
    model, processor = _load_qwen_model()
                       ^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 186, in _load_qwen_model
    model = Qwen3VLForConditionalGeneration.from_pretrained(QWEN_MODEL_ID, **kwargs)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/modeling_utils.py", line 4286, in from_pretrained
    _adapter_model_path, pretrained_model_name_or_path, adapter_kwargs = maybe_load_adapters(
                                                                         ^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/integrations/peft.py", line 672, in maybe_load_adapters
    resolved_config_file = cached_file(
                           ^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 293, in cached_file
    file = cached_files(path_or_repo_id=path_or_repo_id, filenames=[filename], **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 488, in cached_files
    raise OSError(f"{e}") from e
OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)


*(trang rỗng / OCR không trả về nội dung)*

---

## Trang 24

> ⚠️ **LỖI OCR ở trang này:** OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 437, in cached_files
    hf_hub_download(
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1013, in hf_hub_download
    return _hf_hub_download_to_cache_dir(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1088, in _hf_hub_download_to_cache_dir
    (url_to_download, etag, commit_hash, expected_size, xet_file_data, head_call_error) = _get_metadata_or_catch_error(
                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1707, in _get_metadata_or_catch_error
    metadata = get_hf_file_metadata(
               ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1615, in get_hf_file_metadata
    response = _httpx_follow_relative_redirects_with_backoff(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 719, in _httpx_follow_relative_redirects_with_backoff
    response = http_backoff(
               ^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 596, in http_backoff
    return next(
           ^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 504, in _http_backoff_base
    response = client.request(method=method, url=url, **kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 812, in request
    request = self.build_request(
              ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 367, in build_request
    headers = self._merge_headers(headers)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 430, in _merge_headers
    merged_headers.update(headers)
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 275, in update
    headers = Headers(headers)
              ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 156, in __init__
    bytes_value = _normalize_header_value(v, encoding)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 82, in _normalize_header_value
    return value.encode(encoding or "ascii")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/app/app/ingestion/parser.py", line 257, in _parse_with_qwen_vlm
    pages_markdown[page_num] = _ocr_page_with_qwen(pil_image)
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 212, in _ocr_page_with_qwen
    model, processor = _load_qwen_model()
                       ^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 186, in _load_qwen_model
    model = Qwen3VLForConditionalGeneration.from_pretrained(QWEN_MODEL_ID, **kwargs)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/modeling_utils.py", line 4286, in from_pretrained
    _adapter_model_path, pretrained_model_name_or_path, adapter_kwargs = maybe_load_adapters(
                                                                         ^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/integrations/peft.py", line 672, in maybe_load_adapters
    resolved_config_file = cached_file(
                           ^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 293, in cached_file
    file = cached_files(path_or_repo_id=path_or_repo_id, filenames=[filename], **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 488, in cached_files
    raise OSError(f"{e}") from e
OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)


*(trang rỗng / OCR không trả về nội dung)*

---

## Trang 25

> ⚠️ **LỖI OCR ở trang này:** OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 437, in cached_files
    hf_hub_download(
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1013, in hf_hub_download
    return _hf_hub_download_to_cache_dir(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1088, in _hf_hub_download_to_cache_dir
    (url_to_download, etag, commit_hash, expected_size, xet_file_data, head_call_error) = _get_metadata_or_catch_error(
                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1707, in _get_metadata_or_catch_error
    metadata = get_hf_file_metadata(
               ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1615, in get_hf_file_metadata
    response = _httpx_follow_relative_redirects_with_backoff(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 719, in _httpx_follow_relative_redirects_with_backoff
    response = http_backoff(
               ^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 596, in http_backoff
    return next(
           ^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 504, in _http_backoff_base
    response = client.request(method=method, url=url, **kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 812, in request
    request = self.build_request(
              ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 367, in build_request
    headers = self._merge_headers(headers)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 430, in _merge_headers
    merged_headers.update(headers)
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 275, in update
    headers = Headers(headers)
              ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 156, in __init__
    bytes_value = _normalize_header_value(v, encoding)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 82, in _normalize_header_value
    return value.encode(encoding or "ascii")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/app/app/ingestion/parser.py", line 257, in _parse_with_qwen_vlm
    pages_markdown[page_num] = _ocr_page_with_qwen(pil_image)
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 212, in _ocr_page_with_qwen
    model, processor = _load_qwen_model()
                       ^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 186, in _load_qwen_model
    model = Qwen3VLForConditionalGeneration.from_pretrained(QWEN_MODEL_ID, **kwargs)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/modeling_utils.py", line 4286, in from_pretrained
    _adapter_model_path, pretrained_model_name_or_path, adapter_kwargs = maybe_load_adapters(
                                                                         ^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/integrations/peft.py", line 672, in maybe_load_adapters
    resolved_config_file = cached_file(
                           ^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 293, in cached_file
    file = cached_files(path_or_repo_id=path_or_repo_id, filenames=[filename], **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 488, in cached_files
    raise OSError(f"{e}") from e
OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)


*(trang rỗng / OCR không trả về nội dung)*

---

## Trang 26

> ⚠️ **LỖI OCR ở trang này:** OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 437, in cached_files
    hf_hub_download(
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1013, in hf_hub_download
    return _hf_hub_download_to_cache_dir(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1088, in _hf_hub_download_to_cache_dir
    (url_to_download, etag, commit_hash, expected_size, xet_file_data, head_call_error) = _get_metadata_or_catch_error(
                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1707, in _get_metadata_or_catch_error
    metadata = get_hf_file_metadata(
               ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1615, in get_hf_file_metadata
    response = _httpx_follow_relative_redirects_with_backoff(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 719, in _httpx_follow_relative_redirects_with_backoff
    response = http_backoff(
               ^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 596, in http_backoff
    return next(
           ^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 504, in _http_backoff_base
    response = client.request(method=method, url=url, **kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 812, in request
    request = self.build_request(
              ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 367, in build_request
    headers = self._merge_headers(headers)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 430, in _merge_headers
    merged_headers.update(headers)
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 275, in update
    headers = Headers(headers)
              ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 156, in __init__
    bytes_value = _normalize_header_value(v, encoding)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 82, in _normalize_header_value
    return value.encode(encoding or "ascii")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/app/app/ingestion/parser.py", line 257, in _parse_with_qwen_vlm
    pages_markdown[page_num] = _ocr_page_with_qwen(pil_image)
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 212, in _ocr_page_with_qwen
    model, processor = _load_qwen_model()
                       ^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 186, in _load_qwen_model
    model = Qwen3VLForConditionalGeneration.from_pretrained(QWEN_MODEL_ID, **kwargs)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/modeling_utils.py", line 4286, in from_pretrained
    _adapter_model_path, pretrained_model_name_or_path, adapter_kwargs = maybe_load_adapters(
                                                                         ^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/integrations/peft.py", line 672, in maybe_load_adapters
    resolved_config_file = cached_file(
                           ^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 293, in cached_file
    file = cached_files(path_or_repo_id=path_or_repo_id, filenames=[filename], **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 488, in cached_files
    raise OSError(f"{e}") from e
OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)


*(trang rỗng / OCR không trả về nội dung)*

---

## Trang 27

> ⚠️ **LỖI OCR ở trang này:** OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 437, in cached_files
    hf_hub_download(
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1013, in hf_hub_download
    return _hf_hub_download_to_cache_dir(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1088, in _hf_hub_download_to_cache_dir
    (url_to_download, etag, commit_hash, expected_size, xet_file_data, head_call_error) = _get_metadata_or_catch_error(
                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1707, in _get_metadata_or_catch_error
    metadata = get_hf_file_metadata(
               ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1615, in get_hf_file_metadata
    response = _httpx_follow_relative_redirects_with_backoff(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 719, in _httpx_follow_relative_redirects_with_backoff
    response = http_backoff(
               ^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 596, in http_backoff
    return next(
           ^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 504, in _http_backoff_base
    response = client.request(method=method, url=url, **kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 812, in request
    request = self.build_request(
              ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 367, in build_request
    headers = self._merge_headers(headers)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 430, in _merge_headers
    merged_headers.update(headers)
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 275, in update
    headers = Headers(headers)
              ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 156, in __init__
    bytes_value = _normalize_header_value(v, encoding)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 82, in _normalize_header_value
    return value.encode(encoding or "ascii")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/app/app/ingestion/parser.py", line 257, in _parse_with_qwen_vlm
    pages_markdown[page_num] = _ocr_page_with_qwen(pil_image)
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 212, in _ocr_page_with_qwen
    model, processor = _load_qwen_model()
                       ^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 186, in _load_qwen_model
    model = Qwen3VLForConditionalGeneration.from_pretrained(QWEN_MODEL_ID, **kwargs)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/modeling_utils.py", line 4286, in from_pretrained
    _adapter_model_path, pretrained_model_name_or_path, adapter_kwargs = maybe_load_adapters(
                                                                         ^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/integrations/peft.py", line 672, in maybe_load_adapters
    resolved_config_file = cached_file(
                           ^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 293, in cached_file
    file = cached_files(path_or_repo_id=path_or_repo_id, filenames=[filename], **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 488, in cached_files
    raise OSError(f"{e}") from e
OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)


*(trang rỗng / OCR không trả về nội dung)*

---

## Trang 28

> ⚠️ **LỖI OCR ở trang này:** OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 437, in cached_files
    hf_hub_download(
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1013, in hf_hub_download
    return _hf_hub_download_to_cache_dir(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1088, in _hf_hub_download_to_cache_dir
    (url_to_download, etag, commit_hash, expected_size, xet_file_data, head_call_error) = _get_metadata_or_catch_error(
                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1707, in _get_metadata_or_catch_error
    metadata = get_hf_file_metadata(
               ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1615, in get_hf_file_metadata
    response = _httpx_follow_relative_redirects_with_backoff(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 719, in _httpx_follow_relative_redirects_with_backoff
    response = http_backoff(
               ^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 596, in http_backoff
    return next(
           ^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 504, in _http_backoff_base
    response = client.request(method=method, url=url, **kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 812, in request
    request = self.build_request(
              ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 367, in build_request
    headers = self._merge_headers(headers)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 430, in _merge_headers
    merged_headers.update(headers)
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 275, in update
    headers = Headers(headers)
              ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 156, in __init__
    bytes_value = _normalize_header_value(v, encoding)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 82, in _normalize_header_value
    return value.encode(encoding or "ascii")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/app/app/ingestion/parser.py", line 257, in _parse_with_qwen_vlm
    pages_markdown[page_num] = _ocr_page_with_qwen(pil_image)
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 212, in _ocr_page_with_qwen
    model, processor = _load_qwen_model()
                       ^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 186, in _load_qwen_model
    model = Qwen3VLForConditionalGeneration.from_pretrained(QWEN_MODEL_ID, **kwargs)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/modeling_utils.py", line 4286, in from_pretrained
    _adapter_model_path, pretrained_model_name_or_path, adapter_kwargs = maybe_load_adapters(
                                                                         ^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/integrations/peft.py", line 672, in maybe_load_adapters
    resolved_config_file = cached_file(
                           ^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 293, in cached_file
    file = cached_files(path_or_repo_id=path_or_repo_id, filenames=[filename], **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 488, in cached_files
    raise OSError(f"{e}") from e
OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)


*(trang rỗng / OCR không trả về nội dung)*

---

## Trang 29

> ⚠️ **LỖI OCR ở trang này:** OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 437, in cached_files
    hf_hub_download(
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1013, in hf_hub_download
    return _hf_hub_download_to_cache_dir(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1088, in _hf_hub_download_to_cache_dir
    (url_to_download, etag, commit_hash, expected_size, xet_file_data, head_call_error) = _get_metadata_or_catch_error(
                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1707, in _get_metadata_or_catch_error
    metadata = get_hf_file_metadata(
               ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1615, in get_hf_file_metadata
    response = _httpx_follow_relative_redirects_with_backoff(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 719, in _httpx_follow_relative_redirects_with_backoff
    response = http_backoff(
               ^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 596, in http_backoff
    return next(
           ^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 504, in _http_backoff_base
    response = client.request(method=method, url=url, **kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 812, in request
    request = self.build_request(
              ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 367, in build_request
    headers = self._merge_headers(headers)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 430, in _merge_headers
    merged_headers.update(headers)
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 275, in update
    headers = Headers(headers)
              ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 156, in __init__
    bytes_value = _normalize_header_value(v, encoding)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 82, in _normalize_header_value
    return value.encode(encoding or "ascii")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/app/app/ingestion/parser.py", line 257, in _parse_with_qwen_vlm
    pages_markdown[page_num] = _ocr_page_with_qwen(pil_image)
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 212, in _ocr_page_with_qwen
    model, processor = _load_qwen_model()
                       ^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 186, in _load_qwen_model
    model = Qwen3VLForConditionalGeneration.from_pretrained(QWEN_MODEL_ID, **kwargs)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/modeling_utils.py", line 4286, in from_pretrained
    _adapter_model_path, pretrained_model_name_or_path, adapter_kwargs = maybe_load_adapters(
                                                                         ^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/integrations/peft.py", line 672, in maybe_load_adapters
    resolved_config_file = cached_file(
                           ^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 293, in cached_file
    file = cached_files(path_or_repo_id=path_or_repo_id, filenames=[filename], **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 488, in cached_files
    raise OSError(f"{e}") from e
OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)


*(trang rỗng / OCR không trả về nội dung)*

---

## Trang 30

> ⚠️ **LỖI OCR ở trang này:** OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 437, in cached_files
    hf_hub_download(
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1013, in hf_hub_download
    return _hf_hub_download_to_cache_dir(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1088, in _hf_hub_download_to_cache_dir
    (url_to_download, etag, commit_hash, expected_size, xet_file_data, head_call_error) = _get_metadata_or_catch_error(
                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1707, in _get_metadata_or_catch_error
    metadata = get_hf_file_metadata(
               ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1615, in get_hf_file_metadata
    response = _httpx_follow_relative_redirects_with_backoff(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 719, in _httpx_follow_relative_redirects_with_backoff
    response = http_backoff(
               ^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 596, in http_backoff
    return next(
           ^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 504, in _http_backoff_base
    response = client.request(method=method, url=url, **kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 812, in request
    request = self.build_request(
              ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 367, in build_request
    headers = self._merge_headers(headers)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 430, in _merge_headers
    merged_headers.update(headers)
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 275, in update
    headers = Headers(headers)
              ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 156, in __init__
    bytes_value = _normalize_header_value(v, encoding)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 82, in _normalize_header_value
    return value.encode(encoding or "ascii")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/app/app/ingestion/parser.py", line 257, in _parse_with_qwen_vlm
    pages_markdown[page_num] = _ocr_page_with_qwen(pil_image)
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 212, in _ocr_page_with_qwen
    model, processor = _load_qwen_model()
                       ^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 186, in _load_qwen_model
    model = Qwen3VLForConditionalGeneration.from_pretrained(QWEN_MODEL_ID, **kwargs)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/modeling_utils.py", line 4286, in from_pretrained
    _adapter_model_path, pretrained_model_name_or_path, adapter_kwargs = maybe_load_adapters(
                                                                         ^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/integrations/peft.py", line 672, in maybe_load_adapters
    resolved_config_file = cached_file(
                           ^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 293, in cached_file
    file = cached_files(path_or_repo_id=path_or_repo_id, filenames=[filename], **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 488, in cached_files
    raise OSError(f"{e}") from e
OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)


*(trang rỗng / OCR không trả về nội dung)*

---

## Trang 31

> ⚠️ **LỖI OCR ở trang này:** OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 437, in cached_files
    hf_hub_download(
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1013, in hf_hub_download
    return _hf_hub_download_to_cache_dir(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1088, in _hf_hub_download_to_cache_dir
    (url_to_download, etag, commit_hash, expected_size, xet_file_data, head_call_error) = _get_metadata_or_catch_error(
                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1707, in _get_metadata_or_catch_error
    metadata = get_hf_file_metadata(
               ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1615, in get_hf_file_metadata
    response = _httpx_follow_relative_redirects_with_backoff(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 719, in _httpx_follow_relative_redirects_with_backoff
    response = http_backoff(
               ^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 596, in http_backoff
    return next(
           ^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 504, in _http_backoff_base
    response = client.request(method=method, url=url, **kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 812, in request
    request = self.build_request(
              ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 367, in build_request
    headers = self._merge_headers(headers)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 430, in _merge_headers
    merged_headers.update(headers)
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 275, in update
    headers = Headers(headers)
              ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 156, in __init__
    bytes_value = _normalize_header_value(v, encoding)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 82, in _normalize_header_value
    return value.encode(encoding or "ascii")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/app/app/ingestion/parser.py", line 257, in _parse_with_qwen_vlm
    pages_markdown[page_num] = _ocr_page_with_qwen(pil_image)
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 212, in _ocr_page_with_qwen
    model, processor = _load_qwen_model()
                       ^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 186, in _load_qwen_model
    model = Qwen3VLForConditionalGeneration.from_pretrained(QWEN_MODEL_ID, **kwargs)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/modeling_utils.py", line 4286, in from_pretrained
    _adapter_model_path, pretrained_model_name_or_path, adapter_kwargs = maybe_load_adapters(
                                                                         ^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/integrations/peft.py", line 672, in maybe_load_adapters
    resolved_config_file = cached_file(
                           ^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 293, in cached_file
    file = cached_files(path_or_repo_id=path_or_repo_id, filenames=[filename], **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 488, in cached_files
    raise OSError(f"{e}") from e
OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)


*(trang rỗng / OCR không trả về nội dung)*

---

## Trang 32

> ⚠️ **LỖI OCR ở trang này:** OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 437, in cached_files
    hf_hub_download(
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1013, in hf_hub_download
    return _hf_hub_download_to_cache_dir(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1088, in _hf_hub_download_to_cache_dir
    (url_to_download, etag, commit_hash, expected_size, xet_file_data, head_call_error) = _get_metadata_or_catch_error(
                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1707, in _get_metadata_or_catch_error
    metadata = get_hf_file_metadata(
               ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1615, in get_hf_file_metadata
    response = _httpx_follow_relative_redirects_with_backoff(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 719, in _httpx_follow_relative_redirects_with_backoff
    response = http_backoff(
               ^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 596, in http_backoff
    return next(
           ^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 504, in _http_backoff_base
    response = client.request(method=method, url=url, **kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 812, in request
    request = self.build_request(
              ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 367, in build_request
    headers = self._merge_headers(headers)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 430, in _merge_headers
    merged_headers.update(headers)
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 275, in update
    headers = Headers(headers)
              ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 156, in __init__
    bytes_value = _normalize_header_value(v, encoding)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 82, in _normalize_header_value
    return value.encode(encoding or "ascii")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/app/app/ingestion/parser.py", line 257, in _parse_with_qwen_vlm
    pages_markdown[page_num] = _ocr_page_with_qwen(pil_image)
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 212, in _ocr_page_with_qwen
    model, processor = _load_qwen_model()
                       ^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 186, in _load_qwen_model
    model = Qwen3VLForConditionalGeneration.from_pretrained(QWEN_MODEL_ID, **kwargs)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/modeling_utils.py", line 4286, in from_pretrained
    _adapter_model_path, pretrained_model_name_or_path, adapter_kwargs = maybe_load_adapters(
                                                                         ^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/integrations/peft.py", line 672, in maybe_load_adapters
    resolved_config_file = cached_file(
                           ^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 293, in cached_file
    file = cached_files(path_or_repo_id=path_or_repo_id, filenames=[filename], **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 488, in cached_files
    raise OSError(f"{e}") from e
OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)


*(trang rỗng / OCR không trả về nội dung)*

---

## Trang 33

> ⚠️ **LỖI OCR ở trang này:** OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 437, in cached_files
    hf_hub_download(
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1013, in hf_hub_download
    return _hf_hub_download_to_cache_dir(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1088, in _hf_hub_download_to_cache_dir
    (url_to_download, etag, commit_hash, expected_size, xet_file_data, head_call_error) = _get_metadata_or_catch_error(
                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1707, in _get_metadata_or_catch_error
    metadata = get_hf_file_metadata(
               ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1615, in get_hf_file_metadata
    response = _httpx_follow_relative_redirects_with_backoff(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 719, in _httpx_follow_relative_redirects_with_backoff
    response = http_backoff(
               ^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 596, in http_backoff
    return next(
           ^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 504, in _http_backoff_base
    response = client.request(method=method, url=url, **kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 812, in request
    request = self.build_request(
              ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 367, in build_request
    headers = self._merge_headers(headers)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 430, in _merge_headers
    merged_headers.update(headers)
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 275, in update
    headers = Headers(headers)
              ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 156, in __init__
    bytes_value = _normalize_header_value(v, encoding)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 82, in _normalize_header_value
    return value.encode(encoding or "ascii")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/app/app/ingestion/parser.py", line 257, in _parse_with_qwen_vlm
    pages_markdown[page_num] = _ocr_page_with_qwen(pil_image)
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 212, in _ocr_page_with_qwen
    model, processor = _load_qwen_model()
                       ^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 186, in _load_qwen_model
    model = Qwen3VLForConditionalGeneration.from_pretrained(QWEN_MODEL_ID, **kwargs)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/modeling_utils.py", line 4286, in from_pretrained
    _adapter_model_path, pretrained_model_name_or_path, adapter_kwargs = maybe_load_adapters(
                                                                         ^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/integrations/peft.py", line 672, in maybe_load_adapters
    resolved_config_file = cached_file(
                           ^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 293, in cached_file
    file = cached_files(path_or_repo_id=path_or_repo_id, filenames=[filename], **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 488, in cached_files
    raise OSError(f"{e}") from e
OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)


*(trang rỗng / OCR không trả về nội dung)*

---

## Trang 34

> ⚠️ **LỖI OCR ở trang này:** OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 437, in cached_files
    hf_hub_download(
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1013, in hf_hub_download
    return _hf_hub_download_to_cache_dir(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1088, in _hf_hub_download_to_cache_dir
    (url_to_download, etag, commit_hash, expected_size, xet_file_data, head_call_error) = _get_metadata_or_catch_error(
                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1707, in _get_metadata_or_catch_error
    metadata = get_hf_file_metadata(
               ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1615, in get_hf_file_metadata
    response = _httpx_follow_relative_redirects_with_backoff(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 719, in _httpx_follow_relative_redirects_with_backoff
    response = http_backoff(
               ^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 596, in http_backoff
    return next(
           ^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 504, in _http_backoff_base
    response = client.request(method=method, url=url, **kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 812, in request
    request = self.build_request(
              ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 367, in build_request
    headers = self._merge_headers(headers)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 430, in _merge_headers
    merged_headers.update(headers)
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 275, in update
    headers = Headers(headers)
              ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 156, in __init__
    bytes_value = _normalize_header_value(v, encoding)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 82, in _normalize_header_value
    return value.encode(encoding or "ascii")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/app/app/ingestion/parser.py", line 257, in _parse_with_qwen_vlm
    pages_markdown[page_num] = _ocr_page_with_qwen(pil_image)
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 212, in _ocr_page_with_qwen
    model, processor = _load_qwen_model()
                       ^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 186, in _load_qwen_model
    model = Qwen3VLForConditionalGeneration.from_pretrained(QWEN_MODEL_ID, **kwargs)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/modeling_utils.py", line 4286, in from_pretrained
    _adapter_model_path, pretrained_model_name_or_path, adapter_kwargs = maybe_load_adapters(
                                                                         ^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/integrations/peft.py", line 672, in maybe_load_adapters
    resolved_config_file = cached_file(
                           ^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 293, in cached_file
    file = cached_files(path_or_repo_id=path_or_repo_id, filenames=[filename], **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 488, in cached_files
    raise OSError(f"{e}") from e
OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)


*(trang rỗng / OCR không trả về nội dung)*

---

## Trang 35

> ⚠️ **LỖI OCR ở trang này:** OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 437, in cached_files
    hf_hub_download(
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1013, in hf_hub_download
    return _hf_hub_download_to_cache_dir(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1088, in _hf_hub_download_to_cache_dir
    (url_to_download, etag, commit_hash, expected_size, xet_file_data, head_call_error) = _get_metadata_or_catch_error(
                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1707, in _get_metadata_or_catch_error
    metadata = get_hf_file_metadata(
               ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1615, in get_hf_file_metadata
    response = _httpx_follow_relative_redirects_with_backoff(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 719, in _httpx_follow_relative_redirects_with_backoff
    response = http_backoff(
               ^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 596, in http_backoff
    return next(
           ^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 504, in _http_backoff_base
    response = client.request(method=method, url=url, **kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 812, in request
    request = self.build_request(
              ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 367, in build_request
    headers = self._merge_headers(headers)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 430, in _merge_headers
    merged_headers.update(headers)
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 275, in update
    headers = Headers(headers)
              ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 156, in __init__
    bytes_value = _normalize_header_value(v, encoding)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 82, in _normalize_header_value
    return value.encode(encoding or "ascii")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/app/app/ingestion/parser.py", line 257, in _parse_with_qwen_vlm
    pages_markdown[page_num] = _ocr_page_with_qwen(pil_image)
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 212, in _ocr_page_with_qwen
    model, processor = _load_qwen_model()
                       ^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 186, in _load_qwen_model
    model = Qwen3VLForConditionalGeneration.from_pretrained(QWEN_MODEL_ID, **kwargs)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/modeling_utils.py", line 4286, in from_pretrained
    _adapter_model_path, pretrained_model_name_or_path, adapter_kwargs = maybe_load_adapters(
                                                                         ^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/integrations/peft.py", line 672, in maybe_load_adapters
    resolved_config_file = cached_file(
                           ^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 293, in cached_file
    file = cached_files(path_or_repo_id=path_or_repo_id, filenames=[filename], **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 488, in cached_files
    raise OSError(f"{e}") from e
OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)


*(trang rỗng / OCR không trả về nội dung)*

---

## Trang 36

> ⚠️ **LỖI OCR ở trang này:** OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 437, in cached_files
    hf_hub_download(
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1013, in hf_hub_download
    return _hf_hub_download_to_cache_dir(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1088, in _hf_hub_download_to_cache_dir
    (url_to_download, etag, commit_hash, expected_size, xet_file_data, head_call_error) = _get_metadata_or_catch_error(
                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1707, in _get_metadata_or_catch_error
    metadata = get_hf_file_metadata(
               ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1615, in get_hf_file_metadata
    response = _httpx_follow_relative_redirects_with_backoff(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 719, in _httpx_follow_relative_redirects_with_backoff
    response = http_backoff(
               ^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 596, in http_backoff
    return next(
           ^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 504, in _http_backoff_base
    response = client.request(method=method, url=url, **kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 812, in request
    request = self.build_request(
              ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 367, in build_request
    headers = self._merge_headers(headers)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 430, in _merge_headers
    merged_headers.update(headers)
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 275, in update
    headers = Headers(headers)
              ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 156, in __init__
    bytes_value = _normalize_header_value(v, encoding)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 82, in _normalize_header_value
    return value.encode(encoding or "ascii")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/app/app/ingestion/parser.py", line 257, in _parse_with_qwen_vlm
    pages_markdown[page_num] = _ocr_page_with_qwen(pil_image)
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 212, in _ocr_page_with_qwen
    model, processor = _load_qwen_model()
                       ^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 186, in _load_qwen_model
    model = Qwen3VLForConditionalGeneration.from_pretrained(QWEN_MODEL_ID, **kwargs)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/modeling_utils.py", line 4286, in from_pretrained
    _adapter_model_path, pretrained_model_name_or_path, adapter_kwargs = maybe_load_adapters(
                                                                         ^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/integrations/peft.py", line 672, in maybe_load_adapters
    resolved_config_file = cached_file(
                           ^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 293, in cached_file
    file = cached_files(path_or_repo_id=path_or_repo_id, filenames=[filename], **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 488, in cached_files
    raise OSError(f"{e}") from e
OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)


*(trang rỗng / OCR không trả về nội dung)*

---

## Trang 37

> ⚠️ **LỖI OCR ở trang này:** OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 437, in cached_files
    hf_hub_download(
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1013, in hf_hub_download
    return _hf_hub_download_to_cache_dir(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1088, in _hf_hub_download_to_cache_dir
    (url_to_download, etag, commit_hash, expected_size, xet_file_data, head_call_error) = _get_metadata_or_catch_error(
                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1707, in _get_metadata_or_catch_error
    metadata = get_hf_file_metadata(
               ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1615, in get_hf_file_metadata
    response = _httpx_follow_relative_redirects_with_backoff(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 719, in _httpx_follow_relative_redirects_with_backoff
    response = http_backoff(
               ^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 596, in http_backoff
    return next(
           ^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 504, in _http_backoff_base
    response = client.request(method=method, url=url, **kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 812, in request
    request = self.build_request(
              ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 367, in build_request
    headers = self._merge_headers(headers)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 430, in _merge_headers
    merged_headers.update(headers)
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 275, in update
    headers = Headers(headers)
              ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 156, in __init__
    bytes_value = _normalize_header_value(v, encoding)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 82, in _normalize_header_value
    return value.encode(encoding or "ascii")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/app/app/ingestion/parser.py", line 257, in _parse_with_qwen_vlm
    pages_markdown[page_num] = _ocr_page_with_qwen(pil_image)
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 212, in _ocr_page_with_qwen
    model, processor = _load_qwen_model()
                       ^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 186, in _load_qwen_model
    model = Qwen3VLForConditionalGeneration.from_pretrained(QWEN_MODEL_ID, **kwargs)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/modeling_utils.py", line 4286, in from_pretrained
    _adapter_model_path, pretrained_model_name_or_path, adapter_kwargs = maybe_load_adapters(
                                                                         ^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/integrations/peft.py", line 672, in maybe_load_adapters
    resolved_config_file = cached_file(
                           ^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 293, in cached_file
    file = cached_files(path_or_repo_id=path_or_repo_id, filenames=[filename], **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 488, in cached_files
    raise OSError(f"{e}") from e
OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)


*(trang rỗng / OCR không trả về nội dung)*

---

## Trang 38

> ⚠️ **LỖI OCR ở trang này:** OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 437, in cached_files
    hf_hub_download(
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1013, in hf_hub_download
    return _hf_hub_download_to_cache_dir(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1088, in _hf_hub_download_to_cache_dir
    (url_to_download, etag, commit_hash, expected_size, xet_file_data, head_call_error) = _get_metadata_or_catch_error(
                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1707, in _get_metadata_or_catch_error
    metadata = get_hf_file_metadata(
               ^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_validators.py", line 88, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/file_download.py", line 1615, in get_hf_file_metadata
    response = _httpx_follow_relative_redirects_with_backoff(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 719, in _httpx_follow_relative_redirects_with_backoff
    response = http_backoff(
               ^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 596, in http_backoff
    return next(
           ^^^^^
  File "/usr/local/lib/python3.12/site-packages/huggingface_hub/utils/_http.py", line 504, in _http_backoff_base
    response = client.request(method=method, url=url, **kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 812, in request
    request = self.build_request(
              ^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 367, in build_request
    headers = self._merge_headers(headers)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_client.py", line 430, in _merge_headers
    merged_headers.update(headers)
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 275, in update
    headers = Headers(headers)
              ^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 156, in __init__
    bytes_value = _normalize_header_value(v, encoding)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/httpx/_models.py", line 82, in _normalize_header_value
    return value.encode(encoding or "ascii")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/app/app/ingestion/parser.py", line 257, in _parse_with_qwen_vlm
    pages_markdown[page_num] = _ocr_page_with_qwen(pil_image)
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 212, in _ocr_page_with_qwen
    model, processor = _load_qwen_model()
                       ^^^^^^^^^^^^^^^^^^
  File "/app/app/ingestion/parser.py", line 186, in _load_qwen_model
    model = Qwen3VLForConditionalGeneration.from_pretrained(QWEN_MODEL_ID, **kwargs)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/modeling_utils.py", line 4286, in from_pretrained
    _adapter_model_path, pretrained_model_name_or_path, adapter_kwargs = maybe_load_adapters(
                                                                         ^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/integrations/peft.py", line 672, in maybe_load_adapters
    resolved_config_file = cached_file(
                           ^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 293, in cached_file
    file = cached_files(path_or_repo_id=path_or_repo_id, filenames=[filename], **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/site-packages/transformers/utils/hub.py", line 488, in cached_files
    raise OSError(f"{e}") from e
OSError: 'ascii' codec can't encode character '\u1ec9' in position 11: ordinal not in range(128)


*(trang rỗng / OCR không trả về nội dung)*