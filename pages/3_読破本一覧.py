"""読破本一覧画面 - 登録済み本を表紙・評価付きカードで一覧表示。"""

import streamlit as st
from components.ui_helpers import require_auth, sidebar_user_info, render_stars, render_book_card
from services.firestore_service import get_books
from utils.helpers import format_date_jp

st.set_page_config(page_title="読破本一覧 - 読破本履歴", page_icon="📚", layout="wide")

sidebar_user_info()
user = require_auth()
uid = user["uid"]

st.title("📚 読破本一覧")

# ─── データ取得 ───────────────────────────────────────────────────────────────
with st.spinner("読み込み中..."):
    books = get_books(uid)

if not books:
    st.info("まだ本が登録されていません。")
    st.page_link("pages/2_本を登録.py", label="📷 最初の1冊を登録する")
    st.stop()

st.caption(f"全 {len(books)} 冊")
st.write("---")

# ─── 一覧表示（カードレイアウト）─────────────────────────────────────────────
# スマホ: 1列 / PC: 3列
COLS = 3
rows = [books[i : i + COLS] for i in range(0, len(books), COLS)]

for row in rows:
    cols = st.columns(COLS)
    for col, book in zip(cols, row):
        with col:
            with st.container(border=True):
                # 表紙
                if book.get("thumbnail_url"):
                    st.image(book["thumbnail_url"], use_container_width=True)
                else:
                    st.markdown(
                        '<div style="height:160px;display:flex;align-items:center;'
                        'justify-content:center;background:#eee;border-radius:4px;">'
                        '<span style="font-size:48px;">📖</span></div>',
                        unsafe_allow_html=True,
                    )

                # タイトル
                title = book.get("title") or "タイトル不明"
                st.markdown(f"**{title[:30]}{'…' if len(title) > 30 else ''}**")

                # 著者
                authors = book.get("authors", [])
                if isinstance(authors, list):
                    author_str = " / ".join(authors)
                else:
                    author_str = str(authors)
                if author_str:
                    st.caption(author_str[:25] + "…" if len(author_str) > 25 else author_str)

                # 評価
                rating = book.get("rating")
                if rating:
                    st.write(render_stars(int(rating)))
                else:
                    st.write("☆☆☆☆☆")

                # コメント抜粋
                comment = book.get("comment", "")
                if comment:
                    st.caption(
                        f'「{comment[:40]}{"…" if len(comment) > 40 else ""}」'
                    )

                # 読了日
                st.caption(f"📅 {format_date_jp(book.get('read_at'))}")

                # 詳細・編集ボタン
                if st.button("詳細・編集", key=f"detail_{book['id']}", use_container_width=True):
                    st.session_state["selected_book_id"] = book["id"]
                    st.switch_page("pages/4_詳細・編集.py")
