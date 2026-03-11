"""読破本詳細・編集画面 - 評価・コメント・読了日の確認と更新。"""

import streamlit as st
from datetime import date, datetime
from components.ui_helpers import require_auth, sidebar_user_info, render_stars
from services.firestore_service import get_book, update_book, delete_book
from utils.helpers import format_date_jp, to_date

st.set_page_config(page_title="詳細・編集 - 読破本履歴", page_icon="✏️", layout="wide")

sidebar_user_info()
user = require_auth()
uid = user["uid"]

# ─── 選択中の book_id を確認 ─────────────────────────────────────────────────
book_id = st.session_state.get("selected_book_id")
if not book_id:
    st.warning("本が選択されていません。一覧から本を選んでください。")
    st.page_link("pages/3_読破本一覧.py", label="← 読破本一覧へ戻る")
    st.stop()

# ─── データ取得 ───────────────────────────────────────────────────────────────
with st.spinner("データを読み込み中..."):
    book = get_book(uid, book_id)

if not book:
    st.error("本が見つかりませんでした。削除済みの可能性があります。")
    st.page_link("pages/3_読破本一覧.py", label="← 読破本一覧へ戻る")
    st.stop()

st.page_link("pages/3_読破本一覧.py", label="← 読破本一覧へ戻る")
st.title("✏️ 詳細・編集")
st.write("---")

# ─── 書誌情報表示（読み取り専用）────────────────────────────────────────────
col_img, col_meta = st.columns([1, 3])

with col_img:
    if book.get("thumbnail_url"):
        st.image(book["thumbnail_url"], width=150)
    else:
        st.markdown('<div style="font-size:60px;text-align:center;">📖</div>', unsafe_allow_html=True)

with col_meta:
    st.markdown(f"## {book.get('title') or 'タイトル不明'}")

    authors = book.get("authors", [])
    if isinstance(authors, list):
        author_str = " / ".join(authors)
    else:
        author_str = str(authors)
    if author_str:
        st.write(f"**著者:** {author_str}")

    if book.get("publisher"):
        st.write(f"**出版社:** {book['publisher']}")

    if book.get("isbn13"):
        st.write(f"**ISBN:** {book['isbn13']}")

    if book.get("category"):
        st.write(f"**カテゴリ:** {book['category']}")

st.write("---")

# ─── 現在の評価・コメント表示 ────────────────────────────────────────────────
st.subheader("現在の読書記録")
current_rating = book.get("rating", 0)
if current_rating:
    st.write(f"評価: {render_stars(int(current_rating))} （{current_rating} / 5）")
else:
    st.write("評価: 未評価")

current_comment = book.get("comment", "")
if current_comment:
    st.markdown(f"**コメント:**\n\n{current_comment}")
else:
    st.write("コメント: なし")

st.write(f"**読了日:** {format_date_jp(book.get('read_at'))}")

st.write("---")

# ─── 編集フォーム ─────────────────────────────────────────────────────────────
st.subheader("読書記録を編集")

read_at_current = to_date(book.get("read_at")) or date.today()

with st.form("edit_form"):
    read_at_new = st.date_input("読了日", value=read_at_current)

    rating_new = st.select_slider(
        "評価（1〜5）",
        options=[1, 2, 3, 4, 5],
        value=int(current_rating) if current_rating else 3,
        format_func=lambda x: "★" * x + "☆" * (5 - x),
    )

    comment_new = st.text_area(
        "コメント",
        value=current_comment,
        height=160,
        placeholder="感想・学び・印象に残った内容など...",
    )

    save_btn = st.form_submit_button("💾 保存する", type="primary", use_container_width=True)

    if save_btn:
        updates = {
            "rating": int(rating_new),
            "comment": comment_new,
            "read_at": datetime.combine(read_at_new, datetime.min.time()),
        }
        if update_book(uid, book_id, updates):
            st.success("✅ 保存しました！")
            st.rerun()

st.write("---")

# ─── 削除 ────────────────────────────────────────────────────────────────────
st.subheader("この本を削除する")
st.caption("削除すると元に戻せません。")

if "delete_confirm" not in st.session_state:
    st.session_state.delete_confirm = False

if not st.session_state.delete_confirm:
    if st.button("🗑️ 削除する", type="secondary"):
        st.session_state.delete_confirm = True
        st.rerun()
else:
    st.warning("本当に削除しますか？この操作は取り消せません。")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("はい、削除する", type="primary", use_container_width=True):
            if delete_book(uid, book_id):
                st.session_state.pop("selected_book_id", None)
                st.session_state.delete_confirm = False
                st.success("削除しました。")
                st.switch_page("pages/3_読破本一覧.py")
    with col2:
        if st.button("キャンセル", use_container_width=True):
            st.session_state.delete_confirm = False
            st.rerun()
