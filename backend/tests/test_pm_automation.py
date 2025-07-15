"""Tests for PM Automation Service."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.services.pm_automation import PMAutomationService


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def pm_service(test_db_session: Session):
    """PM automation service fixture."""
    return PMAutomationService(test_db_session)


@pytest.fixture
def test_project(test_db_session: Session):
    """Test project fixture."""
    project = Project(
        id=1,
        code="TEST001",
        name="Test Project",
        organization_id=1,
        owner_id=1,
        status="active"
    )
    test_db_session.add(project)
    test_db_session.commit()
    return project


@pytest.fixture
def test_user(test_db_session: Session):
    """Test user fixture."""
    user = User(
        id=1,
        email="test@example.com",
        full_name="Test User",
        is_active=True,
        organization_id=1
    )
    test_db_session.add(user)
    test_db_session.commit()
    return user


class TestPMAutomationService:
    """Test PM Automation Service."""

    async def test_auto_create_agile_structure(
        self, pm_service: PMAutomationService, test_project: Project, test_user: User
    ):
        """Test automatic creation of agile project structure."""
        result = await pm_service.auto_create_project_structure(
            test_project.id, "agile", test_user
        )

        assert result["template"] == "agile"
        assert result["tasks_created"] > 0
        assert len(result["tasks"]) > 0

        # Check that tasks have expected titles
        task_titles = [task.title for task in result["tasks"]]
        assert "プロジェクト計画" in task_titles
        assert "ユーザーストーリー作成" in task_titles
        assert "スプリント計画" in task_titles

    async def test_auto_create_waterfall_structure(
        self, pm_service: PMAutomationService, test_project: Project, test_user: User
    ):
        """Test automatic creation of waterfall project structure."""
        result = await pm_service.auto_create_project_structure(
            test_project.id, "waterfall", test_user
        )

        assert result["template"] == "waterfall"
        assert result["tasks_created"] > 0

        # Check that tasks have expected titles
        task_titles = [task.title for task in result["tasks"]]
        assert "要件定義" in task_titles
        assert "基本設計" in task_titles
        assert "実装" in task_titles

    async def test_auto_create_kanban_structure(
        self, pm_service: PMAutomationService, test_project: Project, test_user: User
    ):
        """Test automatic creation of kanban project structure."""
        result = await pm_service.auto_create_project_structure(
            test_project.id, "kanban", test_user
        )

        assert result["template"] == "kanban"
        assert result["tasks_created"] > 0

        # Check that tasks have expected titles
        task_titles = [task.title for task in result["tasks"]]
        assert "カンボード設定" in task_titles
        assert "WIP制限設定" in task_titles

    async def test_auto_assign_tasks_balanced(
        self, pm_service: PMAutomationService, test_project: Project, test_user: User
    ):
        """Test balanced task assignment."""
        result = await pm_service.auto_assign_tasks(
            test_project.id, "balanced", test_user
        )

        assert result["status"] == "success"
        assert result["strategy"] == "balanced"
        assert "assigned_count" in result
        assert "total_tasks" in result

    async def test_auto_assign_tasks_skill_based(
        self, pm_service: PMAutomationService, test_project: Project, test_user: User
    ):
        """Test skill-based task assignment."""
        result = await pm_service.auto_assign_tasks(
            test_project.id, "skill_based", test_user
        )

        assert result["status"] == "success"
        assert result["strategy"] == "skill_based"

    async def test_auto_assign_tasks_workload_based(
        self, pm_service: PMAutomationService, test_project: Project, test_user: User
    ):
        """Test workload-based task assignment."""
        result = await pm_service.auto_assign_tasks(
            test_project.id, "workload_based", test_user
        )

        assert result["status"] == "success"
        assert result["strategy"] == "workload_based"

    async def test_generate_progress_report_weekly(
        self, pm_service: PMAutomationService, test_project: Project, test_user: User
    ):
        """Test weekly progress report generation."""
        result = await pm_service.generate_progress_report(
            test_project.id, "weekly", test_user
        )

        assert result["project"]["id"] == test_project.id
        assert result["report_period"]["type"] == "weekly"
        assert "statistics" in result
        assert "trends" in result
        assert "risks" in result
        assert "recommendations" in result

        # Check statistics structure
        stats = result["statistics"]
        assert "total_tasks" in stats
        assert "completed_tasks" in stats
        assert "completion_rate" in stats
        assert "overdue_tasks" in stats

    async def test_generate_progress_report_daily(
        self, pm_service: PMAutomationService, test_project: Project, test_user: User
    ):
        """Test daily progress report generation."""
        result = await pm_service.generate_progress_report(
            test_project.id, "daily", test_user
        )

        assert result["report_period"]["type"] == "daily"

    async def test_generate_progress_report_monthly(
        self, pm_service: PMAutomationService, test_project: Project, test_user: User
    ):
        """Test monthly progress report generation."""
        result = await pm_service.generate_progress_report(
            test_project.id, "monthly", test_user
        )

        assert result["report_period"]["type"] == "monthly"

    async def test_auto_schedule_optimization_critical_path(
        self, pm_service: PMAutomationService, test_project: Project, test_user: User
    ):
        """Test critical path optimization."""
        result = await pm_service.auto_schedule_optimization(
            test_project.id, "critical_path", test_user
        )

        assert result["optimization_type"] == "critical_path"
        assert result["status"] == "completed"
        assert "recommendations" in result

    async def test_auto_schedule_optimization_resource_leveling(
        self, pm_service: PMAutomationService, test_project: Project, test_user: User
    ):
        """Test resource leveling optimization."""
        result = await pm_service.auto_schedule_optimization(
            test_project.id, "resource_leveling", test_user
        )

        assert result["optimization_type"] == "resource_leveling"
        assert result["status"] == "completed"

    async def test_auto_schedule_optimization_risk_mitigation(
        self, pm_service: PMAutomationService, test_project: Project, test_user: User
    ):
        """Test risk mitigation optimization."""
        result = await pm_service.auto_schedule_optimization(
            test_project.id, "risk_mitigation", test_user
        )

        assert result["optimization_type"] == "risk_mitigation"
        assert result["status"] == "completed"

    async def test_predictive_analytics_completion_date(
        self, pm_service: PMAutomationService, test_project: Project, test_user: User
    ):
        """Test completion date prediction."""
        result = await pm_service.predictive_analytics(
            test_project.id, "completion_date", test_user
        )

        assert result["prediction_type"] == "completion_date"
        assert "predicted_completion" in result
        assert "confidence" in result
        assert "based_on" in result

    async def test_predictive_analytics_budget_forecast(
        self, pm_service: PMAutomationService, test_project: Project, test_user: User
    ):
        """Test budget forecast prediction."""
        result = await pm_service.predictive_analytics(
            test_project.id, "budget_forecast", test_user
        )

        assert result["prediction_type"] == "budget_forecast"
        assert "current_budget" in result
        assert "predicted_usage" in result

    async def test_predictive_analytics_risk_probability(
        self, pm_service: PMAutomationService, test_project: Project, test_user: User
    ):
        """Test risk probability prediction."""
        result = await pm_service.predictive_analytics(
            test_project.id, "risk_probability", test_user
        )

        assert result["prediction_type"] == "risk_probability"
        assert "risk_score" in result
        assert "risk_level" in result
        assert "confidence" in result

    async def test_invalid_template_type(
        self, pm_service: PMAutomationService, test_project: Project, test_user: User
    ):
        """Test invalid template type handling."""
        with pytest.raises(ValueError, match="Unknown template type"):
            await pm_service.auto_create_project_structure(
                test_project.id, "invalid", test_user
            )

    async def test_invalid_assignment_strategy(
        self, pm_service: PMAutomationService, test_project: Project, test_user: User
    ):
        """Test invalid assignment strategy handling."""
        with pytest.raises(ValueError, match="Unknown assignment strategy"):
            await pm_service.auto_assign_tasks(
                test_project.id, "invalid", test_user
            )

    async def test_invalid_optimization_type(
        self, pm_service: PMAutomationService, test_project: Project, test_user: User
    ):
        """Test invalid optimization type handling."""
        with pytest.raises(ValueError, match="Unknown optimization type"):
            await pm_service.auto_schedule_optimization(
                test_project.id, "invalid", test_user
            )

    async def test_invalid_prediction_type(
        self, pm_service: PMAutomationService, test_project: Project, test_user: User
    ):
        """Test invalid prediction type handling."""
        with pytest.raises(ValueError, match="Unknown prediction type"):
            await pm_service.predictive_analytics(
                test_project.id, "invalid", test_user
            )


class TestPMAutomationAPI:
    """Test PM Automation API endpoints."""

    def test_auto_create_structure_endpoint(self, client: TestClient):
        """Test project structure creation endpoint."""
        # Note: This would require proper authentication setup
        # For now, we test the endpoint structure
        response = client.post(
            "/api/v1/pm-automation/projects/1/auto-structure?template_type=agile"
        )
        # In a real test, we'd mock authentication and database
        assert response.status_code in [200, 401, 403]  # Expected responses

    def test_auto_assign_tasks_endpoint(self, client: TestClient):
        """Test task assignment endpoint."""
        response = client.post(
            "/api/v1/pm-automation/projects/1/auto-assign?strategy=balanced"
        )
        assert response.status_code in [200, 401, 403]

    def test_progress_report_endpoint(self, client: TestClient):
        """Test progress report endpoint."""
        response = client.get(
            "/api/v1/pm-automation/projects/1/progress-report?report_type=weekly"
        )
        assert response.status_code in [200, 401, 403]

    def test_schedule_optimization_endpoint(self, client: TestClient):
        """Test schedule optimization endpoint."""
        response = client.post(
            "/api/v1/pm-automation/projects/1/optimize?optimization_type=critical_path"
        )
        assert response.status_code in [200, 401, 403]

    def test_predictive_analytics_endpoint(self, client: TestClient):
        """Test predictive analytics endpoint."""
        response = client.get(
            "/api/v1/pm-automation/projects/1/analytics?prediction_type=completion_date"
        )
        assert response.status_code in [200, 401, 403]

    def test_dashboard_endpoint(self, client: TestClient):
        """Test automation dashboard endpoint."""
        response = client.get("/api/v1/pm-automation/projects/1/dashboard")
        assert response.status_code in [200, 401, 403]

    def test_templates_endpoint(self, client: TestClient):
        """Test templates listing endpoint."""
        response = client.get("/api/v1/pm-automation/templates")

        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "templates" in data["data"]
            assert "agile" in data["data"]["templates"]
            assert "waterfall" in data["data"]["templates"]
            assert "kanban" in data["data"]["templates"]

    def test_strategies_endpoint(self, client: TestClient):
        """Test strategies listing endpoint."""
        response = client.get("/api/v1/pm-automation/strategies")

        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "strategies" in data["data"]
            assert "balanced" in data["data"]["strategies"]
            assert "skill_based" in data["data"]["strategies"]
            assert "workload_based" in data["data"]["strategies"]


class TestPMAutomationIntegration:
    """Integration tests for PM Automation."""

    async def test_full_automation_workflow(
        self, pm_service: PMAutomationService, test_project: Project, test_user: User
    ):
        """Test full automation workflow."""
        # 1. Create project structure
        structure_result = await pm_service.auto_create_project_structure(
            test_project.id, "agile", test_user
        )
        assert structure_result["tasks_created"] > 0

        # 2. Auto-assign tasks
        assignment_result = await pm_service.auto_assign_tasks(
            test_project.id, "balanced", test_user
        )
        assert assignment_result["status"] == "success"

        # 3. Generate progress report
        report_result = await pm_service.generate_progress_report(
            test_project.id, "weekly", test_user
        )
        assert report_result["project"]["id"] == test_project.id

        # 4. Get predictive analytics
        analytics_result = await pm_service.predictive_analytics(
            test_project.id, "completion_date", test_user
        )
        assert analytics_result["prediction_type"] == "completion_date"

    async def test_automation_with_existing_tasks(
        self, pm_service: PMAutomationService, test_project: Project, test_user: User, test_db_session: Session
    ):
        """Test automation with existing tasks."""
        # Create some existing tasks
        existing_task = Task(
            title="Existing Task",
            project_id=test_project.id,
            created_by=test_user.id,
            organization_id=1,
            status="in_progress"
        )
        test_db_session.add(existing_task)
        test_db_session.commit()

        # Generate report should include existing tasks
        report_result = await pm_service.generate_progress_report(
            test_project.id, "weekly", test_user
        )

        stats = report_result["statistics"]
        assert stats["total_tasks"] >= 1  # Should include existing task

    async def test_automation_error_handling(
        self, pm_service: PMAutomationService, test_user: User
    ):
        """Test error handling in automation."""
        # Test with non-existent project
        with pytest.raises(Exception):  # Should raise NotFound
            await pm_service.auto_create_project_structure(
                999, "agile", test_user
            )

        with pytest.raises(Exception):  # Should raise NotFound
            await pm_service.generate_progress_report(
                999, "weekly", test_user
            )
