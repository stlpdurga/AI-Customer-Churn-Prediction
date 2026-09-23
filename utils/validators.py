from pathlib import Path

ALLOWED_EXTENSIONS = {".csv", ".xlsx"}
MAX_FILE_BYTES = 10 * 1024 * 1024


def validate_upload(file_storage):
    if not file_storage or not file_storage.filename:
        return False, "FILE_INVALID", "Choose a CSV or XLSX file to upload."
    extension = Path(file_storage.filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        return False, "FILE_INVALID", "Only CSV and XLSX files are supported."
    file_storage.stream.seek(0, 2)
    size = file_storage.stream.tell()
    file_storage.stream.seek(0)
    if size > MAX_FILE_BYTES:
        return False, "FILE_TOO_LARGE", "The upload is larger than the 10 MB limit."
    return True, None, None
