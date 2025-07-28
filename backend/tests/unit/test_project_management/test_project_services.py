"""プロジェクト管理サービスのユニットテスト"""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.models.project_management import Project, ProjectMember, Task
from app.schemas.project_management import (
    ProjectCreate,
    ProjectUpdate,
    TaskCreate,
    TaskUpdate,
)
from app.services.project_management import (
    ProjectService,
    ResourceService,
    TaskService,
)


class TestProjectService:
    """プロジェクトサービスのテスト"""

    @pytest.fixture
    def mock_db(self):
        """モックDBセッション"""
        return MagicMock(spec=Session)

    @pytest.fixture
    def project_service(self, mock_db):
        """プロジェクトサービスインスタンス"""
        return ProjectService(mock_db)

    def test_create_project(self, project_service, mock_db):
        """プロジェクト作成のテスト"""
        # テストデータ
        project_data = ProjectCreate(
            code="TEST-001",
            name="テストプロジェクト",
            description="テスト用のプロジェクト",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            budget=Decimal("10000000"),
            status="planning",
        )
        user_id = 1
        organization_id = 1

        # モックの設定
        mock_project = Project(
            id=1,
            code="TEST-001",
            name="テストプロジェクト",
            created_by=user_id,
            organization_id=organization_id,
        )
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        # 実行
        with patch("app.services.project_management.Project", return_value=mock_project):
            result = project_service.create_project(
                project_data, user_id, organization_id
            )

        # 検証
        assert result == mock_project
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_get_project_by_id(self, project_service, mock_db):
        """ID によるプロジェクト取得のテスト"""
        # モックの設定
        mock_project = Project(
            id=1,
            code="TEST-001",
            name="テストプロジェクト",
            deleted_at=None,
        )
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_project
        mock_db.query.return_value = mock_query

        # 実行
        result = project_service.get_project(1)

        # 検証
        assert result == mock_project
        mock_db.query.assert_called_with(Project)
        mock_query.filter.assert_called()

    def test_get_project_not_found(self, project_service, mock_db):
        """存在しないプロジェクト取得のテスト"""
        # モックの設定
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query

        # 実行
        result = project_service.get_project(999)

        # 検証
        assert result is None

    def test_update_project(self, project_service, mock_db):
        """プロジェクト更新のテスト"""
        # テストデータ
        project_id = 1
        update_data = ProjectUpdate(
            name="更新されたプロジェクト",
            end_date=date(2026, 3, 31),
            status="active",
        )

        # モックの設定
        mock_project = Project(
            id=project_id,
            code="TEST-001",
            name="元のプロジェクト",
            end_date=date(2025, 12, 31),
            status="planning",
        )
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_project
        mock_db.query.return_value = mock_query

        # 実行
        result = project_service.update_project(project_id, update_data)

        # 検証
        assert result.name == "更新されたプロジェクト"
        assert result.end_date == date(2026, 3, 31)
        assert result.status == "active"
        mock_db.commit.assert_called_once()

    def test_delete_project_soft_delete(self, project_service, mock_db):
        """プロジェクトの論理削除のテスト"""
        # モックの設定
        mock_project = Project(
            id=1,
            code="TEST-001",
            name="削除対象プロジェクト",
            deleted_at=None,
        )
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_project
        mock_db.query.return_value = mock_query

        # 実行
        result = project_service.delete_project(1)

        # 検証
        assert result is True
        assert mock_project.deleted_at is not None
        mock_db.commit.assert_called_once()

    def test_list_projects_with_filters(self, project_service, mock_db):
        """フィルタ付きプロジェクト一覧取得のテスト"""
        # モックの設定
        mock_projects = [
            Project(id=1, code="TEST-001", name="プロジェクト1", status="active"),
            Project(id=2, code="TEST-002", name="プロジェクト2", status="active"),
        ]
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_projects
        mock_query.count.return_value = 2
        mock_db.query.return_value = mock_query

        # 実行
        projects, total = project_service.list_projects(
            organization_id=1,
            status="active",
            skip=0,
            limit=20,
        )

        # 検証
        assert len(projects) == 2
        assert total == 2
        mock_query.filter.assert_called()

    def test_add_project_member(self, project_service, mock_db):
        """プロジェクトメンバー追加のテスト"""
        # テストデータ
        project_id = 1
        user_id = 2
        role = "developer"
        allocation = 80

        # モックの設定
        mock_project = Project(id=project_id)
        mock_member = ProjectMember(
            project_id=project_id,
            user_id=user_id,
            role=role,
            allocation_percentage=allocation,
        )
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_project
        mock_db.query.return_value = mock_query

        # 実行
        with patch(
            "app.services.project_management.ProjectMember", return_value=mock_member
        ):
            result = project_service.add_member(
                project_id, user_id, role, allocation, date(2025, 1, 1)
            )

        # 検証
        assert result.user_id == user_id
        assert result.role == role
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_calculate_project_progress(self, project_service, mock_db):
        """プロジェクト進捗計算のテスト"""
        # モックの設定
        mock_tasks = [
            Task(
                id=1, progress_percentage=100, estimated_hours=Decimal("40")
            ),  # 完了
            Task(
                id=2, progress_percentage=50, estimated_hours=Decimal("80")
            ),  # 進行中
            Task(
                id=3, progress_percentage=0, estimated_hours=Decimal("40")
            ),  # 未着手
        ]
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = mock_tasks
        mock_db.query.return_value = mock_query

        # 実行
        progress = project_service.calculate_project_progress(1)

        # 検証
        # 加重平均: (100*40 + 50*80 + 0*40) / (40+80+40) = 8000/160 = 50%
        assert progress == 50

    def test_check_project_hierarchy_depth(self, project_service, mock_db):
        """プロジェクト階層深度チェックのテスト"""
        # 最大5階層までの制限をテスト
        parent_id = 1
        current_depth = 0

        # モックの設定
        def get_parent_project(project_id):
            if current_depth < 4:  # 4階層まで親が存在
                return Project(id=project_id, parent_id=project_id + 1)
            return Project(id=project_id, parent_id=None)

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.side_effect = lambda: get_parent_project(parent_id)
        mock_db.query.return_value = mock_query

        # 実行
        depth = project_service.get_project_depth(parent_id)

        # 検証
        assert depth <= 5  # 最大5階層


