import pytest
from app.core.exceptions import OCRError
from app.services.ocr_service import resolve_profile, get_ocr_engine


def test_resolve_profile_aliases():
    assert resolve_profile("english") == "latin"
    assert resolve_profile("en") == "latin"
    assert resolve_profile("ENGLISH") == "latin"
    assert resolve_profile("hindi") == "devanagari"
    assert resolve_profile("hi") == "devanagari"
    assert resolve_profile("marathi") == "devanagari"
    assert resolve_profile("urdu") == "arabic"
    assert resolve_profile("tamil") == "tamil"
    assert resolve_profile("telugu") == "telugu"
    assert resolve_profile("latin") == "latin"


def test_invalid_profile_raises_ocr_error():
    with pytest.raises(OCRError) as exc_info:
        get_ocr_engine("klingon")
    assert "Unsupported OCR profile 'klingon'" in str(exc_info.value)

