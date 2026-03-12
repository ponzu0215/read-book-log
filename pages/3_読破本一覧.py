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

# ─── 検索フィルター ───────────────────────────────────────────────────────────
query = st.text_input("🔍 検索（タイトル・著者・コメント）", placeholder="例: 告白、湊かなえ、感動")

if query:
    q = query.strip().lower()
    def matches(book):
        title = (book.get("title") or "").lower()
        authors = " ".join(book.get("authors") or []).lower()
        comment = (book.get("comment") or "").lower()
        return q in title or q in authors or q in comment
    filtered = [b for b in books if matches(b)]
else:
    filtered = books

total = len(books)
hit = len(filtered)
if query:
    st.caption(f"{total} 冊中 {hit} 冊がヒット")
else:
    st.caption(f"全 {total} 冊")

if not filtered:
    st.info("該当する本が見つかりませんでした。")
    st.stop()

st.write("---")

# ─── 一覧表示（カードレイアウト）─────────────────────────────────────────────
COLS = 3
rows = [filtered[i : i + COLS] for i in range(0, len(filtered), COLS)]

for row in rows:
    cols = st.columns(COLS)
    for col, book in zip(cols, row):
        with col:
            with st.container(border=True):
                # 表紙
                _no_cover = (
                    '<div style="height:160px;display:flex;align-items:center;'
                    'justify-content:center;background:#eee;border-radius:4px;">'
                    '<span style="font-size:48px;">📖</span></div>'
                )
                if book.get("thumbnail_url"):
                    try:
                        st.image(book["thumbnail_url"], use_container_width=True)
                    except Exception:
                        st.markdown(_no_cover, unsafe_allow_html=True)
                else:
                    st.markdown(_no_cover, unsafe_allow_html=True)

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
