"""認証サービス。
アクセスキー方式：secrets.toml に保存したキーと入力値を照合する。
Firebase Auth は使用しない。Firestore アクセスは Admin SDK 経由のみ。
"""

import streamlit as st
import firebase_admin
from firebase_admin import credentials
from typing import Dict, Any


def init_firebase_admin() -> None:
    """Firebase Admin SDK を初期化する（Firestore 用）。"""
    if firebase_admin._apps:
        return
    try:
        cred_dict = {
            "type": st.secrets["firebase_admin"]["type"],
            "project_id": st.secrets["firebase_admin"]["project_id"],
            "private_key_id": st.secrets["firebase_admin"]["private_key_id"],
            "private_key": st.secrets["firebase_admin"]["private_key"].replace("\\n", "\n"),
            "client_email": st.secrets["firebase_admin"]["client_email"],
            "client_id": st.secrets["firebase_admin"]["client_id"],
            "auth_uri": st.secrets["firebase_admin"]["auth_uri"],
            "token_uri": st.secrets["firebase_admin"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["firebase_admin"]["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["firebase_admin"]["client_x509_cert_url"],
        }
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Firebase Admin SDK の初期化に失敗しました: {e}")
        raise


def verify_access_key(key: str) -> bool:
    """入力されたアクセスキーを検証する。"""
    correct_key = st.secrets["app"]["access_key"]
    return key.strip() == correct_key


def get_owner_user() -> Dict[str, Any]:
    """固定のオーナーユーザー情報を返す。"""
    return {
        "uid": st.secrets["app"].get("owner_uid", "owner"),
        "displayName": "管理者",
    }
