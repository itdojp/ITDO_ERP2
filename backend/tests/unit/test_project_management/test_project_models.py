"""プロジェクト管理モデルのユニットテスト"""
from datetime import date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.models.base import Base
from app.models.project_management import (
    Milestone,
    Project,
    ProjectBudget,
    ProjectMember,
    RecurringProjectInstance,
    RecurringProjectTemplate,
    Task,
    TaskDependency,
    TaskProgress,
    TaskResource,
)


@pytest.fixture
def db_session():
    """テスト用のインメモリDBセッション"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


class TestProjectModel:
    """プロジェクトモデルのテスト"""

    def test_create_project(self, db_session: Session):
        """プロジェクトの作成テスト"""
        project = Project(
            code="PROJ-2025-001",
            name="新ERPシステム導入",
            description="基幹システムの刷新プロジェクト",
            start_date=date(2025, 8, 1),
            end_date=date(2026, 3, 31),
            budget=Decimal("50000000"),
            status="planning",
            project_type="standard",
            organization_id=1,
            created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        assert project.id is not None
        assert project.code == "PROJ-2025-001"
        assert project.budget == Decimal("50000000")

    def test_project_code_unique_constraint(self, db_session: Session):
        """プロジェクトコードの一意制約テスト"""
        project1 = Project(
            code="PROJ-001",
            name="プロジェクト1",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            status="active",
            organization_id=1,
            created_by=1,
        )
        db_session.add(project1)
        db_session.commit()

        project2 = Project(
            code="PROJ-001",  # 重複コード
            name="プロジェクト2",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            status="active",
            organization_id=1,
            created_by=1,
        )
        db_session.add(project2)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_project_date_constraint(self, db_session: Session):
        """プロジェクト期間の制約テスト"""
        # 終了日が開始日より前の場合
        project = Project(
            code="PROJ-002",
            name="テストプロジェクト",
            start_date=date(2025, 12, 31),
            end_date=date(2025, 1, 1),  # 開始日より前
            status="planning",
            organization_id=1,
            created_by=1,
        )
        db_session.add(project)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_project_hierarchy(self, db_session: Session):
        """プロジェクト階層構造のテスト"""
        # 親プロジェクト
        parent = Project(
            code="PARENT-001",
            name="親プロジェクト",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            status="active",
            organization_id=1,
            created_by=1,
        )
        db_session.add(parent)
        db_session.commit()

        # サブプロジェクト
        sub1 = Project(
            code="SUB-001",
            name="サブプロジェクト1",
            parent_id=parent.id,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 6, 30),
            status="active",
            organization_id=1,
            created_by=1,
        )
        sub2 = Project(
            code="SUB-002",
            name="サブプロジェクト2",
            parent_id=parent.id,
            start_date=date(2025, 7, 1),
            end_date=date(2025, 12, 31),
            status="planning",
            organization_id=1,
            created_by=1,
        )
        db_session.add_all([sub1, sub2])
        db_session.commit()

        # リレーションシップの確認
        db_session.refresh(parent)
        assert len(parent.sub_projects) == 2
        assert sub1.parent == parent
        assert sub2.parent == parent

    def test_project_soft_delete(self, db_session: Session):
        """プロジェクトの論理削除テスト"""
        project = Project(
            code="DEL-001",
            name="削除テストプロジェクト",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            status="active",
            organization_id=1,
            created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        # 論理削除
        project.deleted_at = datetime.utcnow()
        db_session.commit()

        # 削除フラグの確認
        assert project.deleted_at is not None


class TestProjectMemberModel:
    """プロジェクトメンバーモデルのテスト"""

    def test_add_project_member(self, db_session: Session):
        """プロジェクトメンバー追加テスト"""
        # プロジェクト作成
        project = Project(
            code="MEM-001",
            name="メンバーテストプロジェクト",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            status="active",
            organization_id=1,
            created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        # メンバー追加
        member = ProjectMember(
            project_id=project.id,
            user_id=1,
            role="project_leader",
            allocation_percentage=100,
            start_date=date(2025, 1, 1),
            is_active=True,
        )
        db_session.add(member)
        db_session.commit()

        assert member.id is not None
        assert member.role == "project_leader"
        assert member.allocation_percentage == 100

    def test_member_allocation_constraint(self, db_session: Session):
        """メンバー割当率の制約テスト"""
        project = Project(
            code="ALLOC-001",
            name="割当テストプロジェクト",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            status="active",
            organization_id=1,
            created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        # 無効な割当率（101%）
        member = ProjectMember(
            project_id=project.id,
            user_id=1,
            role="developer",
            allocation_percentage=101,  # 100%超過
            start_date=date(2025, 1, 1),
        )
        db_session.add(member)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_member_unique_constraint(self, db_session: Session):
        """メンバーの一意制約テスト"""
        project = Project(
            code="UNIQ-001",
            name="一意制約テストプロジェクト",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            status="active",
            organization_id=1,
            created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        # 同じユーザーを2回追加
        member1 = ProjectMember(
            project_id=project.id,
            user_id=1,
            role="developer",
            allocation_percentage=50,
            start_date=date(2025, 1, 1),
        )
        db_session.add(member1)
        db_session.commit()

        member2 = ProjectMember(
            project_id=project.id,
            user_id=1,  # 同じユーザー
            role="tester",
            allocation_percentage=50,
            start_date=date(2025, 6, 1),
        )
        db_session.add(member2)
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestTaskModel:
    """タスクモデルのテスト"""

    def test_create_task(self, db_session: Session):
        """タスク作成テスト"""
        project = Project(
            code="TASK-001",
            name="タスクテストプロジェクト",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            status="active",
            organization_id=1,
            created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        task = Task(
            project_id=project.id,
            name="要件定義",
            description="システム要件の定義とドキュメント作成",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 2, 28),
            estimated_hours=Decimal("160"),
            status="not_started",
            priority="high",
            created_by=1,
        )
        db_session.add(task)
        db_session.commit()

        assert task.id is not None
        assert task.progress_percentage == 0
        assert task.actual_hours == Decimal("0")

    def test_task_hierarchy(self, db_session: Session):
        """タスク階層構造のテスト"""
        project = Project(
            code="WBS-001",
            name="WBSテストプロジェクト",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            status="active",
            organization_id=1,
            created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        # 親タスク
        parent_task = Task(
            project_id=project.id,
            name="開発フェーズ",
            start_date=date(2025, 3, 1),
            end_date=date(2025, 8, 31),
            status="not_started",
            created_by=1,
        )
        db_session.add(parent_task)
        db_session.commit()

        # 子タスク
        sub_task1 = Task(
            project_id=project.id,
            parent_task_id=parent_task.id,
            name="詳細設計",
            start_date=date(2025, 3, 1),
            end_date=date(2025, 4, 30),
            estimated_hours=Decimal("320"),
            status="not_started",
            priority="high",
            created_by=1,
        )
        sub_task2 = Task(
            project_id=project.id,
            parent_task_id=parent_task.id,
            name="実装",
            start_date=date(2025, 5, 1),
            end_date=date(2025, 7, 31),
            estimated_hours=Decimal("640"),
            status="not_started",
            priority="high",
            created_by=1,
        )
        db_session.add_all([sub_task1, sub_task2])
        db_session.commit()

        # リレーションシップの確認
        db_session.refresh(parent_task)
        assert len(parent_task.sub_tasks) == 2
        assert sub_task1.parent_task == parent_task

    def test_task_progress_update(self, db_session: Session):
        """タスク進捗更新テスト"""
        project = Project(
            code="PROG-001",
            name="進捗テストプロジェクト",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            status="active",
            organization_id=1,
            created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        task = Task(
            project_id=project.id,
            name="実装タスク",
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 31),
            estimated_hours=Decimal("80"),
            status="in_progress",
            created_by=1,
        )
        db_session.add(task)
        db_session.commit()

        # 進捗更新
        task.progress_percentage = 50
        task.actual_hours = Decimal("45")
        task.status = "in_progress"
        db_session.commit()

        # 進捗履歴の記録
        progress = TaskProgress(
            task_id=task.id,
            progress_percentage=50,
            actual_hours=Decimal("45"),
            comment="画面実装完了、ロジック実装中",
            updated_by=1,
        )
        db_session.add(progress)
        db_session.commit()

        assert progress.id is not None
        assert task.progress_percentage == 50


class TestTaskDependencyModel:
    """タスク依存関係モデルのテスト"""

    def test_create_dependency(self, db_session: Session):
        """タスク依存関係作成テスト"""
        project = Project(
            code="DEP-001",
            name="依存関係テストプロジェクト",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            status="active",
            organization_id=1,
            created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        # タスク作成
        task1 = Task(
            project_id=project.id,
            name="設計",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 2, 28),
            status="not_started",
            created_by=1,
        )
        task2 = Task(
            project_id=project.id,
            name="実装",
            start_date=date(2025, 3, 1),
            end_date=date(2025, 4, 30),
            status="not_started",
            created_by=1,
        )
        db_session.add_all([task1, task2])
        db_session.commit()

        # 依存関係設定（設計→実装）
        dependency = TaskDependency(
            predecessor_id=task1.id,
            successor_id=task2.id,
            dependency_type="finish_to_start",
            lag_days=0,
        )
        db_session.add(dependency)
        db_session.commit()

        assert dependency.id is not None
        assert dependency.dependency_type == "finish_to_start"

    def test_circular_dependency_prevention(self, db_session: Session):
        """循環依存の防止テスト"""
        project = Project(
            code="CIRC-001",
            name="循環依存テストプロジェクト",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            status="active",
            organization_id=1,
            created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        # タスク作成
        task = Task(
            project_id=project.id,
            name="タスクA",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
            status="not_started",
            created_by=1,
        )
        db_session.add(task)
        db_session.commit()

        # 自己参照の依存関係（エラーになるべき）
        dependency = TaskDependency(
            predecessor_id=task.id,
            successor_id=task.id,  # 自己参照
            dependency_type="finish_to_start",
        )
        db_session.add(dependency)
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestProjectBudgetModel:
    """プロジェクト予算モデルのテスト"""

    def test_create_budget(self, db_session: Session):
        """予算作成テスト"""
        project = Project(
            code="BUD-001",
            name="予算テストプロジェクト",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            budget=Decimal("10000000"),
            status="active",
            organization_id=1,
            created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        budget = ProjectBudget(
            project_id=project.id,
            budget_amount=Decimal("10000000"),
            estimated_cost=Decimal("8000000"),
            actual_cost=Decimal("0"),
            labor_cost=Decimal("0"),
            outsourcing_cost=Decimal("0"),
            expense_cost=Decimal("0"),
            revenue=Decimal("10000000"),
        )
        db_session.add(budget)
        db_session.commit()

        assert budget.id is not None
        assert budget.budget_amount == Decimal("10000000")

    def test_budget_calculation(self, db_session: Session):
        """予算計算テスト"""
        project = Project(
            code="CALC-001",
            name="計算テストプロジェクト",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            status="active",
            organization_id=1,
            created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        budget = ProjectBudget(
            project_id=project.id,
            budget_amount=Decimal("20000000"),
            estimated_cost=Decimal("15000000"),
            actual_cost=Decimal("8000000"),
            labor_cost=Decimal("5000000"),
            outsourcing_cost=Decimal("2000000"),
            expense_cost=Decimal("1000000"),
            revenue=Decimal("20000000"),
        )
        db_session.add(budget)
        db_session.commit()

        # 実績原価の内訳確認
        total_actual = (
            budget.labor_cost + budget.outsourcing_cost + budget.expense_cost
        )
        assert total_actual == budget.actual_cost


class TestRecurringProjectModel:
    """繰り返しプロジェクトモデルのテスト"""

    def test_create_recurring_template(self, db_session: Session):
        """繰り返しテンプレート作成テスト"""
        template = RecurringProjectTemplate(
            name="月次システム保守",
            code_prefix="MAINT",
            description="毎月のシステム保守作業",
            duration_days=5,
            budget_per_instance=Decimal("500000"),
            recurrence_pattern="monthly",
            template_data={
                "tasks": [
                    {"name": "バックアップ", "duration": 1},
                    {"name": "パッチ適用", "duration": 2},
                    {"name": "動作確認", "duration": 2},
                ]
            },
        )
        db_session.add(template)
        db_session.commit()

        assert template.id is not None
        assert template.recurrence_pattern == "monthly"
        assert len(template.template_data["tasks"]) == 3

    def test_create_recurring_instance(self, db_session: Session):
        """繰り返しインスタンス作成テスト"""
        # テンプレート作成
        template = RecurringProjectTemplate(
            name="週次レポート作成",
            code_prefix="REPORT",
            description="週次進捗レポート",
            duration_days=1,
            budget_per_instance=Decimal("100000"),
            recurrence_pattern="weekly",
        )
        db_session.add(template)
        db_session.commit()

        # プロジェクトインスタンス作成
        project = Project(
            code="REPORT-2025-W01",
            name="週次レポート作成 2025年第1週",
            start_date=date(2025, 1, 6),
            end_date=date(2025, 1, 6),
            budget=Decimal("100000"),
            status="planning",
            project_type="recurring",
            organization_id=1,
            created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        # インスタンスリンク
        instance = RecurringProjectInstance(
            template_id=template.id,
            project_id=project.id,
            sequence_number=1,
            scheduled_date=date(2025, 1, 6),
        )
        db_session.add(instance)
        db_session.commit()

        assert instance.id is not None
        assert instance.sequence_number == 1


class TestMilestoneModel:
    """マイルストーンモデルのテスト"""

    def test_create_milestone(self, db_session: Session):
        """マイルストーン作成テスト"""
        project = Project(
            code="MILE-001",
            name="マイルストーンテストプロジェクト",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            status="active",
            organization_id=1,
            created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        milestone = Milestone(
            project_id=project.id,
            name="要件定義完了",
            description="全ての要件が確定し、承認を得る",
            target_date=date(2025, 3, 31),
            status="pending",
            deliverable="要件定義書",
            approver_id=2,
        )
        db_session.add(milestone)
        db_session.commit()

        assert milestone.id is not None
        assert milestone.status == "pending"
        assert milestone.achieved_date is None

    def test_milestone_achievement(self, db_session: Session):
        """マイルストーン達成テスト"""
        project = Project(
            code="ACH-001",
            name="達成テストプロジェクト",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            status="active",
            organization_id=1,
            created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        milestone = Milestone(
            project_id=project.id,
            name="設計レビュー完了",
            target_date=date(2025, 4, 30),
            status="pending",
        )
        db_session.add(milestone)
        db_session.commit()

        # マイルストーン達成
        milestone.status = "achieved"
        milestone.achieved_date = date(2025, 4, 28)
        db_session.commit()

        assert milestone.status == "achieved"
        assert milestone.achieved_date < milestone.target_date  # 予定より早く達成


class TestResourceAllocationModel:
    """リソース割当モデルのテスト"""

    def test_task_resource_allocation(self, db_session: Session):
        """タスクへのリソース割当テスト"""
        project = Project(
            code="RES-001",
            name="リソーステストプロジェクト",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            status="active",
            organization_id=1,
            created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        task = Task(
            project_id=project.id,
            name="開発タスク",
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 31),
            estimated_hours=Decimal("160"),
            status="not_started",
            created_by=1,
        )
        db_session.add(task)
        db_session.commit()

        # リソース割当
        resource = TaskResource(
            task_id=task.id,
            user_id=1,
            allocation_percentage=80,
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 31),
            planned_hours=Decimal("128"),  # 160 * 0.8
        )
        db_session.add(resource)
        db_session.commit()

        assert resource.id is not None
        assert resource.planned_hours == Decimal("128")

    def test_resource_overallocation_check(self, db_session: Session):
        """リソース過剰割当チェックテスト"""
        project = Project(
            code="OVER-001",
            name="過剰割当テストプロジェクト",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            status="active",
            organization_id=1,
            created_by=1,
        )
        db_session.add(project)
        db_session.commit()

        # 複数タスク作成
        task1 = Task(
            project_id=project.id,
            name="タスク1",
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 31),
            status="not_started",
            created_by=1,
        )
        task2 = Task(
            project_id=project.id,
            name="タスク2",
            start_date=date(2025, 3, 15),
            end_date=date(2025, 4, 15),
            status="not_started",
            created_by=1,
        )
        db_session.add_all([task1, task2])
        db_session.commit()

        # 同じユーザーを複数タスクに割当
        resource1 = TaskResource(
            task_id=task1.id,
            user_id=1,
            allocation_percentage=60,
            start_date=date(2025, 3, 1),
            end_date=date(2025, 3, 31),
        )
        resource2 = TaskResource(
            task_id=task2.id,
            user_id=1,
            allocation_percentage=50,  # 合計110%で過剰割当
            start_date=date(2025, 3, 15),
            end_date=date(2025, 4, 15),
        )
        db_session.add_all([resource1, resource2])
        db_session.commit()

        # 注: 実際のアプリケーションではビジネスロジックでチェックが必要
        assert resource1.allocation_percentage + resource2.allocation_percentage > 100