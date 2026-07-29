from typing import List

from .models import TextSegment


class OcrCapabilities:
    def __init__(self) -> None:
        self.engine = "none"
        self.available = False
        try:
            import paddleocr  # type: ignore  # noqa: F401

            self.engine = "paddleocr"
            self.available = True
        except Exception:  # noqa: BLE001
            self.engine = "none"
            self.available = False


def get_ocr_capabilities() -> OcrCapabilities:
    return OcrCapabilities()


def detect_text_segments(_image_paths: list[str]) -> List[TextSegment]:
    capabilities = get_ocr_capabilities()
    if not capabilities.available:
        return []
    return []

