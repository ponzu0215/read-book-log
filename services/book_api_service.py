"""書誌情報取得サービス。
Google Books API を使用して ISBN から書籍情報を取得する。
"""

import requests
import streamlit as st
from typing import Optional, Dict, Any


def search_by_isbn(isbn: str) -> Optional[Dict[str, Any]]:
    """ISBN で Google Books API を検索し、書誌情報を返す。"""
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

        # できるだけ大きい画像を取得し HTTPS に統一
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
    except requests.exceptions.Timeout:
        st.error("書誌情報の取得がタイムアウトしました。時間をおいて再度お試しください。")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"書誌情報の取得に失敗しました: {e}")
        return None
    except Exception:
        return None