class TestTaskService:
    """タスクサービスのテスト"""

    @pytest.fixture
    def mock_db(self):
        """モックDBセッション"""
        return MagicMock(spec=Session)

    @pytest.fixture
    def task_service(self, mock_db):
        """タスクサービスインスタンス"""
        return TaskService(mock_db)

    def test_create_task(self, task_service, mock_db):
        """タスク作成のテスト"""
        # テストデータ
        task_data = TaskCreate(
            name="要件定義",
            description="システム要件の定義",
            project_id=1,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 2, 28),
            estimated_hours=Decimal("160"),
            priority="high",
        )
        user_id = 1

        # モックの設定
        mock_task = Task(
            id=1,
            name="要件定義",
            project_id=1,
            created_by=user_id,
        )
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        # 実行
        with patch("app.services.project_management.Task", return_value=mock_task):
            result = task_service.create_task(task_data, user_id)

        # 検証
        assert result == mock_task
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_update_task_progress(self, task_service, mock_db):
        """タスク進捗更新のテスト"""
        # テストデータ
        task_id = 1
        progress = 75
        actual_hours = Decimal("120")
        comment = "実装75%完了"
        user_id = 1

        # モックの設定
        mock_task = Task(
            id=task_id,
            progress_percentage=50,
            actual_hours=Decimal("80"),
            status="in_progress",
        )
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_task
        mock_db.query.return_value = mock_query

        # 実行
        result = task_service.update_progress(
            task_id, progress, actual_hours, comment, user_id
        )

        # 検証
        assert result.progress_percentage == 75
        assert result.actual_hours == Decimal("120")
        mock_db.add.assert_called_once()  # 進捗履歴の追加
        mock_db.commit.assert_called_once()

    def test_create_task_dependency(self, task_service, mock_db):
        """タスク依存関係作成のテスト"""
        # テストデータ
        predecessor_id = 1
        successor_id = 2
        dependency_type = "finish_to_start"
        lag_days = 2

        # モックの設定
        mock_dependency = MagicMock()
        mock_db.add.return_value = None
        mock_db.commit.return_value = None

        # 循環依存チェックのモック
        with patch.object(
            task_service, "_check_circular_dependency", return_value=False
        ):
            # 実行
            result = task_service.create_dependency(
                predecessor_id, successor_id, dependency_type, lag_days
            )

        # 検証
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_detect_circular_dependency(self, task_service, mock_db):
        """循環依存検出のテスト"""
        # テストデータ: A -> B -> C -> A の循環
        task_a = Task(id=1, name="タスクA")
        task_b = Task(id=2, name="タスクB")
        task_c = Task(id=3, name="タスクC")

        # 依存関係の設定
        dependencies = {
            1: [2],  # A -> B
            2: [3],  # B -> C
            3: [1],  # C -> A (循環)
        }

        # モックの設定
        def get_successors(task_id):
            return dependencies.get(task_id, [])

        with patch.object(task_service, "_get_successor_ids", side_effect=get_successors):
            # 実行
            has_circular = task_service._check_circular_dependency(1, 1)

        # 検証
        assert has_circular is True

    def test_calculate_critical_path(self, task_service, mock_db):
        """クリティカルパス計算のテスト"""
        # テストデータ
        project_id = 1

        # タスクのモック
        tasks = [
            Task(
                id=1,
                name="設計",
                start_date=date(2025, 1, 1),
                end_date=date(2025, 1, 31),
                estimated_hours=Decimal("160"),
            ),
            Task(
                id=2,
                name="実装",
                start_date=date(2025, 2, 1),
                end_date=date(2025, 3, 31),
                estimated_hours=Decimal("320"),
            ),
            Task(
                id=3,
                name="テスト",
                start_date=date(2025, 4, 1),
                end_date=date(2025, 4, 30),
                estimated_hours=Decimal("160"),
            ),
        ]

        # 依存関係: 設計 -> 実装 -> テスト
        dependencies = [(1, 2), (2, 3)]

        # モックの設定
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = tasks
        mock_db.query.return_value = mock_query

        with patch.object(
            task_service, "_get_task_dependencies", return_value=dependencies
        ):
            # 実行
            critical_path = task_service.calculate_critical_path(project_id)

        # 検証
        assert len(critical_path) == 3
        assert critical_path == [1, 2, 3]

    def test_auto_schedule_tasks(self, task_service, mock_db):
        """タスク自動スケジューリングのテスト"""
        # テストデータ
        project_id = 1
        project_start = date(2025, 1, 1)

        # タスクのモック（期間のみ設定、日付は未設定）
        tasks = [
            Task(id=1, name="タスク1", estimated_hours=Decimal("40")),  # 5日
            Task(id=2, name="タスク2", estimated_hours=Decimal("80")),  # 10日
            Task(id=3, name="タスク3", estimated_hours=Decimal("40")),  # 5日
        ]

        # 依存関係: 1 -> 2, 1 -> 3（並行実行可能）
        dependencies = {1: [2, 3]}

        # モックの設定
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = tasks
        mock_db.query.return_value = mock_query

        with patch.object(task_service, "_get_dependencies", return_value=dependencies):
            # 実行
            scheduled_tasks = task_service.auto_schedule(project_id, project_start)

        # 検証
        assert len(scheduled_tasks) == 3
        # タスク1は開始日から
        assert scheduled_tasks[0].start_date == project_start
        # タスク2と3はタスク1の後
        assert scheduled_tasks[1].start_date > scheduled_tasks[0].end_date
        assert scheduled_tasks[2].start_date > scheduled_tasks[0].end_date


