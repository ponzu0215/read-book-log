"""再利用可能な UI コンポーネント。"""

import streamlit as st
from typing import Dict, Any, Optional


def render_stars(rating: int, max_stars: int = 5) -> str:
    """数値評価を星文字列に変換する。"""
    return "★" * rating + "☆" * (max_stars - rating)


def render_book_card(book: Dict[str, Any]) -> None:
    """読破本カードを描画する。"""
    col_img, col_info = st.columns([1, 4])

    with col_img:
        thumbnail = book.get("thumbnail_url", "")
        if thumbnail:
            st.image(thumbnail, width=80)
        else:
            st.markdown("📖")

    with col_info:
        title = book.get("title") or "タイトル不明"
        st.markdown(f"**{title}**")

        authors = book.get("authors", [])
        if isinstance(authors, list):
            author_str = " / ".join(authors)
        else:
            author_str = str(authors)
        if author_str:
            st.caption(author_str)

        rating = book.get("rating")
        if rating:
            st.write(render_stars(int(rating)))

        comment = book.get("comment", "")
        if comment:
            preview = comment[:60] + "..." if len(comment) > 60 else comment
            st.caption(f'「{preview}」')

        read_at = book.get("read_at")
        if read_at:
            if hasattr(read_at, "strftime"):
                st.caption(f"読了日: {read_at.strftime('%Y年%m月%d日')}")
            else:
                st.caption(f"読了日: {read_at}")

    st.divider()


def require_auth() -> Dict[str, Any]:
    """
    認証チェック。未ログインの場合は警告を表示して処理を停止する。
    ログイン済みの場合はユーザー情報を返す。
    """
    if "user" not in st.session_state or not st.session_state["user"]:
        st.warning("このページを利用するにはログインが必要です。")
        st.page_link("app.py", label="ログインページへ")
        st.stop()
    return st.session_state["user"]


def sidebar_user_info() -> None:
    """サイドバーにユーザー情報とログアウトボタンを表示する。"""
    user = st.session_state.get("user")
    if not user:
        return
    with st.sidebar:
        name = user.get("displayName") or user.get("email") or "ユーザー"
        photo = user.get("photoUrl")
        if photo:
            st.image(photo, width=40)
        st.write(f"👤 {name}")
        if st.button("ログアウト", key="sidebar_logout"):
            st.session_state.pop("user", None)
            st.switch_page("app.py")
