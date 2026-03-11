"""Firestore CRUD サービス。
Firebase Admin SDK を使用してユーザーの読破本データを管理する。
データ構造: users/{uid}/books/{book_id}
"""

import uuid
import streamlit as st
from datetime import datetime, date
from typing import Optional, Dict, Any, List

import firebase_admin
from firebase_admin import firestore


def _get_db():
    """Firestore クライアントを返す。"""
    return firestore.client()


def save_book(uid: str, book_data: Dict[str, Any]) -> Optional[str]:
    """読破本データを Firestore に保存する。保存した book_id を返す。"""
    try:
        db = _get_db()
        book_id = str(uuid.uuid4())
        now = datetime.utcnow()
        book_data["created_at"] = now
        book_data["updated_at"] = now

        db.collection("users").document(uid).collection("books").document(book_id).set(
            book_data
        )
        return book_id
    except Exception as e:
        st.error(f"保存に失敗しました。時間をおいて再度お試しください。({e})")
        return None


def get_books(uid: str) -> List[Dict[str, Any]]:
    """ユーザーの全読破本を読了日の降順で返す。"""
    try:
        db = _get_db()
        docs = (
            db.collection("users")
            .document(uid)
            .collection("books")
            .order_by("read_at", direction=firestore.Query.DESCENDING)
            .stream()
        )
        books = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            books.append(data)
        return books
    except Exception as e:
        st.error(f"データ取得に失敗しました: {e}")
        return []


def get_book(uid: str, book_id: str) -> Optional[Dict[str, Any]]:
    """単一の読破本データを返す。"""
    try:
        db = _get_db()
        doc = (
            db.collection("users")
            .document(uid)
            .collection("books")
            .document(book_id)
            .get()
        )
        if doc.exists:
            data = doc.to_dict()
            data["id"] = doc.id
            return data
        return None
    except Exception:
        return None


def update_book(uid: str, book_id: str, updates: Dict[str, Any]) -> bool:
    """読破本データを更新する。"""
    try:
        db = _get_db()
        updates["updated_at"] = datetime.utcnow()
        (
            db.collection("users")
            .document(uid)
            .collection("books")
            .document(book_id)
            .update(updates)
        )
        return True
    except Exception as e:
        st.error(f"更新に失敗しました: {e}")
        return False


def delete_book(uid: str, book_id: str) -> bool:
    """読破本データを削除する。"""
    try:
        db = _get_db()
        db.collection("users").document(uid).collection("books").document(book_id).delete()
        return True
    except Exception as e:
        st.error(f"削除に失敗しました: {e}")
        return False


def check_duplicate(uid: str, isbn: str, read_date: date) -> List[Dict[str, Any]]:
    """同一 ISBN・同一読了日の重複登録を確認する。"""
    try:
        db = _get_db()
        docs = (
            db.collection("users")
            .document(uid)
            .collection("books")
            .where("isbn13", "==", isbn)
            .stream()
        )
        duplicates = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            doc_read_at = data.get("read_at")
            if doc_read_at:
                # Firestore Timestamp -> date への変換
                if hasattr(doc_read_at, "date"):
                    if doc_read_at.date() == read_date:
                        duplicates.append(data)
                elif hasattr(doc_read_at, "strftime"):
                    if doc_read_at.strftime("%Y-%m-%d") == read_date.strftime("%Y-%m-%d"):
                        duplicates.append(data)
        return duplicates
    except Exception:
        return []
