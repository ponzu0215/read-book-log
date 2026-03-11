"""バーコード読み取りサービス。
主方式: pyzbar による EAN-13 / ISBN-13 バーコード読み取り
補助方式: pytesseract による OCR フォールバック
"""

import re
import io
from typing import Optional, List
from PIL import Image


def read_barcode(image_bytes: bytes) -> Optional[str]:
    """
    画像バイト列からバーコードを読み取る。
    EAN-13 / ISBN-13 を優先的に返す。
    """
    try:
        from pyzbar.pyzbar import decode, ZBarSymbol

        image = Image.open(io.BytesIO(image_bytes))
        if image.mode not in ("RGB", "L", "RGBA"):
            image = image.convert("RGB")

        # EAN-13 を優先して読み取る
        decoded = decode(image, symbols=[ZBarSymbol.EAN13])
        for obj in decoded:
            code = obj.data.decode("utf-8").strip()
            if is_valid_isbn_or_jan(code):
                return code

        # シンボル指定なしで再試行
        decoded = decode(image)
        for obj in decoded:
            code = obj.data.decode("utf-8").strip()
            if is_valid_isbn_or_jan(code):
                return code

        return None
    except ImportError:
        return None
    except Exception:
        return None


def read_isbn_from_ocr(image_bytes: bytes) -> List[str]:
    """
    OCR で画像から ISBN / JAN の候補を抽出する（バーコード読み取り失敗時の補助）。
    """
    candidates: List[str] = []
    try:
        import pytesseract

        image = Image.open(io.BytesIO(image_bytes))
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")

        # 複数の PSM モードで試行して候補を集める
        for psm in [6, 7, 8, 13]:
            config = f"--oem 3 --psm {psm} -c tessedit_char_whitelist=0123456789"
            text = pytesseract.image_to_string(image, config=config)
            # スペース・改行を除去して 13 桁列を抽出
            clean = re.sub(r"\s+", "", text)
            for num in re.findall(r"\d{13}", clean):
                if is_valid_isbn_or_jan(num) and num not in candidates:
                    candidates.append(num)
            # ISBN-10 も試みる
            for num in re.findall(r"\d{9}[\dX]", clean):
                isbn13 = isbn10_to_isbn13(num)
                if isbn13 and isbn13 not in candidates:
                    candidates.append(isbn13)

    except ImportError:
        pass
    except Exception:
        pass

    return candidates


def is_valid_isbn_or_jan(code: str) -> bool:
    """EAN-13 チェックサムを検証する。"""
    if not re.fullmatch(r"\d{13}", code):
        return False
    total = sum(
        int(d) * (1 if i % 2 == 0 else 3)
        for i, d in enumerate(code[:-1])
    )
    check = (10 - total % 10) % 10
    return check == int(code[-1])


def isbn10_to_isbn13(isbn10: str) -> Optional[str]:
    """ISBN-10 を ISBN-13 に変換する。"""
    if not re.fullmatch(r"\d{9}[\dX]", isbn10):
        return None
    base = "978" + isbn10[:9]
    total = sum(
        int(d) * (1 if i % 2 == 0 else 3)
        for i, d in enumerate(base)
    )
    check = (10 - total % 10) % 10
    return base + str(check)
