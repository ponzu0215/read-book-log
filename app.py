"""読破本履歴管理 Webアプリ - エントリーポイント / ログイン画面。
認証方式: アクセスキー入力（secrets.toml で管理）
"""

import streamlit as st
from services.auth_service import init_firebase_admin, verify_access_key, get_owner_user

st.set_page_config(
    page_title="読破本履歴",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Firebase Admin SDK を初期化（Firestore 用）
try:
    init_firebase_admin()
except Exception:
    pass

# ─── ログイン済みの場合 ───────────────────────────────────────────────────────
if st.session_state.get("authenticated"):
    user = st.session_state["user"]
    st.title("📚 読破本履歴")
    st.success("ログイン中です。左のメニューからページを選んでください。")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.page_link("pages/1_ホーム.py", label="🏠 ホーム", use_container_width=True)
    with col2:
        st.page_link("pages/2_本を登録.py", label="📷 本を登録", use_container_width=True)
    with col3:
        st.page_link("pages/3_読破本一覧.py", label="📚 読破本一覧", use_container_width=True)

    with st.sidebar:
        st.write("📚 読破本履歴")
        if st.button("ログアウト"):
            st.session_state.clear()
            st.rerun()

# ─── 未ログイン：ログイン画面 ─────────────────────────────────────────────────
else:
    st.title("📚 読破本履歴")
    st.markdown("読んだ本をバーコードで簡単に記録・管理できるWebアプリです。")
    st.write("---")

    st.markdown("### ログイン")
    key_input = st.text_input(
        "アクセスキー",
        type="password",
        placeholder="アクセスキーを入力してください",
    )

    if st.button("ログイン", type="primary"):
        if not key_input:
            st.warning("アクセスキーを入力してください。")
        elif verify_access_key(key_input):
            st.session_state["authenticated"] = True
            st.session_state["user"] = get_owner_user()
            st.rerun()
        else:
            st.error("アクセスキーが正しくありません。")

    st.write("---")
    st.markdown("""
    **主な機能:**
    - 📷 本の裏面バーコードを撮影して書籍情報を自動取得
    - ⭐ 5点満点の評価とコメントを記録
    - 📖 読破本一覧を表紙つきで閲覧
    - ✏️ いつでも評価・コメントを編集
    """)
