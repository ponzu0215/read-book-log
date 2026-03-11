"""読破本履歴管理 Webアプリ - エントリーポイント / ログイン画面。"""

import streamlit as st
from services.auth_service import init_firebase_admin, get_google_sign_in_url, handle_oauth_callback

st.set_page_config(
    page_title="読破本履歴",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Firebase Admin SDK を初期化
try:
    init_firebase_admin()
except Exception:
    pass

# ─── OAuth コールバック処理 ───────────────────────────────────────────────────
# Google から戻ってきたときにクエリパラメータが付いている
query = dict(st.query_params)
if "code" in query and "user" not in st.session_state:
    redirect_uri = st.secrets["app"]["redirect_uri"]
    with st.spinner("認証処理中..."):
        user = handle_oauth_callback(query, redirect_uri)
    if user:
        st.session_state["user"] = user
        st.query_params.clear()
        st.rerun()
    else:
        st.query_params.clear()
        st.error("ログインに失敗しました。もう一度お試しください。")

# ─── ログイン済みの場合はホームへ誘導 ────────────────────────────────────────
if "user" in st.session_state and st.session_state["user"]:
    user = st.session_state["user"]
    name = user.get("displayName") or user.get("email") or "ユーザー"
    st.title("📚 読破本履歴")
    st.success(f"ようこそ、{name} さん！")
    st.write("左のメニュー、またはボタンからページを選んでください。")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.page_link("pages/1_ホーム.py", label="🏠 ホーム", use_container_width=True)
    with col2:
        st.page_link("pages/2_本を登録.py", label="📷 本を登録", use_container_width=True)
    with col3:
        st.page_link("pages/3_読破本一覧.py", label="📚 読破本一覧", use_container_width=True)

    with st.sidebar:
        photo = user.get("photoUrl")
        if photo:
            st.image(photo, width=40)
        st.write(f"👤 {name}")
        if st.button("ログアウト"):
            st.session_state.pop("user", None)
            st.rerun()
else:
    # ─── 未ログイン：ログイン画面 ────────────────────────────────────────────
    st.title("📚 読破本履歴")
    st.markdown("読んだ本をバーコードで簡単に記録・管理できるWebアプリです。")
    st.write("---")

    redirect_uri = st.secrets.get("app", {}).get("redirect_uri", "http://localhost:8501")
    sign_in_url = get_google_sign_in_url(redirect_uri)

    if sign_in_url:
        st.markdown("### ログイン")
        st.markdown(
            f'<a href="{sign_in_url}" target="_self">'
            '<button style="background:#4285F4;color:white;border:none;padding:12px 24px;'
            'border-radius:6px;font-size:16px;cursor:pointer;font-weight:bold;">'
            '🔑 Googleでログイン</button></a>',
            unsafe_allow_html=True,
        )
        st.caption("Googleアカウントを使って安全にログインします。")
    else:
        st.error("認証サービスに接続できませんでした。設定を確認してください。")

    st.write("---")
    st.markdown("""
    **主な機能:**
    - 📷 本の裏面バーコードを撮影して書籍情報を自動取得
    - ⭐ 5点満点の評価とコメントを記録
    - 📖 読破本一覧を表紙つきで閲覧
    - ✏️ いつでも評価・コメントを編集
    """)
