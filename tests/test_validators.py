import io
from werkzeug.datastructures import FileStorage
from utils.validators import validate_upload


def test_valid_csv_upload():
    file = FileStorage(stream=io.BytesIO(b"a,b\n1,2"), filename="data.csv")
    assert validate_upload(file)[0]


def test_rejects_other_extensions():
    file = FileStorage(stream=io.BytesIO(b"hello"), filename="data.txt")
    assert validate_upload(file)[1] == "FILE_INVALID"
