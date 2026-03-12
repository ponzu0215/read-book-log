"""再利用可能な UI コンポーネント。"""

import streamlit as st
from typing import Dict, Any, Optional


def apply_book_style() -> None:
    """絵本風スタイルを全ページに適用する。"""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Zen+Maru+Gothic:wght@400;500;700&display=swap');

        /* ── 基盤：背景・フォント ── */
        .stApp {
            background-color: #FFFBF4;
            font-family: 'Zen Maru Gothic', 'Hiragino Maru Gothic Pro',
                         'Rounded Mplus 1c', 'Yu Gothic', sans-serif !important;
        }
        .block-container { padding-top: 1.8rem; }

        /* ── 見出し ── */
        h1 { color: #BF6352 !important; letter-spacing: 0.04em; }
        h2 { color: #A05540 !important; }
        h3 { color: #A05540 !important; }

        /* ── 水平線 ── */
        hr { border-color: #F2C8A8 !important; opacity: 0.6; }

        /* ── ボタン（全般） ── */
        .stButton button {
            border-radius: 999px !important;
            border: 2px solid #F0AA88 !important;
            background: linear-gradient(135deg, #FFF4EE 0%, #FFE2D0 100%) !important;
            color: #8B4513 !important;
            font-weight: 600 !important;
            font-family: 'Zen Maru Gothic', sans-serif !important;
            box-shadow: 1px 3px 8px rgba(200,100,60,.15) !important;
            transition: transform 0.15s, box-shadow 0.15s !important;
        }
        .stButton button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 2px 5px 14px rgba(200,100,60,.25) !important;
        }
        /* プライマリボタン */
        .stButton button[kind="primary"],
        .stButton button[data-testid="baseButton-primary"] {
            background: linear-gradient(135deg, #F4926A 0%, #DF6C4A 100%) !important;
            color: #fff !important;
            border-color: #DF6C4A !important;
        }

        /* ── テキスト入力 / テキストエリア / 日付 ── */
        .stTextInput input,
        .stTextArea textarea,
        .stDateInput input {
            border-radius: 12px !important;
            border: 2px solid #F2CAA8 !important;
            background-color: #FFFAF6 !important;
            font-family: 'Zen Maru Gothic', sans-serif !important;
        }
        .stTextInput input:focus,
        .stTextArea textarea:focus {
            border-color: #E8906A !important;
            box-shadow: 0 0 0 3px rgba(232,144,106,.2) !important;
        }

        /* ── ページリンク ── */
        [data-testid="stPageLink"] a {
            border-radius: 12px !important;
            border: 2px solid #F2CAA8 !important;
            background: linear-gradient(135deg, #FFF4EE, #FFE2D0) !important;
            color: #8B4513 !important;
            font-weight: 600 !important;
            box-shadow: 1px 2px 6px rgba(200,100,60,.12) !important;
        }

        /* ── メトリクスカード ── */
        [data-testid="stMetric"] {
            background: linear-gradient(135deg, #FFF6EE, #FFE8D4) !important;
            border-radius: 18px !important;
            border: 2px solid #F2CAA8 !important;
            padding: 14px 18px !important;
            box-shadow: 1px 3px 10px rgba(200,100,60,.10) !important;
        }

        /* ── サイドバー ── */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #FFF5EE 0%, #FFE8D4 100%) !important;
        }
        [data-testid="stSidebar"] hr {
            border-color: #F2C4A4 !important;
        }

        /* ── ボーダー付きコンテナ（本カード）── */
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 18px !important;
            border: 2px solid #F0D0B4 !important;
            background: #FFFAF6 !important;
            box-shadow: 2px 4px 14px rgba(200,120,60,.08) !important;
        }

        /* ── アラート ── */
        .stAlert {
            border-radius: 12px !important;
        }

        /* ── フォーム ── */
        [data-testid="stForm"] {
            border-radius: 16px !important;
            border: 2px solid #F0D0B4 !important;
            background: #FFFAF6 !important;
            padding: 16px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


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
    if not st.session_state.get("authenticated") or not st.session_state.get("user"):
        st.warning("このページを利用するにはログインが必要です。")
        st.page_link("app.py", label="ログインページへ")
        st.stop()
    return st.session_state["user"]


def sidebar_user_info() -> None:
    """サイドバーにログアウトボタンを表示する。"""
    apply_book_style()
    if not st.session_state.get("authenticated"):
        return
    with st.sidebar:
        st.write("📚 読破本履歴")
        if st.button("ログアウト", key="sidebar_logout"):
            st.session_state.clear()
            st.switch_page("app.py")
