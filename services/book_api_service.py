"""書誌情報取得サービス。
楽天ブックス API を主方式、OpenBD API をフォールバックとして使用する。
"""

import requests
import streamlit as st
from typing import Optional, Dict, Any

# Streamlit Cloud のアプリURL（楽天 API の Referer ヘッダーに使用）
_APP_URL = "https://read-book-log-dmtuq2kj8hfnro9sudxtdc.streamlit.app/"
_HEADERS = {"Referer": _APP_URL}


def search_by_isbn(isbn: str) -> Optional[Dict[str, Any]]:
    """ISBN で書誌情報を検索する。楽天 → OpenBD の順で試みる。"""
    book = _search_rakuten(isbn)
    if book:
        return book
    return _search_openbd(isbn)


def _search_rakuten(isbn: str) -> Optional[Dict[str, Any]]:
    """楽天ブックス API で書籍を検索する。"""
    try:
        app_id = st.secrets.get("rakuten", {}).get("application_id", "")
        if not app_id:
            return None
        url = "https://app.rakuten.co.jp/services/api/BooksBook/Search/20170404"
        params = {
            "applicationId": app_id,
            "isbn": isbn,
            "formatVersion": 2,
        }
        response = requests.get(url, params=params, headers=_HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()

        items = data.get("Items", [])
        st.info(f"[DEBUG] 楽天API成功 Items件数={len(items)}")
        if not items:
            return None

        item = items[0]
        author_raw = item.get("author", "")
        authors = [a.strip() for a in author_raw.split("/")] if author_raw else []
        thumbnail = (
            item.get("largeImageUrl")
            or item.get("mediumImageUrl")
            or item.get("smallImageUrl", "")
        )
        st.info(f"[DEBUG] thumbnail_url = '{thumbnail}'")

        return {
            "isbn13": isbn,
            "title": item.get("title", ""),
            "authors": authors,
            "publisher": item.get("publisherName", ""),
            "thumbnail_url": thumbnail,
            "category": item.get("booksGenreName", ""),
            "source": "rakuten",
        }
    except Exception as e:
        st.warning(f"[DEBUG] 楽天APIエラー: {e}")
        return None


def _search_openbd(isbn: str) -> Optional[Dict[str, Any]]:
    """OpenBD API で書籍を検索する（APIキー不要・フォールバック）。"""
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
        if not cover:
            for resource in onix.get("CollateralDetail", {}).get("SupportingResource", []):
                for version in resource.get("ResourceVersion", []):
                    link = version.get("ResourceLink", "")
                    if link:
                        cover = link
                        break
                if cover:
                    break

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
