"""Firebase Authentication サービス。
Google OAuth (Firebase REST API) + Firebase Admin SDK を使用。
"""

import streamlit as st
import requests
import firebase_admin
from firebase_admin import auth, credentials
from typing import Optional, Dict, Any


def init_firebase_admin() -> None:
    """Firebase Admin SDK を初期化する（未初期化の場合のみ）。"""
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


def get_google_sign_in_url(redirect_uri: str) -> Optional[str]:
    """Firebase REST API 経由で Google OAuth URL を生成する。"""
    api_key = st.secrets["firebase"]["api_key"]
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:createAuthUri?key={api_key}"
    data = {
        "continueUri": redirect_uri,
        "providerId": "google.com",
    }
    try:
        response = requests.post(url, json=data, timeout=10)
        response.raise_for_status()
        return response.json().get("authUri")
    except Exception as e:
        st.error(f"ログインURLの生成に失敗しました: {e}")
        return None


def handle_oauth_callback(query_params: Dict[str, str], redirect_uri: str) -> Optional[Dict[str, Any]]:
    """OAuth コールバックを処理して Firebase ID トークンを取得する。"""
    api_key = st.secrets["firebase"]["api_key"]

    # クエリパラメータを含む完全なリダイレクト URL を再構築
    params_str = "&".join(f"{k}={v}" for k, v in query_params.items())
    request_uri = f"{redirect_uri}?{params_str}"

    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithIdp?key={api_key}"
    data = {
        "requestUri": request_uri,
        "postBody": "",
        "returnSecureToken": True,
        "returnIdpCredential": True,
    }
    try:
        response = requests.post(url, json=data, timeout=10)
        response.raise_for_status()
        result = response.json()

        if "error" in result:
            st.error(f"認証エラー: {result['error'].get('message', '不明なエラー')}")
            return None

        return {
            "uid": result.get("localId"),
            "email": result.get("email"),
            "displayName": result.get("displayName"),
            "photoUrl": result.get("photoUrl"),
            "idToken": result.get("idToken"),
            "refreshToken": result.get("refreshToken"),
        }
    except Exception as e:
        st.error(f"認証処理に失敗しました: {e}")
        return None


def refresh_id_token(refresh_token: str) -> Optional[str]:
    """Firebase ID トークンをリフレッシュする。"""
    api_key = st.secrets["firebase"]["api_key"]
    url = f"https://securetoken.googleapis.com/v1/token?key={api_key}"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    try:
        response = requests.post(url, json=data, timeout=10)
        response.raise_for_status()
        return response.json().get("id_token")
    except Exception:
        return None


def verify_id_token(id_token: str) -> Optional[Dict[str, Any]]:
    """Firebase Admin SDK で ID トークンを検証する。"""
    try:
        return auth.verify_id_token(id_token)
    except Exception:
        return None
