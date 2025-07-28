"""プロジェクト管理システムのサービス層"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessLogicError, NotFoundError
from app.models.project_management import (
    Milestone,
    Project,
    ProjectBudget,
    ProjectMember,
    Task,
    TaskDependency,
    TaskProgress,
    TaskResource,
)
from app.models.user import User
from app.schemas.project_management import (
    MilestoneCreate,
    ProjectCreate,
    ProjectUpdate,
    RecurringProjectCreate,
    TaskCreate,
    TaskUpdate,
)


class ProjectService:
    """プロジェクトサービス"""

    def __init__(self, db: Session):
        self.db = db

    def create_project(
        self, project_data: ProjectCreate, user_id: int, organization_id: int
    ) -> Project:
        """プロジェクトを作成"""
        # 親プロジェクトの階層チェック
        if project_data.parent_id:
            parent_depth = self.get_project_depth(project_data.parent_id)
            if parent_depth >= 5:
                raise BusinessLogicError("プロジェクトの階層は最大5階層までです")

        # プロジェクト作成
        project = Project(
            **project_data.model_dump(),
            created_by=user_id,
            organization_id=organization_id,
        )
        self.db.add(project)

        # 予算情報を作成
        budget = ProjectBudget(
            project_id=project.id,
            budget_amount=project_data.budget,
        )
        self.db.add(budget)

        self.db.commit()
        self.db.refresh(project)
        return project

    def get_project(self, project_id: int) -> Optional[Project]:
        """プロジェクトを取得"""
        return (
            self.db.query(Project)
            .filter(Project.id == project_id, Project.deleted_at.is_(None))
            .first()
        )

    def update_project(self, project_id: int, update_data: ProjectUpdate) -> Project:
        """プロジェクトを更新"""
        project = self.get_project(project_id)
        if not project:
            raise NotFoundError("プロジェクトが見つかりません")

        for key, value in update_data.model_dump(exclude_unset=True).items():
            setattr(project, key, value)

        project.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(project)
        return project

    def delete_project(self, project_id: int) -> bool:
        """プロジェクトを削除（論理削除）"""
        project = self.get_project(project_id)
        if not project:
            return False

        project.deleted_at = datetime.now()
        self.db.commit()
        return True

    def list_projects(
        self,
        organization_id: int,
        status: Optional[str] = None,
        parent_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Project], int]:
        """プロジェクト一覧を取得"""
        query = self.db.query(Project).filter(
            Project.organization_id == organization_id,
            Project.deleted_at.is_(None),
        )

        if status:
            query = query.filter(Project.status == status)
        if parent_id is not None:
            query = query.filter(Project.parent_id == parent_id)

        total = query.count()
        projects = query.offset(skip).limit(limit).all()
        return projects, total

    def get_project_depth(self, project_id: int) -> int:
        """プロジェクトの階層深度を取得"""
        depth = 0
        current_id = project_id

        while current_id and depth < 10:  # 無限ループ防止
            project = self.db.query(Project).filter(Project.id == current_id).first()
            if not project or not project.parent_id:
                break
            current_id = project.parent_id
            depth += 1

        return depth

    def add_member(
        self,
        project_id: int,
        user_id: int,
        role: str,
        allocation_percentage: int,
        start_date: date,
        end_date: Optional[date] = None,
    ) -> ProjectMember:
        """プロジェクトメンバーを追加"""
        # 既存メンバーチェック
        existing = (
            self.db.query(ProjectMember)
            .filter(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id,
                ProjectMember.is_active.is_(True),
            )
            .first()
        )
        if existing:
            raise BusinessLogicError("既にプロジェクトメンバーです")

        member = ProjectMember(
            project_id=project_id,
            user_id=user_id,
            role=role,
            allocation_percentage=allocation_percentage,
            start_date=start_date,
            end_date=end_date,
        )
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        return member

    def remove_member(self, project_id: int, user_id: int) -> bool:
        """プロジェクトメンバーを削除"""
        member = (
            self.db.query(ProjectMember)
            .filter(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id,
                ProjectMember.is_active.is_(True),
            )
            .first()
        )
        if not member:
            return False

        member.is_active = False
        member.end_date = date.today()
        self.db.commit()
        return True

    def calculate_project_progress(self, project_id: int) -> int:
        """プロジェクトの進捗率を計算"""
        tasks = (
            self.db.query(Task)
            .filter(
                Task.project_id == project_id,
                Task.deleted_at.is_(None),
            )
            .all()
        )

        if not tasks:
            return 0

        # 工数による加重平均
        total_hours = sum(task.estimated_hours or 0 for task in tasks)
        if total_hours == 0:
            # 工数が設定されていない場合は単純平均
            return int(sum(task.progress_percentage for task in tasks) / len(tasks))

        weighted_progress = sum(
            (task.estimated_hours or 0) * task.progress_percentage for task in tasks
        )
        return int(weighted_progress / total_hours)

    def get_budget_summary(self, project_id: int) -> Dict:
        """プロジェクトの予算サマリーを取得"""
        budget = (
            self.db.query(ProjectBudget)
            .filter(ProjectBudget.project_id == project_id)
            .first()
        )

        if not budget:
            return {
                "budget_amount": Decimal("0"),
                "actual_cost": Decimal("0"),
                "consumption_rate": 0.0,
            }

        consumption_rate = (
            float(budget.actual_cost / budget.budget_amount * 100)
            if budget.budget_amount > 0
            else 0.0
        )

        return {
            "budget_amount": budget.budget_amount,
            "actual_cost": budget.actual_cost,
            "consumption_rate": consumption_rate,
        }

    def create_recurring_projects(
        self, recurring_data: RecurringProjectCreate, user_id: int, organization_id: int
    ) -> List[Project]:
        """繰り返しプロジェクトを作成"""
        projects = []
        template_data = recurring_data.template

        # 繰り返しパターンに基づいて日付を計算
        current_date = recurring_data.start_date
        for i in range(recurring_data.recurrence_count):
            # プロジェクトコードにシーケンス番号を付与
            project_data = template_data.model_copy()
            project_data.code = f"{template_data.code}-{i + 1:03d}"
            project_data.name = f"{template_data.name} #{i + 1}"
            project_data.start_date = current_date

            # 終了日を計算
            duration = template_data.end_date - template_data.start_date
            project_data.end_date = current_date + duration

            # プロジェクトを作成
            project = self.create_project(project_data, user_id, organization_id)
            projects.append(project)

            # 次の開始日を計算
            if recurring_data.recurrence_pattern == "daily":
                current_date += timedelta(days=1)
            elif recurring_data.recurrence_pattern == "weekly":
                current_date += timedelta(weeks=1)
            elif recurring_data.recurrence_pattern == "monthly":
                # 月末処理を考慮
                if current_date.month == 12:
                    current_date = current_date.replace(
                        year=current_date.year + 1, month=1
                    )
                else:
                    current_date = current_date.replace(month=current_date.month + 1)
            elif recurring_data.recurrence_pattern == "yearly":
                current_date = current_date.replace(year=current_date.year + 1)

        return projects


class TaskService:
    """タスクサービス"""

    def __init__(self, db: Session):
        self.db = db

    def create_task(self, task_data: TaskCreate, user_id: int) -> Task:
        """タスクを作成"""
        # 親タスクの存在確認
        if task_data.parent_task_id:
            parent = self.get_task(task_data.parent_task_id)
            if not parent:
                raise NotFoundError("親タスクが見つかりません")

        task = Task(**task_data.model_dump(), created_by=user_id)
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def get_task(self, task_id: int) -> Optional[Task]:
        """タスクを取得"""
        return (
            self.db.query(Task)
            .filter(Task.id == task_id, Task.deleted_at.is_(None))
            .first()
        )

    def update_task(self, task_id: int, update_data: TaskUpdate) -> Task:
        """タスクを更新"""
        task = self.get_task(task_id)
        if not task:
            raise NotFoundError("タスクが見つかりません")

        for key, value in update_data.model_dump(exclude_unset=True).items():
            setattr(task, key, value)

        # ステータスの自動更新
        if hasattr(update_data, "progress_percentage"):
            if update_data.progress_percentage == 0:
                task.status = "not_started"
            elif update_data.progress_percentage == 100:
                task.status = "completed"
            else:
                task.status = "in_progress"

        task.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(task)
        return task

    def delete_task(self, task_id: int) -> bool:
        """タスクを削除（論理削除）"""
        task = self.get_task(task_id)
        if not task:
            return False

        task.deleted_at = datetime.now()
        self.db.commit()
        return True

    def update_progress(
        self,
        task_id: int,
        progress_percentage: int,
        actual_hours: Decimal,
        comment: Optional[str],
        user_id: int,
    ) -> Task:
        """タスクの進捗を更新"""
        task = self.get_task(task_id)
        if not task:
            raise NotFoundError("タスクが見つかりません")

        # 進捗履歴を記録
        progress_entry = TaskProgress(
            task_id=task_id,
            progress_percentage=progress_percentage,
            actual_hours=actual_hours,
            comment=comment,
            updated_by=user_id,
        )
        self.db.add(progress_entry)

        # タスクを更新
        task.progress_percentage = progress_percentage
        task.actual_hours = actual_hours

        # ステータスの自動更新
        if progress_percentage == 0:
            task.status = "not_started"
        elif progress_percentage == 100:
            task.status = "completed"
        else:
            task.status = "in_progress"

        task.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(task)
        return task

    def create_dependency(
        self,
        predecessor_id: int,
        successor_id: int,
        dependency_type: str = "finish_to_start",
        lag_days: int = 0,
    ) -> TaskDependency:
        """タスク依存関係を作成"""
        # 循環依存チェック
        if self._check_circular_dependency(predecessor_id, successor_id):
            raise BusinessLogicError("循環依存が発生します")

        dependency = TaskDependency(
            predecessor_id=predecessor_id,
            successor_id=successor_id,
            dependency_type=dependency_type,
            lag_days=lag_days,
        )
        self.db.add(dependency)
        self.db.commit()
        self.db.refresh(dependency)
        return dependency

    def _check_circular_dependency(
        self, predecessor_id: int, new_successor_id: int
    ) -> bool:
        """循環依存をチェック"""
        visited = set()

        def has_path(from_id: int, to_id: int) -> bool:
            if from_id == to_id:
                return True
            if from_id in visited:
                return False

            visited.add(from_id)
            successors = self._get_successor_ids(from_id)

            for successor in successors:
                if has_path(successor, to_id):
                    return True

            return False

        return has_path(new_successor_id, predecessor_id)

    def _get_successor_ids(self, task_id: int) -> List[int]:
        """タスクの後続タスクIDを取得"""
        dependencies = (
            self.db.query(TaskDependency)
            .filter(TaskDependency.predecessor_id == task_id)
            .all()
        )
        return [dep.successor_id for dep in dependencies]

    def get_task_tree(self, project_id: int) -> List[Task]:
        """プロジェクトのタスクツリーを取得"""
        tasks = (
            self.db.query(Task)
            .filter(
                Task.project_id == project_id,
                Task.deleted_at.is_(None),
            )
            .all()
        )

        # 親タスクIDでグループ化
        task_map = {task.id: task for task in tasks}
        root_tasks = []

        for task in tasks:
            if task.parent_task_id is None:
                root_tasks.append(task)
            else:
                parent = task_map.get(task.parent_task_id)
                if parent:
                    if not hasattr(parent, "sub_tasks"):
                        parent.sub_tasks = []
                    parent.sub_tasks.append(task)

        return root_tasks

    def calculate_critical_path(self, project_id: int) -> List[int]:
        """クリティカルパスを計算"""
        tasks = (
            self.db.query(Task)
            .filter(
                Task.project_id == project_id,
                Task.deleted_at.is_(None),
            )
            .all()
        )

        if not tasks:
            return []

        # タスクの依存関係を取得
        task_ids = [task.id for task in tasks]
        dependencies = (
            self.db.query(TaskDependency)
            .filter(
                TaskDependency.predecessor_id.in_(task_ids),
                TaskDependency.successor_id.in_(task_ids),
            )
            .all()
        )

        # ネットワーク図を構築してクリティカルパスを計算
        # 簡略化のため、最長パスを返す
        task_map = {task.id: task for task in tasks}

        # 各タスクの最早開始時刻を計算
        earliest_start = {}
        for task in tasks:
            earliest_start[task.id] = 0

        # トポロジカルソート順に処理
        changed = True
        while changed:
            changed = False
            for dep in dependencies:
                pred_task = task_map[dep.predecessor_id]
                pred_finish = (
                    earliest_start[dep.predecessor_id]
                    + (pred_task.end_date - pred_task.start_date).days
                )

                if earliest_start[dep.successor_id] < pred_finish + dep.lag_days:
                    earliest_start[dep.successor_id] = pred_finish + dep.lag_days
                    changed = True

        # 最も遅く終わるタスクから逆算してクリティカルパスを特定
        critical_path = []
        max_finish = max(
            earliest_start[task.id] + (task.end_date - task.start_date).days
            for task in tasks
        )

        # 簡略化のため、最長パスのタスクIDを返す
        for task in sorted(tasks, key=lambda t: earliest_start[t.id], reverse=True):
            finish = earliest_start[task.id] + (task.end_date - task.start_date).days
            if finish == max_finish:
                critical_path.append(task.id)

        return critical_path

    def auto_schedule(self, project_id: int, start_date: date) -> List[Task]:
        """タスクを自動スケジューリング"""
        tasks = (
            self.db.query(Task)
            .filter(
                Task.project_id == project_id,
                Task.deleted_at.is_(None),
            )
            .all()
        )

        if not tasks:
            return []

        # 依存関係を取得
        dependencies = self._get_dependencies(project_id)

        # トポロジカルソートでタスクを並べ替え
        sorted_tasks = self._topological_sort(tasks, dependencies)

        # 各タスクの開始日・終了日を計算
        task_dates = {}
        for task in sorted_tasks:
            # 前提タスクの最遅終了日を取得
            latest_finish = start_date
            for pred_id in dependencies.get(task.id, {}).get("predecessors", []):
                if pred_id in task_dates:
                    pred_finish = task_dates[pred_id]["end_date"]
                    if pred_finish >= latest_finish:
                        latest_finish = pred_finish + timedelta(days=1)

            # タスクの期間を計算（8時間/日で計算）
            duration_days = int((task.estimated_hours or 40) / 8)

            # 開始日・終了日を設定
            task.start_date = latest_finish
            task.end_date = latest_finish + timedelta(days=duration_days - 1)

            task_dates[task.id] = {
                "start_date": task.start_date,
                "end_date": task.end_date,
            }

        # 更新をコミット
        self.db.commit()
        return sorted_tasks

    def _get_dependencies(self, project_id: int) -> Dict:
        """プロジェクトの依存関係を取得"""
        tasks = (
            self.db.query(Task)
            .filter(
                Task.project_id == project_id,
                Task.deleted_at.is_(None),
            )
            .all()
        )

        task_ids = [task.id for task in tasks]
        dependencies = (
            self.db.query(TaskDependency)
            .filter(
                TaskDependency.predecessor_id.in_(task_ids),
                TaskDependency.successor_id.in_(task_ids),
            )
            .all()
        )

        # 依存関係マップを構築
        dep_map = {}
        for task_id in task_ids:
            dep_map[task_id] = {"predecessors": [], "successors": []}

        for dep in dependencies:
            dep_map[dep.successor_id]["predecessors"].append(dep.predecessor_id)
            dep_map[dep.predecessor_id]["successors"].append(dep.successor_id)

        return dep_map

    def _topological_sort(self, tasks: List[Task], dependencies: Dict) -> List[Task]:
        """タスクをトポロジカルソート"""
        task_map = {task.id: task for task in tasks}
        visited = set()
        result = []

        def visit(task_id: int):
            if task_id in visited:
                return
            visited.add(task_id)

            # 前提タスクを先に処理
            for pred_id in dependencies.get(task_id, {}).get("predecessors", []):
                if pred_id not in visited:
                    visit(pred_id)

            result.append(task_map[task_id])

        # すべてのタスクを処理
        for task in tasks:
            visit(task.id)

        return result


class ResourceService:
    """リソース管理サービス"""

    def __init__(self, db: Session):
        self.db = db

    def check_availability(
        self,
        user_id: int,
        start_date: date,
        end_date: date,
        required_percentage: int,
    ) -> bool:
        """リソースの利用可能性をチェック"""
        # 期間内の既存割当を取得
        existing_allocations = (
            self.db.query(TaskResource)
            .filter(
                TaskResource.user_id == user_id,
                or_(
                    and_(
                        TaskResource.start_date <= start_date,
                        TaskResource.end_date >= start_date,
                    ),
                    and_(
                        TaskResource.start_date <= end_date,
                        TaskResource.end_date >= end_date,
                    ),
                    and_(
                        TaskResource.start_date >= start_date,
                        TaskResource.end_date <= end_date,
                    ),
                ),
            )
            .all()
        )

        # 日ごとの割当率を計算
        daily_allocation = {}
        current_date = start_date
        while current_date <= end_date:
            daily_allocation[current_date] = 0
            current_date += timedelta(days=1)

        for allocation in existing_allocations:
            alloc_start = max(allocation.start_date or start_date, start_date)
            alloc_end = min(allocation.end_date or end_date, end_date)

            current_date = alloc_start
            while current_date <= alloc_end:
                daily_allocation[current_date] += allocation.allocation_percentage
                current_date += timedelta(days=1)

        # 利用可能性をチェック
        for date_key, total_percentage in daily_allocation.items():
            if total_percentage + required_percentage > 100:
                return False

        return True

    def assign_resource(
        self,
        task_id: int,
        user_id: int,
        allocation_percentage: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        planned_hours: Optional[Decimal] = None,
    ) -> TaskResource:
        """リソースをタスクに割り当て"""
        # タスクの存在確認
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise NotFoundError("タスクが見つかりません")

        # デフォルト日付の設定
        if not start_date:
            start_date = task.start_date
        if not end_date:
            end_date = task.end_date

        # 利用可能性チェック
        if not self.check_availability(
            user_id, start_date, end_date, allocation_percentage
        ):
            raise BusinessLogicError("リソースが利用できません")

        resource = TaskResource(
            task_id=task_id,
            user_id=user_id,
            allocation_percentage=allocation_percentage,
            start_date=start_date,
            end_date=end_date,
            planned_hours=planned_hours,
        )
        self.db.add(resource)
        self.db.commit()
        self.db.refresh(resource)
        return resource

    def get_overallocations(
        self, user_id: int, start_date: date, end_date: date
    ) -> List[Dict]:
        """過剰割当期間を取得"""
        allocations = (
            self.db.query(TaskResource)
            .filter(
                TaskResource.user_id == user_id,
                or_(
                    and_(
                        TaskResource.start_date <= start_date,
                        TaskResource.end_date >= start_date,
                    ),
                    and_(
                        TaskResource.start_date <= end_date,
                        TaskResource.end_date >= end_date,
                    ),
                    and_(
                        TaskResource.start_date >= start_date,
                        TaskResource.end_date <= end_date,
                    ),
                ),
            )
            .all()
        )

        # 日ごとの割当率を計算
        daily_allocation = {}
        current_date = start_date
        while current_date <= end_date:
            daily_allocation[current_date] = 0
            current_date += timedelta(days=1)

        for allocation in allocations:
            alloc_start = max(allocation.start_date or start_date, start_date)
            alloc_end = min(allocation.end_date or end_date, end_date)

            current_date = alloc_start
            while current_date <= alloc_end:
                daily_allocation[current_date] += allocation.allocation_percentage
                current_date += timedelta(days=1)

        # 過剰割当期間を抽出
        overallocations = []
        for date_key, total_percentage in daily_allocation.items():
            if total_percentage > 100:
                overallocations.append(
                    {
                        "date": date_key,
                        "percentage": total_percentage,
                    }
                )

        return overallocations

    def calculate_utilization(
        self, user_id: int, start_date: date, end_date: date
    ) -> Dict:
        """リソース稼働率を計算"""
        allocations = (
            self.db.query(TaskResource)
            .filter(
                TaskResource.user_id == user_id,
                or_(
                    and_(
                        TaskResource.start_date <= start_date,
                        TaskResource.end_date >= start_date,
                    ),
                    and_(
                        TaskResource.start_date <= end_date,
                        TaskResource.end_date >= end_date,
                    ),
                    and_(
                        TaskResource.start_date >= start_date,
                        TaskResource.end_date <= end_date,
                    ),
                ),
            )
            .all()
        )

        # 日ごとの稼働率を計算
        daily_utilization = {}
        current_date = start_date
        total_days = 0
        while current_date <= end_date:
            daily_utilization[current_date] = 0
            current_date += timedelta(days=1)
            total_days += 1

        for allocation in allocations:
            alloc_start = max(allocation.start_date or start_date, start_date)
            alloc_end = min(allocation.end_date or end_date, end_date)

            current_date = alloc_start
            while current_date <= alloc_end:
                daily_utilization[current_date] += allocation.allocation_percentage
                current_date += timedelta(days=1)

        # 統計を計算
        utilization_values = list(daily_utilization.values())
        average_utilization = (
            sum(utilization_values) / total_days if total_days > 0 else 0
        )
        peak_utilization = max(utilization_values) if utilization_values else 0
        overallocated_days = sum(1 for v in utilization_values if v > 100)

        return {
            "average_utilization": average_utilization,
            "peak_utilization": peak_utilization,
            "overallocated_days": overallocated_days,
            "daily_utilization": [
                {"date": date_key, "utilization": value}
                for date_key, value in daily_utilization.items()
            ],
        }

    def find_available_resources(
        self,
        required_skills: List[str],
        start_date: date,
        end_date: date,
        min_availability: int = 50,
    ) -> List[User]:
        """利用可能なリソースを検索"""
        # スキルを持つユーザーを検索
        # TODO: スキルマスタが実装されたら、スキルによるフィルタリングを追加
        users = self.db.query(User).filter(User.is_active.is_(True)).all()

        available_users = []
        for user in users:
            # 利用可能性をチェック
            if self.check_availability(user.id, start_date, end_date, min_availability):
                available_users.append(user)

        return available_users

    def forecast_resource_needs(self, project_id: int, months_ahead: int = 3) -> Dict:
        """リソース需要を予測"""
        # プロジェクトのタスクを取得
        end_date = date.today() + timedelta(days=months_ahead * 30)
        tasks = (
            self.db.query(Task)
            .filter(
                Task.project_id == project_id,
                Task.deleted_at.is_(None),
                Task.start_date <= end_date,
            )
            .all()
        )

        # 月ごとの必要工数を計算
        monthly_hours = {}
        for task in tasks:
            if task.start_date <= end_date:
                month_key = task.start_date.strftime("%Y-%m")
                if month_key not in monthly_hours:
                    monthly_hours[month_key] = Decimal("0")
                monthly_hours[month_key] += task.estimated_hours or Decimal("0")

        # 必要リソース数を計算（160時間/月として）
        monthly_resources = {}
        for month, hours in monthly_hours.items():
            monthly_resources[month] = int(hours / 160) + (1 if hours % 160 > 0 else 0)

        total_hours = sum(monthly_hours.values())

        return {
            "total_hours": total_hours,
            "monthly_hours": monthly_hours,
            "required_resources": monthly_resources,
        }


class MilestoneService:
    """マイルストーンサービス"""

    def __init__(self, db: Session):
        self.db = db

    def create_milestone(
        self, project_id: int, milestone_data: MilestoneCreate
    ) -> Milestone:
        """マイルストーンを作成"""
        milestone = Milestone(
            project_id=project_id,
            **milestone_data.model_dump(),
        )
        self.db.add(milestone)
        self.db.commit()
        self.db.refresh(milestone)
        return milestone

    def update_milestone_status(
        self, milestone_id: int, status: str, achieved_date: Optional[date] = None
    ) -> Milestone:
        """マイルストーンのステータスを更新"""
        milestone = (
            self.db.query(Milestone).filter(Milestone.id == milestone_id).first()
        )
        if not milestone:
            raise NotFoundError("マイルストーンが見つかりません")

        milestone.status = status
        if status == "achieved" and achieved_date:
            milestone.achieved_date = achieved_date
        elif status == "achieved" and not achieved_date:
            milestone.achieved_date = date.today()

        self.db.commit()
        self.db.refresh(milestone)
        return milestone

    def get_project_milestones(
        self, project_id: int, status: Optional[str] = None
    ) -> List[Milestone]:
        """プロジェクトのマイルストーンを取得"""
        query = self.db.query(Milestone).filter(Milestone.project_id == project_id)

        if status:
            query = query.filter(Milestone.status == status)

        return query.order_by(Milestone.target_date).all()


class BudgetService:
    """予算管理サービス"""

    def __init__(self, db: Session):
        self.db = db

    def update_budget(
        self,
        project_id: int,
        budget_amount: Optional[Decimal] = None,
        estimated_cost: Optional[Decimal] = None,
        actual_cost: Optional[Decimal] = None,
    ) -> ProjectBudget:
        """プロジェクト予算を更新"""
        budget = (
            self.db.query(ProjectBudget)
            .filter(ProjectBudget.project_id == project_id)
            .first()
        )

        if not budget:
            budget = ProjectBudget(project_id=project_id)
            self.db.add(budget)

        if budget_amount is not None:
            budget.budget_amount = budget_amount
        if estimated_cost is not None:
            budget.estimated_cost = estimated_cost
        if actual_cost is not None:
            budget.actual_cost = actual_cost

        budget.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(budget)
        return budget

    def calculate_budget_variance(self, project_id: int) -> Dict:
        """予算差異を計算"""
        budget = (
            self.db.query(ProjectBudget)
            .filter(ProjectBudget.project_id == project_id)
            .first()
        )

        if not budget:
            return {
                "budget_variance": Decimal("0"),
                "cost_variance": Decimal("0"),
                "variance_percentage": 0.0,
            }

        budget_variance = budget.budget_amount - budget.actual_cost
        cost_variance = budget.estimated_cost - budget.actual_cost
        variance_percentage = (
            float(budget_variance / budget.budget_amount * 100)
            if budget.budget_amount > 0
            else 0.0
        )

        return {
            "budget_variance": budget_variance,
            "cost_variance": cost_variance,
            "variance_percentage": variance_percentage,
        }

    def update_cost_breakdown(
        self,
        project_id: int,
        labor_cost: Optional[Decimal] = None,
        outsourcing_cost: Optional[Decimal] = None,
        expense_cost: Optional[Decimal] = None,
    ) -> ProjectBudget:
        """コスト内訳を更新"""
        budget = (
            self.db.query(ProjectBudget)
            .filter(ProjectBudget.project_id == project_id)
            .first()
        )

        if not budget:
            raise NotFoundError("予算情報が見つかりません")

        if labor_cost is not None:
            budget.labor_cost = labor_cost
        if outsourcing_cost is not None:
            budget.outsourcing_cost = outsourcing_cost
        if expense_cost is not None:
            budget.expense_cost = expense_cost

        # 実績コストを再計算
        budget.actual_cost = (
            budget.labor_cost + budget.outsourcing_cost + budget.expense_cost
        )

        budget.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(budget)
        return budget

    def calculate_project_profitability(self, project_id: int) -> Dict:
        """プロジェクト収益性を計算"""
        budget = (
            self.db.query(ProjectBudget)
            .filter(ProjectBudget.project_id == project_id)
            .first()
        )

        if not budget:
            return {
                "revenue": Decimal("0"),
                "profit": Decimal("0"),
                "profit_rate": 0.0,
            }

        profit = budget.revenue - budget.actual_cost
        profit_rate = (
            float(profit / budget.revenue * 100) if budget.revenue > 0 else 0.0
        )

        return {
            "revenue": budget.revenue,
            "profit": profit,
            "profit_rate": profit_rate,
        }
