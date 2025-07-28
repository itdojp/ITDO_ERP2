"""プロジェクト管理システムのAPIエンドポイント"""

from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.schemas.project_management import (
    BudgetResponse,
    BudgetUpdate,
    GanttChartResponse,
    MilestoneCreate,
    MilestoneListResponse,
    MilestoneResponse,
    ProgressReportResponse,
    ProgressUpdate,
    ProjectCreate,
    ProjectDetailResponse,
    ProjectListResponse,
    ProjectMemberCreate,
    ProjectMemberListResponse,
    ProjectResponse,
    ProjectUpdate,
    RecurringProjectCreate,
    RecurringProjectResponse,
    ResourceAssignment,
    ResourceListResponse,
    TaskCreate,
    TaskDependencyCreate,
    TaskDetailResponse,
    TaskResponse,
    TaskTreeResponse,
    TaskUpdate,
    UtilizationResponse,
)
from app.services.project_management import (
    BudgetService,
    MilestoneService,
    ProjectService,
    ResourceService,
    TaskService,
)

router = APIRouter(prefix="/projects", tags=["projects"])


# プロジェクト関連エンドポイント


@router.post("/", response_model=ProjectResponse)
def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ProjectResponse:
    """プロジェクトを作成"""
    service = ProjectService(db)

    # 現在のユーザーの組織IDを取得
    organization_id = current_user.organization_memberships[0].organization_id

    try:
        result = service.create_project(project, current_user.id, organization_id)
        return ProjectResponse.model_validate(result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{project_id}", response_model=ProjectDetailResponse)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ProjectDetailResponse:
    """プロジェクトの詳細を取得"""
    service = ProjectService(db)
    project = service.get_project(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="プロジェクトが見つかりません")

    # 権限チェック
    user_org_ids = [om.organization_id for om in current_user.organization_memberships]
    if project.organization_id not in user_org_ids:
        raise HTTPException(status_code=403, detail="アクセス権限がありません")

    # 追加情報を取得
    budget_summary = service.get_budget_summary(project_id)

    response = ProjectDetailResponse.model_validate(project)
    response.budget_info = budget_summary
    return response


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ProjectResponse:
    """プロジェクトを更新"""
    service = ProjectService(db)

    # 存在確認と権限チェック
    project = service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="プロジェクトが見つかりません")

    user_org_ids = [om.organization_id for om in current_user.organization_memberships]
    if project.organization_id not in user_org_ids:
        raise HTTPException(status_code=403, detail="アクセス権限がありません")

    try:
        result = service.update_project(project_id, project_update)
        return ProjectResponse.model_validate(result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """プロジェクトを削除"""
    service = ProjectService(db)

    # 存在確認と権限チェック
    project = service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="プロジェクトが見つかりません")

    user_org_ids = [om.organization_id for om in current_user.organization_memberships]
    if project.organization_id not in user_org_ids:
        raise HTTPException(status_code=403, detail="アクセス権限がありません")

    if not service.delete_project(project_id):
        raise HTTPException(status_code=400, detail="プロジェクトの削除に失敗しました")


