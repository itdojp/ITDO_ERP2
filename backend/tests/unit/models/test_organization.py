"""
Organization model unit tests.

Following TDD approach - Red phase: Writing tests before implementation.
"""

from datetime import datetime

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.organization import Organization
from tests.factories import create_test_organization, create_test_user


class TestOrganizationModel:
    """Test cases for Organization model."""

    def test_create_organization(self, db_session) -> None:
        """TEST-ORG-001: 組織が正しく作成されることを確認."""
        # Given: 組織データ
        org_data = {
            "code": "ITDO",
            "name": "株式会社ITDO",
            "name_kana": "カブシキガイシャアイティーディーオー",
            "postal_code": "100-0001",
            "address_line1": "東京都千代田区...",
            "phone": "03-1234-5678",
            "email": "info@itdo.jp",
            "website": "https://itdo.jp",
            "fiscal_year_end": "03-31",
        }

        # When: 組織作成
        org = Organization(**org_data)
        db_session.add(org)
        db_session.commit()

        # Then:
        assert org.id is not None
        assert org.code == "ITDO"
        assert org.name == "株式会社ITDO"
        assert org.email == "info@itdo.jp"
        assert org.fiscal_year_end == "03-31"
        assert org.is_active is True
        assert isinstance(org.created_at, datetime)
        assert isinstance(org.updated_at, datetime)

    def test_duplicate_organization_code(self, db_session) -> None:
        """TEST-ORG-002: 重複する組織コードが拒否されることを確認."""
        # Given: 既存組織
        create_test_organization(db_session, code="ITDO")

        # When/Then: 同じコードで作成時に例外
        org2 = Organization(code="ITDO", name="新組織")
        db_session.add(org2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_update_organization(self, db_session) -> None:
        """TEST-ORG-003: 組織情報が更新できることを確認."""
        # Given: 既存組織
        org = create_test_organization(
            db_session, name="旧名称", email="old@example.com"
        )
        original_created_at = org.created_at

        # When: 更新
        org.update(db=db_session, updated_by=1, name="新名称", email="new@example.com")
        db_session.commit()

        # Then:
        assert org.name == "新名称"
        assert org.email == "new@example.com"
        assert org.created_at == original_created_at
        assert org.updated_at > original_created_at

    def test_soft_delete_organization(self, db_session) -> None:
        """組織の論理削除が正しく動作することを確認."""
        # Given: アクティブな組織
        org = create_test_organization(db_session, is_active=True)

        # When: 論理削除
        org.is_active = False
        db_session.commit()

        # Then:
        assert org.is_active is False
        # データは物理的に残っている
        assert db_session.query(Organization).filter_by(id=org.id).first() is not None

    def test_organization_created_by_tracking(self, db_session) -> None:
        """組織作成者が記録されることを確認."""
        # Given: ユーザー
        user = create_test_user(db_session)

        # When: 組織作成
        org = Organization(code="TRACK", name="追跡テスト", created_by=user.id)
        db_session.add(org)
        db_session.commit()

        # Then:
        assert org.created_by == user.id
        assert org.creator.id == user.id

    def test_organization_validation(self, db_session) -> None:
        """組織データのバリデーションが動作することを確認."""
        # Invalid fiscal year end format
        with pytest.raises(ValueError):
            org = Organization(
                code="INVALID",
                name="無効な組織",
                fiscal_year_end="invalid",  # 無効な形式
            )
            org.validate()

    def test_organization_string_representation(self, db_session) -> None:
        """組織の文字列表現が正しいことを確認."""
        # Given: 組織
        org = Organization(code="REPR", name="表現テスト株式会社")

        # Then:
        assert str(org) == "REPR - 表現テスト株式会社"
        assert repr(org).startswith("<Organization(")

    def test_organization_to_dict(self, db_session) -> None:
        """組織データの辞書変換が正しいことを確認."""
        # Given: 組織
        org = create_test_organization(db_session)

        # When: 辞書変換
        org_dict = org.to_dict()

        # Then:
        assert isinstance(org_dict, dict)
        assert org_dict["id"] == org.id
        assert org_dict["code"] == org.code
        assert org_dict["name"] == org.name
        assert "created_at" in org_dict
        assert "updated_at" in org_dict
