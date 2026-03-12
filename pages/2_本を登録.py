"""本登録画面 - ISBN 手入力 → 書誌情報取得 → 評価・コメント入力 → 保存。"""

import streamlit as st
from datetime import date, datetime
from components.ui_helpers import require_auth, sidebar_user_info
from services.book_api_service import search_by_isbn
from services.firestore_service import save_book, check_duplicate

st.set_page_config(page_title="本を登録 - 読破本履歴", page_icon="📖", layout="wide")

sidebar_user_info()
user = require_auth()
uid = user["uid"]

st.title("📖 本を登録")

# ─── セッション状態の初期化 ──────────────────────────────────────────────────
for key, default in [
    ("detected_isbn", ""),
    ("book_info", None),
    ("force_save", False),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ─── STEP 1: ISBN 手入力 ──────────────────────────────────────────────────────
st.subheader("STEP 1：ISBN を入力")
st.caption("本の裏面に記載されている ISBN-13（978から始まる13桁の数字）を入力してください。")

isbn_input = st.text_input(
    "ISBN-13（13桁の数字）",
    value=st.session_state.detected_isbn,
    placeholder="例: 9784XXXXXXXXX",
    max_chars=13,
)

if isbn_input:
    st.session_state.detected_isbn = isbn_input.strip()

current_isbn = st.session_state.detected_isbn

# ISBN 簡易バリデーション（13桁数字かどうか）
isbn_valid = bool(current_isbn) and len(current_isbn) == 13 and current_isbn.isdigit()

if current_isbn and not isbn_valid:
    st.warning("13桁の数字を入力してください（ハイフンなし）。")

# ─── STEP 2: 書誌情報取得 ────────────────────────────────────────────────────
if isbn_valid:
    if st.button("🔍 書誌情報を取得", type="primary"):
        current_info = st.session_state.book_info
        if not current_info or current_info.get("isbn13") != current_isbn:
            with st.spinner("書誌情報を取得中..."):
                book_info = search_by_isbn(current_isbn)
            if book_info:
                st.session_state.book_info = book_info
                st.success("書誌情報を取得しました！")
            else:
                st.error(
                    "書誌情報を取得できませんでした。\n\n"
                    "**考えられる原因:**\n"
                    "- 楽天 application_id が Secrets に未設定\n"
                    "- ISBN の数字が間違っている\n\n"
                    "Streamlit Cloud の Secrets に `[rakuten]` セクションが設定されているか確認してください。"
                )

# ─── STEP 3: 書誌情報確認 + 読書情報入力 ─────────────────────────────────────
if st.session_state.book_info:
    book = st.session_state.book_info
    st.write("---")
    st.subheader("STEP 2：書誌情報の確認")

    col_img, col_meta = st.columns([1, 3])
    with col_img:
        if book.get("thumbnail_url"):
            st.markdown(
                f'<img src="{book["thumbnail_url"]}" style="width:120px;max-height:160px;'
                f'object-fit:contain;" onerror="this.style.display=\'none\'">',
                unsafe_allow_html=True,
            )
        else:
            st.markdown("🔲 表紙なし")
    with col_meta:
        st.markdown(f"**タイトル:** {book.get('title') or '不明'}")
        authors = book.get("authors", [])
        if isinstance(authors, list):
            st.write(f"**著者:** {' / '.join(authors)}")
        else:
            st.write(f"**著者:** {authors}")
        st.write(f"**出版社:** {book.get('publisher') or '不明'}")
        st.write(f"**ISBN:** {book.get('isbn13', '')}")
        if book.get("category"):
            st.write(f"**カテゴリ:** {book.get('category')}")
        source_map = {"openbd": "OpenBD", "google_books": "Google Books", "rakuten": "楽天ブックス"}
        source = source_map.get(book.get("source", ""), "不明")
        st.caption(f"情報ソース: {source}")

    st.write("---")
    st.subheader("STEP 3：読書情報を入力")

    with st.form("registration_form", clear_on_submit=False):
        read_at = st.date_input("読了日", value=date.today())

        rating = st.select_slider(
            "評価（1〜5）",
            options=[1, 2, 3, 4, 5],
            value=3,
            format_func=lambda x: "★" * x + "☆" * (5 - x),
        )

        comment = st.text_area(
            "コメント（任意）",
            placeholder="感想・学び・印象に残った内容など...",
            height=140,
        )

        submitted = st.form_submit_button(
            "📖 読破本として保存", type="primary", use_container_width=True
        )

        if submitted:
            if not st.session_state.force_save:
                duplicates = check_duplicate(uid, book.get("isbn13", ""), read_at)
                if duplicates:
                    st.warning(
                        f"⚠️ この本は同じ読了日（{read_at}）で既に登録されています。"
                        "再登録する場合は下の「それでも登録する」ボタンを押してください。"
                    )
                    st.session_state.force_save = True
                    st.stop()

            book_data = {
                "isbn13": book.get("isbn13", ""),
                "title": book.get("title", ""),
                "authors": book.get("authors", []),
                "publisher": book.get("publisher", ""),
                "thumbnail_url": book.get("thumbnail_url", ""),
                "category": book.get("category", ""),
                "rating": int(rating),
                "comment": comment,
                "read_at": datetime.combine(read_at, datetime.min.time()),
                "scan_method": book.get("source", "manual"),
            }
            book_id = save_book(uid, book_data)
            if book_id:
                st.success("✅ 保存しました！")
                st.balloons()
                st.session_state.book_info = None
                st.session_state.detected_isbn = ""
                st.session_state.force_save = False
                st.rerun()

    if st.session_state.force_save:
        if st.button("それでも登録する", type="secondary"):
            st.session_state.force_save = True
            st.info("フォームをもう一度「保存」ボタンで送信してください。")
