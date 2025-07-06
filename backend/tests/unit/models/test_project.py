"""Project model tests."""

import pytest
from datetime import date, datetime
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessLogicError
from app.models.project import Project
from tests.factories import create_test_organization, create_test_user


class TestProjectModel:
    """Project model test class."""

    def test_project_creation(self, db_session: Session) -> None:
        """TEST-PROJ-MODEL-001: プロジェクト作成の基本テスト."""
        # Given: プロジェクト作成データ
        organization = create_test_organization()
        user = create_test_user()
        db_session.add_all([organization, user])
        db_session.commit()
        
        project_data = {
            "name": "テストプロジェクト",
            "description": "テスト用プロジェクト",
            "start_date": date(2025, 7, 1),
            "end_date": date(2025, 12, 31),
            "status": "planning",
            "organization_id": organization.id,
            "created_by": user.id
        }
        
        # When: プロジェクトを作成
        project = Project.create(db_session, **project_data)
        
        # Then: 正常に作成される
        assert project.id is not None
        assert project.name == "テストプロジェクト"
        assert project.description == "テスト用プロジェクト"
        assert project.status == "planning"
        assert project.start_date == date(2025, 7, 1)
        assert project.end_date == date(2025, 12, 31)
        assert project.organization_id == organization.id
        assert project.created_by == user.id
        assert project.created_at is not None
        assert project.updated_at is not None

    def test_project_name_validation(self, db_session: Session) -> None:
        """TEST-PROJ-MODEL-002: プロジェクト名のバリデーションテスト."""
        # Given: 必要なエンティティ
        organization = create_test_organization()
        user = create_test_user()
        db_session.add_all([organization, user])
        db_session.commit()
        
        # When/Then: 空文字列で作成→バリデーションエラー
        with pytest.raises(BusinessLogicError, match="プロジェクト名は必須です"):
            Project.create(
                db_session,
                name="",
                start_date=date(2025, 7, 1),
                organization_id=organization.id,
                created_by=user.id
            )
        
        # When/Then: 101文字で作成→バリデーションエラー
        with pytest.raises(BusinessLogicError, match="プロジェクト名は100文字以内で入力してください"):
            Project.create(
                db_session,
                name="a" * 101,
                start_date=date(2025, 7, 1),
                organization_id=organization.id,
                created_by=user.id
            )

    def test_project_status_transition(self, db_session: Session) -> None:
        """TEST-PROJ-MODEL-003: プロジェクトステータス遷移テスト."""
        # Given: 計画中のプロジェクト
        organization = create_test_organization()
        user = create_test_user()
        db_session.add_all([organization, user])
        db_session.commit()
        
        project = Project.create(
            db_session,
            name="ステータステスト",
            start_date=date(2025, 7, 1),
            status="planning",
            organization_id=organization.id,
            created_by=user.id
        )
        original_updated_at = project.updated_at
        
        # When: ステータスを実行中に変更
        project.update_status("in_progress", user.id)
        db_session.commit()
        
        # Then: ステータスが更新される
        assert project.status == "in_progress"
        assert project.updated_at > original_updated_at
        assert project.updated_by == user.id

    def test_project_date_validation(self, db_session: Session) -> None:
        """TEST-PROJ-MODEL-004: プロジェクト日付のバリデーションテスト."""
        # Given: 必要なエンティティ
        organization = create_test_organization()
        user = create_test_user()
        db_session.add_all([organization, user])
        db_session.commit()
        
        # When/Then: 終了日が開始日より前→バリデーションエラー
        with pytest.raises(BusinessLogicError, match="終了日は開始日以降である必要があります"):
            Project.create(
                db_session,
                name="日付テスト",
                start_date=date(2025, 12, 31),
                end_date=date(2025, 7, 1),
                organization_id=organization.id,
                created_by=user.id
            )

    def test_project_soft_delete(self, db_session: Session) -> None:
        """TEST-PROJ-MODEL-005: プロジェクトソフトデリートテスト."""
        # Given: 既存プロジェクト
        organization = create_test_organization()
        user = create_test_user()
        deleter = create_test_user(email="deleter@example.com")
        db_session.add_all([organization, user, deleter])
        db_session.commit()
        
        project = Project.create(
            db_session,
            name="削除テスト",
            start_date=date(2025, 7, 1),
            organization_id=organization.id,
            created_by=user.id
        )
        project_id = project.id
        
        # When: ソフトデリート実行
        project.soft_delete(db_session, deleter.id)
        db_session.commit()
        
        # Then: deleted_atが設定される
        assert project.deleted_at is not None
        assert project.deleted_by == deleter.id
        
        # And: アクティブなプロジェクトのクエリでは取得されない
        active_projects = db_session.query(Project).filter(
            Project.id == project_id,
            Project.deleted_at.is_(None)
        ).all()
        assert len(active_projects) == 0

    def test_project_status_validation(self, db_session: Session) -> None:
        """プロジェクトステータスのバリデーションテスト."""
        # Given: 必要なエンティティ
        organization = create_test_organization()
        user = create_test_user()
        db_session.add_all([organization, user])
        db_session.commit()
        
        # When/Then: 不正なステータスで作成→バリデーションエラー
        with pytest.raises(BusinessLogicError, match="不正なステータスです"):
            Project.create(
                db_session,
                name="ステータステスト",
                start_date=date(2025, 7, 1),
                status="invalid_status",
                organization_id=organization.id,
                created_by=user.id
            )

    def test_project_organization_validation(self, db_session: Session) -> None:
        """プロジェクト組織のバリデーションテスト."""
        # Given: ユーザーのみ（組織なし）
        user = create_test_user()
        db_session.add(user)
        db_session.commit()
        
        # When/Then: 存在しない組織IDで作成→バリデーションエラー
        with pytest.raises(BusinessLogicError, match="指定された組織が見つかりません"):
            Project.create(
                db_session,
                name="組織テスト",
                start_date=date(2025, 7, 1),
                organization_id=999,  # 存在しない組織ID
                created_by=user.id
            )

    def test_project_update(self, db_session: Session) -> None:
        """プロジェクト更新テスト."""
        # Given: 既存プロジェクト
        organization = create_test_organization()
        user = create_test_user()
        db_session.add_all([organization, user])
        db_session.commit()
        
        project = Project.create(
            db_session,
            name="更新前",
            start_date=date(2025, 7, 1),
            organization_id=organization.id,
            created_by=user.id
        )
        original_updated_at = project.updated_at
        
        # When: プロジェクトを更新
        project.update(
            db_session,
            name="更新後",
            description="更新された説明",
            end_date=date(2025, 12, 31),
            updated_by=user.id
        )
        db_session.commit()
        
        # Then: 更新される
        assert project.name == "更新後"
        assert project.description == "更新された説明"
        assert project.end_date == date(2025, 12, 31)
        assert project.updated_by == user.id
        assert project.updated_at > original_updated_at

    def test_project_completion(self, db_session: Session) -> None:
        """プロジェクト完了テスト."""
        # Given: 実行中のプロジェクト
        organization = create_test_organization()
        user = create_test_user()
        db_session.add_all([organization, user])
        db_session.commit()
        
        project = Project.create(
            db_session,
            name="完了テスト",
            start_date=date(2025, 7, 1),
            status="in_progress",
            organization_id=organization.id,
            created_by=user.id
        )
        
        # When: プロジェクトを完了
        project.complete(user.id)
        db_session.commit()
        
        # Then: ステータスが完了になる
        assert project.status == "completed"
        assert project.updated_by == user.id
        assert project.actual_end_date is not None

    def test_project_get_active_projects(self, db_session: Session) -> None:
        """アクティブプロジェクト取得テスト."""
        # Given: アクティブと削除済みプロジェクト
        organization = create_test_organization()
        user = create_test_user()
        db_session.add_all([organization, user])
        db_session.commit()
        
        active_project = Project.create(
            db_session,
            name="アクティブ",
            start_date=date(2025, 7, 1),
            organization_id=organization.id,
            created_by=user.id
        )
        
        deleted_project = Project.create(
            db_session,
            name="削除済み",
            start_date=date(2025, 7, 1),
            organization_id=organization.id,
            created_by=user.id
        )
        deleted_project.soft_delete(db_session, user.id)
        db_session.commit()
        
        # When: アクティブプロジェクトを取得
        active_projects = Project.get_active_projects(db_session, organization.id)
        
        # Then: アクティブプロジェクトのみ取得される
        assert len(active_projects) == 1
        assert active_projects[0].id == active_project.id
        assert active_projects[0].name == "アクティブ"