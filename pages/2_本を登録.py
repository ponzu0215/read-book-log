"""本登録画面 - バーコード読み取り → 書誌情報取得 → 評価・コメント入力 → 保存。"""

import streamlit as st
from datetime import date, datetime
from components.ui_helpers import require_auth, sidebar_user_info
from services.barcode_service import read_barcode, read_isbn_from_ocr, is_valid_isbn_or_jan
from services.book_api_service import search_by_isbn
from services.firestore_service import save_book, check_duplicate

st.set_page_config(page_title="本を登録 - 読破本履歴", page_icon="📷", layout="wide")

sidebar_user_info()
user = require_auth()
uid = user["uid"]

st.title("📷 本を登録")

# ─── セッション状態の初期化 ──────────────────────────────────────────────────
for key, default in [
    ("detected_isbn", ""),
    ("book_info", None),
    ("force_save", False),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ─── STEP 1: 画像アップロード ─────────────────────────────────────────────────
st.subheader("STEP 1：本の裏面画像をアップロード")
st.caption("バーコード（EAN-13 / ISBN-13）が写っている面を撮影してアップロードしてください。")

uploaded = st.file_uploader(
    "画像を選択",
    type=["jpg", "jpeg", "png", "webp", "bmp"],
    label_visibility="collapsed",
)

if uploaded:
    image_bytes = uploaded.read()
    col_preview, col_result = st.columns([1, 2])
    with col_preview:
        st.image(image_bytes, caption="アップロード画像", width=200)

    with col_result:
        with st.spinner("バーコードを読み取り中..."):
            isbn = read_barcode(image_bytes)

        if isbn:
            st.success(f"✅ バーコードを認識しました: `{isbn}`")
            st.session_state.detected_isbn = isbn
        else:
            st.warning("⚠️ バーコードを直接読み取れませんでした。OCRで補助認識を試みます...")
            with st.spinner("OCR処理中..."):
                candidates = read_isbn_from_ocr(image_bytes)

            if candidates:
                selected = st.selectbox(
                    "検出した ISBN 候補を選択してください",
                    candidates,
                    key="ocr_candidate",
                )
                if selected:
                    st.session_state.detected_isbn = selected
            else:
                st.error(
                    "バーコードを認識できませんでした。"
                    "明るい場所で再撮影するか、下の入力欄に ISBN を直接入力してください。"
                )

st.write("---")

# ─── STEP 2: ISBN 手入力（アップロードの補助または代替）──────────────────────
st.subheader("STEP 2：ISBN を確認 / 手入力")
isbn_input = st.text_input(
    "ISBN-13 / JAN（13桁の数字）",
    value=st.session_state.detected_isbn,
    placeholder="例: 9784XXXXXXXXX",
    max_chars=13,
    key="isbn_text_input",
)

if isbn_input:
    st.session_state.detected_isbn = isbn_input.strip()

# ISBN 検証
current_isbn = st.session_state.detected_isbn
isbn_valid = bool(current_isbn) and len(current_isbn) == 13 and is_valid_isbn_or_jan(current_isbn)

if current_isbn and not isbn_valid:
    st.warning("入力された ISBN のチェックサムが一致しません。数字を確認してください。")

# ─── STEP 3: 書誌情報取得 ────────────────────────────────────────────────────
if isbn_valid:
    fetch_clicked = st.button("🔍 書誌情報を取得", type="primary", disabled=not isbn_valid)

    if fetch_clicked:
        # ISBN が変わった場合は再取得
        current_info = st.session_state.book_info
        if not current_info or current_info.get("isbn13") != current_isbn:
            with st.spinner("書誌情報を取得中..."):
                book_info = search_by_isbn(current_isbn)
            if book_info:
                st.session_state.book_info = book_info
                st.success("書誌情報を取得しました！")
            else:
                st.error(
                    "書誌情報を取得できませんでした。"
                    "ISBN を確認するか、再撮影してください。"
                )

# ─── STEP 4: 書誌情報確認 + 読書情報入力 ─────────────────────────────────────
if st.session_state.book_info:
    book = st.session_state.book_info
    st.write("---")
    st.subheader("STEP 3：書誌情報の確認")

    col_img, col_meta = st.columns([1, 3])
    with col_img:
        if book.get("thumbnail_url"):
            st.image(book["thumbnail_url"], width=120)
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
        source = "楽天ブックス" if book.get("source") == "rakuten" else "Google Books"
        st.caption(f"情報ソース: {source}")

    st.write("---")
    st.subheader("STEP 4：読書情報を入力")

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
            # 重複チェック
            if not st.session_state.force_save:
                duplicates = check_duplicate(uid, book.get("isbn13", ""), read_at)
                if duplicates:
                    st.warning(
                        f"⚠️ この本は同じ読了日（{read_at}）で既に登録されています。"
                        "再登録する場合は下の「それでも登録する」ボタンを押してください。"
                    )
                    st.session_state.force_save = True
                    st.stop()

            # 保存
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
                # フォームをリセット
                st.session_state.book_info = None
                st.session_state.detected_isbn = ""
                st.session_state.force_save = False
                st.rerun()

    # 重複確認後の強制保存ボタン（form の外）
    if st.session_state.force_save:
        if st.button("それでも登録する", type="secondary"):
            st.session_state.force_save = True  # フラグ維持のためダミー更新
            # 上のフォームを再送信する代わりに、直接保存する
            st.info("フォームをもう一度「保存」ボタンで送信してください。")
