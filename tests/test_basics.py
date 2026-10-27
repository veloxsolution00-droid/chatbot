from app.retrieval.chunker import chunk_text,digest
from app.ingestion.extractor import extract
import pytest
def test_chunks():
    assert len(chunk_text("hello. "*100,100,10))>1
def test_digest():
    assert digest("a")==digest("a") and digest("a")!=digest("b")
def test_txt(tmp_path):
    p=tmp_path/"a.txt"; p.write_text("sample",encoding="utf-8")
    assert extract(p)[0][1]=="sample"
def test_unsupported(tmp_path):
    p=tmp_path/"a.exe"; p.write_text("x")
    with pytest.raises(ValueError): extract(p)