@router.get("/", response_model=ProjectListResponse)
def list_projects(
    status: Optional[str] = Query(None),
    parent_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ProjectListResponse:
    """プロジェクト一覧を取得"""
    service = ProjectService(db)

    # 現在のユーザーの組織IDを取得
    organization_id = current_user.organization_memberships[0].organization_id

    skip = (page - 1) * page_size
    projects, total = service.list_projects(
        organization_id=organization_id,
        status=status,
        parent_id=parent_id,
        skip=skip,
        limit=page_size,
    )

    return ProjectListResponse(
        items=[ProjectResponse.model_validate(p) for p in projects],
        total=total,
        page=page,
        page_size=page_size,
    )


# プロジェクトメンバー関連エンドポイント


@router.post("/{project_id}/members", response_model=ProjectMemberListResponse)
def add_project_member(
    project_id: int,
    member: ProjectMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ProjectMemberListResponse:
    """プロジェクトメンバーを追加"""
    service = ProjectService(db)

    # プロジェクトの存在確認と権限チェック
    project = service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="プロジェクトが見つかりません")

    try:
        service.add_member(
            project_id=project_id,
            user_id=member.user_id,
            role=member.role,
            allocation_percentage=member.allocation_percentage,
            start_date=member.start_date,
            end_date=member.end_date,
        )
        # メンバー一覧を返す
        return ProjectMemberListResponse(
            items=[m for m in project.members if m.is_active],
            total=len([m for m in project.members if m.is_active]),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/{project_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT
)
def remove_project_member(
    project_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """プロジェクトメンバーを削除"""
    service = ProjectService(db)

    # プロジェクトの存在確認と権限チェック
    project = service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="プロジェクトが見つかりません")

    if not service.remove_member(project_id, user_id):
        raise HTTPException(status_code=400, detail="メンバーの削除に失敗しました")


# タスク関連エンドポイント


@router.post("/{project_id}/tasks", response_model=TaskResponse)
def create_task(
    project_id: int,
    task: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TaskResponse:
    """タスクを作成"""
    service = TaskService(db)

    # プロジェクトの存在確認
    project_service = ProjectService(db)
    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="プロジェクトが見つかりません")

    try:
        # project_idを設定
        task_data = task.model_copy()
        task_data.project_id = project_id

        result = service.create_task(task_data, current_user.id)
        return TaskResponse.model_validate(result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{project_id}/tasks/{task_id}", response_model=TaskDetailResponse)
def get_task(
    project_id: int,
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TaskDetailResponse:
    """タスクの詳細を取得"""
    service = TaskService(db)
    task = service.get_task(task_id)

    if not task or task.project_id != project_id:
        raise HTTPException(status_code=404, detail="タスクが見つかりません")

    return TaskDetailResponse.model_validate(task)


@router.put("/{project_id}/tasks/{task_id}", response_model=TaskResponse)
def update_task(
    project_id: int,
    task_id: int,
    task_update: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TaskResponse:
    """タスクを更新"""
    service = TaskService(db)

    # タスクの存在確認
    task = service.get_task(task_id)
    if not task or task.project_id != project_id:
        raise HTTPException(status_code=404, detail="タスクが見つかりません")

    try:
        result = service.update_task(task_id, task_update)
        return TaskResponse.model_validate(result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{project_id}/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    project_id: int,
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """タスクを削除"""
    service = TaskService(db)

    # タスクの存在確認
    task = service.get_task(task_id)
    if not task or task.project_id != project_id:
        raise HTTPException(status_code=404, detail="タスクが見つかりません")

    if not service.delete_task(task_id):
        raise HTTPException(status_code=400, detail="タスクの削除に失敗しました")


@router.get("/{project_id}/tasks", response_model=TaskTreeResponse)
def get_task_tree(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TaskTreeResponse:
    """プロジェクトのタスクツリーを取得"""
    service = TaskService(db)

    # プロジェクトの存在確認
    project_service = ProjectService(db)
    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="プロジェクトが見つかりません")

    tasks = service.get_task_tree(project_id)
    return TaskTreeResponse(tasks=tasks)


# タスク進捗更新


@router.put("/{project_id}/tasks/{task_id}/progress", response_model=TaskResponse)
def update_task_progress(
    project_id: int,
    task_id: int,
    progress: ProgressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TaskResponse:
    """タスクの進捗を更新"""
    service = TaskService(db)

    # タスクの存在確認
    task = service.get_task(task_id)
    if not task or task.project_id != project_id:
        raise HTTPException(status_code=404, detail="タスクが見つかりません")

    try:
        result = service.update_progress(
            task_id=task_id,
            progress_percentage=progress.progress_percentage,
            actual_hours=progress.actual_hours,
            comment=progress.comment,
            user_id=current_user.id,
        )
        return TaskResponse.model_validate(result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# タスク依存関係


@router.post("/{project_id}/tasks/{task_id}/dependencies")
def create_task_dependency(
    project_id: int,
    task_id: int,
    dependency: TaskDependencyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """タスク依存関係を作成"""
    service = TaskService(db)

    # タスクの存在確認
    task = service.get_task(task_id)
    if not task or task.project_id != project_id:
        raise HTTPException(status_code=404, detail="タスクが見つかりません")

    try:
        service.create_dependency(
            predecessor_id=dependency.predecessor_id,
            successor_id=task_id,
            dependency_type=dependency.dependency_type,
            lag_days=dependency.lag_days,
        )
        return {"message": "依存関係を作成しました"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ガントチャート


@router.get("/{project_id}/gantt", response_model=GanttChartResponse)
def get_gantt_chart(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> GanttChartResponse:
    """ガントチャートデータを取得"""
    task_service = TaskService(db)

    # プロジェクトの存在確認
    project_service = ProjectService(db)
    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="プロジェクトが見つかりません")

    # タスクとクリティカルパスを取得
    tasks = task_service.get_task_tree(project_id)
    critical_path = task_service.calculate_critical_path(project_id)

    # ガントチャート用にデータを変換
    gantt_tasks = []
    gantt_dependencies = []

    def process_task(task, level=0) -> dict:
        gantt_task = {
            "id": task.id,
            "name": task.name,
            "start_date": task.start_date,
            "end_date": task.end_date,
            "progress": task.progress_percentage,
            "level": level,
            "is_milestone": False,
            "resources": [r.user.name for r in task.resources],
        }
        gantt_tasks.append(gantt_task)

        # 依存関係を追加
        for dep in task.dependencies_as_successor:
            gantt_dependencies.append(
                {
                    "source": dep.predecessor_id,
                    "target": dep.successor_id,
                    "type": dep.dependency_type,
                }
            )

        # サブタスクを処理
        if hasattr(task, "sub_tasks"):
            for sub_task in task.sub_tasks:
                process_task(sub_task, level + 1)

    for task in tasks:
        process_task(task)

    return GanttChartResponse(
        tasks=gantt_tasks,
        dependencies=gantt_dependencies,
        critical_path=critical_path,
    )


# リソース管理


@router.get("/{project_id}/resources", response_model=ResourceListResponse)
def get_project_resources(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ResourceListResponse:
    """プロジェクトのリソース一覧を取得"""
    project_service = ProjectService(db)
    project = project_service.get_project(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="プロジェクトが見つかりません")

    # プロジェクトメンバーをリソースとして返す
    resources = []
    for member in project.members:
        if member.is_active:
            resources.append(
                {
                    "id": member.user.id,
                    "name": member.user.full_name,
                    "email": member.user.email,
                    "skills": [],  # TODO: スキルマスタ実装後に対応
                    "max_allocation": 100,
                    "current_allocation": member.allocation_percentage,
                }
            )

    return ResourceListResponse(items=resources, total=len(resources))


@router.post("/{project_id}/tasks/{task_id}/resources")
def assign_resource_to_task(
    project_id: int,
    task_id: int,
    assignment: ResourceAssignment,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """タスクにリソースを割り当て"""
    resource_service = ResourceService(db)

    # タスクの存在確認
    task_service = TaskService(db)
    task = task_service.get_task(task_id)
    if not task or task.project_id != project_id:
        raise HTTPException(status_code=404, detail="タスクが見つかりません")

    try:
        resource_service.assign_resource(
            task_id=task_id,
            user_id=assignment.resource_id,
            allocation_percentage=assignment.allocation_percentage,
            start_date=assignment.start_date,
            end_date=assignment.end_date,
            planned_hours=assignment.planned_hours,
        )
        return {"message": "リソースを割り当てました"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/resources/{user_id}/utilization", response_model=UtilizationResponse)
def get_resource_utilization(
    user_id: int,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> UtilizationResponse:
    """リソースの稼働率を取得"""
    service = ResourceService(db)
    utilization = service.calculate_utilization(user_id, start_date, end_date)

    return UtilizationResponse(
        resource_id=user_id,
        period={"start_date": start_date, "end_date": end_date},
        daily_utilization=utilization["daily_utilization"],
        average_utilization=utilization["average_utilization"],
        peak_utilization=utilization["peak_utilization"],
        overallocated_days=utilization["overallocated_days"],
    )


# マイルストーン


@router.post("/{project_id}/milestones", response_model=MilestoneResponse)
def create_milestone(
    project_id: int,
    milestone: MilestoneCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> MilestoneResponse:
    """マイルストーンを作成"""
    service = MilestoneService(db)

    # プロジェクトの存在確認
    project_service = ProjectService(db)
    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="プロジェクトが見つかりません")

    try:
        result = service.create_milestone(project_id, milestone)
        return MilestoneResponse.model_validate(result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{project_id}/milestones", response_model=MilestoneListResponse)
def get_project_milestones(
    project_id: int,
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> MilestoneListResponse:
    """プロジェクトのマイルストーン一覧を取得"""
    service = MilestoneService(db)

    # プロジェクトの存在確認
    project_service = ProjectService(db)
    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="プロジェクトが見つかりません")

    milestones = service.get_project_milestones(project_id, status)
    return MilestoneListResponse(
        items=[MilestoneResponse.model_validate(m) for m in milestones],
        total=len(milestones),
    )


# 予算管理


@router.get("/{project_id}/budget", response_model=BudgetResponse)
def get_project_budget(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> BudgetResponse:
    """プロジェクトの予算情報を取得"""
    budget_service = BudgetService(db)
    project_service = ProjectService(db)

    # プロジェクトの存在確認
    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="プロジェクトが見つかりません")

    # 予算情報を取得
    budget = project.budget_info
    if not budget:
        # 予算情報がない場合はデフォルト値を返す
        return BudgetResponse(
            budget_amount=Decimal("0"),
            estimated_cost=Decimal("0"),
            actual_cost=Decimal("0"),
            cost_breakdown={
                "labor": {"planned": 0, "actual": 0, "variance": 0},
                "outsourcing": {"planned": 0, "actual": 0, "variance": 0},
                "expense": {"planned": 0, "actual": 0, "variance": 0},
            },
            consumption_rate=0.0,
            forecast_at_completion=Decimal("0"),
            variance=Decimal("0"),
            revenue=Decimal("0"),
            profit=Decimal("0"),
            profit_rate=0.0,
        )

    # 差異を計算
    variance_info = budget_service.calculate_budget_variance(project_id)
    profitability = budget_service.calculate_project_profitability(project_id)

    return BudgetResponse(
        budget_amount=budget.budget_amount,
        estimated_cost=budget.estimated_cost,
        actual_cost=budget.actual_cost,
        cost_breakdown={
            "labor": {
                "planned": budget.labor_cost,
                "actual": budget.labor_cost,
                "variance": 0,
            },
            "outsourcing": {
                "planned": budget.outsourcing_cost,
                "actual": budget.outsourcing_cost,
                "variance": 0,
            },
            "expense": {
                "planned": budget.expense_cost,
                "actual": budget.expense_cost,
                "variance": 0,
            },
        },
        consumption_rate=float(budget.actual_cost / budget.budget_amount * 100)
        if budget.budget_amount > 0
        else 0.0,
        forecast_at_completion=budget.estimated_cost,
        variance=variance_info["budget_variance"],
        revenue=profitability["revenue"],
        profit=profitability["profit"],
        profit_rate=profitability["profit_rate"],
    )


@router.put("/{project_id}/budget", response_model=BudgetResponse)
def update_project_budget(
    project_id: int,
    budget_update: BudgetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> BudgetResponse:
    """プロジェクトの予算を更新"""
    budget_service = BudgetService(db)

    # プロジェクトの存在確認
    project_service = ProjectService(db)
    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="プロジェクトが見つかりません")

    try:
        # 予算を更新
        budget_service.update_budget(
            project_id=project_id,
            budget_amount=None,  # プロジェクト側で管理
            estimated_cost=budget_update.estimated_cost,
            actual_cost=budget_update.actual_cost,
        )

        # コスト内訳を更新
        if any(
            [
                budget_update.labor_cost,
                budget_update.outsourcing_cost,
                budget_update.expense_cost,
            ]
        ):
            budget_service.update_cost_breakdown(
                project_id=project_id,
                labor_cost=budget_update.labor_cost,
                outsourcing_cost=budget_update.outsourcing_cost,
                expense_cost=budget_update.expense_cost,
            )

        # 更新後の情報を返す
        return get_project_budget(project_id, db, current_user)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# レポート


@router.get("/{project_id}/reports/progress", response_model=ProgressReportResponse)
def get_progress_report(
    project_id: int,
    report_date: date = Query(default=date.today()),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ProgressReportResponse:
    """プロジェクトの進捗レポートを取得"""
    project_service = ProjectService(db)
    milestone_service = MilestoneService(db)

    # プロジェクトの存在確認
    project = project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="プロジェクトが見つかりません")

    # 進捗情報を収集
    overall_progress = project_service.calculate_project_progress(project_id)

    # マイルストーンのステータス集計
    milestones = milestone_service.get_project_milestones(project_id)
    milestone_status = {
        "pending": len([m for m in milestones if m.status == "pending"]),
        "achieved": len([m for m in milestones if m.status == "achieved"]),
        "delayed": len([m for m in milestones if m.status == "delayed"]),
        "cancelled": len([m for m in milestones if m.status == "cancelled"]),
    }

    # タスクのステータス集計
    tasks = project.tasks
    task_status = {
        "not_started": len([t for t in tasks if t.status == "not_started"]),
        "in_progress": len([t for t in tasks if t.status == "in_progress"]),
        "completed": len([t for t in tasks if t.status == "completed"]),
        "on_hold": len([t for t in tasks if t.status == "on_hold"]),
    }

    # 予算情報
    budget_summary = project_service.get_budget_summary(project_id)

    # リスク情報（簡略版）
    risks = []
    if (
        overall_progress < 50
        and report_date
        > project.start_date + (project.end_date - project.start_date) / 2
    ):
        risks.append(
            {
                "type": "schedule",
                "description": "進捗が予定より遅れています",
                "impact": "high",
            }
        )

    if budget_summary["consumption_rate"] > 80 and overall_progress < 80:
        risks.append(
            {
                "type": "budget",
                "description": "予算消化率が進捗率を上回っています",
                "impact": "medium",
            }
        )

    return ProgressReportResponse(
        project={
            "id": project.id,
            "code": project.code,
            "name": project.name,
            "status": project.status,
        },
        report_date=report_date,
        overall_progress=overall_progress,
        milestone_status=milestone_status,
        task_status=task_status,
        budget_status=budget_summary,
        risks=risks,
    )


# 繰り返しプロジェクト


@router.post("/recurring", response_model=RecurringProjectResponse)
def create_recurring_projects(
    recurring_project: RecurringProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> RecurringProjectResponse:
    """繰り返しプロジェクトを作成"""
    service = ProjectService(db)

    # 現在のユーザーの組織IDを取得
    organization_id = current_user.organization_memberships[0].organization_id

    try:
        projects = service.create_recurring_projects(
            recurring_project, current_user.id, organization_id
        )

        # レスポンスを構築
        master_project = projects[0] if projects else None
        total_budget = sum(p.budget for p in projects)

        return RecurringProjectResponse(
            master_project=ProjectResponse.model_validate(master_project)
            if master_project
            else None,
            generated_projects=[ProjectResponse.model_validate(p) for p in projects],
            total_budget=total_budget,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
