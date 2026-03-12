"""書誌情報取得サービス。
楽天ブックス API を主方式、Google Books API をフォールバックとして使用する。
"""

import requests
import streamlit as st
from typing import Optional, Dict, Any


def search_by_isbn(isbn: str) -> Optional[Dict[str, Any]]:
    """ISBN で書誌情報を検索する。楽天 → Google Books の順で試みる。"""
    book = _search_rakuten(isbn)
    if book:
        return book
    return _search_google_books(isbn)


def _search_rakuten(isbn: str) -> Optional[Dict[str, Any]]:
    """楽天ブックス API で書籍を検索する。"""
    try:
        rakuten_secrets = st.secrets.get("rakuten", {})
        app_id = rakuten_secrets.get("application_id", "")
        if not app_id:
            return None
        url = "https://app.rakuten.co.jp/services/api/BooksBook/Search/20170404"
        params = {
            "applicationId": app_id,
            "isbn": isbn,
            "formatVersion": 2,
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        items = data.get("Items", [])
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

        return {
            "isbn13": isbn,
            "title": item.get("title", ""),
            "authors": authors,
            "publisher": item.get("publisherName", ""),
            "thumbnail_url": thumbnail,
            "category": item.get("booksGenreName", ""),
            "source": "rakuten",
        }
    except Exception:
        return None


def _search_google_books(isbn: str) -> Optional[Dict[str, Any]]:
    """Google Books API で書籍を検索する（フォールバック）。"""
    try:
        api_key = st.secrets.get("google_books", {}).get("api_key", "")
        url = "https://www.googleapis.com/books/v1/volumes"
        params: Dict[str, str] = {"q": f"isbn:{isbn}"}
        if api_key:
            params["key"] = api_key

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        items = data.get("items", [])
        if not items:
            return None

        volume = items[0].get("volumeInfo", {})
        image_links = volume.get("imageLinks", {})
        thumbnail = (
            image_links.get("thumbnail")
            or image_links.get("smallThumbnail", "")
        )
        if thumbnail:
            thumbnail = thumbnail.replace("http://", "https://").replace("zoom=1", "zoom=0")

        return {
            "isbn13": isbn,
            "title": volume.get("title", ""),
            "authors": volume.get("authors", []),
            "publisher": volume.get("publisher", ""),
            "thumbnail_url": thumbnail,
            "category": ", ".join(volume.get("categories", [])),
            "source": "google_books",
        }
    except Exception:
        return None
