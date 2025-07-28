"""ユーザー管理APIのテストモジュール

Phase 3: Validation - 失敗するテストを先に作成
"""
from typing import List

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class TestUserList:
    """ユーザー一覧取得のテスト"""

    @pytest.mark.asyncio
    async def test_get_users_as_admin(
        self, async_client: AsyncClient, admin_headers: dict, test_users: List[User]
    ):
        """
        Given: 管理者としてログイン済み
        When: ユーザー一覧を取得
        Then: ページネーション付きでユーザーリストが返される
        """
        response = await async_client.get(
            "/api/v1/users",
            headers=admin_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert len(data["users"]) <= 20  # デフォルトのper_page

    @pytest.mark.asyncio
    async def test_get_users_with_pagination(
        self, async_client: AsyncClient, admin_headers: dict
    ):
        """
        Given: 管理者としてログイン済み
        When: ページネーションパラメータを指定してユーザー一覧を取得
        Then: 指定されたページのユーザーが返される
        """
        response = await async_client.get(
            "/api/v1/users?page=2&per_page=10",
            headers=admin_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["page"] == 2
        assert data["per_page"] == 10

    @pytest.mark.asyncio
    async def test_get_users_as_regular_user(
        self, async_client: AsyncClient, user_headers: dict
    ):
        """
        Given: 一般ユーザーとしてログイン済み
        When: ユーザー一覧を取得しようとする
        Then: 403エラーが返される（権限不足）
        """
        response = await async_client.get(
            "/api/v1/users",
            headers=user_headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        assert data["code"] == "AUTH004"


class TestUserCreate:
    """ユーザー作成のテスト"""

    @pytest.mark.asyncio
    async def test_create_user_as_admin(
        self, async_client: AsyncClient, admin_headers: dict
    ):
        """
        Given: 管理者としてログイン済み
        When: 新規ユーザーを作成
        Then: ユーザーが作成される
        """
        new_user = {
            "email": "newuser@example.com",
            "full_name": "新規 ユーザー",
            "department": "営業部",
            "role": "user",
            "password": "SecurePass123!"
        }
        
        response = await async_client.post(
            "/api/v1/users",
            json=new_user,
            headers=admin_headers
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == new_user["email"]
        assert data["full_name"] == new_user["full_name"]
        assert data["department"] == new_user["department"]
        assert data["role"] == new_user["role"]
        assert "id" in data
        assert "password" not in data  # パスワードは返さない

    @pytest.mark.asyncio
    async def test_create_user_with_duplicate_email(
        self, async_client: AsyncClient, admin_headers: dict, test_user: User
    ):
        """
        Given: 既存のユーザーが存在する
        When: 同じメールアドレスでユーザーを作成しようとする
        Then: 409エラーが返される
        """
        new_user = {
            "email": test_user.email,
            "full_name": "重複 ユーザー",
            "password": "SecurePass123!"
        }
        
        response = await async_client.post(
            "/api/v1/users",
            json=new_user,
            headers=admin_headers
        )
        
        assert response.status_code == status.HTTP_409_CONFLICT
        data = response.json()
        assert data["code"] == "USER001"

    @pytest.mark.asyncio
    async def test_create_user_with_weak_password(
        self, async_client: AsyncClient, admin_headers: dict
    ):
        """
        Given: 管理者としてログイン済み
        When: 弱いパスワードでユーザーを作成しようとする
        Then: 400エラーが返される
        """
        new_user = {
            "email": "weakpass@example.com",
            "full_name": "弱パス ユーザー",
            "password": "weak"
        }
        
        response = await async_client.post(
            "/api/v1/users",
            json=new_user,
            headers=admin_headers
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "password" in str(data["detail"]).lower()


class TestUserDetail:
    """ユーザー詳細取得のテスト"""

    @pytest.mark.asyncio
    async def test_get_user_detail_as_admin(
        self, async_client: AsyncClient, admin_headers: dict, test_user: User
    ):
        """
        Given: 管理者としてログイン済み
        When: 他のユーザーの詳細を取得
        Then: ユーザー情報が返される
        """
        response = await async_client.get(
            f"/api/v1/users/{test_user.id}",
            headers=admin_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email

    @pytest.mark.asyncio
    async def test_get_nonexistent_user(
        self, async_client: AsyncClient, admin_headers: dict
    ):
        """
        Given: 管理者としてログイン済み
        When: 存在しないユーザーIDで取得を試みる
        Then: 404エラーが返される
        """
        response = await async_client.get(
            "/api/v1/users/99999",
            headers=admin_headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["code"] == "USER002"


class TestUserUpdate:
    """ユーザー更新のテスト"""

    @pytest.mark.asyncio
    async def test_update_user_as_admin(
        self, async_client: AsyncClient, admin_headers: dict, test_user: User
    ):
        """
        Given: 管理者としてログイン済み
        When: ユーザー情報を更新
        Then: 更新されたユーザー情報が返される
        """
        update_data = {
            "full_name": "更新された 名前",
            "department": "開発部"
        }
        
        response = await async_client.patch(
            f"/api/v1/users/{test_user.id}",
            json=update_data,
            headers=admin_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["full_name"] == update_data["full_name"]
        assert data["department"] == update_data["department"]

    @pytest.mark.asyncio
    async def test_update_user_role(
        self, async_client: AsyncClient, admin_headers: dict, test_user: User
    ):
        """
        Given: 管理者としてログイン済み
        When: ユーザーのロールを変更
        Then: ロールが更新される
        """
        update_data = {"role": "admin"}
        
        response = await async_client.patch(
            f"/api/v1/users/{test_user.id}",
            json=update_data,
            headers=admin_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["role"] == "admin"

    @pytest.mark.asyncio
    async def test_regular_user_cannot_update_others(
        self, async_client: AsyncClient, user_headers: dict, test_user: User
    ):
        """
        Given: 一般ユーザーとしてログイン済み
        When: 他のユーザー情報を更新しようとする
        Then: 403エラーが返される
        """
        update_data = {"full_name": "不正な更新"}
        
        response = await async_client.patch(
            f"/api/v1/users/{test_user.id}",
            json=update_data,
            headers=user_headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestUserDelete:
    """ユーザー無効化のテスト"""

    @pytest.mark.asyncio
    async def test_delete_user_as_admin(
        self, async_client: AsyncClient, admin_headers: dict, test_user: User
    ):
        """
        Given: 管理者としてログイン済み
        When: ユーザーを無効化（論理削除）
        Then: ユーザーが無効化される
        """
        response = await async_client.delete(
            f"/api/v1/users/{test_user.id}",
            headers=admin_headers
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # 無効化されたユーザーでログインできない
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user.email,
                "password": "SecurePass123!"
            }
        )
        assert login_response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_cannot_delete_self(
        self, async_client: AsyncClient, admin_headers: dict, admin_user: User
    ):
        """
        Given: 管理者としてログイン済み
        When: 自分自身を無効化しようとする
        Then: 400エラーが返される
        """
        response = await async_client.delete(
            f"/api/v1/users/{admin_user.id}",
            headers=admin_headers
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "self" in data["detail"].lower()


class TestUserMe:
    """自分のユーザー情報のテスト"""

    @pytest.mark.asyncio
    async def test_get_my_profile(
        self, async_client: AsyncClient, user_headers: dict, test_user: User
    ):
        """
        Given: ユーザーとしてログイン済み
        When: 自分のプロフィールを取得
        Then: 自分のユーザー情報が返される
        """
        response = await async_client.get(
            "/api/v1/users/me",
            headers=user_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == test_user.email
        assert data["id"] == test_user.id

    @pytest.mark.asyncio
    async def test_update_my_profile(
        self, async_client: AsyncClient, user_headers: dict
    ):
        """
        Given: ユーザーとしてログイン済み
        When: 自分のプロフィールを更新
        Then: 更新された情報が返される
        """
        update_data = {
            "full_name": "自己更新 名前",
            "department": "マーケティング部"
        }
        
        response = await async_client.patch(
            "/api/v1/users/me",
            json=update_data,
            headers=user_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["full_name"] == update_data["full_name"]
        assert data["department"] == update_data["department"]

    @pytest.mark.asyncio
    async def test_regular_user_cannot_change_own_role(
        self, async_client: AsyncClient, user_headers: dict
    ):
        """
        Given: 一般ユーザーとしてログイン済み
        When: 自分のロールを変更しようとする
        Then: 403エラーが返される（権限昇格の防止）
        """
        update_data = {"role": "admin"}
        
        response = await async_client.patch(
            "/api/v1/users/me",
            json=update_data,
            headers=user_headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        assert "role" in data["detail"].lower()


class TestUserPasswordChange:
    """パスワード変更のテスト"""

    @pytest.mark.asyncio
    async def test_change_own_password(
        self, async_client: AsyncClient, user_headers: dict
    ):
        """
        Given: ユーザーとしてログイン済み
        When: 自分のパスワードを変更
        Then: パスワードが更新される
        """
        password_data = {
            "current_password": "SecurePass123!",
            "new_password": "NewSecurePass456!"
        }
        
        response = await async_client.post(
            "/api/v1/users/me/password",
            json=password_data,
            headers=user_headers
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # 新しいパスワードでログイン可能
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "NewSecurePass456!"
            }
        )
        assert login_response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_change_password_with_wrong_current(
        self, async_client: AsyncClient, user_headers: dict
    ):
        """
        Given: ユーザーとしてログイン済み
        When: 誤った現在のパスワードで変更を試みる
        Then: 401エラーが返される
        """
        password_data = {
            "current_password": "WrongPassword123!",
            "new_password": "NewSecurePass456!"
        }
        
        response = await async_client.post(
            "/api/v1/users/me/password",
            json=password_data,
            headers=user_headers
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_password_history_check(
        self, async_client: AsyncClient, user_headers: dict
    ):
        """
        Given: ユーザーとしてログイン済み
        When: 過去5回以内に使用したパスワードを設定しようとする
        Then: 400エラーが返される
        """
        # 履歴に同じパスワードがある前提
        password_data = {
            "current_password": "SecurePass123!",
            "new_password": "SecurePass123!"  # 同じパスワード
        }
        
        response = await async_client.post(
            "/api/v1/users/me/password",
            json=password_data,
            headers=user_headers
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "history" in data["detail"].lower() or "reuse" in data["detail"].lower()