"""書誌情報取得サービス。
OpenBD API を主方式、Google Books API をフォールバックとして使用する。
"""

import requests
import streamlit as st
from typing import Optional, Dict, Any


def search_by_isbn(isbn: str) -> Optional[Dict[str, Any]]:
    """ISBN で書誌情報を検索する。OpenBD → Google Books の順で試みる。"""
    book = _search_openbd(isbn)
    if book:
        return book
    return _search_google_books(isbn)


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
        contributors = (
            onix.get("DescriptiveDetail", {}).get("Contributor", [])
        )
        for c in contributors:
            name = c.get("PersonName", {}).get("content", "")
            if name:
                authors.append(name)

        if not authors:
            author_raw = summary.get("author", "")
            if author_raw:
                authors = [a.strip() for a in author_raw.split("/")]

        # 表紙URL: summary.cover → ONIX SupportingResource の順で探す
        cover = summary.get("cover", "")
        if not cover:
            for resource in (
                onix.get("CollateralDetail", {}).get("SupportingResource", [])
            ):
                for feature in resource.get("ResourceFeature", []):
                    link = feature.get("ResourceLink", "")
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
    except Exception as e:
        st.warning(f"[DEBUG] OpenBDエラー: {e}")
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
    except Exception as e:
        st.warning(f"[DEBUG] Google BooksAPIエラー: {e}")
        return None
