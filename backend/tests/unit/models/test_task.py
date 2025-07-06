"""Task model tests."""

import pytest
from datetime import date, datetime
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessLogicError
from app.models.task import Task
from tests.factories import create_test_organization, create_test_user, create_test_project


class TestTaskModel:
    """Task model test class."""

    def test_task_creation(self, db_session: Session) -> None:
        """TEST-TASK-MODEL-001: タスク作成の基本テスト."""
        # Given: プロジェクトとタスクデータ
        organization = create_test_organization()
        user = create_test_user()
        db_session.add_all([organization, user])
        db_session.commit()
        
        project = create_test_project(organization_id=organization.id, created_by=user.id)
        db_session.add(project)
        db_session.commit()
        
        task_data = {
            "title": "テストタスク",
            "description": "テスト用タスク",
            "status": "not_started",
            "priority": "medium",
            "project_id": project.id,
            "created_by": user.id
        }
        
        # When: タスクを作成
        task = Task.create(db_session, **task_data)
        
        # Then: 正常に作成される
        assert task.id is not None
        assert task.title == "テストタスク"
        assert task.description == "テスト用タスク"
        assert task.status == "not_started"
        assert task.priority == "medium"
        assert task.project_id == project.id
        assert task.created_by == user.id
        assert task.created_at is not None
        assert task.updated_at is not None

    def test_task_title_validation(self, db_session: Session) -> None:
        """TEST-TASK-MODEL-002: タスクタイトルのバリデーションテスト."""
        # Given: 必要なエンティティ
        organization = create_test_organization()
        user = create_test_user()
        db_session.add_all([organization, user])
        db_session.commit()
        
        project = create_test_project(organization_id=organization.id, created_by=user.id)
        db_session.add(project)
        db_session.commit()
        
        # When/Then: 空文字列で作成→バリデーションエラー
        with pytest.raises(BusinessLogicError, match="タスクタイトルは必須です"):
            Task.create(
                db_session,
                title="",
                project_id=project.id,
                created_by=user.id
            )
        
        # When/Then: 201文字で作成→バリデーションエラー
        with pytest.raises(BusinessLogicError, match="タスクタイトルは200文字以内で入力してください"):
            Task.create(
                db_session,
                title="a" * 201,
                project_id=project.id,
                created_by=user.id
            )

    def test_task_priority_and_status(self, db_session: Session) -> None:
        """TEST-TASK-MODEL-003: タスク優先度とステータスのテスト."""
        # Given: 必要なエンティティ
        organization = create_test_organization()
        user = create_test_user()
        db_session.add_all([organization, user])
        db_session.commit()
        
        project = create_test_project(organization_id=organization.id, created_by=user.id)
        db_session.add(project)
        db_session.commit()
        
        # Given: 各優先度とステータス
        priorities = ["low", "medium", "high", "urgent"]
        statuses = ["not_started", "in_progress", "completed", "on_hold"]
        
        for priority in priorities:
            for status in statuses:
                # When: タスクを作成
                task = Task.create(
                    db_session,
                    title=f"タスク_{priority}_{status}",
                    priority=priority,
                    status=status,
                    project_id=project.id,
                    created_by=user.id
                )
                
                # Then: 正常に作成される
                assert task.priority == priority
                assert task.status == status

    def test_task_assignment(self, db_session: Session) -> None:
        """TEST-TASK-MODEL-004: タスク担当者割り当てテスト."""
        # Given: プロジェクトとユーザー
        organization = create_test_organization()
        creator = create_test_user(email="creator@example.com")
        assignee = create_test_user(email="assignee@example.com")
        db_session.add_all([organization, creator, assignee])
        db_session.commit()
        
        project = create_test_project(organization_id=organization.id, created_by=creator.id)
        db_session.add(project)
        db_session.commit()
        
        # When: 担当者を割り当て
        task = Task.create(
            db_session,
            title="担当者テスト",
            project_id=project.id,
            assigned_to=assignee.id,
            created_by=creator.id
        )
        
        # Then: 担当者が設定される
        assert task.assigned_to == assignee.id
        assert task.assignee.email == assignee.email

    def test_task_date_management(self, db_session: Session) -> None:
        """TEST-TASK-MODEL-005: タスク日付管理テスト."""
        # Given: 必要なエンティティ
        organization = create_test_organization()
        user = create_test_user()
        db_session.add_all([organization, user])
        db_session.commit()
        
        project = create_test_project(organization_id=organization.id, created_by=user.id)
        db_session.add(project)
        db_session.commit()
        
        # Given: 日付を指定してタスクを作成
        task = Task.create(
            db_session,
            title="日付テスト",
            project_id=project.id,
            estimated_start_date=date(2025, 7, 1),
            estimated_end_date=date(2025, 7, 31),
            created_by=user.id
        )
        
        # When: 実際の日付を更新
        task.start_task(user.id)  # actual_start_dateを設定
        db_session.commit()
        
        task.complete_task(user.id)  # actual_end_dateを設定
        db_session.commit()
        
        # Then: 実際の日付が設定される
        assert task.actual_start_date is not None
        assert task.actual_end_date is not None
        assert task.status == "completed"
        assert task.updated_by == user.id

    def test_task_status_validation(self, db_session: Session) -> None:
        """タスクステータスのバリデーションテスト."""
        # Given: 必要なエンティティ
        organization = create_test_organization()
        user = create_test_user()
        db_session.add_all([organization, user])
        db_session.commit()
        
        project = create_test_project(organization_id=organization.id, created_by=user.id)
        db_session.add(project)
        db_session.commit()
        
        # When/Then: 不正なステータスで作成→バリデーションエラー
        with pytest.raises(BusinessLogicError, match="不正なステータスです"):
            Task.create(
                db_session,
                title="ステータステスト",
                project_id=project.id,
                status="invalid_status",
                created_by=user.id
            )

    def test_task_priority_validation(self, db_session: Session) -> None:
        """タスク優先度のバリデーションテスト."""
        # Given: 必要なエンティティ
        organization = create_test_organization()
        user = create_test_user()
        db_session.add_all([organization, user])
        db_session.commit()
        
        project = create_test_project(organization_id=organization.id, created_by=user.id)
        db_session.add(project)
        db_session.commit()
        
        # When/Then: 不正な優先度で作成→バリデーションエラー
        with pytest.raises(BusinessLogicError, match="不正な優先度です"):
            Task.create(
                db_session,
                title="優先度テスト",
                project_id=project.id,
                priority="invalid_priority",
                created_by=user.id
            )

    def test_task_project_validation(self, db_session: Session) -> None:
        """タスクプロジェクトのバリデーションテスト."""
        # Given: ユーザーのみ（プロジェクトなし）
        user = create_test_user()
        db_session.add(user)
        db_session.commit()
        
        # When/Then: 存在しないプロジェクトIDで作成→バリデーションエラー
        with pytest.raises(BusinessLogicError, match="指定されたプロジェクトが見つかりません"):
            Task.create(
                db_session,
                title="プロジェクトテスト",
                project_id=999,  # 存在しないプロジェクトID
                created_by=user.id
            )

    def test_task_update(self, db_session: Session) -> None:
        """タスク更新テスト."""
        # Given: 既存タスク
        organization = create_test_organization()
        user = create_test_user()
        db_session.add_all([organization, user])
        db_session.commit()
        
        project = create_test_project(organization_id=organization.id, created_by=user.id)
        db_session.add(project)
        db_session.commit()
        
        task = Task.create(
            db_session,
            title="更新前",
            project_id=project.id,
            created_by=user.id
        )
        original_updated_at = task.updated_at
        
        # When: タスクを更新
        task.update(
            db_session,
            title="更新後",
            description="更新された説明",
            priority="high",
            updated_by=user.id
        )
        db_session.commit()
        
        # Then: 更新される
        assert task.title == "更新後"
        assert task.description == "更新された説明"
        assert task.priority == "high"
        assert task.updated_by == user.id
        assert task.updated_at > original_updated_at

    def test_task_soft_delete(self, db_session: Session) -> None:
        """タスクソフトデリートテスト."""
        # Given: 既存タスク
        organization = create_test_organization()
        user = create_test_user()
        deleter = create_test_user(email="deleter@example.com")
        db_session.add_all([organization, user, deleter])
        db_session.commit()
        
        project = create_test_project(organization_id=organization.id, created_by=user.id)
        db_session.add(project)
        db_session.commit()
        
        task = Task.create(
            db_session,
            title="削除テスト",
            project_id=project.id,
            created_by=user.id
        )
        task_id = task.id
        
        # When: ソフトデリート実行
        task.soft_delete(db_session, deleter.id)
        db_session.commit()
        
        # Then: deleted_atが設定される
        assert task.deleted_at is not None
        assert task.deleted_by == deleter.id
        
        # And: アクティブなタスクのクエリでは取得されない
        active_tasks = db_session.query(Task).filter(
            Task.id == task_id,
            Task.deleted_at.is_(None)
        ).all()
        assert len(active_tasks) == 0

    def test_task_get_by_project(self, db_session: Session) -> None:
        """プロジェクト別タスク取得テスト."""
        # Given: プロジェクトと複数タスク
        organization = create_test_organization()
        user = create_test_user()
        db_session.add_all([organization, user])
        db_session.commit()
        
        project1 = create_test_project(name="プロジェクト1", organization_id=organization.id, created_by=user.id)
        project2 = create_test_project(name="プロジェクト2", organization_id=organization.id, created_by=user.id)
        db_session.add_all([project1, project2])
        db_session.commit()
        
        # プロジェクト1のタスク
        task1 = Task.create(db_session, title="タスク1", project_id=project1.id, created_by=user.id)
        task2 = Task.create(db_session, title="タスク2", project_id=project1.id, created_by=user.id)
        
        # プロジェクト2のタスク
        task3 = Task.create(db_session, title="タスク3", project_id=project2.id, created_by=user.id)
        
        db_session.commit()
        
        # When: プロジェクト1のタスクを取得
        project1_tasks = Task.get_by_project(db_session, project1.id)
        
        # Then: プロジェクト1のタスクのみ取得される
        assert len(project1_tasks) == 2
        task_titles = [task.title for task in project1_tasks]
        assert "タスク1" in task_titles
        assert "タスク2" in task_titles
        assert "タスク3" not in task_titles

    def test_task_estimated_date_validation(self, db_session: Session) -> None:
        """タスク予定日のバリデーションテスト."""
        # Given: 必要なエンティティ
        organization = create_test_organization()
        user = create_test_user()
        db_session.add_all([organization, user])
        db_session.commit()
        
        project = create_test_project(organization_id=organization.id, created_by=user.id)
        db_session.add(project)
        db_session.commit()
        
        # When/Then: 終了予定日が開始予定日より前→バリデーションエラー
        with pytest.raises(BusinessLogicError, match="終了予定日は開始予定日以降である必要があります"):
            Task.create(
                db_session,
                title="日付テスト",
                project_id=project.id,
                estimated_start_date=date(2025, 7, 31),
                estimated_end_date=date(2025, 7, 1),
                created_by=user.id
            )