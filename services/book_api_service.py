"""書誌情報取得サービス。
OpenBD API を主方式、NDL サムネイルで表紙を補完する。
"""

import requests
from typing import Optional, Dict, Any


def search_by_isbn(isbn: str) -> Optional[Dict[str, Any]]:
    """ISBN で書誌情報を検索する。"""
    book = _search_openbd(isbn)
    if book:
        if not book.get("thumbnail_url"):
            book["thumbnail_url"] = _get_cover_ndl(isbn)
        return book
    return None


def _search_openbd(isbn: str) -> Optional[Dict[str, Any]]:
    """OpenBD API で書籍を検索する（APIキー不要）。"""
    try:
        url = f"https://api.openbd.jp/v1/get?isbn={isbn}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data or data[0] is None:
            return None

        item = data[0]
        summary = item.get("summary", {})
        onix = item.get("onix", {})

        title = summary.get("title", "")
        authors = []
        for c in onix.get("DescriptiveDetail", {}).get("Contributor", []):
            name = c.get("PersonName", {}).get("content", "")
            if name:
                authors.append(name)
        if not authors:
            author_raw = summary.get("author", "")
            if author_raw:
                authors = [a.strip() for a in author_raw.split("/")]

        cover = summary.get("cover", "")
        return {
            "isbn13": isbn,
            "title": title,
            "authors": authors,
            "publisher": summary.get("publisher", ""),
            "thumbnail_url": cover,
            "category": "",
            "source": "openbd",
        }
    except Exception:
        return None


def _get_cover_ndl(isbn: str) -> str:
    """国立国会図書館サムネイルAPIから表紙URLを取得する（APIキー不要）。"""
    try:
        url = f"https://ndlsearch.ndl.go.jp/thumbnail/{isbn}.jpg"
        r = requests.get(url, timeout=5)
        # NDL は画像がない場合も 200 を返すことがある。
        # Content-Type が image/* かつ一定サイズ以上であれば有効とみなす。
        content_type = r.headers.get("Content-Type", "")
        if r.status_code == 200 and "image" in content_type and len(r.content) > 2000:
            return url
    except Exception:
        pass
    return ""
