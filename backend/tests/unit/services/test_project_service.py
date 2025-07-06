"""Project service tests."""

import pytest
from datetime import date
from sqlalchemy.orm import Session

from app.core.exceptions import PermissionDenied, NotFound
from app.services.project import ProjectService
from app.schemas.project import ProjectCreateRequest, ProjectSearchParams, ProjectUpdateRequest
from tests.factories import create_test_organization, create_test_user, create_test_project, create_test_role, create_test_user_role


class TestProjectService:
    """Project service test class."""

    def test_project_service_create(self, db_session: Session) -> None:
        """TEST-PROJ-SERVICE-001: プロジェクト作成サービステスト."""
        # Given: プロジェクトサービスと作成者
        service = ProjectService()
        organization = create_test_organization()
        creator = create_test_user()
        db_session.add_all([organization, creator])
        db_session.commit()
        
        project_data = ProjectCreateRequest(
            name="サービステスト",
            description="テスト用プロジェクト",
            start_date=date(2025, 7, 1),
            end_date=date(2025, 12, 31),
            organization_id=organization.id
        )
        
        # When: プロジェクトを作成
        project = service.create_project(
            data=project_data,
            creator=creator,
            db=db_session
        )
        
        # Then: 正常に作成される
        assert project.name == "サービステスト"
        assert project.description == "テスト用プロジェクト"
        assert project.start_date == date(2025, 7, 1)
        assert project.end_date == date(2025, 12, 31)
        assert project.organization_id == organization.id
        assert project.created_by == creator.id

    def test_project_service_multi_tenant_isolation(self, db_session: Session) -> None:
        """TEST-PROJ-SERVICE-002: マルチテナント分離テスト."""
        # Given: 異なる組織のユーザーとプロジェクト
        org1 = create_test_organization(code="ORG1")
        org2 = create_test_organization(code="ORG2")
        
        org1_user = create_test_user(email="user1@org1.com")
        org2_user = create_test_user(email="user2@org2.com")
        
        # ユーザーロール設定
        member_role = create_test_role(code="MEMBER")
        create_test_user_role(user=org1_user, role=member_role, organization=org1)
        create_test_user_role(user=org2_user, role=member_role, organization=org2)
        
        db_session.add_all([org1, org2, org1_user, org2_user, member_role])
        db_session.commit()
        
        org1_project = create_test_project(
            name="組織1プロジェクト",
            organization_id=org1.id,
            created_by=org1_user.id
        )
        db_session.add(org1_project)
        db_session.commit()
        
        service = ProjectService()
        
        # When: 組織2のユーザーが組織1のプロジェクトにアクセス
        with pytest.raises(PermissionDenied, match="このプロジェクトへのアクセス権限がありません"):
            # Then: アクセスが拒否される
            service.get_project(
                project_id=org1_project.id,
                viewer=org2_user,
                db=db_session
            )

    def test_project_service_search_filters(self, db_session: Session) -> None:
        """TEST-PROJ-SERVICE-003: プロジェクト検索フィルタテスト."""
        # Given: 複数のプロジェクト
        organization = create_test_organization()
        user = create_test_user()
        member_role = create_test_role(code="MEMBER")
        create_test_user_role(user=user, role=member_role, organization=organization)
        
        db_session.add_all([organization, user, member_role])
        db_session.commit()
        
        projects = [
            create_test_project(
                name="プロジェクトA",
                status="planning",
                organization_id=organization.id,
                created_by=user.id
            ),
            create_test_project(
                name="プロジェクトB",
                status="in_progress",
                organization_id=organization.id,
                created_by=user.id
            ),
            create_test_project(
                name="プロジェクトC",
                status="completed",
                organization_id=organization.id,
                created_by=user.id
            )
        ]
        db_session.add_all(projects)
        db_session.commit()
        
        service = ProjectService()
        
        # When: ステータスでフィルタ
        search_params = ProjectSearchParams(status="in_progress")
        result = service.search_projects(
            params=search_params,
            searcher=user,
            db=db_session
        )
        
        # Then: 該当するプロジェクトのみ返される
        assert result.total == 1
        assert result.items[0].name == "プロジェクトB"
        assert result.items[0].status == "in_progress"

    def test_project_service_permission_check(self, db_session: Session) -> None:
        """TEST-PROJ-SERVICE-004: プロジェクト権限チェックテスト."""
        # Given: プロジェクトと一般ユーザー、管理者
        organization = create_test_organization()
        normal_user = create_test_user(email="normal@example.com")
        admin_user = create_test_user(email="admin@example.com", is_superuser=True)
        creator = create_test_user(email="creator@example.com")
        
        member_role = create_test_role(code="MEMBER")
        admin_role = create_test_role(code="PROJECT_ADMIN")
        
        create_test_user_role(user=normal_user, role=member_role, organization=organization)
        create_test_user_role(user=creator, role=admin_role, organization=organization)
        
        db_session.add_all([organization, normal_user, admin_user, creator, member_role, admin_role])
        db_session.commit()
        
        project = create_test_project(
            name="権限テスト",
            organization_id=organization.id,
            created_by=creator.id
        )
        db_session.add(project)
        db_session.commit()
        
        service = ProjectService()
        
        # When: 一般ユーザーがプロジェクトを削除しようとする
        with pytest.raises(PermissionDenied, match="プロジェクトを削除する権限がありません"):
            # Then: 権限エラーが発生
            service.delete_project(
                project_id=project.id,
                deleter=normal_user,
                db=db_session
            )
        
        # When: 管理者がプロジェクトを削除
        service.delete_project(
            project_id=project.id,
            deleter=admin_user,
            db=db_session
        )
        
        # Then: 正常に削除される
        db_session.refresh(project)
        assert project.deleted_at is not None

    def test_project_service_get_project_detail(self, db_session: Session) -> None:
        """プロジェクト詳細取得サービステスト."""
        # Given: プロジェクトとユーザー
        organization = create_test_organization()
        user = create_test_user()
        member_role = create_test_role(code="MEMBER")
        create_test_user_role(user=user, role=member_role, organization=organization)
        
        db_session.add_all([organization, user, member_role])
        db_session.commit()
        
        project = create_test_project(
            name="詳細テスト",
            description="詳細取得テスト",
            organization_id=organization.id,
            created_by=user.id
        )
        db_session.add(project)
        db_session.commit()
        
        service = ProjectService()
        
        # When: プロジェクト詳細を取得
        result = service.get_project(
            project_id=project.id,
            viewer=user,
            db=db_session
        )
        
        # Then: プロジェクト詳細が返される
        assert result.id == project.id
        assert result.name == "詳細テスト"
        assert result.description == "詳細取得テスト"
        assert result.organization_id == organization.id

    def test_project_service_update_project(self, db_session: Session) -> None:
        """プロジェクト更新サービステスト."""
        # Given: プロジェクトと更新者
        organization = create_test_organization()
        user = create_test_user()
        admin_role = create_test_role(code="PROJECT_ADMIN")
        create_test_user_role(user=user, role=admin_role, organization=organization)
        
        db_session.add_all([organization, user, admin_role])
        db_session.commit()
        
        project = create_test_project(
            name="更新前",
            organization_id=organization.id,
            created_by=user.id
        )
        db_session.add(project)
        db_session.commit()
        
        update_data = ProjectUpdateRequest(
            name="更新後",
            description="更新されたプロジェクト",
            status="in_progress"
        )
        
        service = ProjectService()
        
        # When: プロジェクトを更新
        updated_project = service.update_project(
            project_id=project.id,
            data=update_data,
            updater=user,
            db=db_session
        )
        
        # Then: プロジェクトが更新される
        assert updated_project.name == "更新後"
        assert updated_project.description == "更新されたプロジェクト"
        assert updated_project.status == "in_progress"
        assert updated_project.updated_by == user.id

    def test_project_service_not_found(self, db_session: Session) -> None:
        """存在しないプロジェクトアクセステスト."""
        # Given: ユーザーのみ（プロジェクトなし）
        user = create_test_user()
        db_session.add(user)
        db_session.commit()
        
        service = ProjectService()
        
        # When: 存在しないプロジェクトにアクセス
        with pytest.raises(NotFound, match="プロジェクトが見つかりません"):
            # Then: NotFoundエラーが発生
            service.get_project(
                project_id=999,
                viewer=user,
                db=db_session
            )

    def test_project_service_search_by_name(self, db_session: Session) -> None:
        """プロジェクト名検索テスト."""
        # Given: 複数のプロジェクト
        organization = create_test_organization()
        user = create_test_user()
        member_role = create_test_role(code="MEMBER")
        create_test_user_role(user=user, role=member_role, organization=organization)
        
        db_session.add_all([organization, user, member_role])
        db_session.commit()
        
        projects = [
            create_test_project(
                name="重要プロジェクト",
                organization_id=organization.id,
                created_by=user.id
            ),
            create_test_project(
                name="一般プロジェクト",
                organization_id=organization.id,
                created_by=user.id
            ),
            create_test_project(
                name="重要な改善プロジェクト",
                organization_id=organization.id,
                created_by=user.id
            )
        ]
        db_session.add_all(projects)
        db_session.commit()
        
        service = ProjectService()
        
        # When: 名前で検索
        search_params = ProjectSearchParams(search="重要")
        result = service.search_projects(
            params=search_params,
            searcher=user,
            db=db_session
        )
        
        # Then: 該当するプロジェクトのみ返される
        assert result.total == 2
        project_names = [item.name for item in result.items]
        assert "重要プロジェクト" in project_names
        assert "重要な改善プロジェクト" in project_names
        assert "一般プロジェクト" not in project_names

    def test_project_service_create_permission_check(self, db_session: Session) -> None:
        """プロジェクト作成権限チェックテスト."""
        # Given: 組織メンバーでないユーザー
        organization = create_test_organization()
        outsider = create_test_user(email="outsider@example.com")
        
        db_session.add_all([organization, outsider])
        db_session.commit()
        
        project_data = ProjectCreateRequest(
            name="権限なしテスト",
            start_date=date(2025, 7, 1),
            organization_id=organization.id
        )
        
        service = ProjectService()
        
        # When: 組織外ユーザーがプロジェクトを作成しようとする
        with pytest.raises(PermissionDenied, match="組織へのアクセス権限がありません"):
            # Then: 権限エラーが発生
            service.create_project(
                data=project_data,
                creator=outsider,
                db=db_session
            )