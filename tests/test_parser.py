import os
import pytest
from app.services.parser import extract_text_from_file

def test_extract_text_from_txt(tmp_path):
    d = tmp_path / "sub"
    d.mkdir()
    p = d / "test_resume.txt"
    p.write_text("Rahul Kumar\nPython Developer with REST APIs experience.", encoding="utf-8")

    text, file_type = extract_text_from_file(str(p), "test_resume.txt")
    assert file_type == "txt"
    assert "Rahul Kumar" in text
    assert "Python Developer" in text

def test_unsupported_file_extension():
    with pytest.raises(ValueError, match="Unsupported file format"):
        extract_text_from_file("invalid.xyz", "invalid.xyz")