class TestResourceService:
    """リソースサービスのテスト"""

    @pytest.fixture
    def mock_db(self):
        """モックDBセッション"""
        return MagicMock(spec=Session)

    @pytest.fixture
    def resource_service(self, mock_db):
        """リソースサービスインスタンス"""
        return ResourceService(mock_db)

    def test_check_resource_availability(self, resource_service, mock_db):
        """リソース利用可能性チェックのテスト"""
        # テストデータ
        user_id = 1
        start_date = date(2025, 3, 1)
        end_date = date(2025, 3, 31)
        required_percentage = 60

        # 既存の割当（40%使用中）
        existing_allocations = [
            MagicMock(allocation_percentage=40, start_date=date(2025, 3, 1), end_date=date(2025, 3, 15))
        ]

        # モックの設定
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = existing_allocations
        mock_db.query.return_value = mock_query

        # 実行
        is_available = resource_service.check_availability(
            user_id, start_date, end_date, required_percentage
        )

        # 検証
        assert is_available is True  # 40% + 60% = 100% なので利用可能

    def test_detect_overallocation(self, resource_service, mock_db):
        """リソース過剰割当検出のテスト"""
        # テストデータ
        user_id = 1
        start_date = date(2025, 3, 1)
        end_date = date(2025, 3, 31)

        # 既存の割当（合計120%で過剰）
        existing_allocations = [
            MagicMock(
                allocation_percentage=60,
                start_date=date(2025, 3, 1),
                end_date=date(2025, 3, 31),
            ),
            MagicMock(
                allocation_percentage=60,
                start_date=date(2025, 3, 15),
                end_date=date(2025, 4, 15),
            ),
        ]

        # モックの設定
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = existing_allocations
        mock_db.query.return_value = mock_query

        # 実行
        overallocated_periods = resource_service.get_overallocations(
            user_id, start_date, end_date
        )

        # 検証
        assert len(overallocated_periods) > 0
        assert overallocated_periods[0]["percentage"] == 120

    def test_calculate_resource_utilization(self, resource_service, mock_db):
        """リソース稼働率計算のテスト"""
        # テストデータ
        user_id = 1
        start_date = date(2025, 3, 1)
        end_date = date(2025, 3, 31)

        # タスク割当
        allocations = [
            MagicMock(
                allocation_percentage=80,
                start_date=date(2025, 3, 1),
                end_date=date(2025, 3, 15),
                actual_hours=Decimal("96"),  # 15日 * 8時間 * 0.8
            ),
            MagicMock(
                allocation_percentage=60,
                start_date=date(2025, 3, 16),
                end_date=date(2025, 3, 31),
                actual_hours=Decimal("76.8"),  # 16日 * 8時間 * 0.6
            ),
        ]

        # モックの設定
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = allocations
        mock_db.query.return_value = mock_query

        # 実行
        utilization = resource_service.calculate_utilization(
            user_id, start_date, end_date
        )

        # 検証
        assert "average_utilization" in utilization
        assert "peak_utilization" in utilization
        assert utilization["average_utilization"] > 0
        assert utilization["peak_utilization"] >= utilization["average_utilization"]

    def test_find_available_resources(self, resource_service, mock_db):
        """利用可能リソース検索のテスト"""
        # テストデータ
        required_skills = ["Python", "React"]
        start_date = date(2025, 4, 1)
        end_date = date(2025, 4, 30)
        min_availability = 60

        # 利用可能なユーザー
        available_users = [
            MagicMock(id=1, name="開発者A", skills=["Python", "React", "Django"]),
            MagicMock(id=2, name="開発者B", skills=["Python", "React", "Vue"]),
        ]

        # モックの設定
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = available_users
        mock_db.query.return_value = mock_query

        # 各ユーザーの稼働率チェックをモック
        with patch.object(
            resource_service, "check_availability", return_value=True
        ):
            # 実行
            resources = resource_service.find_available_resources(
                required_skills, start_date, end_date, min_availability
            )

        # 検証
        assert len(resources) == 2
        assert all(
            all(skill in user.skills for skill in required_skills)
            for user in resources
        )

    def test_resource_allocation_forecast(self, resource_service, mock_db):
        """リソース割当予測のテスト"""
        # テストデータ
        project_id = 1
        forecast_months = 3

        # プロジェクトタスク
        tasks = [
            MagicMock(
                id=1,
                start_date=date(2025, 4, 1),
                end_date=date(2025, 4, 30),
                estimated_hours=Decimal("160"),
            ),
            MagicMock(
                id=2,
                start_date=date(2025, 5, 1),
                end_date=date(2025, 6, 30),
                estimated_hours=Decimal("320"),
            ),
        ]

        # モックの設定
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = tasks
        mock_db.query.return_value = mock_query

        # 実行
        forecast = resource_service.forecast_resource_needs(
            project_id, forecast_months
        )

        # 検証
        assert "total_hours" in forecast
        assert "required_resources" in forecast
        assert forecast["total_hours"] == Decimal("480")  # 160 + 320