"""ホーム画面 - 読破冊数・最近読んだ本・各ページへの導線。"""

import streamlit as st
from components.ui_helpers import require_auth, sidebar_user_info, render_stars
from services.firestore_service import get_books
from utils.helpers import format_date_jp

st.set_page_config(page_title="ホーム - 読破本履歴", page_icon="🏠", layout="wide")

sidebar_user_info()
user = require_auth()
uid = user["uid"]

st.title("🏠 ホーム")

# ─── 統計 ─────────────────────────────────────────────────────────────────────
with st.spinner("データを読み込み中..."):
    books = get_books(uid)

total = len(books)
rated_books = [b for b in books if b.get("rating")]
avg_rating = (
    sum(b["rating"] for b in rated_books) / len(rated_books) if rated_books else 0
)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("📚 読破冊数", f"{total} 冊")
with col2:
    st.metric("⭐ 平均評価", f"{avg_rating:.1f} / 5" if rated_books else "―")
with col3:
    if books:
        latest = books[0]
        st.metric("📖 直近の読了", latest.get("title", "")[:15] + "…" if len(latest.get("title", "")) > 15 else latest.get("title", ""))

st.write("---")

# ─── 操作ボタン ───────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    st.page_link("pages/2_本を登録.py", label="📷 本を登録する", use_container_width=True)
with col2:
    st.page_link("pages/3_読破本一覧.py", label="📚 読破本一覧を見る", use_container_width=True)

st.write("---")

# ─── 最近読んだ本（直近 5 冊）────────────────────────────────────────────────
st.subheader("最近読んだ本")

if not books:
    st.info("まだ本が登録されていません。「本を登録する」から追加しましょう！")
else:
    recent = books[:5]
    for book in recent:
        col_img, col_info = st.columns([1, 5])
        with col_img:
            if book.get("thumbnail_url"):
                st.image(book["thumbnail_url"], width=60)
            else:
                st.markdown("📖")
        with col_info:
            st.markdown(f"**{book.get('title', 'タイトル不明')}**")
            if book.get("rating"):
                st.caption(render_stars(int(book["rating"])))
            st.caption(f"読了日: {format_date_jp(book.get('read_at'))}")
        st.divider()
